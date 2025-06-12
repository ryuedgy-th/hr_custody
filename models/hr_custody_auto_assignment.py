"""
📦 HR Custody Management - Auto Assignment Methods
Contains automated photo type assignment functionality
"""

from odoo import api, fields, models, _
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)

class HrCustodyAutoAssignment(models.TransientModel):
    """
    🔧 Transient model for auto-assignment operations
    """
    _name = 'hr.custody.auto.assignment'
    _description = 'Auto Assignment Helper'

    # Statistics fields
    untyped_photos_count = fields.Integer(
        string='Untyped Photos',
        compute='_compute_statistics',
        help='Number of custody photos without photo type'
    )
    
    total_custody_photos = fields.Integer(
        string='Total Custody Photos',
        compute='_compute_statistics',
        help='Total number of custody photos'
    )
    
    recent_uploads = fields.Integer(
        string='Recent Uploads (24h)',
        compute='_compute_statistics',
        help='Photos uploaded in the last 24 hours'
    )
    
    processed_today = fields.Integer(
        string='Processed Today',
        compute='_compute_statistics',
        help='Photos processed by auto-assignment today'
    )

    @api.depends()
    def _compute_statistics(self):
        """Compute statistics for the dashboard"""
        for record in self:
            # Count untyped photos
            untyped_attachments = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'hr.custody'),
                ('res_id', '!=', False),
                ('mimetype', 'like', 'image%'),
                ('custody_photo_type', '=', False)
            ])
            record.untyped_photos_count = untyped_attachments
            
            # Count total custody photos
            total_photos = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'hr.custody'),
                ('res_id', '!=', False),
                ('mimetype', 'like', 'image%')
            ])
            record.total_custody_photos = total_photos
            
            # Count recent uploads (24 hours)
            yesterday = datetime.now() - timedelta(hours=24)
            recent_photos = self.env['ir.attachment'].search_count([
                ('res_model', '=', 'hr.custody'),
                ('res_id', '!=', False),
                ('mimetype', 'like', 'image%'),
                ('create_date', '>=', yesterday)
            ])
            record.recent_uploads = recent_photos
            
            # Count processed today (approximation based on chatter messages)
            today = fields.Date.today()
            today_start = fields.Datetime.to_datetime(today)
            processed_messages = self.env['mail.message'].search_count([
                ('model', '=', 'hr.custody'),
                ('body', 'like', 'Auto-assigned photo type'),
                ('date', '>=', today_start)
            ])
            record.processed_today = processed_messages

    def process_untyped_attachments(self):
        """
        🔧 Process all custody attachments without photo types
        This method is called by cron job or manually
        """
        _logger.info("🔧 Starting auto-assignment of photo types...")
        
        # Find all custody attachments without photo type
        untyped_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.custody'),
            ('res_id', '!=', False),
            ('mimetype', 'like', 'image%'),
            ('custody_photo_type', '=', False)
        ])
        
        assigned_count = 0
        for attachment in untyped_attachments:
            try:
                # Get the custody record
                custody_record = self.env['hr.custody'].browse(attachment.res_id)
                if custody_record.exists():
                    # Determine photo type based on state
                    if custody_record.state == 'returned':
                        default_type = 'return_overall'
                    elif custody_record.state in ['approved']:
                        default_type = 'handover_overall'
                    else:
                        default_type = 'handover_overall'
                    
                    # Update attachment
                    attachment.write({
                        'custody_photo_type': default_type,
                        'res_field': 'attachment_ids'
                    })
                    
                    assigned_count += 1
                    
                    # Log success
                    photo_type_label = dict(attachment._fields['custody_photo_type'].selection)[default_type]
                    custody_record.message_post(
                        body=_('🤖 Auto-assigned photo type "%s" to: %s') % (
                            photo_type_label, 
                            attachment.name
                        )
                    )
                    
            except Exception as e:
                _logger.error(f"Failed to assign photo type for attachment {attachment.id}: {str(e)}")
                continue
        
        _logger.info(f"🎉 Auto-assignment completed: {assigned_count} photos processed")
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('🤖 Auto-Assignment Complete'),
                'message': _('Successfully processed %d photos!') % assigned_count,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def auto_assign_recent_photos(self, hours=1):
        """
        🔧 Auto-assign photo types for recently uploaded photos
        Called by cron job every hour
        """
        _logger.info(f"🔧 Auto-assigning photos from last {hours} hours...")
        
        # Find recent untyped attachments
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent_attachments = self.env['ir.attachment'].search([
            ('res_model', '=', 'hr.custody'),
            ('res_id', '!=', False),
            ('mimetype', 'like', 'image%'),
            ('custody_photo_type', '=', False),
            ('create_date', '>=', cutoff_time)
        ])
        
        assigned_count = 0
        for attachment in recent_attachments:
            try:
                custody_record = self.env['hr.custody'].browse(attachment.res_id)
                if custody_record.exists():
                    # Auto-assign based on state
                    if custody_record.state == 'returned':
                        default_type = 'return_overall'
                    elif custody_record.state in ['approved']:
                        default_type = 'handover_overall'
                    else:
                        default_type = 'handover_overall'
                    
                    attachment.write({
                        'custody_photo_type': default_type,
                        'res_field': 'attachment_ids'
                    })
                    
                    assigned_count += 1
                    
                    # Log success in chatter
                    photo_type_label = dict(attachment._fields['custody_photo_type'].selection)[default_type]
                    custody_record.message_post(
                        body=_('🤖 Hourly auto-assigned: "%s" to %s') % (
                            photo_type_label, 
                            attachment.name
                        )
                    )
                    
            except Exception as e:
                _logger.error(f"Failed to auto-assign for attachment {attachment.id}: {str(e)}")
                continue
        
        _logger.info(f"🎉 Hourly auto-assignment: {assigned_count} photos processed")
        return assigned_count
    
    def action_view_untyped_photos(self):
        """Open view of untyped photos"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Untyped Custody Photos'),
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [
                ('res_model', '=', 'hr.custody'),
                ('res_id', '!=', False),
                ('mimetype', 'like', 'image%'),
                ('custody_photo_type', '=', False)
            ],
            'context': {'default_res_model': 'hr.custody'},
            'target': 'current',
        }
    
    def action_view_recent_uploads(self):
        """Open view of recent uploads"""
        yesterday = datetime.now() - timedelta(hours=24)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Recent Custody Photo Uploads'),
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [
                ('res_model', '=', 'hr.custody'),
                ('res_id', '!=', False),
                ('mimetype', 'like', 'image%'),
                ('create_date', '>=', yesterday)
            ],
            'context': {'default_res_model': 'hr.custody'},
            'target': 'current',
        }
