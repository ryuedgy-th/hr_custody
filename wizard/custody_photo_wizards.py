# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CustodyPhotoNotesWizard(models.TransientModel):
    """Wizard for adding notes to custody photos"""
    _name = 'custody.photo.notes.wizard'
    _description = 'Add Notes to Custody Photos'

    attachment_id = fields.Many2one(
        'ir.attachment',
        string='Photo',
        required=True,
        readonly=True
    )
    
    attachment_name = fields.Char(
        related='attachment_id.name',
        string='Photo Name',
        readonly=True
    )
    
    current_notes = fields.Text(
        related='attachment_id.custody_notes',
        string='Current Notes',
        readonly=True
    )
    
    notes = fields.Text(
        string='Photo Notes',
        help='Add detailed notes about this photo'
    )
    
    custody_location = fields.Char(
        string='Location',
        help='Where was this photo taken?'
    )

    def action_save_notes(self):
        """Save notes to the attachment"""
        self.ensure_one()
        
        self.attachment_id.write({
            'custody_notes': self.notes,
            'custody_location': self.custody_location,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('📝 Photo notes updated successfully!'),
                'type': 'success',
                'sticky': False,
            }
        }


class CustodyPhotoBulkCategorizeWizard(models.TransientModel):
    """Wizard for bulk categorizing custody photos"""
    _name = 'custody.photo.bulk.categorize.wizard'
    _description = 'Bulk Categorize Custody Photos'

    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Photos',
        required=True,
        readonly=True
    )
    
    photo_count = fields.Integer(
        string='Number of Photos',
        compute='_compute_photo_count'
    )
    
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
    ], string='Photo Type', required=True, help='Select the type for all selected photos')
    
    add_notes = fields.Boolean(
        string='Add Notes',
        help='Add the same notes to all selected photos'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Notes to add to all selected photos'
    )
    
    location = fields.Char(
        string='Location',
        help='Location to set for all selected photos'
    )

    @api.depends('attachment_ids')
    def _compute_photo_count(self):
        for record in self:
            record.photo_count = len(record.attachment_ids)

    def action_categorize_photos(self):
        """Apply categorization to all selected photos"""
        self.ensure_one()
        
        if not self.attachment_ids:
            raise ValidationError(_('No photos selected for categorization'))
        
        update_values = {
            'custody_photo_type': self.custody_photo_type,
        }
        
        if self.add_notes and self.notes:
            update_values['custody_notes'] = self.notes
            
        if self.location:
            update_values['custody_location'] = self.location
        
        self.attachment_ids.write(update_values)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('📸 Successfully categorized %s photos as "%s"!') % (
                    self.photo_count, 
                    dict(self._fields['custody_photo_type'].selection)[self.custody_photo_type]
                ),
                'type': 'success',
                'sticky': False,
            }
        }


class CustodyPhotoQualityAnalysisWizard(models.TransientModel):
    """Wizard for analyzing photo quality across custody records"""
    _name = 'custody.photo.quality.analysis.wizard'
    _description = 'Custody Photo Quality Analysis'

    date_from = fields.Date(
        string='From Date',
        default=fields.Date.today().replace(month=1, day=1),  # Start of year
        required=True
    )
    
    date_to = fields.Date(
        string='To Date',
        default=fields.Date.today(),
        required=True
    )
    
    custody_ids = fields.Many2many(
        'hr.custody',
        string='Custody Records',
        help='Leave empty to analyze all records in date range'
    )
    
    employee_ids = fields.Many2many(
        'hr.employee',
        string='Employees',
        help='Filter by specific employees'
    )
    
    property_ids = fields.Many2many(
        'custody.property',
        string='Properties',
        help='Filter by specific properties'
    )
    
    # Analysis Results (computed)
    total_photos = fields.Integer(
        string='Total Photos',
        compute='_compute_analysis_results'
    )
    
    high_quality_photos = fields.Integer(
        string='High Quality Photos',
        compute='_compute_analysis_results'
    )
    
    quality_percentage = fields.Float(
        string='Quality Percentage',
        compute='_compute_analysis_results'
    )
    
    avg_file_size = fields.Float(
        string='Average File Size (MB)',
        compute='_compute_analysis_results'
    )
    
    missing_handover_photos = fields.Integer(
        string='Missing Handover Photos',
        compute='_compute_analysis_results'
    )
    
    missing_return_photos = fields.Integer(
        string='Missing Return Photos',
        compute='_compute_analysis_results'
    )

    @api.depends('date_from', 'date_to', 'custody_ids', 'employee_ids', 'property_ids')
    def _compute_analysis_results(self):
        for record in self:
            # Build domain for custody records
            domain = [
                ('create_date', '>=', record.date_from),
                ('create_date', '<=', record.date_to)
            ]
            
            if record.custody_ids:
                domain.append(('id', 'in', record.custody_ids.ids))
            
            if record.employee_ids:
                domain.append(('employee_id', 'in', record.employee_ids.ids))
                
            if record.property_ids:
                domain.append(('custody_property_id', 'in', record.property_ids.ids))
            
            custody_records = self.env['hr.custody'].search(domain)
            
            # Analyze photos
            all_photos = self.env['ir.attachment'].search([
                ('res_model', '=', 'hr.custody'),
                ('res_id', 'in', custody_records.ids),
                ('mimetype', 'like', 'image%')
            ])
            
            record.total_photos = len(all_photos)
            record.high_quality_photos = len(all_photos.filtered('is_high_quality'))
            record.quality_percentage = (record.high_quality_photos / record.total_photos * 100) if record.total_photos else 0
            record.avg_file_size = sum(all_photos.mapped('photo_size_mb')) / len(all_photos) if all_photos else 0
            
            # Count missing photos
            approved_or_returned = custody_records.filtered(lambda c: c.state in ['approved', 'returned'])
            record.missing_handover_photos = len(approved_or_returned.filtered(lambda c: not c.has_handover_photos))
            
            returned_records = custody_records.filtered(lambda c: c.state == 'returned')
            record.missing_return_photos = len(returned_records.filtered(lambda c: not c.has_return_photos))

    def action_generate_report(self):
        """Generate detailed photo quality report"""
        self.ensure_one()
        
        # This could be expanded to generate a PDF report
        return {
            'type': 'ir.actions.act_window',
            'name': _('Photo Quality Analysis Report'),
            'res_model': 'custody.photo.quality.analysis.wizard',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': {'show_results': True}
        }

    def action_export_missing_photos(self):
        """Export list of custody records missing photos"""
        self.ensure_one()
        
        # Build domain for custody records
        domain = [
            ('create_date', '>=', self.date_from),
            ('create_date', '<=', self.date_to)
        ]
        
        if self.custody_ids:
            domain.append(('id', 'in', self.custody_ids.ids))
        
        if self.employee_ids:
            domain.append(('employee_id', 'in', self.employee_ids.ids))
            
        if self.property_ids:
            domain.append(('custody_property_id', 'in', self.property_ids.ids))
        
        # Add photo missing conditions
        domain.extend([
            ('state', 'in', ['approved', 'returned']),
            '|',
            ('has_handover_photos', '=', False),
            '&', ('state', '=', 'returned'), ('has_return_photos', '=', False)
        ])
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Custody Records Missing Photos'),
            'res_model': 'hr.custody',
            'view_mode': 'list,form',
            'domain': domain,
            'context': {'create': False},
            'target': 'current'
        }
