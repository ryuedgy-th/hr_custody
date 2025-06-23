from datetime import date, datetime, timedelta

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrCustody(models.Model):
    """
    Hr custody contract creation model.
    
    This model manages company property custody requests with:
    - Employee custody requests and approval workflow
    - Property condition documentation with images
    - Flexible return date management
    - Email notifications and reminders
    """
    _name = 'hr.custody'
    _description = 'Hr Custody Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc'
    _rec_name = 'name'

    # ================================================================
    # CORE FIELDS
    # ================================================================
    
    name = fields.Char(
        string='Code',
        copy=False,
        help='A unique code assigned to this record.',
        readonly=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
        help='The company associated with this record.',
        default=lambda self: self.env.company
    )

    date_request = fields.Date(
        string='Requested Date',
        required=True,
        tracking=True,
        help='The date when the request was made',
        default=fields.Date.today
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        index=True,
        help='The employee associated with this record.',
        default=lambda self: self.env.user.employee_id
    )

    purpose = fields.Char(
        string='Reason',
        tracking=True,
        required=True,
        help='The reason or purpose of the custody'
    )

    custody_property_id = fields.Many2one(
        'custody.property',
        string='Property',
        required=True,
        index=True,
        help='The property associated with this custody record'
    )

    # ================================================================
    # APPROVAL FIELDS
    # ================================================================

    # Related field for property approvers
    property_approver_ids = fields.Many2many(
        related='custody_property_id.approver_ids',
        string='Available Approvers',
        readonly=True,
        help='Users who can approve this request based on the selected property'
    )

    # Category approvers relation
    category_approver_ids = fields.Many2many(
        'res.users',
        string='Category Approvers',
        compute='_compute_category_approvers',
        store=False,
        help='Approvers determined by the property category'
    )
    
    # Combined approvers from property and category
    effective_approver_ids = fields.Many2many(
        'res.users',
        string='Effective Approvers',
        compute='_compute_effective_approvers',
        store=False,
        help='All users who can approve this request'
    )

    # Approval tracking
    approved_by_id = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        index=True,
        tracking=True,
        help='User who approved this request'
    )

    approved_date = fields.Datetime(
        string='Approved Date',
        readonly=True,
        help='When this request was approved'
    )

    # ================================================================
    # RETURN DATE MANAGEMENT FIELDS
    # ================================================================

    return_type = fields.Selection([
        ('date', 'Fixed Return Date'),
        ('flexible', 'No Fixed Return Date'),
        ('term_end', 'Return at Term/Project End')
    ], 
        string='Return Type', 
        default='date', 
        required=True, 
        index=True, 
        tracking=True,
        help='Select the type of return date arrangement'
    )

    return_date = fields.Date(
        string='Return Date',
        tracking=True,
        help='The date when the custody is expected to be returned (for fixed date only)'
    )

    expected_return_period = fields.Char(
        string='Expected Return Period',
        help='E.g. "End of Term 1/2024", "When project finished", "As needed"'
    )

    return_status_display = fields.Char(
        string='Return Status',
        compute='_compute_return_status_display',
        store=False,
        help='Display return status in readable format'
    )

    renew_date = fields.Date(
        string='Renewal Return Date',
        tracking=True,
        help="Return date for the renewal",
        readonly=True,
        copy=False
    )

    # ================================================================
    # STATE AND STATUS FIELDS
    # ================================================================

    rejected_reason = fields.Text(
        string='Rejected Reason',
        copy=False,
        readonly=True,
        help="Reason for the rejection"
    )

    renew_rejected_reason = fields.Text(
        string='Renew Rejected Reason',
        copy=False,
        readonly=True,
        help="Renew rejected reason"
    )

    is_renew_return_date = fields.Boolean(
        default=False,
        copy=False,
        help='Rejected Renew Date'
    )

    is_renew_reject = fields.Boolean(
        default=False,
        copy=False,
        help='Indicates whether the renewal is rejected or not.'
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('returned', 'Returned'),
        ('rejected', 'Refused')
    ],
    string='Status',
    default='draft',
    index=True,
    tracking=True,
    help='Custody states visible in statusbar'
    )

    is_mail_send = fields.Boolean(
        string="Mail Send",
        help='Indicates whether an email has been sent or not.'
    )

    is_read_only = fields.Boolean(
        string="Check Field",
        compute='_compute_is_read_only'
    )

    # ================================================================
    # IMAGE AND DOCUMENTATION FIELDS
    # ================================================================

    # Image fields for documenting equipment condition
    checkout_image = fields.Image(
        string="Checkout Image",
        help="Image of the equipment when checked out to the employee",
        attachment=True,
        max_width=1920,
        max_height=1920,
        prefetch=False
    )
    
    checkout_image_date = fields.Datetime(
        string="Checkout Image Date",
        readonly=True,
        help="Date and time when the checkout image was captured"
    )
    
    checkout_condition_notes = fields.Text(
        string="Checkout Condition Notes",
        help="Notes about the condition of the equipment when checked out"
    )
    
    return_image = fields.Image(
        string="Return Image",
        help="Image of the equipment when returned by the employee",
        attachment=True,
        max_width=1920,
        max_height=1920,
        prefetch=False
    )
    
    return_image_date = fields.Datetime(
        string="Return Image Date",
        readonly=True,
        help="Date and time when the return image was captured"
    )
    
    return_condition_notes = fields.Text(
        string="Return Condition Notes",
        help="Notes about the condition of the equipment when returned"
    )

    notes = fields.Html(
        string='Notes',
        help='Note for Custody',
        sanitize=True,
        prefetch=False
    )

    # Multiple images feature
    image_ids = fields.One2many(
        'custody.image',
        'custody_id',
        string='Additional Images',
        help='Additional images for this custody record',
        prefetch=False,
        copy=False
    )
    
    checkout_image_count = fields.Integer(
        string='Checkout Images',
        compute='_compute_image_counts',
        help='Number of checkout images'
    )
    
    return_image_count = fields.Integer(
        string='Return Images',
        compute='_compute_image_counts',
        help='Number of return images'
    )

    # ================================================================
    # COMPUTED FIELDS
    # ================================================================

    # Add a computed field to display property code in list view
    property_code_display = fields.Char(
        string='Property Code',
        compute='_compute_property_code_display',
        store=True,
        index=True,
        help='Display the property code'
    )

    # ================================================================
    # COMPUTED FIELD METHODS
    # ================================================================

    @api.depends('return_type', 'return_date', 'expected_return_period', 'state')
    def _compute_return_status_display(self):
        """Compute return status display in readable format"""
        for record in self:
            if record.state == 'returned':
                record.return_status_display = 'Returned'
            elif record.return_type == 'date' and record.return_date:
                date_str = record.return_date.strftime("%d/%m/%Y")
                record.return_status_display = f'Due: {date_str}'
            elif record.return_type == 'flexible':
                period = record.expected_return_period or 'No fixed date'
                record.return_status_display = f'Flexible ({period})'
            elif record.return_type == 'term_end':
                period = record.expected_return_period or 'End of term'
                record.return_status_display = f'Return {period}'
            else:
                record.return_status_display = 'Pending'

    @api.depends('employee_id')
    def _compute_is_read_only(self):
        """Use this function to check whether the user has the permission to change the employee"""
        for record in self:
            res_user = self.env.user
            if res_user.has_group('hr.group_hr_user'):
                record.is_read_only = True
            else:
                record.is_read_only = False

    @api.depends('image_ids')
    def _compute_image_counts(self):
        """Compute the number of images for each type"""
        for record in self:
            record.checkout_image_count = len(record.image_ids.filtered(lambda i: i.image_type == 'checkout'))
            record.return_image_count = len(record.image_ids.filtered(lambda i: i.image_type == 'return'))

    @api.depends('custody_property_id', 'custody_property_id.property_code')
    def _compute_property_code_display(self):
        for record in self:
            if record.custody_property_id and record.custody_property_id.property_code:
                record.property_code_display = record.custody_property_id.property_code
            else:
                record.property_code_display = False

    @api.depends('custody_property_id', 'custody_property_id.category_id')
    def _compute_category_approvers(self):
        """Compute approvers based on property category"""
        for record in self:
            approvers = self.env['res.users']
            
            if record.custody_property_id and record.custody_property_id.category_id:
                category = record.custody_property_id.category_id
                if category.requires_approval:
                    approvers = category.get_effective_approvers()
                    
            record.category_approver_ids = approvers

    @api.depends('property_approver_ids', 'category_approver_ids', 'custody_property_id')
    def _compute_effective_approvers(self):
        """Combine all approvers for this custody request using predefined roles"""
        for record in self:
            # Get default approvers from predefined security groups
            custody_officer = self.env.ref('hr_custody.group_custody_officer', raise_if_not_found=False)
            custody_manager = self.env.ref('hr_custody.group_custody_manager', raise_if_not_found=False)
            hr_manager = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
            
            all_approvers = self.env['res.users']
            
            # 1. Property-specific approvers first
            if record.property_approver_ids:
                all_approvers |= record.property_approver_ids
            else:
                # 2. Use security group members as default
                if custody_officer:
                    all_approvers |= custody_officer.users
                if custody_manager:
                    all_approvers |= custody_manager.users
                if hr_manager:
                    all_approvers |= hr_manager.users
            
            # 3. Add category approvers if they exist
            all_approvers |= record.category_approver_ids
            
            record.effective_approver_ids = all_approvers

    # ================================================================
    # ONCHANGE METHODS
    # ================================================================

    @api.onchange('return_type')
    def _onchange_return_type(self):
        """Clear fields when changing return type"""
        if self.return_type != 'date':
            self.return_date = False
        if self.return_type == 'date':
            self.expected_return_period = False
            
    @api.onchange('checkout_image')
    def _onchange_checkout_image(self):
        """Update checkout image timestamp when image uploaded"""
        if self.checkout_image:
            self.checkout_image_date = fields.Datetime.now()
    
    @api.onchange('return_image')
    def _onchange_return_image(self):
        """Update return image timestamp when image uploaded"""
        if self.return_image:
            self.return_image_date = fields.Datetime.now()

    # ================================================================
    # CONSTRAINT METHODS
    # ================================================================

    @api.constrains('return_type', 'return_date', 'expected_return_period', 'date_request')
    def _check_return_requirements(self):
        """Validate required fields based on return type"""
        for record in self:
            # Check for fixed date return type
            if record.return_type == 'date':
                if not record.return_date:
                    raise ValidationError(_('Please specify return date when selecting "Fixed Return Date"'))
                if record.return_date < record.date_request:
                    raise ValidationError(_('Return date must not be before request date'))

            # Check for flexible or term end return types
            elif record.return_type in ['flexible', 'term_end']:
                if not record.expected_return_period:
                    raise ValidationError(_('Please specify expected return period'))

    @api.constrains('return_date', 'date_request')
    def validate_return_date(self):
        """The function validate the return date to ensure it is after the request date"""
        for record in self:
            if record.return_date and record.date_request:
                if record.return_date < record.date_request:
                    raise ValidationError(_('Return date must be after request date'))

    @api.constrains('custody_property_id')
    def _check_property_availability(self):
        """Check if property is available for custody"""
        for record in self:
            if record.custody_property_id:
                property_obj = record.custody_property_id

                # Only allow Available properties
                if property_obj.property_status != 'available':
                    status_name = dict(property_obj._fields['property_status'].selection)[property_obj.property_status]
                    raise ValidationError(
                        _('Cannot request custody for %s. Property status is: %s. Only Available properties can be requested.')
                        % (property_obj.name, status_name)
                    )

                # Related field for property approvers
                if not property_obj.approver_ids:
                    raise ValidationError(
                        _('Property "%s" has no approvers assigned. Please contact administrator to set up approvers for this property.')
                        % property_obj.name
                    )

    # ================================================================
    # EMAIL AND REMINDER METHODS
    # ================================================================

    def mail_reminder(self):
        """Send return reminder mail for FIXED DATE returns only"""
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()

        # Send reminders ONLY for fixed date returns that are overdue
        fixed_date_records = self.search([
            ('state', '=', 'approved'),
            ('return_type', '=', 'date'),
            ('return_date', '!=', False)
        ])

        for custody_record in fixed_date_records:
            if custody_record.return_date <= date_now:
                self._send_fixed_date_reminder(custody_record)

    def _send_fixed_date_reminder(self, custody_record):
        """Send reminder for fixed date returns only"""
        # Get base URL without sudo - use system parameter accessible to current user
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        if not base_url:
            # Fallback to default if parameter not accessible
            base_url = 'http://localhost:8069'
        url = f"{base_url}/web#id={custody_record.id}&view_type=form&model=hr.custody"

        mail_content = _(
            'Hi %s,<br/>As per the %s you took %s on %s for the reason of %s.<br/>'
            'Due date was %s which has passed.<br/><br/>'
            'Please return the property as soon as possible. Otherwise, you can '
            'renew the reference number(%s) by extending the return date through '
            'following link.<br/><br/>'
            '<div style = "text-align: center; margin-top: 16px;"><a href = "%s"'
            'style = "padding: 5px 10px; font-size: 12px; line-height: 18px; color: #FFFFFF; '
            'border-color:#875A7B;text-decoration: none; display: inline-block; '
            'margin-bottom: 0px; font-weight: 400;text-align: center; vertical-align: middle; '
            'cursor: pointer; white-space: nowrap; background-image: none; '
            'background-color: #875A7B; border: 1px solid #875A7B; border-radius:3px;">'
            'Renew %s</a></div>'
        ) % (
            custody_record.employee_id.name,
            custody_record.name,
            custody_record.custody_property_id.name,
            custody_record.date_request,
            custody_record.purpose,
            custody_record.return_date,
            custody_record.name,
            url,
            custody_record.name
        )

        main_content = {
            'subject': _('REMINDER On %s') % custody_record.name,
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': custody_record.employee_id.work_email,
        }

        mail_id = self.env['mail.mail'].create(main_content)
        mail_id.send()

    def send_mail(self):
        """Send email notification using a predefined template."""
        template = self.env.ref('hr_custody.custody_email_notification_template')
        template.send_mail(self.id)
        self.is_mail_send = True

    # ================================================================
    # CRUD METHODS
    # ================================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Create a new record for the HrCustody model.
        
        This method is responsible for creating a new record for the HrCustody model
        with the provided values. It automatically generates a unique name for
        the record using the 'ir.sequence' and assigns it to the 'name' field.
        """
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.custody') or 'New'
        return super(HrCustody, self).create(vals_list)

    def unlink(self):
        """Override unlink to prevent deletion of approved records"""
        for record in self:
            if record.state == 'approved':
                raise UserError(_('You cannot delete approved custody records'))
        return super(HrCustody, self).unlink()

    def write(self, vals):
        """Override write method to handle state changes"""
        result = super(HrCustody, self).write(vals)
        if 'state' in vals:
            for record in self:
                record.message_post(
                    body=_('Custody state changed to %s') % dict(record._fields['state'].selection)[record.state]
                )
        return result

    # ================================================================
    # STATE MANAGEMENT METHODS
    # ================================================================

    def sent(self):
        """Move the current record to the 'to_approve' state."""
        self.state = 'to_approve'
        # Send notification to all approvers
        approver_names = ', '.join(self.property_approver_ids.mapped('name'))
        self.message_post(
            body=_('Custody request sent for approval to: %s') % approver_names,
            message_type='notification'
        )

    def set_to_draft(self):
        """Set the current record to the 'draft' state."""
        self.state = 'draft'

    def renew_approve(self):
        """The function Used to renew and approve the current custody record."""
        for custody in self.env['hr.custody'].search([
            ('custody_property_id', '=', self.custody_property_id.id),
            ('id', '!=', self.id)
        ]):
            if custody.state == "approved":
                raise UserError(_("Custody is not available now"))

        self.return_date = self.renew_date
        self.renew_date = False
        self.state = 'approved'

    def renew_refuse(self):
        """the function used to refuse the renewal of the current custody record"""
        self.renew_date = False
        self.state = 'approved'

    def approve(self):
        """Approve the current custody record.
        
        Validates user permissions, checks property availability,
        records approval metadata, and updates property status.
        """
        # Check if current user has approval permissions
        current_user = self.env.user
        is_hr_manager = current_user.has_group('hr.group_hr_manager')
        is_custody_manager = current_user.has_group('hr_custody.group_custody_manager')
        is_custody_officer = current_user.has_group('hr_custody.group_custody_officer')
        
        for record in self:
            # Refresh approvers to ensure we have the latest
            record._compute_effective_approvers()
            
            # Check approval permissions - use new custody roles
            has_approval_permission = (
                is_custody_manager or 
                is_custody_officer or 
                is_hr_manager or 
                current_user in record.effective_approver_ids
            )
            
            if not has_approval_permission:
                # Get authorized approvers from effective_approver_ids
                authorized_approvers = record.effective_approver_ids
                
                raise UserError(
                    _("You don't have permission to approve this request. Authorized approvers are: %s")
                    % (', '.join(authorized_approvers.mapped('name')))
                )

            # Check property availability - use domain search to avoid N+1 query
            existing_approved = self.env['hr.custody'].search_count([
                ('custody_property_id', '=', record.custody_property_id.id),
                ('id', '!=', record.id),
                ('state', '=', 'approved')
            ])
            if existing_approved > 0:
                raise UserError(_("Custody is not available now"))

            # Record approval information
            record.approved_by_id = current_user
            record.approved_date = fields.Datetime.now()
            
            # Update checkout image date if image exists but date not set
            if record.checkout_image and not record.checkout_image_date:
                record.checkout_image_date = fields.Datetime.now()

            # Update property status to 'in_use' when approved
            if record.custody_property_id.property_status == 'available':
                record.custody_property_id.property_status = 'in_use'

            record.state = 'approved'

            # Post message for tracking
            record.message_post(
                body=_('Request approved by %s') % current_user.name,
                message_type='notification'
            )

    def refuse_with_reason(self):
        """Open wizard to enter rejection reason."""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Refuse Reason'),
            'res_model': 'property.return.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reason': '',
                'model_id': 'hr.custody',
                'reject_id': self.id,
            }
        }

    def set_to_return(self):
        """The function used to set the current custody record to the 'returned' state"""
        # Update return image date if image exists but date not set
        if self.return_image and not self.return_image_date:
            self.return_image_date = fields.Datetime.now()
            
        # Update property status to 'available' when returned
        if self.custody_property_id.property_status == 'in_use':
            self.custody_property_id.property_status = 'available'

        self.state = 'returned'
        # Don't automatically set return_date for flexible returns
        if self.return_type == 'date':
            self.return_date = fields.Date.today()
            
        # Post message about return with condition notes if provided
        message = _('Equipment returned')
        if self.return_condition_notes:
            message += _(' with notes: %s') % self.return_condition_notes
            
        self.message_post(
            body=message,
            message_type='notification'
        )

    # ================================================================
    # UTILITY METHODS
    # ================================================================

    @api.model
    def get_pending_approvals(self, user_id=None):
        """Get custody requests pending approval for specific user"""
        if not user_id:
            user_id = self.env.user.id

        return self.search([
            ('custody_property_id.approver_ids', 'in', [user_id]),
            ('state', '=', 'to_approve')
        ])

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to search in multiple fields"""
        if args is None:
            args = []

        if name:
            domain = [
                '|', '|', '|', '|', '|',
                ('name', operator, name),  # Code
                ('employee_id.name', operator, name),  # Employee name
                ('custody_property_id.name', operator, name),  # Property name
                ('purpose', operator, name),  # Reason
                ('custody_property_id.property_code', operator, name),  # Property code
                ('approved_by_id.name', operator, name)  # Approved by name
            ]
            records = self.search(domain + args, limit=limit)
            return records.name_get()

        return super(HrCustody, self).name_search(name, args, operator, limit)

    def name_get(self):
        """Enhanced name display"""
        result = []
        for record in self:
            name = f"{record.name} - {record.employee_id.name}"
            if record.custody_property_id:
                name += f" ({record.custody_property_id.name})"
            result.append((record.id, name))
        return result

    # ================================================================
    # IMAGE MANAGEMENT METHODS
    # ================================================================

    def action_view_image_comparison(self):
        """Open a wizard to compare checkout and return images side by side"""
        self.ensure_one()
        
        # Check if both types of images exist
        checkout_images = self.env['custody.image'].search([
            ('custody_id', '=', self.id),
            ('image_type', '=', 'checkout')
        ], limit=1)
        
        return_images = self.env['custody.image'].search([
            ('custody_id', '=', self.id),
            ('image_type', '=', 'return')
        ], limit=1)
        
        # If any image type is missing, show notification
        if not checkout_images or not return_images:
            missing = []
            if not checkout_images:
                missing.append("checkout")
            if not return_images:
                missing.append("return")
                
            raise UserError(_("Cannot compare images. Missing %s image(s). Please upload images first.") % (" and ".join(missing)))
        
        # Create context for opening comparison view
        context = self.env.context.copy()
        context.update({
            'default_checkout_images': checkout_images.ids,
            'default_return_images': return_images.ids,
            'no_breadcrumbs': True
        })
        
        # Open comparison view
        return {
            'name': _('Image Comparison - %s') % self.name,
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'hr.custody',
            'res_id': self.id,
            'target': 'new',
            'view_id': self.env.ref('hr_custody.hr_custody_view_image_comparison').id,
            'context': context,
        }

    def action_view_images(self, image_type=None):
        """Open a view to manage images of a specific type or all images"""
        self.ensure_one()
        
        # Always strictly filter by custody_id to prevent mixing images
        domain = [('custody_id', '=', self.id)]
        context = {
            'default_custody_id': self.id,
            'search_default_custody_id': self.id,  # Ensure filtering by current custody
            'strict_custody_filter': self.id,  # Custom key to enforce strict filtering
            'no_breadcrumbs': True,
        }
        
        if image_type:
            # Add domain filter but keep it minimal for better performance
            domain.append(('image_type', '=', image_type))
            context['default_image_type'] = image_type
            context['search_default_' + image_type + '_images'] = 1  # Activate the relevant filter
            
            if image_type == 'checkout':
                title = _('Checkout Images - %s') % self.name
            elif image_type == 'return':
                title = _('Return Images - %s') % self.name
            else:
                title = _('Images - %s') % self.name
        else:
            title = _('All Images - %s') % self.name
        
        # Use a custodial ID in the key to ensure caching doesn't mix images
        view_key = f'custody_images_{self.id}_{image_type or "all"}'
            
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image',
            'view_mode': 'kanban,form',
            'domain': domain,
            'context': context,
            'target': 'current',
            'key2': view_key,  # Use a unique key for this view
            'help': '<p class="o_view_nocontent_smiling_face">No images found</p><p>Upload images for this custody record.</p>'
        }
        
    def action_add_image(self, image_type=None):
        """Quick action to add a new image of a specific type"""
        self.ensure_one()
        
        context = {
            'default_custody_id': self.id,
        }
        
        if image_type:
            context['default_image_type'] = image_type
            
        return {
            'name': _('Add Image'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image',
            'view_mode': 'form',
            'target': 'new',
            'context': context,
        }

    def action_add_multiple_images(self):
        """Open wizard to upload multiple images at once"""
        self.ensure_one()
        
        action = self.env['ir.actions.act_window']._for_xml_id('hr_custody.action_custody_multi_images_upload')
        action['context'] = {
            'default_custody_id': self.id,
            'default_image_type': self.state == 'approved' and 'return' or 'checkout',
        }
        return action
        
    def action_manage_multiple_images(self):
        """Open list view to manage multiple images for this custody"""
        self.ensure_one()
        
        # Use list view first for multi-selection/deletion
        return {
            'name': _('Manage Images - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image',
            'view_mode': 'list,kanban,form',
            'domain': [('custody_id', '=', self.id)],
            'context': {
                'default_custody_id': self.id,
                'search_default_custody_id': self.id,
                'strict_custody_filter': self.id,
                'create': True,
                'edit': True,
                'delete': True
            },
            'help': '<p class="o_view_nocontent_smiling_face">No images found</p>'
                   '<p>You can select multiple images and delete them at once.</p>'
        }