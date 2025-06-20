from odoo import api, fields, models, _
from datetime import timedelta


class RecordMaintenanceWizard(models.TransientModel):
    _name = 'custody.record.maintenance.wizard'
    _description = 'Record Property Maintenance'

    property_id = fields.Many2one(
        'custody.property',
        string='Property',
        required=True,
        readonly=True
    )
    
    maintenance_date = fields.Date(
        string='Maintenance Date',
        required=True,
        default=fields.Date.today
    )
    
    maintenance_type = fields.Selection([
        ('preventive', 'Preventive Maintenance'),
        ('corrective', 'Corrective Maintenance'),
        ('emergency', 'Emergency Repair')
    ], string='Maintenance Type', required=True, default='preventive')
    
    performed_by = fields.Many2one(
        'hr.employee',
        string='Performed By',
        help='Person who performed the maintenance'
    )
    
    vendor_id = fields.Many2one(
        'res.partner',
        string='Vendor',
        domain=[('supplier_rank', '>', 0)],
        help='External vendor who performed the maintenance'
    )
    
    cost = fields.Float(
        string='Cost',
        help='Cost of maintenance'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Notes about the maintenance performed'
    )
    
    next_maintenance_date = fields.Date(
        string='Next Maintenance Date',
        help='Date for the next scheduled maintenance'
    )
    
    update_status = fields.Boolean(
        string='Update Property Status',
        default=True,
        help='Update property status to Available'
    )
    
    preserve_in_use_status = fields.Boolean(
        string='Preserve "In Use" Status',
        default=True,
        help='If checked and property was in use, it will remain in use after maintenance'
    )
    
    image_ids = fields.Many2many(
        'ir.attachment',
        string='Maintenance Images',
        help='Images documenting the maintenance'
    )
    
    @api.onchange('property_id')
    def _onchange_property(self):
        """Set default values based on property settings"""
        if self.property_id:
            # Set default performer to responsible person
            self.performed_by = self.property_id.responsible_person
            
            # Calculate next maintenance date based on frequency
            if self.property_id.maintenance_frequency != 'none':
                base_date = self.maintenance_date
                
                if self.property_id.maintenance_frequency == 'monthly':
                    self.next_maintenance_date = base_date + timedelta(days=30)
                elif self.property_id.maintenance_frequency == 'quarterly':
                    self.next_maintenance_date = base_date + timedelta(days=90)
                elif self.property_id.maintenance_frequency == 'biannual':
                    self.next_maintenance_date = base_date + timedelta(days=182)
                elif self.property_id.maintenance_frequency == 'annual':
                    self.next_maintenance_date = base_date + timedelta(days=365)
                elif self.property_id.maintenance_frequency == 'custom' and self.property_id.maintenance_interval > 0:
                    self.next_maintenance_date = base_date + timedelta(days=self.property_id.maintenance_interval)
    
    def action_record_maintenance(self):
        """Record the maintenance and update the property"""
        self.ensure_one()
        
        # Update property with maintenance information
        vals = {
            'last_maintenance_date': self.maintenance_date,
            'next_maintenance_date': self.next_maintenance_date,
        }
        
        # Update property status if requested
        if self.update_status:
            # Check if we should preserve the 'in_use' status
            if self.preserve_in_use_status and self.property_id.property_status == 'in_use':
                vals['property_status'] = 'in_use'
            else:
                vals['property_status'] = 'available'
            
        # Update the property
        self.property_id.write(vals)
        
        # Create maintenance log message
        message_body = _("""
            <strong>Maintenance Recorded</strong><br/>
            <ul>
                <li><strong>Date:</strong> %s</li>
                <li><strong>Type:</strong> %s</li>
                <li><strong>Performed by:</strong> %s</li>
                <li><strong>Next scheduled:</strong> %s</li>
            </ul>
            <p>%s</p>
        """) % (
            fields.Date.to_string(self.maintenance_date),
            dict(self._fields['maintenance_type'].selection).get(self.maintenance_type),
            self.performed_by.name if self.performed_by else _('N/A'),
            fields.Date.to_string(self.next_maintenance_date) if self.next_maintenance_date else _('N/A'),
            self.notes or ''
        )
        
        # Post message with maintenance details
        self.property_id.message_post(
            body=message_body,
            subtype_id=self.env.ref('mail.mt_note').id
        )
        
        # Attach images if any
        if self.image_ids:
            for attachment in self.image_ids:
                attachment.write({
                    'res_model': 'custody.property',
                    'res_id': self.property_id.id,
                })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Maintenance Recorded'),
                'message': _('Maintenance has been recorded successfully.'),
                'sticky': False,
                'type': 'success',
            }
        } 