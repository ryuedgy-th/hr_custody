import base64
from io import BytesIO

try:
    import PIL
    from PIL import Image
except ImportError:
    PIL = None

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
    
    # Add thumbnail for better performance
    image_128 = fields.Image(
        string='Thumbnail',
        related='image',
        max_width=128,
        max_height=128,
        store=True,
        help='Small-sized image used for thumbnails'
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
        ondelete='cascade',
        index=True,  # Add index for better performance
        help='The custody record this image belongs to'
    )
    
    inspection_id = fields.Many2one(
        'device.inspection',
        string='Inspection Record',
        ondelete='cascade',
        index=True,
        help='The inspection record this image belongs to'
    )
    
    image_type = fields.Selection([
        ('checkout', 'Checkout'),
        ('return', 'Return'),
        ('maintenance', 'Maintenance'),
        ('inspection', 'Inspection'),
        ('other', 'Other')
    ], 
        string='Image Type',
        required=True,
        default='other',
        index=True,  # Add index for better performance
        help='Type of image - used for filtering and organizing'
    )
    
    uploaded_by_id = fields.Many2one(
        'res.users',
        string='Uploaded By',
        default=lambda self: self.env.user.id,
        readonly=True,
        help='User who uploaded this image'
    )
    
    @api.constrains('custody_id', 'inspection_id')
    def _check_record_reference(self):
        """Ensure image belongs to either custody or inspection, not both"""
        for record in self:
            if not record.custody_id and not record.inspection_id:
                raise models.ValidationError(_("Image must belong to either a custody record or an inspection record."))
            if record.custody_id and record.inspection_id:
                raise models.ValidationError(_("Image cannot belong to both custody and inspection records."))
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to optimize images on creation"""
        # Resize large images to improve performance
        if PIL:
            for vals in vals_list:
                if vals.get('image') and isinstance(vals['image'], str):
                    try:
                        image_data = base64.b64decode(vals['image'])
                        img = Image.open(BytesIO(image_data))
                        
                        # Don't process if already reasonable size
                        if img.width <= 1920 and img.height <= 1920:
                            continue
                            
                        # Resize to max dimensions while preserving aspect ratio
                        img.thumbnail((1920, 1920), Image.LANCZOS)
                        
                        # Convert back to base64
                        buffer = BytesIO()
                        img.save(buffer, format=img.format or 'JPEG', quality=85)
                        vals['image'] = base64.b64encode(buffer.getvalue()).decode()
                    except Exception:
                        # If any error occurs, just use the original image
                        pass
                        
        return super().create(vals_list)
        
    def action_view_fullscreen(self):
        """Open the image in fullscreen viewer"""
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image',
            'view_mode': 'form',
            'res_id': self.id,
            'view_id': self.env.ref('hr_custody.custody_image_view_fullscreen').id,
            'target': 'new',
            'flags': {'mode': 'readonly'},
        }
        
    @api.model
    def get_custody_images(self, custody_id, image_type=None):
        """Get images for a specific custody record and optionally filter by image type"""
        domain = [('custody_id', '=', custody_id)]
        if image_type:
            domain.append(('image_type', '=', image_type))
            
        return self.search(domain)
        
    def open_image_viewer(self):
        """Open image in a larger viewer - used from kanban view"""
        self.ensure_one()
        
        # Prepare the context with custody filter and modal settings
        ctx = self.env.context.copy()
        ctx.update({
            'form_view_initial_mode': 'readonly',
            'no_breadcrumbs': True,
            'default_custody_id': self.custody_id.id,
            'force_detailed_view': True,  # Forces the full-sized image view
            'modal_full_screen': True,
            'create': False,
            'edit': False
        })
        
        # Create a more meaningful title
        title = f"{self.name} - {self.image_type} ({self.custody_id.name})"
        
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'custody.image',
            'res_id': self.id,
            'view_id': self.env.ref('hr_custody.custody_image_view_fullscreen').id,
            'target': 'new',
            'context': ctx,
            'flags': {
                'mode': 'readonly', 
                'withControlPanel': False,
                'no_breadcrumbs': True,
                'hasSearchView': False,
                'hasSidebar': False,
                'headless': True,
                'fullscreen': True  # Add fullscreen flag for better display
            }
        }