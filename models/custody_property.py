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
             "this provider, limited to 1024x1024px"
    )

    desc = fields.Html(
        string='Description',
        help='A detailed description of the item.'
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
        help='Total number of custody records for this property'
    )

    active_custody_count = fields.Integer(
        string='Active Custodies',
        compute='_compute_custody_counts',
        help='Number of active custodies for this property'
    )

    current_borrower_id = fields.Many2one(
        'hr.employee',
        string='Current Borrower',
        compute='_compute_current_borrower',
        help='Employee currently borrowing this property'
    )

    current_custody_id = fields.Many2one(
        'hr.custody',
        string='Current Custody',
        compute='_compute_current_borrower',
        help='Current active custody record'
    )

    is_available = fields.Boolean(
        string='Available',
        compute='_compute_is_available',
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
            # This will be used in hr.custody to set default return_type
            return {
                'domain': {},
                'value': {
                    # These values can be used when creating custody records
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

    @api.depends('name')
    def _compute_custody_counts(self):
        """Compute the number of custodies for this property"""
        for record in self:
            custody_records = self.env['hr.custody'].search([
                ('custody_property_id', '=', record.id)
            ])
            record.custody_count = len(custody_records)

            active_custody = custody_records.filtered(
                lambda r: r.state == 'approved'
            )
            record.active_custody_count = len(active_custody)

    @api.depends('active_custody_count')
    def _compute_current_borrower(self):
        """Compute current borrower information and auto-update status"""
        for record in self:
            current_custody = self.env['hr.custody'].search([
                ('custody_property_id', '=', record.id),
                ('state', '=', 'approved')
            ], limit=1)

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
