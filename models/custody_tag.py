from odoo import api, fields, models, _


class CustodyTag(models.Model):
    """
    Model for tagging custody properties.
    Tags allow flexible labeling and filtering of properties.
    """
    _name = 'custody.tag'
    _description = 'Custody Property Tag'
    _order = 'name'
    
    name = fields.Char(
        string='Tag Name',
        required=True,
        translate=True,
        help='Name of the tag'
    )
    
    color = fields.Integer(
        string='Color Index',
        help='Color for the tag when displayed in kanban view'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to hide the tag without removing it'
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help='A description of what this tag represents'
    )
    
    property_count = fields.Integer(
        compute='_compute_property_count',
        string='Properties Count',
        help='Number of properties with this tag'
    )
    
    @api.depends('property_ids')
    def _compute_property_count(self):
        """Compute the number of properties for each tag"""
        property_data = self.env['custody.property'].read_group(
            [('tag_ids', 'in', self.ids)],
            ['tag_ids'],
            ['tag_ids']
        )
        
        # Create a dictionary with the count for each tag
        count_dict = {}
        for data in property_data:
            for tag_id in data.get('tag_ids', []):
                count_dict[tag_id] = data['tag_ids_count']
        
        # Set the count for each tag
        for tag in self:
            tag.property_count = count_dict.get(tag.id, 0)
    
    def action_view_properties(self):
        """Action to view properties with this tag"""
        self.ensure_one()
        return {
            'name': _('Properties with tag %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.property',
            'view_mode': 'list,form',
            'domain': [('tag_ids', 'in', self.id)],
            'context': {
                'default_tag_ids': [(4, self.id)]
            }
        } 