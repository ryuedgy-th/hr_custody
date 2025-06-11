from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class IrAttachment(models.Model):
    """
    Enhanced ir.attachment model for custody photo management
    Inspired by hr_expense attachment handling with custody-specific features
    """
    _inherit = 'ir.attachment'

    # ===== 📸 CUSTODY PHOTO CATEGORIZATION =====
    
    custody_photo_type = fields.Selection([
        # Handover photos
        ('handover_overall', '📸 Handover - Overall View'),
        ('handover_detail', '🔍 Handover - Detail View'),
        ('handover_serial', '🏷️ Handover - Serial Number'),
        
        # Return photos
        ('return_overall', '📦 Return - Overall View'),
        ('return_detail', '🔍 Return - Detail View'),
        ('return_damage', '⚠️ Return - Damage Report'),
        
        # Maintenance photos
        ('maintenance', '🔧 Maintenance Photo'),
        
        # Property master photos  
        ('property_master', '🏢 Property Master Photo'),
        
        # Other documents
        ('document', '📄 Document'),
        ('receipt', '🧾 Receipt'),
        ('other', '📎 Other')
    ], string='Photo Type', help='Categorize the type of photo or document')
    
    custody_timestamp = fields.Datetime(
        string='Photo Timestamp',
        default=fields.Datetime.now,
        help='When this photo was taken or uploaded'
    )
    
    custody_notes = fields.Text(
        string='Photo Notes',
        help='Additional notes about this photo or document'
    )
    
    custody_location = fields.Char(
        string='Photo Location',
        help='Location where the photo was taken (GPS coordinates, room, etc.)'
    )
    
    # Related custody information
    custody_id = fields.Many2one(
        'hr.custody',
        string='Related Custody',
        compute='_compute_custody_id',
        store=True,
        help='The custody record this photo belongs to'
    )
    
    custody_property_id = fields.Many2one(
        related='custody_id.custody_property_id',
        string='Property',
        store=True,
        help='The property this photo is related to'
    )
    
    custody_employee_id = fields.Many2one(
        related='custody_id.employee_id', 
        string='Employee',
        store=True,
        help='The employee this photo is related to'
    )
    
    # Photo analysis fields (for future AI integration)
    photo_width = fields.Integer(
        string='Photo Width',
        help='Width of the photo in pixels'
    )
    
    photo_height = fields.Integer(
        string='Photo Height', 
        help='Height of the photo in pixels'
    )
    
    photo_size_mb = fields.Float(
        string='Size (MB)',
        compute='_compute_photo_size_mb',
        help='File size in megabytes'
    )
    
    # Quality indicators
    is_high_quality = fields.Boolean(
        string='High Quality',
        compute='_compute_photo_quality',
        help='True if photo meets quality standards'
    )
    
    quality_score = fields.Float(
        string='Quality Score',
        compute='_compute_photo_quality',
        help='Photo quality score (0-100)'
    )

    # ===== 📊 COMPUTED METHODS =====
    
    @api.depends('res_model', 'res_id')
    def _compute_custody_id(self):
        """Compute the related custody record"""
        for attachment in self:
            if attachment.res_model == 'hr.custody' and attachment.res_id:
                attachment.custody_id = attachment.res_id
            else:
                attachment.custody_id = False
    
    @api.depends('file_size')
    def _compute_photo_size_mb(self):
        """Convert file size to MB"""
        for attachment in self:
            if attachment.file_size:
                attachment.photo_size_mb = attachment.file_size / (1024 * 1024)
            else:
                attachment.photo_size_mb = 0.0
    
    @api.depends('photo_width', 'photo_height', 'file_size')
    def _compute_photo_quality(self):
        """Compute photo quality indicators"""
        for attachment in self:
            if attachment.mimetype and attachment.mimetype.startswith('image/'):
                # Basic quality scoring based on resolution and file size
                score = 0
                
                # Resolution scoring (0-40 points)
                if attachment.photo_width and attachment.photo_height:
                    total_pixels = attachment.photo_width * attachment.photo_height
                    if total_pixels >= 2073600:  # >= 1920x1080 (Full HD)
                        score += 40
                    elif total_pixels >= 921600:  # >= 1280x720 (HD)
                        score += 30
                    elif total_pixels >= 307200:  # >= 640x480 (VGA)
                        score += 20
                    else:
                        score += 10
                
                # File size scoring (0-30 points) - reasonable size for quality
                if attachment.photo_size_mb:
                    if 1 <= attachment.photo_size_mb <= 5:  # Sweet spot
                        score += 30
                    elif 0.5 <= attachment.photo_size_mb <= 10:  # Good range
                        score += 20
                    elif attachment.photo_size_mb <= 20:  # Acceptable
                        score += 10
                
                # Format scoring (0-30 points)
                if attachment.mimetype in ['image/jpeg', 'image/jpg']:
                    score += 30
                elif attachment.mimetype == 'image/png':
                    score += 25
                elif attachment.mimetype == 'image/webp':
                    score += 20
                else:
                    score += 10
                
                attachment.quality_score = min(score, 100)
                attachment.is_high_quality = score >= 70
            else:
                attachment.quality_score = 0
                attachment.is_high_quality = False

    # ===== 🎯 BUSINESS METHODS =====
    
    def action_set_photo_type(self, photo_type):
        """Set photo type for multiple attachments"""
        self.write({'custody_photo_type': photo_type})
        return True
    
    def action_add_photo_notes(self):
        """Open wizard to add notes to photo"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Add Photo Notes'),
            'res_model': 'custody.photo.notes.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_attachment_id': self.id,
                'default_notes': self.custody_notes or '',
            }
        }
    
    @api.model
    def get_custody_photos_by_type(self, custody_id, photo_type):
        """Get custody photos filtered by type"""
        return self.search([
            ('res_model', '=', 'hr.custody'),
            ('res_id', '=', custody_id),
            ('custody_photo_type', '=', photo_type),
            ('mimetype', 'like', 'image%')
        ])
    
    @api.model
    def get_custody_photo_summary(self, custody_id):
        """Get summary of all custody photos"""
        custody_photos = self.search([
            ('res_model', '=', 'hr.custody'),
            ('res_id', '=', custody_id),
            ('mimetype', 'like', 'image%')
        ])
        
        summary = {}
        for photo in custody_photos:
            photo_type = photo.custody_photo_type or 'other'
            if photo_type not in summary:
                summary[photo_type] = {
                    'count': 0,
                    'total_size_mb': 0,
                    'latest_photo': False,
                    'photos': self.env['ir.attachment']
                }
            
            summary[photo_type]['count'] += 1
            summary[photo_type]['total_size_mb'] += photo.photo_size_mb
            summary[photo_type]['photos'] |= photo
            
            # Update latest photo
            if (not summary[photo_type]['latest_photo'] or 
                photo.custody_timestamp > summary[photo_type]['latest_photo'].custody_timestamp):
                summary[photo_type]['latest_photo'] = photo
        
        return summary

    # ===== 📱 MOBILE SUPPORT METHODS =====
    
    def action_rotate_photo(self, direction='clockwise'):
        """Rotate photo (placeholder for future implementation)"""
        # This would integrate with image processing libraries
        # For now, just log the action
        self.message_post(
            body=_('Photo rotated %s by %s') % (direction, self.env.user.name)
        )
        return True
    
    def action_compress_photo(self):
        """Compress photo to reduce file size (placeholder for future implementation)"""
        # This would integrate with image processing libraries
        # For now, just log the action
        self.message_post(
            body=_('Photo compression requested by %s') % self.env.user.name
        )
        return True

    # ===== 🔍 VALIDATION METHODS =====
    
    @api.constrains('custody_photo_type', 'mimetype')
    def _check_photo_type_consistency(self):
        """Validate that photo types are only set for images"""
        for attachment in self:
            if (attachment.custody_photo_type and 
                attachment.custody_photo_type != 'document' and
                attachment.custody_photo_type != 'receipt' and
                attachment.custody_photo_type != 'other' and
                attachment.mimetype and 
                not attachment.mimetype.startswith('image/')):
                raise ValidationError(
                    _('Photo type "%s" can only be set for image files. File "%s" is of type: %s') 
                    % (attachment.custody_photo_type, attachment.name, attachment.mimetype)
                )

    # ===== 📊 ANALYTICS METHODS =====
    
    @api.model
    def get_custody_photo_analytics(self, date_from=None, date_to=None):
        """Get analytics data for custody photos"""
        domain = [
            ('res_model', '=', 'hr.custody'),
            ('mimetype', 'like', 'image%')
        ]
        
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))
        
        photos = self.search(domain)
        
        analytics = {
            'total_photos': len(photos),
            'total_size_gb': sum(photos.mapped('photo_size_mb')) / 1024,
            'avg_quality_score': sum(photos.mapped('quality_score')) / len(photos) if photos else 0,
            'high_quality_percentage': len(photos.filtered('is_high_quality')) / len(photos) * 100 if photos else 0,
            'photos_by_type': {},
            'photos_by_month': {},
        }
        
        # Group by photo type
        for photo_type in photos.mapped('custody_photo_type'):
            type_photos = photos.filtered(lambda p: p.custody_photo_type == photo_type)
            analytics['photos_by_type'][photo_type or 'undefined'] = len(type_photos)
        
        return analytics
