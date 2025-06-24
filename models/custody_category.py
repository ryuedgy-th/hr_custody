from lxml import etree

from odoo import api, fields, models, _

# Category prediction keywords - configurable constants
DEFAULT_CATEGORY_KEYWORDS = {
    'laptop': 'IT Equipment',
    'computer': 'IT Equipment',
    'mouse': 'IT Equipment',
    'keyboard': 'IT Equipment',
    'monitor': 'IT Equipment',
    'printer': 'IT Equipment',
    'phone': 'Communication Devices',
    'mobile': 'Communication Devices',
    'desk': 'Furniture',
    'chair': 'Furniture',
    'table': 'Furniture',
    'cabinet': 'Furniture',
    'car': 'Vehicles',
    'vehicle': 'Vehicles',
    'book': 'Office Supplies',
    'pen': 'Office Supplies',
    'paper': 'Office Supplies',
}


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
    
    # NEW FIELDS: Category Lifecycle Management
    lifecycle_stage = fields.Selection([
        ('active', 'Active'),
        ('phasing_out', 'Phasing Out'),
        ('archived', 'Archived')
    ], string='Lifecycle Stage', default='active', tracking=True,
       help='Stage in the category lifecycle')
    
    # NEW FIELDS: Approval Requirements
    requires_approval = fields.Boolean(
        string='Requires Specific Approvers',
        default=False,
        help='Enable to specify approvers for properties in this category'
    )
    
    approver_ids = fields.Many2many(
        'res.users',
        'custody_category_approver_rel',
        'category_id',
        'user_id',
        string='Default Approvers',
        help='Users who can approve custody requests for properties in this category'
    )
    
    inherit_parent_approvers = fields.Boolean(
        string='Inherit Parent Approvers',
        default=True,
        help='Also use approvers from parent category'
    )
    
    # Extended property count to include subcategories
    total_property_count = fields.Integer(
        compute='_compute_total_property_count',
        string='Total Properties',
        help='Total number of properties in this category and subcategories'
    )
    
    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        """Compute the complete name including parent hierarchy"""
        for category in self:
            if category.parent_id:
                category.complete_name = f"{category.parent_id.complete_name} / {category.name}"
            else:
                category.complete_name = category.name
    
    @api.depends('property_ids')
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
    
    @api.depends('property_count', 'child_ids.property_count', 'child_ids.total_property_count')
    def _compute_total_property_count(self):
        """Compute total number of properties including subcategories"""
        for category in self:
            total = category.property_count
            for child in category.child_ids:
                total += child.total_property_count
            category.total_property_count = total
    
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
        
    # NEW METHODS: Category Lifecycle Management
    def action_set_phasing_out(self):
        """Start phasing out this category"""
        self.lifecycle_stage = 'phasing_out'
        return self._notify_lifecycle_change('phasing_out')
        
    def action_set_archived(self):
        """Archive this category"""
        self.lifecycle_stage = 'archived'
        self.active = False
        return self._notify_lifecycle_change('archived')
        
    def action_set_active(self):
        """Set category back to active"""
        self.lifecycle_stage = 'active'
        self.active = True
        return self._notify_lifecycle_change('active')
        
    def _notify_lifecycle_change(self, stage):
        """Send notification about lifecycle change"""
        for category in self:
            category.message_post(
                body=_("Category lifecycle changed to: %s") % dict(
                    self._fields['lifecycle_stage'].selection).get(stage)
            )
        return True
        
    @api.model
    def predict_category_for_property(self, property_name, description=None):
        """Predict the most appropriate category for a property based on its name and description"""
        # A simple keyword-based approach - could be enhanced with ML techniques
        property_name = (property_name or "").lower()
        description = (description or "").lower()
        
        # Create a combined text for searching
        text = f"{property_name} {description}"
        
        # Get category keywords from system parameter or use defaults
        category_keywords = self.env['ir.config_parameter'].get_param(
            'hr_custody.category_keywords'
        )
        if category_keywords:
            try:
                import json
                category_keywords = json.loads(category_keywords)
            except (ValueError, json.JSONDecodeError):
                category_keywords = DEFAULT_CATEGORY_KEYWORDS
        else:
            category_keywords = DEFAULT_CATEGORY_KEYWORDS
        
        # Find matching categories
        matches = {}
        for keyword, category_name in category_keywords.items():
            if keyword in text:
                matches[category_name] = matches.get(category_name, 0) + 1
        
        # Return the category with the most matches
        if matches:
            best_match = max(matches.items(), key=lambda x: x[1])[0]
            category = self.search([('name', '=', best_match)], limit=1)
            if category:
                return category.id
        
        # Default to uncategorized if no match found
        return False

    @api.model
    def get_property_fields_view(self, view_id=None, view_type='form', **options):
        """Get a customized form view for property based on category"""
        # Get the standard view first
        res = self.env['custody.property'].fields_view_get(view_id=view_id, view_type=view_type, **options)
        
        # Check if we're in a context with a specific category
        category_id = options.get('default_category_id')
        if view_type == 'form' and category_id:
            category = self.browse(category_id)
            if category.exists():
                # Parse the view
                doc = etree.XML(res['arch'])
                
                # Example: Add category-specific fields to a notebook page
                # This is just a demonstration - real implementation would be more complex
                if category.name == 'IT Equipment':
                    # Add IT specific fields to a new notebook page
                    notebook = doc.xpath("//notebook")
                    if notebook:
                        page = etree.SubElement(notebook[0], 'page', {
                            'string': 'IT Specifications',
                            'name': 'it_specs',
                        })
                        group = etree.SubElement(page, 'group')
                        # These would need to be actual fields on the model
                        fields = [
                            ('processor', 'Processor'),
                            ('ram', 'RAM'),
                            ('storage', 'Storage'),
                            ('os', 'Operating System'),
                        ]
                        for field, label in fields:
                            field_elem = etree.SubElement(group, 'field', {'name': field})
                            field_elem.set('invisible', "context.get('hide_it_fields', False)")
                
                # Update the arch
                res['arch'] = etree.tostring(doc, encoding='unicode')
        
        return res

    def get_effective_approvers(self):
        """Get all approvers for this category, including inherited ones"""
        self.ensure_one()
        
        approvers = self.approver_ids
        
        # Add parent approvers if needed
        if self.inherit_parent_approvers and self.parent_id:
            parent_approvers = self.parent_id.get_effective_approvers()
            approvers |= parent_approvers
            
        return approvers 