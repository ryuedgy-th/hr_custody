# -*- coding: utf-8 -*-

from odoo import models, fields, api


class DeviceInspectionType(models.Model):
    _name = 'device.inspection.type'
    _description = 'Device Inspection Type'
    _order = 'sequence, name'

    name = fields.Char(
        string='Inspection Type',
        required=True,
        translate=True,
        help="Name of the inspection type (e.g., End of Term Check, Renewal Check)"
    )
    description = fields.Text(
        string='Description',
        translate=True,
        help="Description of when and why this inspection type is used"
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Sequence for ordering inspection types"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help="Uncheck to archive this inspection type"
    )
    color = fields.Integer(
        string='Color',
        default=0,
        help="Color index for kanban view"
    )
    inspection_count = fields.Integer(
        string='Inspection Count',
        compute='_compute_inspection_count',
        help="Number of inspections using this type"
    )

    @api.depends('name')
    def _compute_inspection_count(self):
        """Compute the number of inspections for each type"""
        for record in self:
            record.inspection_count = self.env['device.inspection'].search_count([
                ('inspection_type_id', '=', record.id)
            ])

    def action_view_inspections(self):
        """Action to view inspections of this type"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'hr_custody.action_device_inspection'
        )
        action['domain'] = [('inspection_type_id', '=', self.id)]
        action['context'] = {
            'default_inspection_type_id': self.id,
            'search_default_inspection_type_id': self.id,
        }
        return action

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            result.append((record.id, record.name))
        return result

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Custom name search"""
        if args is None:
            args = []
        if name:
            records = self.search([
                '|',
                ('name', operator, name),
                ('description', operator, name)
            ] + args, limit=limit)
        else:
            records = self.search(args, limit=limit)
        return records.name_get()