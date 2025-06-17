from odoo import api, fields, models, _
import base64
import logging

_logger = logging.getLogger(__name__)

class MultiImagesUpload(models.TransientModel):
    _name = 'custody.multi.images.upload'
    _description = 'Upload Multiple Images'

    custody_id = fields.Many2one(
        'hr.custody',
        string='Custody Record',
        required=True,
        ondelete='cascade'
    )
    
    image_type = fields.Selection([
        ('checkout', 'Checkout'),
        ('return', 'Return'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other')
    ], 
        string='Image Type',
        required=True,
        default='other'
    )
    
    name = fields.Char(
        string='Title Base',
        help='Base title for the images (will be appended with a number)',
        default='Image'
    )
    
    notes = fields.Text(
        string='Common Notes',
        help='Notes to apply to all uploaded images'
    )
    
    file_ids = fields.Many2many(
        'ir.attachment',
        string='Image Files',
        required=True,
        help='Select multiple image files to upload'
    )
    
    def action_upload_images(self):
        """Process selected files and create custody.image records"""
        self.ensure_one()
        
        CustodyImage = self.env['custody.image']
        images_created = 0
        
        for i, attachment in enumerate(self.file_ids):
            try:
                # Skip non-image files
                mimetype = attachment.mimetype or ''
                if not mimetype.startswith('image/'):
                    continue
                
                # Create image title
                image_number = i + 1
                name = f"{self.name} {image_number}" if len(self.file_ids) > 1 else self.name
                
                # Create custody image
                CustodyImage.create({
                    'name': name,
                    'image': attachment.datas,
                    'custody_id': self.custody_id.id,
                    'image_type': self.image_type,
                    'notes': self.notes,
                })
                images_created += 1
                
            except Exception as e:
                _logger.error("Failed to process image: %s", e)
        
        # Show success message
        message = _(f"{images_created} images successfully uploaded")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': message,
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window_close'
                }
            }
        } 