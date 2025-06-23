from datetime import timedelta

from dateutil.relativedelta import relativedelta

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
    _inherit = ['mail.thread', 'mail.activity.mixin']

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
        string='Device Type',
        help='Type or model of the device (e.g., Laptop, Phone, Tablet)'
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
    ], string='Property Status', default='available', help='Current status of the property', tracking=True)

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
        help='Date of last maintenance or inspection',
        tracking=True
    )

    next_maintenance_date = fields.Date(
        string='Next Maintenance Date',
        help='Scheduled date for next maintenance',
        tracking=True
    )

    # NEW: Maintenance fields
    maintenance_frequency = fields.Selection([
        ('none', 'No Regular Maintenance'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('biannual', 'Bi-annual'),
        ('annual', 'Annual'),
        ('custom', 'Custom')
    ], 
        string='Maintenance Frequency', 
        default='none',
        help='Frequency of regular maintenance for this property',
        tracking=True
    )
    
    maintenance_interval = fields.Integer(
        string='Custom Interval (Days)',
        default=30,
        help='Custom maintenance interval in days',
        tracking=True
    )
    
    maintenance_notes = fields.Text(
        string='Maintenance Notes',
        help='Special instructions or notes for maintenance',
        tracking=True
    )
    
    days_to_maintenance = fields.Integer(
        string='Days to Next Maintenance',
        compute='_compute_maintenance_status',
        store=True,
        help='Number of days until next scheduled maintenance'
    )
    
    maintenance_overdue = fields.Boolean(
        string='Maintenance Overdue',
        compute='_compute_maintenance_status',
        store=True,
        help='Indicates if maintenance is overdue'
    )
    
    maintenance_due_soon = fields.Boolean(
        string='Maintenance Due Soon',
        compute='_compute_maintenance_status',
        store=True,
        help='Indicates if maintenance is due within the reminder period'
    )
    
    maintenance_status_display = fields.Char(
        string='Maintenance Status',
        compute='_compute_maintenance_status_display',
        store=True,
        help='Human readable maintenance status'
    )

    # Purchase Information
    purchase_date = fields.Date(
        string='Purchase Date',
        help='Date when this property was purchased'
    )

    purchase_value = fields.Float(
        string='Purchase Value',
        help='Original purchase value of this property'
    )

    warranty_expire_month = fields.Selection([
        ('01', 'January'), ('02', 'February'), ('03', 'March'),
        ('04', 'April'), ('05', 'May'), ('06', 'June'),
        ('07', 'July'), ('08', 'August'), ('09', 'September'),
        ('10', 'October'), ('11', 'November'), ('12', 'December')
    ], string='Warranty Expire Month', help='Month when warranty expires')

    warranty_expire_year = fields.Integer(
        string='Warranty Expire Year',
        help='Year when warranty expires (e.g., 2025, 2026)'
    )

    warranty_status = fields.Char(
        string='Warranty Status',
        compute='_compute_warranty_status',
        store=True,
        help='Current warranty status'
    )

    # Device Technical Information
    ip_address = fields.Char(
        string='IP Address',
        help='Network IP address of the device (e.g., 192.168.1.100)'
    )

    serial_number = fields.Char(
        string='Serial Number',
        help='Manufacturer serial number of the device'
    )

    operating_system = fields.Char(
        string='Operating System',
        help='Operating system and version (e.g., Windows 11, macOS 14.0, Ubuntu 22.04)'
    )

    manufacturer = fields.Char(
        string='Manufacturer',
        help='Device manufacturer (e.g., Apple, Dell, HP, Lenovo)'
    )

    model = fields.Char(
        string='Model',
        help='Device model name or number (e.g., MacBook Pro 13", ThinkPad X1 Carbon)'
    )

    mac_address = fields.Char(
        string='MAC Address',
        help='Network MAC address of the device (e.g., 00:1B:44:11:3A:B7)'
    )
    
    # Maintenance History Tracking - handled by separate model custody.maintenance.history

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

    @api.onchange('product_id')
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
            else:
                record.current_borrower_id = False
                record.current_custody_id = False

    @api.depends('property_status', 'active_custody_count')
    def _compute_is_available(self):
        """Compute whether the property is available for custody"""
        for record in self:
            record.is_available = (
                record.property_status == 'available' and 
                record.active_custody_count == 0
            )
    
    # NEW: Compute maintenance status
    @api.depends('next_maintenance_date')
    def _compute_maintenance_status(self):
        """Compute maintenance status indicators"""
        today = fields.Date.today()
        # Get maintenance reminder days without sudo - use accessible parameter or default
        reminder_days_param = self.env['ir.config_parameter'].get_param(
            'hr_custody.maintenance_reminder_days', '7')
        try:
            reminder_days = int(reminder_days_param)
        except (ValueError, TypeError):
            reminder_days = 7  # Default fallback
        
        for record in self:
            if record.next_maintenance_date:
                # Calculate days to maintenance
                delta = (record.next_maintenance_date - today).days
                record.days_to_maintenance = delta
                
                # Check if maintenance is overdue
                record.maintenance_overdue = delta < 0
                
                # Check if maintenance is due soon
                record.maintenance_due_soon = 0 <= delta <= reminder_days
            else:
                record.days_to_maintenance = 0
                record.maintenance_overdue = False
                record.maintenance_due_soon = False
    
    @api.depends('maintenance_frequency', 'next_maintenance_date')
    def _compute_maintenance_status_display(self):
        """Compute human readable maintenance status"""
        today = fields.Date.today()
        # Get maintenance reminder days without sudo - use accessible parameter or default
        reminder_days_param = self.env['ir.config_parameter'].get_param(
            'hr_custody.maintenance_reminder_days', '7')
        try:
            reminder_days = int(reminder_days_param)
        except (ValueError, TypeError):
            reminder_days = 7  # Default fallback
        
        for record in self:
            if record.maintenance_frequency == 'none':
                record.maintenance_status_display = _('No Schedule')
            elif not record.next_maintenance_date:
                record.maintenance_status_display = _('Not Scheduled')
            else:
                # Calculate days to maintenance locally
                delta = (record.next_maintenance_date - today).days
                
                if delta < 0:
                    days_overdue = abs(delta)
                    record.maintenance_status_display = _('🔴 Overdue (%s days)') % days_overdue
                elif 0 <= delta <= reminder_days:
                    record.maintenance_status_display = _('🟡 Due Soon (%s days)') % delta
                elif delta > 0:
                    record.maintenance_status_display = _('🟢 OK (%s days left)') % delta
                else:
                    record.maintenance_status_display = _('Due Today')
    
    @api.depends('warranty_expire_month', 'warranty_expire_year')
    def _compute_warranty_status(self):
        """Compute warranty status based on expire month and year"""
        today = fields.Date.today()
        current_year = today.year
        current_month = today.month
        
        for record in self:
            if not record.warranty_expire_month or not record.warranty_expire_year:
                record.warranty_status = _('Not Set')
                continue
                
            expire_year = record.warranty_expire_year
            expire_month = int(record.warranty_expire_month)
            
            # Create date for last day of warranty month
            from calendar import monthrange
            last_day = monthrange(expire_year, expire_month)[1]
            expire_date = fields.Date.from_string(f'{expire_year}-{expire_month:02d}-{last_day}')
            
            if expire_date < today:
                # Warranty expired
                months_expired = (current_year - expire_year) * 12 + (current_month - expire_month)
                if months_expired == 1:
                    record.warranty_status = _('🔴 Expired (1 month ago)')
                elif months_expired < 12:
                    record.warranty_status = _('🔴 Expired (%s months ago)') % months_expired
                else:
                    years_expired = months_expired // 12
                    remaining_months = months_expired % 12
                    if remaining_months == 0:
                        year_text = _('years') if years_expired > 1 else _('year')
                        record.warranty_status = _('🔴 Expired (%s %s ago)') % (years_expired, year_text)
                    else:
                        record.warranty_status = _('🔴 Expired (%sy %sm ago)') % (years_expired, remaining_months)
            else:
                # Warranty still active
                months_left = (expire_year - current_year) * 12 + (expire_month - current_month)
                if months_left == 0:
                    record.warranty_status = _('🟡 Expires This Month')
                elif months_left == 1:
                    record.warranty_status = _('🟡 Expires Next Month')
                elif months_left <= 3:
                    record.warranty_status = _('🟡 Expires in %s months') % months_left
                elif months_left < 12:
                    record.warranty_status = _('🟢 Active (%s months left)') % months_left
                else:
                    years_left = months_left // 12
                    remaining_months = months_left % 12
                    if remaining_months == 0:
                        year_text = _('years') if years_left > 1 else _('year')
                        record.warranty_status = _('🟢 Active (%s %s left)') % (years_left, year_text)
                    else:
                        record.warranty_status = _('🟢 Active (%sy %sm left)') % (years_left, remaining_months)
    
    
    # NEW: Update next maintenance date based on frequency
    @api.onchange('maintenance_frequency', 'maintenance_interval', 'last_maintenance_date')
    def _onchange_maintenance_settings(self):
        """Update next maintenance date when frequency or last date changes"""
        if self.last_maintenance_date and self.maintenance_frequency != 'none':
            base_date = self.last_maintenance_date
            
            if self.maintenance_frequency == 'monthly':
                self.next_maintenance_date = base_date + timedelta(days=30)
            elif self.maintenance_frequency == 'quarterly':
                self.next_maintenance_date = base_date + timedelta(days=90)
            elif self.maintenance_frequency == 'biannual':
                self.next_maintenance_date = base_date + timedelta(days=182)
            elif self.maintenance_frequency == 'annual':
                self.next_maintenance_date = base_date + timedelta(days=365)
            elif self.maintenance_frequency == 'custom' and self.maintenance_interval > 0:
                self.next_maintenance_date = base_date + timedelta(days=self.maintenance_interval)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Improved name search to include property code"""
        args = args or []
        domain = []
        
        if name:
            domain = ['|', ('name', operator, name), ('property_code', operator, name)]
            
        pos = self.search(domain + args, limit=limit)
        return pos.name_get()
        
    def name_get(self):
        """Override name_get to include property code"""
        result = []
        for record in self:
            if record.property_code:
                name = f"[{record.property_code}] {record.name}"
            else:
                name = record.name
            result.append((record.id, name))
        return result
        
    def action_view_custodies(self):
        """Action to view all custodies for this property"""
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
        """Action to view current custody for this property"""
        self.ensure_one()
        if self.current_custody_id:
            return {
                'name': _('Current Custody'),
                'type': 'ir.actions.act_window',
                'res_model': 'hr.custody',
                'view_mode': 'form',
                'res_id': self.current_custody_id.id,
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Active Custody'),
                    'message': _('This property is not currently in custody.'),
                    'sticky': False,
                    'type': 'warning',
                }
            }
    
    def action_set_maintenance(self):
        """Set property status to Under Maintenance"""
        self.write({'property_status': 'maintenance'})
        return True
        
    def action_set_available(self):
        """Set property status to Available"""
        self.write({'property_status': 'available'})
        return True
        
    # NEW: Record maintenance
    def action_record_maintenance(self):
        """Record maintenance for this property"""
        self.ensure_one()
        return {
            'name': _('Record Maintenance'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.record.maintenance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_property_id': self.id,
                'default_maintenance_date': fields.Date.today(),
            }
        }
    
    # NEW: Send maintenance reminder
    def _send_maintenance_reminder(self):
        """Send maintenance reminder email"""
        self.ensure_one()
        if not self.responsible_person or not self.responsible_person.work_email:
            return False
            
        template = self.env.ref('hr_custody.email_template_maintenance_reminder')
        if template:
            template.send_mail(self.id, force_send=True)
            
            # Add note in chatter
            days_left = (self.next_maintenance_date - fields.Date.today()).days
            self.message_post(
                body=_("Maintenance reminder sent to %s. Maintenance due in %s days.") % 
                     (self.responsible_person.name, days_left),
                subtype_id=self.env.ref('mail.mt_note').id
            )
            return True
        return False
    
    # NEW: Send overdue maintenance reminder
    def _send_overdue_maintenance_reminder(self):
        """Send overdue maintenance reminder email"""
        self.ensure_one()
        if not self.responsible_person or not self.responsible_person.work_email:
            return False
            
        template = self.env.ref('hr_custody.email_template_maintenance_overdue')
        if template:
            template.send_mail(self.id, force_send=True)
            
            # Add note in chatter
            days_overdue = abs((self.next_maintenance_date - fields.Date.today()).days)
            self.message_post(
                body=_("Overdue maintenance reminder sent to %s. Maintenance is %s days overdue.") % 
                     (self.responsible_person.name, days_overdue),
                subtype_id=self.env.ref('mail.mt_note').id
            )
            return True
        return False
    
    # NEW: Cron job for maintenance reminders
    @api.model
    def _cron_maintenance_reminder(self):
        """Send reminders for upcoming maintenance"""
        today = fields.Date.today()
        # Get maintenance reminder days without sudo - use accessible parameter or default
        reminder_days_param = self.env['ir.config_parameter'].get_param(
            'hr_custody.maintenance_reminder_days', '7')
        try:
            reminder_days = int(reminder_days_param)
        except (ValueError, TypeError):
            reminder_days = 7  # Default fallback
        
        # Calculate the date range for sending reminders
        reminder_date = today + timedelta(days=reminder_days)
        
        # Find properties that need maintenance soon
        properties = self.search([
            ('next_maintenance_date', '>=', today),
            ('next_maintenance_date', '<=', reminder_date),
            ('property_status', '!=', 'maintenance'),  # Not already under maintenance
        ])
        
        # Send reminders for each property
        for prop in properties:
            if prop.responsible_person and prop.responsible_person.work_email:
                prop._send_maintenance_reminder()
                
        # Also send reminders for overdue maintenance
        overdue = self.search([
            ('next_maintenance_date', '<', today),
            ('property_status', '!=', 'maintenance'),
        ])
        
        for prop in overdue:
            if prop.responsible_person and prop.responsible_person.work_email:
                prop._send_overdue_maintenance_reminder()
        
        return True

    def action_auto_categorize(self):
        """Auto-categorize property based on name and description"""
        for record in self:
            if not record.category_id:
                category_id = self.env['custody.category'].predict_category_for_property(
                    record.name, record.desc)
                if category_id:
                    record.category_id = category_id
        return True
    
    def action_view_maintenance_history(self):
        """Action to view maintenance history in user-friendly format"""
        self.ensure_one()
        
        # Get maintenance history records
        maintenance_records = self.env['custody.maintenance.history'].search([
            ('property_id', '=', self.id)
        ])
        
        if not maintenance_records:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Maintenance History'),
                    'message': _('No maintenance records found for %s.\n\nUse the "🔧 Record Maintenance" button to add maintenance records.') % self.name,
                    'sticky': False,
                    'type': 'info',
                }
            }
        
        # Open user-friendly maintenance history view
        return {
            'name': _('🔧 Maintenance History - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.maintenance.history',
            'view_mode': 'list,form',
            'domain': [('property_id', '=', self.id)],
            'context': {
                'default_property_id': self.id,
                'property_name': self.name,
            }
        }
        
    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        """Override to customize views based on category"""
        res = super(CustodyProperty, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
            
        # If category_id is in context, try to get custom view
        category_id = self.env.context.get('default_category_id')
        if category_id and view_type == 'form':
            category = self.env['custody.category'].browse(category_id)
            custom_view = category.get_property_fields_view(view_id, view_type)
            if custom_view:
                res = custom_view
                
        return res
        
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle additional logic"""
        for vals in vals_list:
            # Auto-set next maintenance date if frequency is set
            if vals.get('last_maintenance_date') and vals.get('maintenance_frequency', 'none') != 'none':
                base_date = fields.Date.from_string(vals['last_maintenance_date'])
                
                if vals['maintenance_frequency'] == 'monthly':
                    vals['next_maintenance_date'] = base_date + timedelta(days=30)
                elif vals['maintenance_frequency'] == 'quarterly':
                    vals['next_maintenance_date'] = base_date + timedelta(days=90)
                elif vals['maintenance_frequency'] == 'biannual':
                    vals['next_maintenance_date'] = base_date + timedelta(days=182)
                elif vals['maintenance_frequency'] == 'annual':
                    vals['next_maintenance_date'] = base_date + timedelta(days=365)
                elif vals['maintenance_frequency'] == 'custom' and vals.get('maintenance_interval', 0) > 0:
                    vals['next_maintenance_date'] = base_date + timedelta(days=vals['maintenance_interval'])
                    
        return super(CustodyProperty, self).create(vals_list)
