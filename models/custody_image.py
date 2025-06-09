from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CustodyImage(models.Model):
    """Model to store custody-related images for before/after documentation"""

    _name = 'custody.image'
    _description = 'Custody Images'
    _order = 'image_type, sequence, create_date'
    _rec_name = 'display_name'

    # Basic Information
    custody_id = fields.Many2one(
        'hr.custody',
        string='Custody Record',
        required=True,
        ondelete='cascade',
        help='Related custody record'
    )

    image_type = fields.Selection([
        ('before', 'Before Handover'),
        ('after', 'After Return'),
        ('damage', 'Damage Documentation')
    ],
        string='Image Type',
        required=True,
        help='Type of documentation photo'
    )

    # Image Data
    image = fields.Image(
        string='Image',
        max_width=1920,
        max_height=1920,
        help='Equipment condition photo (max 5MB, resized to 1920x1920px)'
    )

    # Description and Notes
    description = fields.Char(
        string='Description',
        help='Brief description of the photo or notes about condition'
    )

    notes = fields.Text(
        string='Detailed Notes',
        help='Detailed notes about equipment condition or any issues found'
    )

    # Sequence and Organization
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of photos in the documentation'
    )

    # Audit Trail
    taken_by_id = fields.Many2one(
        'res.users',
        string='Taken By',
        default=lambda self: self.env.user,
        readonly=True,
        help='User who uploaded this photo'
    )

    taken_date = fields.Datetime(
        string='Taken Date',
        default=fields.Datetime.now,
        readonly=True,
        help='When this photo was uploaded'
    )

    # Location and Context
    location_notes = fields.Char(
        string='Location Notes',
        help='Where the photo was taken (e.g., "IT Room", "Teacher Office")'
    )

    # Related Information
    employee_id = fields.Many2one(
        related='custody_id.employee_id',
        string='Employee',
        readonly=True,
        store=True,
        help='Employee associated with this custody'
    )

    property_id = fields.Many2one(
        related='custody_id.custody_property_id',
        string='Property',
        readonly=True,
        store=True,
        help='Property shown in this photo'
    )

    company_id = fields.Many2one(
        related='custody_id.company_id',
        string='Company',
        readonly=True,
        store=True,
        help='Company associated with this record'
    )

    # Computed Fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help='Display name for this image record'
    )

    file_size_kb = fields.Float(
        string='File Size (KB)',
        compute='_compute_file_size',
        help='Approximate file size in KB'
    )

    @api.depends('custody_id', 'image_type', 'sequence', 'description')
    def _compute_display_name(self):
        """Compute display name for image records"""
        for record in self:
            if record.custody_id and record.image_type:
                type_name = dict(record._fields['image_type'].selection).get(record.image_type, '')
                base_name = f"{record.custody_id.name} - {type_name}"

                if record.description:
                    base_name += f" ({record.description})"
                elif record.sequence > 1:
                    base_name += f" #{record.sequence}"

                record.display_name = base_name
            else:
                record.display_name = _('New Image')

    @api.depends('image')
    def _compute_file_size(self):
        """Compute approximate file size"""
        for record in self:
            if record.image:
                # Rough estimation: base64 is ~33% larger than binary
                base64_size = len(record.image) if record.image else 0
                estimated_size = (base64_size * 0.75) / 1024  # Convert to KB
                record.file_size_kb = round(estimated_size, 2)
            else:
                record.file_size_kb = 0.0

    @api.constrains('image')
    def _check_image_size(self):
        """Validate image file size (max 5MB)"""
        max_size_mb = 5
        max_size_bytes = max_size_mb * 1024 * 1024

        for record in self:
            if record.image:
                # Rough estimation of file size from base64
                base64_size = len(record.image)
                estimated_size = base64_size * 0.75  # base64 is ~33% larger

                if estimated_size > max_size_bytes:
                    raise ValidationError(
                        _('Image file size exceeds the maximum limit of %d MB. '
                          'Please compress the image or choose a smaller file.') % max_size_mb
                    )

    @api.constrains('custody_id', 'image_type')
    def _check_custody_state(self):
        """Validate that images are only added at appropriate custody states"""
        for record in self:
            if record.custody_id:
                custody_state = record.custody_id.state

                # ✅ FIXED: Before images can be added when custody is to_approve, approved or returned
                if record.image_type == 'before' and custody_state not in ['to_approve', 'approved', 'returned']:
                    raise ValidationError(
                        _('Before images can only be added when custody is waiting for approval or later.')
                    )

                # After images: only when custody is approved or returned
                if record.image_type == 'after' and custody_state not in ['approved', 'returned']:
                    raise ValidationError(
                        _('After images can only be added when custody is approved or being returned.')
                    )

    def name_get(self):
        """Enhanced name display"""
        result = []
        for record in self:
            if record.display_name:
                name = record.display_name
            else:
                name = f"Image #{record.id}"
            result.append((record.id, name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced search functionality"""
        if args is None:
            args = []

        if name:
            domain = [
                '|', '|', '|', '|',
                ('description', operator, name),
                ('notes', operator, name),
                ('custody_id.name', operator, name),
                ('employee_id.name', operator, name),
                ('property_id.name', operator, name)
            ]
            records = self.search(domain + args, limit=limit)
            return records.name_get()

        return super(CustodyImage, self).name_search(name, args, operator, limit)

    def action_view_full_image(self):
        """Action to view full-size image"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/image/custody.image/{self.id}/image',
            'target': 'new',
        }

    def file_size_info(self):
        """Action for file size button - show info"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('File Information'),
                'message': _('File size: %s KB') % self.file_size_kb,
                'type': 'info'
            }
        }

    @api.model
    def get_before_after_comparison(self, custody_id):
        """Get before and after images for comparison"""
        before_images = self.search([
            ('custody_id', '=', custody_id),
            ('image_type', '=', 'before')
        ], order='sequence, create_date')

        after_images = self.search([
            ('custody_id', '=', custody_id),
            ('image_type', '=', 'after')
        ], order='sequence, create_date')

        return {
            'before_images': before_images,
            'after_images': after_images,
            'total_before': len(before_images),
            'total_after': len(after_images)
        }
