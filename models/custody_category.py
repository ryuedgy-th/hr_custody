from odoo import api, fields, models, _


class CustodyCategory(models.Model):
    """
    Model for categorizing custody properties.
    This allows better organization and filtering of company assets.
    """
    _name = 'custody.category'
    _description = 'Custody Property Category'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True,
        help='Name of the category'
    )
    
    code = fields.Char(
        string='Category Code',
        help='Short code for the category (e.g., IT, FURN, VEHICLE)'
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Determines the display order'
    )
    
    description = fields.Text(
        string='Description',
        translate=True,
        help='Detailed description of this category'
    )
    
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Set to false to hide the category without removing it.'
    )
    
    parent_id = fields.Many2one(
        'custody.category',
        string='Parent Category',
        index=True,
        ondelete='cascade',
        help='Parent category for hierarchical categorization'
    )
    
    child_ids = fields.One2many(
        'custody.category',
        'parent_id',
        string='Child Categories',
        help='Sub-categories under this category'
    )
    
    property_count = fields.Integer(
        compute='_compute_property_count',
        string='Properties Count',
        help='Number of properties in this category'
    )
    
    # Default return period for this category (if applicable)
    default_return_type = fields.Selection([
        ('date', 'Fixed Return Date'),
        ('flexible', 'No Fixed Return Date'),
        ('term_end', 'Return at Term/Project End')
    ], 
        string='Default Return Type',
        help='Default return type for properties in this category'
    )
    
    default_return_days = fields.Integer(
        string='Default Return Days',
        help='Default number of days for return (if fixed date)'
    )
    
    color = fields.Integer(
        string='Color Index',
        help='Color for the category when displayed in kanban view'
    )

    complete_name = fields.Char(
        string='Complete Name',
        compute='_compute_complete_name',
        store=True,
        help='Full hierarchical name'
    )
    
    # For image and icon
    image = fields.Binary(
        string="Category Image",
        attachment=True,
        help="This field holds an image used for this category"
    )
    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        """Compute the complete name including parent hierarchy"""
        for category in self:
            if category.parent_id:
                category.complete_name = f"{category.parent_id.complete_name} / {category.name}"
            else:
                category.complete_name = category.name
    
    @api.depends()
    def _compute_property_count(self):
        """Compute the number of properties in each category"""
        property_data = self.env['custody.property'].read_group(
            [('category_id', 'in', self.ids)],
            ['category_id'],
            ['category_id']
        )
        
        # Create a dictionary with the count for each category
        count_dict = {data['category_id'][0]: data['category_id_count'] for data in property_data}
        
        # Set the count for each category
        for category in self:
            category.property_count = count_dict.get(category.id, 0)
    
    def action_view_properties(self):
        """Action to view properties in this category"""
        self.ensure_one()
        return {
            'name': _('Properties in %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.property',
            'view_mode': 'list,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id}
        }
    
    def name_get(self):
        """Override name_get to show hierarchical names"""
        result = []
        for category in self:
            name = category.complete_name or category.name
            if category.code:
                name = f"[{category.code}] {name}"
            result.append((category.id, name))
        return result 