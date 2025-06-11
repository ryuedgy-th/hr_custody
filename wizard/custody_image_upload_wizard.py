from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
import base64
import imghdr
import io
import logging
import json

_logger = logging.getLogger(__name__)


class CustodyImageUploadWizard(models.TransientModel):
    """
    Modern Wizard for uploading multiple custody images
    Enhanced for Odoo 18 with improved error handling and logging
    """
    
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
    
    # 🎯 ENHANCED: File Storage with better field definition
    images_data = fields.Text(
        string='Images Data',
        help='JSON storage for uploaded images data - automatically populated by JavaScript'
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
    
    # 🎯 NEW: Enhanced computed fields for better UI
    custody_state_display = fields.Char(
        related='custody_id.state',
        string='Custody State',
        readonly=True
    )
    
    existing_images_count = fields.Integer(
        string='Existing Images',
        compute='_compute_existing_images_count',
        help='Number of existing images of this type'
    )
    
    @api.depends('custody_id', 'image_type')
    def _compute_existing_images_count(self):
        """Count existing images of the same type"""
        for wizard in self:
            if wizard.custody_id and wizard.image_type:
                wizard.existing_images_count = self.env['custody.image'].search_count([
                    ('custody_id', '=', wizard.custody_id.id),
                    ('image_type', '=', wizard.image_type)
                ])
            else:
                wizard.existing_images_count = 0
    
    @api.depends('custody_id.state', 'image_type')
    def _compute_can_upload(self):
        """Enhanced upload permission logic"""
        for wizard in self:
            if not wizard.custody_id:
                wizard.can_upload = False
                continue
                
            custody_state = wizard.custody_id.state
            image_type = wizard.image_type
            
            # Define upload rules clearly
            upload_rules = {
                'before': ['to_approve', 'approved', 'returned'],
                'after': ['approved', 'returned'],
                'damage': ['approved', 'returned']
            }
            
            allowed_states = upload_rules.get(image_type, [])
            wizard.can_upload = custody_state in allowed_states
            
            # 🎯 ENHANCED: Log permission checks for debugging
            if not wizard.can_upload:
                _logger.debug(
                    f"Upload not allowed - State: {custody_state}, Type: {image_type}, "
                    f"Allowed states: {allowed_states}"
                )
    
    def _validate_upload_permissions(self):
        """Centralized permission validation"""
        self.ensure_one()
        
        if not self.can_upload:
            state_labels = dict(self.custody_id._fields['state'].selection)
            current_state = state_labels.get(self.custody_id.state, self.custody_id.state)
            type_labels = dict(self._fields['image_type'].selection)
            image_type_label = type_labels.get(self.image_type, self.image_type)
            
            raise UserError(_(
                'Cannot upload %s images when custody is in "%s" state. '
                'Please check the custody workflow requirements.'
            ) % (image_type_label, current_state))
    
    def _validate_image_file(self, file_data, filename):
        """
        🎯 ENHANCED: Comprehensive image validation with better error messages
        """
        try:
            if not file_data:
                raise ValidationError(_('File "%s" contains no data') % filename)
            
            # Handle different base64 formats more robustly
            original_data = file_data
            if 'data:' in file_data and ',' in file_data:
                # Extract base64 from data URL
                file_data = file_data.split(',')[1]
            
            if not file_data.strip():
                raise ValidationError(_('File "%s" has invalid or empty base64 data') % filename)
            
            # Decode with enhanced error handling
            try:
                binary_data = base64.b64decode(file_data, validate=True)
            except Exception as e:
                _logger.warning(f"Base64 decode failed for {filename}: {str(e)}")
                raise ValidationError(_('File "%s" contains corrupted image data') % filename)
            
            if len(binary_data) == 0:
                raise ValidationError(_('File "%s" is empty after processing') % filename)
            
            # Enhanced size validation with exact limits
            max_size_bytes = 5 * 1024 * 1024  # 5MB
            actual_size_mb = len(binary_data) / (1024 * 1024)
            
            if len(binary_data) > max_size_bytes:
                raise ValidationError(_(
                    'File "%s" is too large (%.2f MB). Maximum allowed: 5 MB. '
                    'Please compress the image and try again.'
                ) % (filename, actual_size_mb))
            
            # Enhanced image format validation
            try:
                img_stream = io.BytesIO(binary_data)
                img_format = imghdr.what(img_stream)
                img_stream.seek(0)
                
                # Additional validation: try to read basic image properties
                if not img_format:
                    # Try alternative validation
                    if binary_data[:4] == b'\xff\xd8\xff\xe0' or binary_data[:4] == b'\xff\xd8\xff\xe1':
                        img_format = 'jpeg'
                    elif binary_data[:8] == b'\x89PNG\r\n\x1a\n':
                        img_format = 'png'
                    elif binary_data[:6] in [b'GIF87a', b'GIF89a']:
                        img_format = 'gif'
            
            except Exception as e:
                _logger.warning(f"Image validation failed for {filename}: {str(e)}")
                raise ValidationError(_('File "%s" cannot be processed as a valid image') % filename)
            
            if not img_format:
                raise ValidationError(_(
                    'File "%s" is not a recognized image format. '
                    'Supported formats: JPEG, PNG, GIF, WebP, BMP'
                ) % filename)
            
            # 🎯 NEW: Log successful validation
            _logger.debug(f"✅ Validated {filename}: {img_format} format, {len(binary_data)} bytes")
            
            return binary_data
            
        except ValidationError:
            raise
        except Exception as e:
            _logger.error(f"Unexpected validation error for {filename}: {str(e)}")
            raise ValidationError(_('Unexpected error validating file "%s": %s') % (filename, str(e)))
    
    def action_upload_images(self):
        """
        🎯 ENHANCED: Modern upload process with comprehensive error handling
        """
        self.ensure_one()
        
        try:
            # 🎯 ENHANCED: Detailed logging for debugging
            _logger.info(f"🚀 UPLOAD START - Wizard {self.id} for custody {self.custody_id.id}")
            _logger.info(f"📊 Upload details - Type: {self.image_type}, Data length: {len(self.images_data or '')}")
            
            # Step 1: Validate permissions
            self._validate_upload_permissions()
            
            # Step 2: Validate input data
            if not self.images_data:
                raise UserError(_(
                    'No image data found. Please select images using the upload interface and try again.'
                ))
            
            # Update status to uploading
            self.write({
                'upload_status': 'uploading',
                'error_message': False
            })
            
            # Step 3: Parse and validate JSON data
            try:
                images_list = json.loads(self.images_data)
                _logger.info(f"✅ Successfully parsed {len(images_list)} images from JSON")
            except json.JSONDecodeError as e:
                _logger.error(f"❌ JSON parsing failed: {str(e)}")
                raise UserError(_(
                    'Invalid image data format. The uploaded data appears to be corrupted. '
                    'Please refresh the page and try uploading again.'
                ))
            
            if not images_list:
                raise UserError(_('No valid images found in the uploaded data'))
            
            # Step 4: Process images with detailed tracking
            return self._process_images(images_list)
            
        except UserError:
            # UserErrors should be shown to user as-is
            self.write({'upload_status': 'error'})
            raise
        except Exception as e:
            # Unexpected errors should be logged and converted to user-friendly messages
            error_msg = str(e)
            _logger.error(f"❌ Unexpected upload error in wizard {self.id}: {error_msg}")
            
            self.write({
                'upload_status': 'error',
                'error_message': f'System error: {error_msg}'
            })
            
            raise UserError(_(
                'An unexpected error occurred during upload. '
                'Please try again or contact your system administrator if the problem persists.'
            ))
    
    def _process_images(self, images_list):
        """
        🎯 NEW: Separated image processing logic for better maintainability
        """
        total_images = len(images_list)
        created_images = []
        failed_images = []
        
        # Get starting sequence number
        if self.auto_sequence:
            existing_images = self.env['custody.image'].search([
                ('custody_id', '=', self.custody_id.id),
                ('image_type', '=', self.image_type)
            ])
            next_sequence = max(existing_images.mapped('sequence') or [0]) + 1
        else:
            next_sequence = 10
        
        _logger.info(f"🔄 Processing {total_images} images, starting sequence: {next_sequence}")
        
        # Process each image with individual error handling
        for idx, image_info in enumerate(images_list):
            try:
                filename = image_info.get('filename', f'image_{idx+1}')
                _logger.debug(f"Processing image {idx+1}/{total_images}: {filename}")
                
                image_record = self._create_single_image(image_info, idx, next_sequence)
                created_images.append(image_record)
                
            except ValidationError as ve:
                error_msg = str(ve)
                _logger.warning(f"⚠️ Validation failed for image {idx+1}: {error_msg}")
                failed_images.append({
                    'filename': image_info.get('filename', f'image_{idx+1}'),
                    'error': error_msg
                })
                continue
                
            except Exception as e:
                error_msg = f'Processing error: {str(e)}'
                _logger.error(f"❌ Failed to process image {idx+1}: {error_msg}")
                failed_images.append({
                    'filename': image_info.get('filename', f'image_{idx+1}'),
                    'error': error_msg
                })
                continue
        
        # Generate final result
        return self._generate_upload_result(created_images, failed_images, total_images)
    
    def _create_single_image(self, image_info, index, base_sequence):
        """Create a single image record with comprehensive validation"""
        filename = image_info.get('filename', f'image_{index+1}')
        file_data = image_info.get('data', '')
        description = image_info.get('description', '') or self.bulk_description or ''
        
        # Validate and process image data
        binary_data = self._validate_image_file(file_data, filename)
        
        # Create image record with all metadata
        image_vals = {
            'custody_id': self.custody_id.id,
            'image_type': self.image_type,
            'image': base64.b64encode(binary_data).decode('utf-8'),
            'description': description or f'{filename} #{index+1}',
            'sequence': base_sequence + index if self.auto_sequence else 10,
            'location_notes': self.location_notes,
            'notes': f'Uploaded via multiple upload wizard (v2.0)',
        }
        
        image_record = self.env['custody.image'].create(image_vals)
        _logger.debug(f"✅ Created image record {image_record.id} for {filename}")
        
        return image_record
    
    def _generate_upload_result(self, created_images, failed_images, total_images):
        """
        🎯 ENHANCED: Generate comprehensive upload result with proper notifications
        """
        success_count = len(created_images)
        failed_count = len(failed_images)
        
        # Update wizard status
        if success_count > 0:
            status = 'done'
            if failed_count > 0:
                error_msg = self._format_partial_failure_message(failed_images)
            else:
                error_msg = False
        else:
            status = 'error'
            error_msg = self._format_complete_failure_message(failed_images)
        
        self.write({
            'upload_status': status,
            'error_message': error_msg
        })
        
        # 🎯 ENHANCED: Post message to custody record (like hr_expense does)
        if success_count > 0:
            self._post_success_message(created_images, failed_count)
        
        # Generate appropriate user notification
        if success_count > 0:
            return self._success_notification(success_count, failed_count)
        else:
            raise UserError(_('No images were successfully uploaded. Please check the errors and try again.'))
    
    def _format_partial_failure_message(self, failed_images):
        """Format error message for partial failures"""
        error_details = []
        for img in failed_images[:3]:  # Show first 3 errors
            error_details.append(f"• {img['filename']}: {img['error']}")
        
        if len(failed_images) > 3:
            error_details.append(f"• ... and {len(failed_images) - 3} more files")
        
        return "Some uploads failed:\n" + "\n".join(error_details)
    
    def _format_complete_failure_message(self, failed_images):
        """Format error message for complete failures"""
        if not failed_images:
            return "Upload failed for unknown reasons"
        
        error_details = []
        for img in failed_images[:5]:  # Show first 5 errors for complete failure
            error_details.append(f"• {img['filename']}: {img['error']}")
        
        if len(failed_images) > 5:
            error_details.append(f"• ... and {len(failed_images) - 5} more files")
        
        return "All uploads failed:\n" + "\n".join(error_details)
    
    def _post_success_message(self, created_images, failed_count):
        """
        🎯 NEW: Post success message to custody record (following hr_expense pattern)
        """
        try:
            image_type_label = dict(self._fields['image_type'].selection)[self.image_type]
            
            message_body = _(
                "Multiple %s images uploaded successfully: %d files"
            ) % (image_type_label.lower(), len(created_images))
            
            if failed_count > 0:
                message_body += _(" (%d files failed)") % failed_count
            
            # Create message with image attachments
            attachment_ids = []
            for image_record in created_images:
                if image_record.image:
                    attachment = self.env['ir.attachment'].create({
                        'name': image_record.description or 'Custody Image',
                        'type': 'binary',
                        'datas': image_record.image,
                        'res_model': 'hr.custody',
                        'res_id': self.custody_id.id,
                        'mimetype': 'image/jpeg',  # Default mimetype
                    })
                    attachment_ids.append(attachment.id)
            
            self.custody_id.message_post(
                body=message_body,
                attachment_ids=[(6, 0, attachment_ids)] if attachment_ids else False,
                message_type='notification'
            )
            
            _logger.info(f"✅ Posted success message to custody {self.custody_id.id}")
            
        except Exception as e:
            _logger.warning(f"⚠️ Failed to post message to custody record: {str(e)}")
    
    def _success_notification(self, success_count, failed_count):
        """
        🎯 ENHANCED: Generate success notification following Odoo 18 patterns
        """
        if failed_count == 0:
            title = _('Upload Completed Successfully!')
            message = _('Successfully uploaded %d images') % success_count
            notification_type = 'success'
        else:
            title = _('Upload Partially Completed')
            message = _('Uploaded %d images successfully, %d failed') % (success_count, failed_count)
            notification_type = 'warning'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': title,
                'message': message,
                'type': notification_type,
                'sticky': False,
                'next': {
                    'type': 'ir.actions.act_window_close'
                }
            }
        }
    
    def action_reset_wizard(self):
        """Reset wizard to initial state"""
        self.ensure_one()
        self.write({
            'images_data': False,
            'total_files': 0,
            'total_size_mb': 0.0,
            'upload_status': 'draft',
            'error_message': False,
        })
        return {'type': 'ir.actions.do_nothing'}
    
    def action_close_wizard(self):
        """Close wizard and return to custody record"""
        return {'type': 'ir.actions.act_window_close'}
    
    def action_view_uploaded_images(self):
        """View uploaded images in kanban/list view"""
        self.ensure_one()
        
        domain = [
            ('custody_id', '=', self.custody_id.id),
            ('image_type', '=', self.image_type)
        ]
        
        image_type_label = dict(self._fields['image_type'].selection)[self.image_type]
        
        return {
            'name': _('Uploaded %s Images') % image_type_label,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image',
            'view_mode': 'kanban,tree,form',
            'domain': domain,
            'context': {
                'default_custody_id': self.custody_id.id,
                'default_image_type': self.image_type,
            },
            'target': 'current',
        }
    
    @api.model
    def default_get(self, fields_list):
        """Enhanced default values with better context handling"""
        defaults = super().default_get(fields_list)
        
        # Get custody_id from context
        custody_id = self.env.context.get('default_custody_id') or self.env.context.get('active_id')
        if custody_id:
            defaults['custody_id'] = custody_id
        
        # Get image_type from context
        image_type = self.env.context.get('default_image_type')
        if image_type:
            defaults['image_type'] = image_type
        
        return defaults