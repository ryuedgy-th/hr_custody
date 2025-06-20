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
    
    # Temporarily removed image_ids to fix OwlError
    # image_ids = fields.Many2many(
    #     'ir.attachment',
    #     string='Maintenance Images',
    #     help='Images documenting the maintenance'
    # )
    
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
        
        # Create maintenance history record
        self.env['custody.maintenance.history'].create({
            'property_id': self.property_id.id,
            'maintenance_date': self.maintenance_date,
            'maintenance_type': self.maintenance_type,
            'performed_by': self.performed_by.id if self.performed_by else False,
            'vendor_id': self.vendor_id.id if self.vendor_id else False,
            'cost': self.cost,
            'notes': self.notes,
            'next_maintenance_date': self.next_maintenance_date,
        })
        
        # Create enhanced maintenance log message
        maintenance_details = []
        maintenance_details.append(f"<strong>📅 Date:</strong> {fields.Date.to_string(self.maintenance_date)}")
        maintenance_details.append(f"<strong>🔧 Type:</strong> {dict(self._fields['maintenance_type'].selection).get(self.maintenance_type)}")
        
        if self.performed_by:
            maintenance_details.append(f"<strong>👤 Performed by:</strong> {self.performed_by.name}")
        if self.vendor_id:
            maintenance_details.append(f"<strong>🏢 Vendor:</strong> {self.vendor_id.name}")
        if self.cost:
            maintenance_details.append(f"<strong>💰 Cost:</strong> {self.cost:,.2f}")
        if self.next_maintenance_date:
            maintenance_details.append(f"<strong>📅 Next scheduled:</strong> {fields.Date.to_string(self.next_maintenance_date)}")
        
        message_body = f"""
            <div style="border-left: 4px solid #17a2b8; padding-left: 15px; margin: 10px 0;">
                <h4 style="color: #17a2b8; margin-bottom: 10px;">🔧 Maintenance Recorded</h4>
                <ul style="list-style: none; padding-left: 0;">
                    {''.join(f'<li style="margin: 5px 0;">{detail}</li>' for detail in maintenance_details)}
                </ul>
                {f'<div style="margin-top: 10px;"><strong>📝 Notes:</strong><br/>{self.notes}</div>' if self.notes else ''}
            </div>
        """
        
        # Post message with enhanced maintenance details
        self.property_id.message_post(
            body=message_body,
            subject=f"Maintenance Recorded - {self.maintenance_type.replace('_', ' ').title()}",
            subtype_id=self.env.ref('mail.mt_note').id
        )
        
        # Attach images if any
        # Temporarily disabled to fix OwlError
        # if self.image_ids:
        #     for attachment in self.image_ids:
        #         attachment.write({
        #             'res_model': 'custody.property',
        #             'res_id': self.property_id.id,
        #         })
        
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