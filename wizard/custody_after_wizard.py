from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CustodyAfterWizard(models.TransientModel):
    """Wizard for taking after photos and processing return"""

    _name = 'custody.after.wizard'
    _description = 'Take After Photos & Return Wizard'

    # Custody Information
    custody_id = fields.Many2one(
        'hr.custody',
        string='Custody Record',
        required=True,
        help='Related custody record'
    )

    property_name = fields.Char(
        string='Property',
        readonly=True,
        help='Property being returned'
    )

    employee_name = fields.Char(
        string='Employee',
        readonly=True,
        help='Employee returning the property'
    )

    # Comparison Information
    before_image_count = fields.Integer(
        string='Before Photos Count',
        readonly=True,
        help='Number of before photos for comparison'
    )

    existing_after_count = fields.Integer(
        string='Existing After Photos',
        compute='_compute_existing_images',
        help='Number of existing after photos'
    )

    # Return Assessment
    condition_assessment = fields.Selection([
        ('excellent', 'Excellent - No issues'),
        ('good', 'Good - Minor wear'),
        ('fair', 'Fair - Noticeable wear'),
        ('poor', 'Poor - Significant issues'),
        ('damaged', 'Damaged - Requires repair')
    ],
        string='Equipment Condition',
        required=True,
        default='good',
        help='Overall assessment of equipment condition'
    )

    return_notes = fields.Text(
        string='Return Condition Notes',
        required=True,
        help='Detailed notes about the equipment condition upon return'
    )

    damage_found = fields.Boolean(
        string='Damage Found',
        help='Check if any damage or issues were found'
    )

    damage_description = fields.Text(
        string='Damage Description',
        help='Detailed description of any damage found'
    )

    # Instructions
    instructions = fields.Html(
        string='Instructions',
        default="""
        <h4>📸 After Return Photo Documentation</h4>
        <p><strong>Please take photos showing:</strong></p>
        <ul>
            <li>Current condition of the equipment</li>
            <li>Any damage, wear, or issues</li>
            <li>All returned accessories</li>
            <li>Compare with before photos if possible</li>
        </ul>
        <p><strong>Important:</strong></p>
        <ul>
            <li>Document any differences from handover condition</li>
            <li>Focus on problem areas if damage found</li>
            <li>Include serial numbers for verification</li>
        </ul>
        """,
        readonly=True
    )

    location_notes = fields.Char(
        string='Return Location',
        default='IT Office',
        help='Where the equipment is being returned'
    )

    # Dynamic Image Upload Lines
    image_line_ids = fields.One2many(
        'custody.after.wizard.line',
        'wizard_id',
        string='Return Photos'
    )

    # Processing Options
    auto_return = fields.Boolean(
        string='Auto-process return after saving photos',
        default=True,
        help='Automatically process the return after saving photos'
    )

    total_images = fields.Integer(
        string='Total Images',
        compute='_compute_total_images',
        help='Total number of images to be uploaded'
    )

    # Computed Methods
    @api.depends('custody_id')
    def _compute_existing_images(self):
        """Compute existing after images count"""
        for wizard in self:
            if wizard.custody_id:
                wizard.existing_after_count = len(wizard.custody_id.after_image_ids)
            else:
                wizard.existing_after_count = 0

    @api.depends('image_line_ids')
    def _compute_total_images(self):
        """Compute total number of images"""
        for wizard in self:
            wizard.total_images = len([line for line in wizard.image_line_ids if line.image])

    # Onchange Methods
    @api.onchange('damage_found')
    def _onchange_damage_found(self):
        """Update condition assessment when damage is found"""
        if self.damage_found:
            if self.condition_assessment in ['excellent', 'good']:
                self.condition_assessment = 'fair'
        else:
            self.damage_description = ''

    @api.onchange('condition_assessment')
    def _onchange_condition_assessment(self):
        """Update damage found based on condition assessment"""
        if self.condition_assessment in ['poor', 'damaged']:
            self.damage_found = True
        elif self.condition_assessment in ['excellent', 'good']:
            self.damage_found = False

    # Default Methods
    @api.model
    def default_get(self, fields_list):
        """Set default values"""
        result = super(CustodyAfterWizard, self).default_get(fields_list)

        custody_id = self.env.context.get('default_custody_id')
        if custody_id:
            custody = self.env['hr.custody'].browse(custody_id)
            result.update({
                'custody_id': custody_id,
                'property_name': custody.custody_property_id.name,
                'employee_name': custody.employee_id.name,
                'before_image_count': len(custody.before_image_ids),
            })

            # Add 3 empty image lines by default
            result['image_line_ids'] = [(0, 0, {'sequence': i}) for i in range(1, 4)]

        return result

    # Action Methods
    def action_add_image_slot(self):
        """Add a new image upload slot"""
        max_images = 15
        current_count = len(self.image_line_ids)

        if current_count >= max_images:
            raise UserError(_('Maximum %d images allowed per session') % max_images)

        # Add new line
        self.image_line_ids = [(0, 0, {'sequence': current_count + 1})]

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'custody.before.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context,
        }

    def action_view_before_photos(self):
        """View before photos for comparison"""
        return {
            'name': _('📸 Before Photos - %s') % self.property_name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image',
            'view_mode': 'kanban',
            'domain': [
                ('custody_id', '=', self.custody_id.id),
                ('image_type', '=', 'before')
            ],
            'target': 'new',
        }

    def action_save_photos_only(self):
        """Save photos without auto-processing return"""
        self._save_images()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%d after photos saved successfully') % self.total_images,
                'type': 'success'
            }
        }

    def action_save_and_return(self):
        """Save photos and process return"""
        if not self.image_line_ids.filtered(lambda l: l.image):
            raise UserError(_('Please upload at least one photo before processing return'))

        if not self.return_notes.strip():
            raise UserError(_('Please provide return condition notes'))

        # Save images first
        self._save_images()

        # Then process the return
        try:
            self.custody_id.set_to_return()
        except UserError as e:
            raise UserError(_('Failed to process return: %s') % str(e))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('📦 %d photos saved and equipment returned!') % self.total_images,
                'type': 'success'
            }
        }

    def _save_images(self):
        """Save all uploaded images and assessment"""
        saved_count = 0

        for line in self.image_line_ids:
            if line.image:
                # Determine image type based on damage
                image_type = 'damage' if self.damage_found and line.is_damage_photo else 'after'

                self.env['custody.image'].create({
                    'custody_id': self.custody_id.id,
                    'image_type': image_type,
                    'image': line.image,
                    'description': line.description or f'After Photo #{line.sequence}',
                    'notes': line.notes,
                    'sequence': line.sequence,
                    'location_notes': self.location_notes,
                })
                saved_count += 1

        # Save return assessment to custody record
        assessment_text = dict(self._fields['condition_assessment'].selection)[self.condition_assessment]

        return_message = _(
            '📦 Equipment returned in %s condition. %s'
        ) % (assessment_text, self.return_notes)

        if self.damage_found and self.damage_description:
            return_message += _('\n⚠️ Damage reported: %s') % self.damage_description

        self.custody_id.message_post(
            body=return_message,
            message_type='comment'
        )

        return saved_count

    # Validation Methods
    @api.constrains('image_line_ids')
    def _check_image_limits(self):
        """Validate image upload limits"""
        max_images = 15

        for wizard in self:
            image_count = len([line for line in wizard.image_line_ids if line.image])

            if image_count > max_images:
                raise ValidationError(
                    _('Maximum %d images allowed. You have %d images.') % (max_images, image_count)
                )

    @api.constrains('return_notes')
    def _check_return_notes(self):
        """Validate return notes are provided"""
        for wizard in self:
            if not wizard.return_notes or not wizard.return_notes.strip():
                raise ValidationError(_('Return condition notes are required'))


class CustodyAfterWizardLine(models.TransientModel):
    """Individual image upload line for after photos wizard"""

    _name = 'custody.after.wizard.line'
    _description = 'After Photos Upload Line'
    _order = 'sequence'

    wizard_id = fields.Many2one(
        'custody.after.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=1,
        help='Order of this photo'
    )

    image = fields.Image(
        string='Photo',
        max_width=1920,
        max_height=1920,
        help='Equipment return photo (max 5MB)'
    )

    description = fields.Char(
        string='Description',
        help='Brief description of this photo'
    )

    notes = fields.Text(
        string='Notes',
        help='Detailed notes about what this photo shows'
    )

    is_damage_photo = fields.Boolean(
        string='Damage Documentation',
        help='Check if this photo documents damage or issues'
    )

    # Computed display name
    display_name = fields.Char(
        string='Photo Name',
        compute='_compute_display_name'
    )

    @api.depends('sequence', 'description', 'image', 'is_damage_photo')
    def _compute_display_name(self):
        """Compute display name for photo line"""
        for line in self:
            prefix = "⚠️ " if line.is_damage_photo else ""

            if line.description:
                line.display_name = f"{prefix}#{line.sequence}: {line.description}"
            elif line.image:
                base_name = "Damage Photo" if line.is_damage_photo else "Return Photo"
                line.display_name = f"{prefix}{base_name} #{line.sequence}"
            else:
                line.display_name = f"Empty slot #{line.sequence}"

    @api.constrains('image')
    def _check_image_size(self):
        """Validate individual image size"""
        max_size_mb = 5
        max_size_bytes = max_size_mb * 1024 * 1024

        for line in self:
            if line.image:
                # Rough estimation of file size from base64
                base64_size = len(line.image)
                estimated_size = base64_size * 0.75

                if estimated_size > max_size_bytes:
                    raise ValidationError(
                        _('Image #%d exceeds %dMB limit. Please compress or choose a smaller image.')
                        % (line.sequence, max_size_mb)
                    )
