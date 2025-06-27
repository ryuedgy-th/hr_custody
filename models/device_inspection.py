# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime


class DeviceInspection(models.Model):
    _name = 'device.inspection'
    _description = 'Device Inspection'
    _order = 'inspection_date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Inspection Reference',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New'),
        help="Unique reference for this inspection"
    )
    property_id = fields.Many2one(
        'custody.property',
        string='Property',
        required=True,
        tracking=True,
        help="Asset/Property being inspected"
    )
    inspection_type_id = fields.Many2one(
        'device.inspection.type',
        string='Inspection Type',
        required=True,
        tracking=True,
        help="Type of inspection being performed"
    )
    inspection_date = fields.Datetime(
        string='Inspection Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        help="Date and time when inspection was performed"
    )
    inspector_id = fields.Many2one(
        'res.users',
        string='Inspector',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help="Person who performed the inspection"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string='Status', 
       default='draft',
       required=True,
       tracking=True,
       help="Current status of the inspection")
    
    overall_condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
    ], string='Overall Condition',
       tracking=True,
       help="Overall assessment of the device condition")
    
    notes = fields.Text(
        string='Inspector Notes',
        help="Additional notes and observations from the inspector"
    )
    issues_found = fields.Text(
        string='Issues Found',
        help="List of issues or problems identified during inspection"
    )
    recommendations = fields.Text(
        string='Recommendations',
        help="Recommended actions based on inspection results"
    )
    
    # Inspection lines
    inspection_line_ids = fields.One2many(
        'device.inspection.line',
        'inspection_id',
        string='Inspection Items',
        help="Detailed inspection checklist items"
    )
    
    # Related fields from property
    property_name = fields.Char(
        related='property_id.name',
        string='Property Name',
        store=True,
        readonly=True
    )
    property_code = fields.Char(
        related='property_id.code',
        string='Property Code',
        store=True,
        readonly=True
    )
    current_custody_id = fields.Many2one(
        related='property_id.custody_id',
        string='Current Custody',
        store=True,
        readonly=True
    )
    current_user_id = fields.Many2one(
        related='property_id.custody_id.employee_id.user_id',
        string='Current User',
        store=True,
        readonly=True
    )
    
    # Computed fields
    line_count = fields.Integer(
        string='Items Count',
        compute='_compute_line_count',
        help="Number of inspection items"
    )
    passed_count = fields.Integer(
        string='Passed Items',
        compute='_compute_line_counts',
        help="Number of items that passed inspection"
    )
    failed_count = fields.Integer(
        string='Failed Items',
        compute='_compute_line_counts',
        help="Number of items that failed inspection"
    )
    pass_rate = fields.Float(
        string='Pass Rate (%)',
        compute='_compute_pass_rate',
        help="Percentage of items that passed inspection"
    )
    
    # Images
    image_ids = fields.One2many(
        'custody.image',
        'inspection_id',
        string='Inspection Photos',
        help="Photos taken during inspection"
    )
    image_count = fields.Integer(
        string='Photos Count',
        compute='_compute_image_count',
        help="Number of photos attached"
    )

    @api.model
    def create(self, vals):
        """Generate sequence number on create"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('device.inspection') or _('New')
        return super().create(vals)

    @api.depends('inspection_line_ids')
    def _compute_line_count(self):
        """Compute the number of inspection lines"""
        for record in self:
            record.line_count = len(record.inspection_line_ids)

    @api.depends('inspection_line_ids.result')
    def _compute_line_counts(self):
        """Compute passed and failed counts"""
        for record in self:
            lines = record.inspection_line_ids
            record.passed_count = len(lines.filtered(lambda l: l.result == 'pass'))
            record.failed_count = len(lines.filtered(lambda l: l.result == 'fail'))

    @api.depends('passed_count', 'line_count')
    def _compute_pass_rate(self):
        """Compute pass rate percentage"""
        for record in self:
            if record.line_count > 0:
                record.pass_rate = (record.passed_count / record.line_count) * 100
            else:
                record.pass_rate = 0.0

    @api.depends('image_ids')
    def _compute_image_count(self):
        """Compute the number of images"""
        for record in self:
            record.image_count = len(record.image_ids)

    def action_start_inspection(self):
        """Start the inspection process"""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_("Only draft inspections can be started."))
        self.write({
            'state': 'in_progress',
            'inspection_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Inspection started by %s") % self.env.user.name)

    def action_complete_inspection(self):
        """Complete the inspection"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise ValidationError(_("Only in-progress inspections can be completed."))
        if not self.inspection_line_ids:
            raise ValidationError(_("Please add at least one inspection item before completing."))
        self.write({'state': 'completed'})
        self.message_post(body=_("Inspection completed by %s") % self.env.user.name)

    def action_approve(self):
        """Approve the inspection"""
        self.ensure_one()
        if self.state != 'completed':
            raise ValidationError(_("Only completed inspections can be approved."))
        self.write({'state': 'approved'})
        self.message_post(body=_("Inspection approved by %s") % self.env.user.name)

    def action_reject(self):
        """Reject the inspection"""
        self.ensure_one()
        if self.state not in ['completed', 'approved']:
            raise ValidationError(_("Only completed or approved inspections can be rejected."))
        self.write({'state': 'rejected'})
        self.message_post(body=_("Inspection rejected by %s") % self.env.user.name)

    def action_reset_to_draft(self):
        """Reset inspection to draft"""
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_("Inspection reset to draft by %s") % self.env.user.name)

    def action_view_images(self):
        """Action to view inspection images"""
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'hr_custody.action_custody_image'
        )
        action['domain'] = [('inspection_id', '=', self.id)]
        action['context'] = {
            'default_inspection_id': self.id,
            'search_default_inspection_id': self.id,
        }
        return action

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.name} - {record.property_name}"
            if record.inspection_type_id:
                name += f" ({record.inspection_type_id.name})"
            result.append((record.id, name))
        return result

    @api.onchange('property_id')
    def _onchange_property_id(self):
        """Update related fields when property changes"""
        if self.property_id and not self.inspection_line_ids:
            # Auto-create some basic inspection lines
            basic_items = [
                {'name': 'Physical Condition', 'description': 'Check overall physical condition'},
                {'name': 'Power/Battery', 'description': 'Check power supply and battery'},
                {'name': 'Screen/Display', 'description': 'Check screen condition and display'},
                {'name': 'Keyboard/Input', 'description': 'Check keyboard and input devices'},
                {'name': 'Ports/Connectivity', 'description': 'Check USB ports and connectivity'},
                {'name': 'Accessories', 'description': 'Check included accessories'},
            ]
            
            lines = []
            for item in basic_items:
                lines.append((0, 0, {
                    'name': item['name'],
                    'description': item['description'],
                    'sequence': len(lines) + 1,
                }))
            self.inspection_line_ids = lines