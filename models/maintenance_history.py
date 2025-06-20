from odoo import api, fields, models, _


class MaintenanceHistory(models.Model):
    _name = 'custody.maintenance.history'
    _description = 'Property Maintenance History'
    _order = 'maintenance_date desc'
    _rec_name = 'display_name'

    property_id = fields.Many2one(
        'custody.property',
        string='Property',
        required=True,
        ondelete='cascade'
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
    ], string='Maintenance Type', required=True)
    
    performed_by = fields.Many2one(
        'hr.employee',
        string='Performed By',
        help='Internal employee who performed the maintenance'
    )
    
    vendor_id = fields.Many2one(
        'res.partner',
        string='External Vendor',
        domain=[('supplier_rank', '>', 0)],
        help='External vendor who performed the maintenance'
    )
    
    cost = fields.Float(
        string='Cost',
        help='Cost of maintenance'
    )
    
    notes = fields.Text(
        string='Notes',
        help='Detailed notes about the maintenance performed'
    )
    
    next_maintenance_date = fields.Date(
        string='Next Scheduled Date',
        help='Date for the next scheduled maintenance'
    )
    
    # Computed fields for display
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    performer_display = fields.Char(
        string='Performed By',
        compute='_compute_performer_display',
        store=True
    )
    
    type_display = fields.Char(
        string='Type',
        compute='_compute_type_display',
        store=True
    )
    
    @api.depends('maintenance_date', 'maintenance_type', 'property_id')
    def _compute_display_name(self):
        """Compute display name for record"""
        type_map = {
            'preventive': 'Preventive',
            'corrective': 'Corrective', 
            'emergency': 'Emergency'
        }
        for record in self:
            type_name = type_map.get(record.maintenance_type, 'Maintenance')
            record.display_name = f"{type_name} - {record.maintenance_date} - {record.property_id.name}"
    
    @api.depends('performed_by', 'vendor_id')
    def _compute_performer_display(self):
        """Compute who performed the maintenance"""
        for record in self:
            if record.performed_by:
                record.performer_display = f"👤 {record.performed_by.name}"
            elif record.vendor_id:
                record.performer_display = f"🏢 {record.vendor_id.name}"
            else:
                record.performer_display = "Not specified"
    
    @api.depends('maintenance_type')
    def _compute_type_display(self):
        """Compute maintenance type with emoji"""
        type_emoji = {
            'preventive': '🟢 Preventive Maintenance',
            'corrective': '🟡 Corrective Maintenance',
            'emergency': '🔴 Emergency Repair'
        }
        for record in self:
            record.type_display = type_emoji.get(record.maintenance_type, record.maintenance_type)