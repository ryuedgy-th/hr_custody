# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class DeviceInspectionLine(models.Model):
    _name = 'device.inspection.line'
    _description = 'Device Inspection Line'
    _order = 'inspection_id, sequence, id'

    inspection_id = fields.Many2one(
        'device.inspection',
        string='Inspection',
        required=True,
        ondelete='cascade',
        help="Related inspection record"
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help="Sequence for ordering inspection items"
    )
    name = fields.Char(
        string='Item Name',
        required=True,
        help="Name of the inspection item"
    )
    description = fields.Text(
        string='Description',
        help="Detailed description of what to check"
    )
    
    result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('na', 'Not Applicable'),
    ], string='Result',
       help="Result of the inspection for this item")
    
    condition = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged'),
    ], string='Condition',
       help="Condition assessment for this specific item")
    
    notes = fields.Text(
        string='Notes',
        help="Additional notes for this inspection item"
    )
    issues = fields.Text(
        string='Issues',
        help="Specific issues found with this item"
    )
    
    # Scoring system (optional - for more detailed assessments)
    score = fields.Float(
        string='Score',
        help="Numeric score for this item (0-10 scale)",
        default=0.0
    )
    max_score = fields.Float(
        string='Max Score',
        help="Maximum possible score for this item",
        default=10.0
    )
    score_percentage = fields.Float(
        string='Score %',
        compute='_compute_score_percentage',
        help="Score as percentage"
    )
    
    # Related fields
    inspection_state = fields.Selection(
        related='inspection_id.state',
        string='Inspection Status',
        readonly=True,
        store=True
    )
    property_id = fields.Many2one(
        related='inspection_id.property_id',
        string='Property',
        readonly=True,
        store=True
    )
    inspector_id = fields.Many2one(
        related='inspection_id.inspector_id',
        string='Inspector',
        readonly=True,
        store=True
    )

    @api.depends('score', 'max_score')
    def _compute_score_percentage(self):
        """Compute score percentage"""
        for record in self:
            if record.max_score > 0:
                record.score_percentage = (record.score / record.max_score) * 100
            else:
                record.score_percentage = 0.0

    @api.onchange('result')
    def _onchange_result(self):
        """Auto-update score based on result"""
        if self.result == 'pass':
            self.score = self.max_score
        elif self.result == 'fail':
            self.score = 0.0
        elif self.result == 'na':
            self.score = 0.0

    @api.onchange('condition')
    def _onchange_condition(self):
        """Auto-update result and score based on condition"""
        condition_mapping = {
            'excellent': {'result': 'pass', 'score': 10.0},
            'good': {'result': 'pass', 'score': 8.0},
            'fair': {'result': 'pass', 'score': 6.0},
            'poor': {'result': 'fail', 'score': 3.0},
            'damaged': {'result': 'fail', 'score': 0.0},
        }
        
        if self.condition and self.condition in condition_mapping:
            mapping = condition_mapping[self.condition]
            self.result = mapping['result']
            self.score = mapping['score']

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.name
            if record.result:
                name += f" [{record.result.upper()}]"
            result.append((record.id, name))
        return result