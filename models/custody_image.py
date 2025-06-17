from odoo import api, fields, models, _


class CustodyImage(models.Model):
    """Model for storing multiple images for custody records."""
    _name = 'custody.image'
    _description = 'Custody Images'
    _order = 'sequence, id'

    name = fields.Char(
        string='Title',
        help='Title or brief description of this image'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Determines the order of images'
    )
    
    image = fields.Image(
        string='Image',
        max_width=1920,
        max_height=1920,
        attachment=True,
        required=True,
        help='The image file'
    )
    
    image_date = fields.Datetime(
        string='Image Date',
        default=fields.Datetime.now,
        help='When this image was taken'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Additional notes or description for this image'
    )
    
    custody_id = fields.Many2one(
        'hr.custody',
        string='Custody Record',
        required=True,
        ondelete='cascade',
        help='The custody record this image belongs to'
    )
    
    image_type = fields.Selection([
        ('checkout', 'Checkout'),
        ('return', 'Return'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other')
    ], 
        string='Image Type',
        required=True,
        default='other',
        help='Type of image - used for filtering and organizing'
    )
    
    uploaded_by_id = fields.Many2one(
        'res.users',
        string='Uploaded By',
        default=lambda self: self.env.user.id,
        readonly=True,
        help='User who uploaded this image'
    ) 