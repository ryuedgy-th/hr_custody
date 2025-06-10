from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PropertyCategory(models.Model):
    """
    Hierarchical categories for custody properties
    Allows organizing equipment into tree structure like:
    - Electronics
      - Computers
        - Laptops
        - Desktops
      - Audio/Visual
        - Projectors
        - Speakers
    - Furniture
      - Office Furniture
      - Classroom Furniture
    """
    _name = 'property.category'
    _description = 'Property Category'
    _order = 'complete_name'
    _rec_name = 'complete_name'
    _parent_store = True  # Enables efficient tree operations
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Enable chatter

    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True,
        help='Name of the property category',
        tracking=True
    )

    complete_name = fields.Char(
        string='Complete Name',
        compute='_compute_complete_name',
        recursive=True,
        store=True,
        help='Complete path of the category (e.g., "Electronics / Computers / Laptops")'
    )

    parent_id = fields.Many2one(
        'property.category',
        string='Parent Category',
        index=True,
        ondelete='cascade',
        help='Parent category in the hierarchy',
        tracking=True
    )

    child_ids = fields.One2many(
        'property.category',
        'parent_id',
        string='Child Categories',
        help='Sub-categories under this category'
    )

    parent_path = fields.Char(
        index=True,
        help='Technical field for hierarchical operations'
    )

    # ⭐ NEW: Relationship to properties
    property_ids = fields.One2many(
        'custody.property',
        'category_id',
        string='Properties',
        help='Properties directly assigned to this category'
    )

    # Category Information
    description = fields.Text(
        string='Description',
        translate=True,
        help='Detailed description of this category',
        tracking=True
    )

    image = fields.Image(
        string='Category Image',
        help='Image representing this category'
    )

    # Category Settings
    active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, this category will be hidden from selection',
        tracking=True
    )

    color = fields.Integer(
        string='Color',
        help='Color for visual identification in interfaces'
    )

    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order of display within the same parent category'
    )

    # Category Management
    approver_ids = fields.Many2many(
        'res.users',
        'category_approver_rel',
        'category_id',
        'user_id',
        string='Default Approvers',
        help='Default approvers for properties in this category (inherited by properties)',
        tracking=True
    )

    responsible_department_id = fields.Many2one(
        'hr.department',
        string='Responsible Department',
        help='Default department responsible for properties in this category',
        tracking=True
    )

    # ⭐ FIXED: Category Statistics with store=True and recursive=True for searchability
    property_count = fields.Integer(
        string='Properties Count',
        compute='_compute_property_statistics',
        store=True,
        recursive=True,  # ⭐ Added recursive=True to fix warning
        help='Number of properties directly in this category'
    )

    total_property_count = fields.Integer(
        string='Total Properties',
        compute='_compute_property_statistics',
        store=True,
        recursive=True,  # ⭐ Added recursive=True to fix warning
        help='Total properties in this category and all subcategories'
    )

    active_custody_count = fields.Integer(
        string='Active Custodies',
        compute='_compute_property_statistics',
        store=True,
        help='Number of active custodies for properties in this category tree'
    )

    # Technical fields for performance
    is_parent = fields.Boolean(
        string='Is Parent',
        compute='_compute_is_parent',
        store=True,
        help='Technical field to identify parent categories'
    )

    level = fields.Integer(
        string='Level',
        compute='_compute_level',
        help='Depth level in the hierarchy (0 for root categories)'
    )

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        """Compute the complete hierarchical name"""
        for category in self:
            if category.parent_id:
                category.complete_name = f"{category.parent_id.complete_name} / {category.name}"
            else:
                category.complete_name = category.name

    @api.depends('child_ids')
    def _compute_is_parent(self):
        """Compute if this category has children"""
        for category in self:
            category.is_parent = bool(category.child_ids)

    @api.depends('parent_path')
    def _compute_level(self):
        """Compute the hierarchy level"""
        for category in self:
            if category.parent_path:
                # parent_path format: "1/2/3/" - count slashes and subtract 1
                category.level = category.parent_path.count('/') - 1
            else:
                category.level = 0

    # ⭐ FIXED: Simplified dependencies to avoid field resolution errors
    @api.depends('property_ids', 'child_ids.property_count', 'child_ids.total_property_count')
    def _compute_property_statistics(self):
        """Compute statistics about properties in this category"""
        for category in self:
            # Direct properties in this category
            direct_properties = self.env['custody.property'].search([
                ('category_id', '=', category.id)
            ])
            category.property_count = len(direct_properties)

            # All properties in this category tree (including subcategories)
            all_category_ids = self._get_all_children_ids(category.id)
            all_properties = self.env['custody.property'].search([
                ('category_id', 'in', all_category_ids)
            ])
            category.total_property_count = len(all_properties)

            # Active custodies for all properties in this category tree
            active_custodies = self.env['hr.custody'].search([
                ('custody_property_id', 'in', all_properties.ids),
                ('state', '=', 'approved')
            ])
            category.active_custody_count = len(active_custodies)

    def _get_all_children_ids(self, category_id):
        """Get all children category IDs including the category itself"""
        if not category_id:
            return []
        
        # Use parent_path for efficient tree query
        category = self.browse(category_id)
        if not category.exists():
            return []
            
        # Find all categories that have this category in their parent_path
        children = self.search([
            ('parent_path', '=like', f"{category.parent_path}%")
        ])
        return children.ids

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        """Prevent circular references in the hierarchy"""
        # ⭐ FIXED: Use not _has_cycle() instead of _check_recursion() for Odoo 18
        if self._has_cycle():
            raise ValidationError(_('You cannot create recursive categories.'))

    @api.constrains('parent_id')
    def _check_parent_company(self):
        """Ensure parent category belongs to the same company if applicable"""
        for category in self:
            if category.parent_id:
                # Add company validation if needed in the future
                pass

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Enhanced search to find categories by complete name"""
        if args is None:
            args = []

        if name:
            # Search in both name and complete_name
            domain = [
                '|',
                ('name', operator, name),
                ('complete_name', operator, name)
            ]
            categories = self.search(domain + args, limit=limit)
            return categories.name_get()

        return super().name_search(name, args, operator, limit)

    def name_get(self):
        """Return complete name for better identification"""
        result = []
        for category in self:
            name = category.complete_name or category.name
            if category.property_count > 0:
                name += f" ({category.property_count})"
            result.append((category.id, name))
        return result

    # Actions
    def action_view_properties(self):
        """View all properties in this category and subcategories"""
        self.ensure_one()
        all_category_ids = self._get_all_children_ids(self.id)
        
        return {
            'name': _('Properties in %s') % self.complete_name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.property',
            'view_mode': 'list,form',
            'domain': [('category_id', 'in', all_category_ids)],
            'context': {
                'default_category_id': self.id,
                'search_default_group_by_category': 1
            }
        }

    def action_view_custodies(self):
        """View all custodies for properties in this category"""
        self.ensure_one()
        all_category_ids = self._get_all_children_ids(self.id)
        property_ids = self.env['custody.property'].search([
            ('category_id', 'in', all_category_ids)
        ]).ids

        return {
            'name': _('Custodies in %s') % self.complete_name,
            'type': 'ir.actions.act_window',
            'res_model': 'hr.custody',
            'view_mode': 'list,form',
            'domain': [('custody_property_id', 'in', property_ids)],
            'context': {
                'search_default_group_by_property': 1
            }
        }

    def action_create_subcategory(self):
        """Create a new subcategory under this category"""
        self.ensure_one()
        return {
            'name': _('Create Subcategory'),
            'type': 'ir.actions.act_window',
            'res_model': 'property.category',
            'view_mode': 'form',
            'context': {
                'default_parent_id': self.id
            },
            'target': 'new'
        }

    @api.model
    def create_default_categories(self):
        """Create default category structure for international schools"""
        # This method can be called to set up initial categories
        categories_data = [
            # Electronics
            {
                'name': 'Electronics',
                'description': 'Electronic devices and equipment',
                'children': [
                    {
                        'name': 'Computers',
                        'description': 'Desktop and laptop computers',
                        'children': [
                            {'name': 'Laptops', 'description': 'Portable computers'},
                            {'name': 'Desktops', 'description': 'Desktop computers'},
                            {'name': 'Tablets', 'description': 'Tablet devices including iPads'},
                        ]
                    },
                    {
                        'name': 'Audio/Visual',
                        'description': 'Audio and visual equipment',
                        'children': [
                            {'name': 'Projectors', 'description': 'Display projectors'},
                            {'name': 'Speakers', 'description': 'Audio speakers and sound systems'},
                            {'name': 'Cameras', 'description': 'Digital cameras and recording equipment'},
                            {'name': 'Microphones', 'description': 'Microphones and audio input devices'},
                        ]
                    },
                    {
                        'name': 'Accessories',
                        'description': 'Electronic accessories',
                        'children': [
                            {'name': 'Cables', 'description': 'Various cables and adapters'},
                            {'name': 'Chargers', 'description': 'Device chargers and power supplies'},
                            {'name': 'Storage', 'description': 'External drives and storage devices'},
                        ]
                    }
                ]
            },
            # Furniture
            {
                'name': 'Furniture',
                'description': 'Furniture and fixtures',
                'children': [
                    {'name': 'Office Furniture', 'description': 'Desks, chairs, and office equipment'},
                    {'name': 'Classroom Furniture', 'description': 'Student desks, whiteboards, etc.'},
                    {'name': 'Storage Furniture', 'description': 'Cabinets, shelves, and storage units'},
                ]
            },
            # Educational Materials
            {
                'name': 'Educational Materials',
                'description': 'Teaching and learning materials',
                'children': [
                    {'name': 'Books', 'description': 'Textbooks and reference materials'},
                    {'name': 'Laboratory Equipment', 'description': 'Science lab equipment and supplies'},
                    {'name': 'Sports Equipment', 'description': 'Physical education and sports equipment'},
                    {'name': 'Art Supplies', 'description': 'Art and craft materials'},
                ]
            },
            # Vehicles
            {
                'name': 'Vehicles',
                'description': 'School vehicles and transportation',
                'children': [
                    {'name': 'School Buses', 'description': 'School transportation buses'},
                    {'name': 'Staff Vehicles', 'description': 'Vehicles for staff use'},
                ]
            }
        ]

        def create_category_tree(data, parent_id=None):
            """Recursively create category tree"""
            for item in data:
                category_vals = {
                    'name': item['name'],
                    'description': item.get('description', ''),
                    'parent_id': parent_id,
                }
                category = self.create(category_vals)
                
                if 'children' in item:
                    create_category_tree(item['children'], category.id)

        create_category_tree(categories_data)
        return True
