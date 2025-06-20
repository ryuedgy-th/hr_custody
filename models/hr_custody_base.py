from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrCustodyBase(models.AbstractModel):
    """
    Base mixin for Hr Custody with core fields and basic functionality.
    """
    _name = 'hr.custody.base'
    _description = 'Hr Custody Base Mixin'

    # Core field definitions
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

    # Return date management fields
    return_type = fields.Selection([
        ('date', 'Fixed Return Date'),
        ('flexible', 'No Fixed Return Date'),
        ('term_end', 'Return at Term/Project End')
    ], string='Return Type', default='date', required=True, index=True, tracking=True,
    help='Select the type of return date arrangement')

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

    notes = fields.Html(
        string='Notes',
        help='Note for Custody',
        sanitize=True,
        prefetch=False
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

    # Computed field for property code display
    property_code_display = fields.Char(
        string='Property Code',
        compute='_compute_property_code_display',
        store=True,
        index=True,
        help='Display the property code'
    )

    # Computed Fields
    @api.depends('return_type', 'return_date', 'expected_return_period', 'state')
    def _compute_return_status_display(self):
        """Compute return status display in readable format"""
        for record in self:
            if record.state == 'returned':
                record.return_status_display = 'Returned'
            elif record.return_type == 'date' and record.return_date:
                record.return_status_display = f'Due: {record.return_date.strftime("%d/%m/%Y")}'
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

    @api.depends('custody_property_id', 'custody_property_id.property_code')
    def _compute_property_code_display(self):
        for record in self:
            if record.custody_property_id and record.custody_property_id.property_code:
                record.property_code_display = record.custody_property_id.property_code
            else:
                record.property_code_display = False

    # Onchange Methods
    @api.onchange('return_type')
    def _onchange_return_type(self):
        """Clear fields when changing return type"""
        if self.return_type != 'date':
            self.return_date = False
        if self.return_type == 'date':
            self.expected_return_period = False

    # Constraint Methods
    @api.constrains('return_type', 'return_date', 'expected_return_period', 'date_request')
    def _check_return_requirements(self):
        """Validate required fields based on return type"""
        for record in self:
            # Check for fixed date return type
            if record.return_type == 'date':
                if not record.return_date:
                    raise ValidationError('Please specify return date when selecting "Fixed Return Date"')
                if record.return_date < record.date_request:
                    raise ValidationError('Return date must not be before request date')

            # Check for flexible or term end return types
            elif record.return_type in ['flexible', 'term_end']:
                if not record.expected_return_period:
                    raise ValidationError('Please specify expected return period')

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

    # Basic state management methods
    def set_to_draft(self):
        """Set the current record to the 'draft' state."""
        self.state = 'draft'

    def set_to_return(self):
        """The function used to set the current custody record to the 'returned' state"""
        # Update property status to 'available' when returned
        if self.custody_property_id.property_status == 'in_use':
            self.custody_property_id.property_status = 'available'

        self.state = 'returned'
        # Don't automatically set return_date for flexible returns
        if self.return_type == 'date':
            self.return_date = fields.Date.today()
            
        # Post message about return
        message = _('Equipment returned')
        self.message_post(
            body=message,
            message_type='notification'
        )

    # Email and Reminder Methods - UPDATED: Only for Fixed Return Date
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
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
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

    def unlink(self):
        """Override unlink to prevent deletion of approved records"""
        for record in self:
            if record.state == 'approved':
                raise UserError(_('You cannot delete approved custody records'))
        return super(HrCustodyBase, self).unlink()

    def write(self, vals):
        """Override write method to handle state changes"""
        result = super(HrCustodyBase, self).write(vals)
        if 'state' in vals:
            for record in self:
                record.message_post(
                    body=_('Custody state changed to %s') % dict(record._fields['state'].selection)[record.state]
                )
        return result

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

        return super(HrCustodyBase, self).name_search(name, args, operator, limit)

    def name_get(self):
        """Enhanced name display"""
        result = []
        for record in self:
            name = f"{record.name} - {record.employee_id.name}"
            if record.custody_property_id:
                name += f" ({record.custody_property_id.name})"
            result.append((record.id, name))
        return result