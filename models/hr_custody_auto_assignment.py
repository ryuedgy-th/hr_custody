"""
📦 HR Custody Management - Auto Assignment Methods
Contains automated photo type assignment functionality
"""

from odoo import api, fields, models, _
import logging

_logger = logging.getLogger(__name__)

class HrCustodyAutoAssignment(models.TransientModel):
    """
    🔧 Transient model for auto-assignment operations
    """
    _name = 'hr.custody.auto.assignment'
    _description = 'Auto Assignment Helper'

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
        from datetime import datetime, timedelta
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
                    
            except Exception as e:
                _logger.error(f"Failed to auto-assign for attachment {attachment.id}: {str(e)}")
                continue
        
        _logger.info(f"🎉 Hourly auto-assignment: {assigned_count} photos processed")
        return assigned_count
