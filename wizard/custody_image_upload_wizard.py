from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import base64
import imghdr
import io


class CustodyImageUploadWizard(models.TransientModel):
    """Wizard for uploading multiple custody images at once"""
    
    _name = 'custody.image.upload.wizard'
    _description = 'Custody Multiple Image Upload Wizard'
    
    # Basic Information
    custody_id = fields.Many2one(
        'hr.custody',
        string='Custody Record',
        required=True,
        readonly=True,
        help='Related custody record'
    )
    
    image_type = fields.Selection([
        ('before', 'Before Handover'),
        ('after', 'After Return'),
        ('damage', 'Damage Documentation')
    ],
        string='Image Type',
        required=True,
        help='Type of documentation photos to upload'
    )
    
    # Upload Information
    total_files = fields.Integer(
        string='Total Files',
        readonly=True,
        help='Number of files selected for upload'
    )
    
    total_size_mb = fields.Float(
        string='Total Size (MB)',
        readonly=True,
        help='Total size of all selected files'
    )
    
    # Configuration
    auto_sequence = fields.Boolean(
        string='Auto Sequence',
        default=True,
        help='Automatically assign sequence numbers to uploaded images'
    )
    
    location_notes = fields.Char(
        string='Location Notes',
        help='Where the photos were taken (applies to all uploaded images)'
    )
    
    bulk_description = fields.Char(
        string='Bulk Description',
        help='Description to apply to all uploaded images (optional)'
    )
    
    # File Storage (JSON-like field for storing multiple files temporarily)
    images_data = fields.Text(
        string='Images Data',
        help='Temporary storage for uploaded images data'
    )
    
    # Status and Progress
    upload_status = fields.Selection([
        ('draft', 'Ready to Upload'),
        ('uploading', 'Uploading...'),
        ('done', 'Upload Complete'),
        ('error', 'Upload Failed')
    ],
        string='Upload Status',
        default='draft',
        readonly=True
    )
    
    progress_percentage = fields.Float(
        string='Progress %',
        readonly=True,
        help='Upload progress percentage'
    )
    
    error_message = fields.Text(
        string='Error Message',
        readonly=True,
        help='Error details if upload fails'
    )
    
    # Computed Fields
    employee_name = fields.Char(
        related='custody_id.employee_id.name',
        string='Employee',
        readonly=True
    )
    
    property_name = fields.Char(
        related='custody_id.custody_property_id.name',
        string='Property',
        readonly=True
    )
    
    can_upload = fields.Boolean(
        string='Can Upload',
        compute='_compute_can_upload',
        help='Whether images can be uploaded based on custody state'
    )
    
    @api.depends('custody_id.state', 'image_type')
    def _compute_can_upload(self):
        """Check if images can be uploaded based on custody state and image type"""
        for wizard in self:
            if not wizard.custody_id:
                wizard.can_upload = False
                continue
                
            custody_state = wizard.custody_id.state
            image_type = wizard.image_type
            
            # Before images: can upload when custody is to_approve, approved or returned
            if image_type == 'before' and custody_state in ['to_approve', 'approved', 'returned']:
                wizard.can_upload = True
            # After images: can upload when custody is approved or returned  
            elif image_type == 'after' and custody_state in ['approved', 'returned']:
                wizard.can_upload = True
            # Damage images: can upload when custody is approved or returned
            elif image_type == 'damage' and custody_state in ['approved', 'returned']:
                wizard.can_upload = True
            else:
                wizard.can_upload = False
    
    @api.constrains('total_files')
    def _check_file_limit(self):
        """Validate file count limits"""
        max_files = 20  # Maximum files per upload
        for wizard in self:
            if wizard.total_files > max_files:
                raise ValidationError(
                    _('Maximum %d files allowed per upload. You selected %d files.') 
                    % (max_files, wizard.total_files)
                )
    
    @api.constrains('total_size_mb')
    def _check_total_size(self):
        """Validate total file size"""
        max_total_mb = 100  # Maximum total size in MB
        for wizard in self:
            if wizard.total_size_mb > max_total_mb:
                raise ValidationError(
                    _('Total file size exceeds %d MB limit. Current total: %.2f MB') 
                    % (max_total_mb, wizard.total_size_mb)
                )
    
    def _validate_image_file(self, file_data, filename):
        """Validate individual image file"""
        try:
            # Decode base64 data
            if ',' in file_data:
                file_data = file_data.split(',')[1]
            
            binary_data = base64.b64decode(file_data)
            
            # Check file size (5MB per file)
            max_size_bytes = 5 * 1024 * 1024
            if len(binary_data) > max_size_bytes:
                raise ValidationError(
                    _('File "%s" exceeds 5MB limit. Please compress the image.') % filename
                )
            
            # Validate image format
            img_format = imghdr.what(io.BytesIO(binary_data))
            if not img_format:
                raise ValidationError(
                    _('File "%s" is not a valid image format.') % filename
                )
            
            # Check if format is web-compatible
            allowed_formats = ['jpeg', 'png', 'gif', 'webp', 'bmp']
            if img_format not in allowed_formats:
                raise ValidationError(
                    _('File "%s" format "%s" is not supported. Allowed: %s') 
                    % (filename, img_format, ', '.join(allowed_formats))
                )
            
            return True
            
        except Exception as e:
            raise ValidationError(
                _('Error validating file "%s": %s') % (filename, str(e))
            )
    
    def action_upload_images(self):
        """Process and upload multiple images"""
        self.ensure_one()
        
        if not self.can_upload:
            raise UserError(
                _('Cannot upload %s images when custody is in state "%s"') 
                % (self.image_type, self.custody_id.state)
            )
        
        if not self.images_data:
            raise UserError(_('No images selected for upload'))
        
        try:
            self.upload_status = 'uploading'
            self.progress_percentage = 0.0
            
            # Parse images data (expecting JSON format from JavaScript)
            import json
            images_list = json.loads(self.images_data)
            
            if not images_list:
                raise UserError(_('No valid images found to upload'))
            
            total_images = len(images_list)
            created_images = []
            
            # Get starting sequence number
            if self.auto_sequence:
                existing_images = self.env['custody.image'].search([
                    ('custody_id', '=', self.custody_id.id),
                    ('image_type', '=', self.image_type)
                ])
                next_sequence = max(existing_images.mapped('sequence') or [0]) + 1
            else:
                next_sequence = 10
            
            # Process each image
            for idx, image_info in enumerate(images_list):
                try:
                    filename = image_info.get('filename', f'image_{idx+1}')
                    file_data = image_info.get('data', '')
                    description = image_info.get('description', '') or self.bulk_description or ''
                    
                    # Validate image
                    self._validate_image_file(file_data, filename)
                    
                    # Create custody image record
                    image_vals = {
                        'custody_id': self.custody_id.id,
                        'image_type': self.image_type,
                        'image': file_data,
                        'description': description or f'{filename} #{idx+1}',
                        'sequence': next_sequence + idx if self.auto_sequence else 10,
                        'location_notes': self.location_notes,
                        'notes': f'Uploaded via batch upload wizard ({total_images} files)',
                    }
                    
                    image_record = self.env['custody.image'].create(image_vals)
                    created_images.append(image_record)
                    
                    # Update progress
                    progress = ((idx + 1) / total_images) * 100
                    self.progress_percentage = progress
                    
                except Exception as e:
                    # Log error but continue with other images
                    self.error_message = f'Error processing {filename}: {str(e)}'
                    continue
            
            # Update final status
            if created_images:
                self.upload_status = 'done'
                self.progress_percentage = 100.0
                
                # Show success message
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Upload Successful!'),
                        'message': _('Successfully uploaded %d images') % len(created_images),
                        'type': 'success',
                        'sticky': False
                    }
                }
            else:
                self.upload_status = 'error'
                raise UserError(_('No images were successfully uploaded. Check error messages.'))
        
        except Exception as e:
            self.upload_status = 'error'
            self.error_message = str(e)
            raise UserError(_('Upload failed: %s') % str(e))
    
    def action_reset_wizard(self):
        """Reset wizard to initial state"""
        self.ensure_one()
        self.write({
            'images_data': False,
            'total_files': 0,
            'total_size_mb': 0.0,
            'upload_status': 'draft',
            'progress_percentage': 0.0,
            'error_message': False,
        })
        
        return {
            'type': 'ir.actions.do_nothing'
        }
    
    def action_close_wizard(self):
        """Close wizard and return to custody form"""
        return {
            'type': 'ir.actions.act_window_close'
        }
    
    def action_view_uploaded_images(self):
        """View uploaded images"""
        self.ensure_one()
        
        domain = [
            ('custody_id', '=', self.custody_id.id),
            ('image_type', '=', self.image_type)
        ]
        
        return {
            'name': _('Uploaded %s Images') % dict(self._fields['image_type'].selection).get(self.image_type),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image',
            'view_mode': 'kanban,list,form',
            'domain': domain,
            'context': {
                'default_custody_id': self.custody_id.id,
                'default_image_type': self.image_type,
            },
            'target': 'current',
        }
    
    @api.model
    def default_get(self, fields_list):
        """Set default values from context"""
        defaults = super().default_get(fields_list)
        
        # Get custody_id from context
        custody_id = self.env.context.get('default_custody_id')
        if custody_id:
            defaults['custody_id'] = custody_id
        
        # Get image_type from context
        image_type = self.env.context.get('default_image_type')
        if image_type:
            defaults['image_type'] = image_type
        
        return defaults
