from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CustodyProperty(models.Model):
    """
        Hr property creation model.
    """
    _name = 'custody.property'
    _description = 'Custody Property'
    _order = 'name'
    _rec_name = 'name'

    name = fields.Char(
        string='Property Name',
        required=True,
        help='Enter the name of the custody property'
    )

    image = fields.Image(
        string="Image",
        help="This field holds the image used for "
             "this provider, limited to 1024x1024px",
        prefetch=False
    )

    desc = fields.Html(
        string='Description',
        help='A detailed description of the item.',
        sanitize=True,
        prefetch=False
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        help='The company associated with this record.',
        default=lambda self: self.env.company
    )

    property_selection = fields.Selection([
        ('empty', 'No Connection'),
        ('product', 'Products')
    ],
        default='empty',
        string='Property From',
        help="Select the property"
    )

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help="Select the Product"
    )

    # Categories and Tags
    category_id = fields.Many2one(
        'custody.category',
        string='Category',
        index=True,
        help='Category of this property'
    )
    
    tag_ids = fields.Many2many(
        'custody.tag',
        'custody_property_tag_rel',
        'property_id',
        'tag_id',
        string='Tags',
        help='Tags to categorize properties'
    )

    # Storage and Location Information
    storage_location = fields.Char(
        string='Storage Location',
        help='Where this property is normally stored (e.g., "IT Room Cabinet A1", "Storage Room Shelf 5")'
    )

    department_id = fields.Many2one(
        'hr.department',
        string='Responsible Department',
        help='Department responsible for this property'
    )

    responsible_person = fields.Many2one(
        'hr.employee',
        string='Responsible Person',
        help='Person responsible for maintaining this property'
    )

    property_code = fields.Char(
        string='Property Code',
        help='Internal code or asset tag for this property'
    )

    # Multiple Approvers
    approver_ids = fields.Many2many(
        'res.users',
        'custody_property_approver_rel',
        'property_id',
        'user_id',
        string='Approvers',
        help='Users who can approve custody requests for this property'
    )

    # Property Status and Availability
    property_status = fields.Selection([
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
        ('damaged', 'Damaged'),
        ('retired', 'Retired')
    ], string='Property Status', default='available', help='Current status of the property')

    # Computed fields for better tracking
    custody_count = fields.Integer(
        string='Total Custodies',
        compute='_compute_custody_counts',
        store=True,
        help='Total number of custody records for this property'
    )

    active_custody_count = fields.Integer(
        string='Active Custodies',
        compute='_compute_custody_counts',
        store=True,
        help='Number of active custodies for this property'
    )

    current_borrower_id = fields.Many2one(
        'hr.employee',
        string='Current Borrower',
        compute='_compute_current_borrower',
        store=True,
        help='Employee currently borrowing this property'
    )

    current_custody_id = fields.Many2one(
        'hr.custody',
        string='Current Custody',
        compute='_compute_current_borrower',
        store=True,
        help='Current active custody record'
    )

    is_available = fields.Boolean(
        string='Available',
        compute='_compute_is_available',
        store=True,
        help='Whether this property is available for custody'
    )

    # History fields
    last_maintenance_date = fields.Date(
        string='Last Maintenance Date',
        help='Date of last maintenance or inspection'
    )

    next_maintenance_date = fields.Date(
        string='Next Maintenance Date',
        help='Scheduled date for next maintenance'
    )

    purchase_date = fields.Date(
        string='Purchase Date',
        help='Date when this property was purchased'
    )

    purchase_value = fields.Float(
        string='Purchase Value',
        help='Original purchase value of this property'
    )

    # Auto-select default return period based on category
    @api.onchange('category_id')
    def _onchange_category_id(self):
        """Auto-fill default return period based on category settings"""
        if self.category_id and self.category_id.default_return_type:
            # Get and set default values from category
            self.approver_ids = self.category_id.get_effective_approvers()
            
            return {
                'domain': {},
                'value': {
                    # Add values to be set when creating custody records
                }
            }

    @api.depends('product_id')
    def _onchange_product_id(self):
        """The function is used to
            change product Automatic
            fill name field"""
        for record in self:
            if record.product_id:
                record.name = record.product_id.name
                
                # Try to predict category if not already set
                if not record.category_id:
                    category_id = self.env['custody.category'].predict_category_for_property(
                        record.name, record.desc)
                    if category_id:
                        record.category_id = category_id

    @api.depends()
    def _compute_custody_counts(self):
        """Compute the number of custodies for this property using read_group for better performance"""
        # Get all custody counts in one query
        all_custody_data = self.env['hr.custody'].read_group(
            [('custody_property_id', 'in', self.ids)],
            ['custody_property_id'],
            ['custody_property_id']
        )
        
        # Get active custody counts in one query
        active_custody_data = self.env['hr.custody'].read_group(
            [('custody_property_id', 'in', self.ids), ('state', '=', 'approved')],
            ['custody_property_id'],
            ['custody_property_id']
        )
        
        # Create dictionaries for faster lookup
        all_counts = {data['custody_property_id'][0]: data['custody_property_id_count'] for data in all_custody_data}
        active_counts = {data['custody_property_id'][0]: data['custody_property_id_count'] for data in active_custody_data}
        
        # Set the values for each property
        for record in self:
            record.custody_count = all_counts.get(record.id, 0)
            record.active_custody_count = active_counts.get(record.id, 0)

    @api.depends('active_custody_count', 'property_status')
    def _compute_current_borrower(self):
        """Compute current borrower information and auto-update status using efficient queries"""
        # Get all active custodies in one query for better performance
        active_custodies = self.env['hr.custody'].search([
            ('custody_property_id', 'in', self.ids),
            ('state', '=', 'approved')
        ])
        
        # Create a dictionary mapping property_id to custody record
        property_to_custody = {}
        for custody in active_custodies:
            if custody.custody_property_id.id not in property_to_custody:
                property_to_custody[custody.custody_property_id.id] = custody
        
        # Process each property
        for record in self:
            current_custody = property_to_custody.get(record.id, False)
            
            if current_custody:
                record.current_borrower_id = current_custody.employee_id
                record.current_custody_id = current_custody
                # Auto update status to 'in_use' when someone borrows
                if record.property_status == 'available':
                    record.property_status = 'in_use'
            else:
                record.current_borrower_id = False
                record.current_custody_id = False
                # Auto update status to 'available' when returned (only if it was in_use)
                if record.property_status == 'in_use':
                    record.property_status = 'available'

    @api.depends('property_status', 'active_custody_count')
    def _compute_is_available(self):
        """Compute if the property is available for custody"""
        for record in self:
            record.is_available = (
                record.property_status == 'available' and
                record.active_custody_count == 0
            )

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to search in multiple fields"""
        if args is None:
            args = []

        if name:
            domain = [
                '|', '|', '|', '|', '|',
                ('name', operator, name),  # Property name
                ('property_code', operator, name),  # Property code
                ('desc', operator, name),  # Description
                ('storage_location', operator, name),  # Storage location
                ('current_borrower_id.name', operator, name),  # Current borrower name
                ('department_id.name', operator, name)  # Department name
            ]
            records = self.search(domain + args, limit=limit)
            return records.name_get()

        return super(CustodyProperty, self).name_search(name, args, operator, limit)

    def name_get(self):
        """Override name_get to show availability status and current borrower"""
        result = []
        for record in self:
            name = record.name
            if record.property_code:
                name = f"[{record.property_code}] {name}"

            if record.current_borrower_id:
                name += _(f' (Used by {record.current_borrower_id.name})')
            elif not record.is_available:
                name += _(f' ({dict(record._fields["property_status"].selection)[record.property_status]})')

            result.append((record.id, name))
        return result

    def action_view_custodies(self):
        """Action to view all custodies related to this property"""
        self.ensure_one()
        return {
            'name': _('Custodies for %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'hr.custody',
            'view_mode': 'list,form',
            'domain': [('custody_property_id', '=', self.id)],
            'context': {'default_custody_property_id': self.id}
        }

    def action_view_current_custody(self):
        """Action to view current active custody"""
        self.ensure_one()
        if self.current_custody_id:
            return {
                'name': _('Current Custody'),
                'type': 'ir.actions.act_window',
                'res_model': 'hr.custody',
                'view_mode': 'form',
                'res_id': self.current_custody_id.id,
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Information'),
                    'message': _('This property is not currently in use.'),
                    'type': 'info'
                }
            }

    def action_set_maintenance(self):
        """Set property status to under maintenance"""
        for record in self:
            if record.active_custody_count > 0:
                raise UserError(_('Cannot set to maintenance while property is in use'))
            record.property_status = 'maintenance'

    def action_set_available(self):
        """Set property status to available"""
        for record in self:
            record.property_status = 'available'

    # Method for auto categorize button
    def action_auto_categorize(self):
        """Auto-categorize this property based on name and description"""
        for record in self:
            if not record.category_id and record.name:
                category_id = self.env['custody.category'].predict_category_for_property(
                    record.name, record.desc)
                if category_id:
                    record.category_id = category_id
                    # Also set approvers if needed
                    category = self.env['custody.category'].browse(category_id)
                    approvers = category.get_effective_approvers()
                    if approvers:
                        record.approver_ids = [(6, 0, approvers.ids)]
                    
                    # Show success message
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Auto-Categorization'),
                            'message': _('Property categorized as: %s') % category.name,
                            'type': 'success',
                            'sticky': False,
                        }
                    }
                else:
                    # Show warning if no category found
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Auto-Categorization'),
                            'message': _('Could not find an appropriate category.'),
                            'type': 'warning',
                            'sticky': False,
                        }
                    }
            elif record.category_id:
                # Show info message if already categorized
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Auto-Categorization'),
                        'message': _('Property is already categorized as: %s') % record.category_id.name,
                        'type': 'info',
                        'sticky': False,
                    }
                }
        
        return True

    # Inherit fields_view_get to customize form based on category
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """Customize form view based on selected category"""
        res = super(CustodyProperty, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu
        )
        
        # If we're on a form view and there's a category_id in context
        if view_type == 'form' and self._context.get('default_category_id'):
            category_id = self._context.get('default_category_id')
            category = self.env['custody.category'].browse(category_id)
            
            if category.exists():
                # Use the category's customization method
                res = category.get_property_fields_view(
                    view_id=view_id, view_type=view_type, 
                    toolbar=toolbar, submenu=submenu,
                    default_category_id=category_id
                )
        
        return res

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle auto-categorization"""
        for vals in vals_list:
            # Try to predict category if not provided
            if 'category_id' not in vals and 'name' in vals:
                description = vals.get('desc', '')
                category_id = self.env['custody.category'].predict_category_for_property(
                    vals['name'], description)
                if category_id:
                    vals['category_id'] = category_id
                    
                    # If we have a category, also set default approvers
                    if category_id and 'approver_ids' not in vals:
                        category = self.env['custody.category'].browse(category_id)
                        approvers = category.get_effective_approvers()
                        if approvers:
                            vals['approver_ids'] = [(6, 0, approvers.ids)]
        
        return super(CustodyProperty, self).create(vals_list)
