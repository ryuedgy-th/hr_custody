from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    # Count only active custodies
    custody_count = fields.Integer(
        compute='_compute_custody_count',
        string='# Active Custody',
        help='Number of active custody requests'
    )

    # Track total custody history
    total_custody_count = fields.Integer(
        compute='_compute_total_custody_count',
        string='# Total Custody',
        help='Total number of custody requests (all states)'
    )

    equipment_count = fields.Integer(
        compute='_compute_equipment_count',
        string='# Equipment',
        help='Number of equipment currently in possession'
    )

    @api.depends('custody_count')
    def _compute_custody_count(self):
        """Count only ACTIVE custody (approved state)"""
        for employee in self:
            active_custody = self.env['hr.custody'].search_count([
                ('employee_id', '=', employee.id),
                ('state', '=', 'approved')  # Only approved state
            ])
            employee.custody_count = active_custody

    @api.depends('total_custody_count')
    def _compute_total_custody_count(self):
        """Count ALL custody requests (all states)"""
        for employee in self:
            total_custody = self.env['hr.custody'].search_count([
                ('employee_id', '=', employee.id)
                # No filter on state = all states
            ])
            employee.total_custody_count = total_custody

    @api.depends('equipment_count')
    def _compute_equipment_count(self):
        """Count unique equipment currently in possession (approved state only)"""
        for employee in self:
            equipment_records = self.env['hr.custody'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'approved')  # Only approved state
            ])

            # Count unique properties
            unique_properties = set()
            for custody in equipment_records:
                unique_properties.add(custody.custody_property_id.id)

            employee.equipment_count = len(unique_properties)

    def custody_view(self):
        """View all custody records for this employee"""
        self.ensure_one()
        custody_records = self.env['hr.custody'].search([
            ('employee_id', '=', self.id)
        ])

        if not custody_records:
            return {
                'type': 'ir.actions.act_window_close',
            }

        return {
            'name': _('Custody History - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'hr.custody',
            'view_mode': 'list,form',
            'domain': [('employee_id', '=', self.id)],
            'context': {
                'default_employee_id': self.id,
                'search_default_group_status': 1  # Group by status
            }
        }

    def equipment_view(self):
        """View equipment currently in possession (approved custody only)"""
        self.ensure_one()
        approved_custody = self.env['hr.custody'].search([
            ('employee_id', '=', self.id),
            ('state', '=', 'approved')
        ])

        if not approved_custody:
            return {
                'type': 'ir.actions.act_window_close',
            }

        property_ids = approved_custody.mapped('custody_property_id').ids

        return {
            'name': _('Equipment in Possession - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.property',
            'view_mode': 'list,form',
            'domain': [('id', 'in', property_ids)],
            'context': {'create': False, 'edit': False}  # Read-only
        }
