# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You can modify it under the terms of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CustodyBeforeWizard(models.TransientModel):
    """Wizard for taking before photos and approving custody"""

    _name = 'custody.before.wizard'
    _description = 'Take Before Photos Wizard'

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
        help='Property being handed over'
    )

    employee_name = fields.Char(
        string='Employee',
        readonly=True,
        help='Employee receiving the property'
    )

    # Current State Info
    current_state = fields.Selection(
        related='custody_id.state',
        string='Current State',
        readonly=True
    )

    existing_before_count = fields.Integer(
        string='Existing Before Photos',
        compute='_compute_existing_images',
        help='Number of existing before photos'
    )

    # Instructions and Notes
    instructions = fields.Html(
        string='Instructions',
        default="""
        <h4>📸 Before Handover Photo Documentation</h4>
        <p><strong>Please take photos showing:</strong></p>
        <ul>
            <li>Overall condition of the equipment</li>
            <li>Any existing damage or wear</li>
            <li>Serial numbers or asset tags (if visible)</li>
            <li>All included accessories</li>
        </ul>
        <p><strong>Tips:</strong></p>
        <ul>
            <li>Use good lighting for clear photos</li>
            <li>Take multiple angles if needed</li>
            <li>Maximum 15 photos, 5MB each</li>
        </ul>
        """,
        readonly=True
    )

    location_notes = fields.Char(
        string='Location',
        default='IT Office',
        help='Where these photos are being taken'
    )

    general_notes = fields.Text(
        string='General Notes',
        help='Any general notes about the equipment condition'
    )

    # Dynamic Image Upload Lines
    image_line_ids = fields.One2many(
        'custody.before.wizard.line',
        'wizard_id',
        string='Photos to Upload'
    )

    # Validation and Controls
    auto_approve = fields.Boolean(
        string='Auto-approve after saving photos',
        default=True,
        help='Automatically approve the custody request after saving photos'
    )

    total_images = fields.Integer(
        string='Total Images',
        compute='_compute_total_images',
        help='Total number of images to be uploaded'
    )

    # Computed Methods
    @api.depends('custody_id')
    def _compute_existing_images(self):
        """Compute existing before images count"""
        for wizard in self:
            if wizard.custody_id:
                wizard.existing_before_count = len(wizard.custody_id.before_image_ids)
            else:
                wizard.existing_before_count = 0

    @api.depends('image_line_ids')
    def _compute_total_images(self):
        """Compute total number of images"""
        for wizard in self:
            wizard.total_images = len([line for line in wizard.image_line_ids if line.image])

    # Default Methods
    @api.model
    def default_get(self, fields_list):
        """Set default values"""
        result = super(CustodyBeforeWizard, self).default_get(fields_list)

        custody_id = self.env.context.get('default_custody_id')
        if custody_id:
            custody = self.env['hr.custody'].browse(custody_id)
            result.update({
                'custody_id': custody_id,
                'property_name': custody.custody_property_id.name,
                'employee_name': custody.employee_id.name,
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
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_remove_empty_slots(self):
        """Remove empty image slots"""
        empty_lines = self.image_line_ids.filtered(lambda l: not l.image)
        empty_lines.unlink()

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    def action_save_photos_only(self):
        """Save photos without auto-approving"""
        self._save_images()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('%d before photos saved successfully') % self.total_images,
                'type': 'success'
            }
        }

    def action_save_and_approve(self):
        """Save photos and approve custody"""
        if not self.image_line_ids.filtered(lambda l: l.image):
            raise UserError(_('Please upload at least one photo before approving'))

        # Save images first
        self._save_images()

        # Then approve the custody
        try:
            self.custody_id.approve()
        except UserError as e:
            raise UserError(_('Failed to approve custody: %s') % str(e))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('✅ %d photos saved and custody approved!') % self.total_images,
                'type': 'success'
            }
        }

    def _save_images(self):
        """Save all uploaded images"""
        saved_count = 0

        for line in self.image_line_ids:
            if line.image:
                self.env['custody.image'].create({
                    'custody_id': self.custody_id.id,
                    'image_type': 'before',
                    'image': line.image,
                    'description': line.description or f'Before Photo #{line.sequence}',
                    'notes': line.notes,
                    'sequence': line.sequence,
                    'location_notes': self.location_notes,
                })
                saved_count += 1

        # Add general notes to custody if provided
        if self.general_notes:
            self.custody_id.message_post(
                body=_('📸 Before photos uploaded with notes: %s') % self.general_notes,
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


class CustodyBeforeWizardLine(models.TransientModel):
    """Individual image upload line for before photos wizard"""

    _name = 'custody.before.wizard.line'
    _description = 'Before Photos Upload Line'
    _order = 'sequence'

    wizard_id = fields.Many2one(
        'custody.before.wizard',
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
        help='Equipment photo (max 5MB)'
    )

    description = fields.Char(
        string='Description',
        help='Brief description of this photo'
    )

    notes = fields.Text(
        string='Notes',
        help='Detailed notes about what this photo shows'
    )

    # Computed display name
    display_name = fields.Char(
        string='Photo Name',
        compute='_compute_display_name'
    )

    @api.depends('sequence', 'description', 'image')
    def _compute_display_name(self):
        """Compute display name for photo line"""
        for line in self:
            if line.description:
                line.display_name = f"#{line.sequence}: {line.description}"
            elif line.image:
                line.display_name = f"Photo #{line.sequence}"
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
