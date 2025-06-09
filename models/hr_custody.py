from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrCustody(models.Model):
    """
        Hr custody contract creation model.
    """
    _name = 'hr.custody'
    _description = 'Hr Custody Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc'
    _rec_name = 'name'

    # Field definitions - Updated for Odoo 18
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
        help='The property associated with this custody record'
    )

    # ⭐ NEW: Related field for property approvers
    property_approver_ids = fields.Many2many(
        related='custody_property_id.approver_ids',
        string='Available Approvers',
        readonly=True,
        help='Users who can approve this request based on the selected property'
    )

    # ⭐ NEW: Approval tracking
    approved_by_id = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        tracking=True,
        help='User who approved this request'
    )

    approved_date = fields.Datetime(
        string='Approved Date',
        readonly=True,
        help='When this request was approved'
    )

    # New fields for flexible return date management
    return_type = fields.Selection([
        ('date', 'Fixed Return Date'),
        ('flexible', 'No Fixed Return Date'),
        ('term_end', 'Return at Term/Project End')
    ], string='Return Type', default='date', required=True, tracking=True,
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

    # Existing fields
    renew_date = fields.Date(
        string='Renewal Return Date',
        tracking=True,
        help="Return date for the renewal",
        readonly=True,
        copy=False
    )

    notes = fields.Html(
        string='Notes',
        help='Note for Custody'
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

    # ===== IMAGE DOCUMENTATION FIELDS =====

    # Image relationships
    before_image_ids = fields.One2many(
        'custody.image', 'custody_id',
        domain=[('image_type', '=', 'before')],
        string='Before Images',
        help='Photos taken before handing over the equipment'
    )

    after_image_ids = fields.One2many(
        'custody.image', 'custody_id',
        domain=[('image_type', '=', 'after')],
        string='After Images',
        help='Photos taken when receiving back the equipment'
    )

    damage_image_ids = fields.One2many(
        'custody.image', 'custody_id',
        domain=[('image_type', '=', 'damage')],
        string='Damage Documentation',
        help='Photos documenting any damage or issues'
    )

    # Image computed fields
    before_image_count = fields.Integer(
        string='Before Images Count',
        compute='_compute_image_counts',
        help='Number of before images'
    )

    after_image_count = fields.Integer(
        string='After Images Count',
        compute='_compute_image_counts',
        help='Number of after images'
    )

    has_before_images = fields.Boolean(
        string='Has Before Images',
        compute='_compute_image_counts',
        help='True if there are before images'
    )

    has_after_images = fields.Boolean(
        string='Has After Images',
        compute='_compute_image_counts',
        help='True if there are after images'
    )

    # Image workflow validation
    can_take_before_photos = fields.Boolean(
        string='Can Take Before Photos',
        compute='_compute_image_permissions',
        help='Whether before photos can be taken in current state'
    )

    can_take_after_photos = fields.Boolean(
        string='Can Take After Photos',
        compute='_compute_image_permissions',
        help='Whether after photos can be taken in current state'
    )

    requires_before_images = fields.Boolean(
        string='Requires Before Images',
        compute='_compute_image_requirements',
        help='Whether before images are required for approval'
    )

    requires_after_images = fields.Boolean(
        string='Requires After Images',
        compute='_compute_image_requirements',
        help='Whether after images are required for return'
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
        """ Use this function to check whether
        the user has the permission
        to change the employee"""
        for record in self:
            res_user = self.env.user
            if res_user.has_group('hr.group_hr_user'):
                record.is_read_only = True
            else:
                record.is_read_only = False

    @api.depends('before_image_ids', 'after_image_ids', 'damage_image_ids')
    def _compute_image_counts(self):
        """Compute image counts and availability"""
        for record in self:
            record.before_image_count = len(record.before_image_ids)
            record.after_image_count = len(record.after_image_ids)
            record.has_before_images = bool(record.before_image_ids)
            record.has_after_images = bool(record.after_image_ids)

    @api.depends('state', 'has_before_images', 'has_after_images')
    def _compute_image_permissions(self):
        """Compute whether images can be taken in current state"""
        for record in self:
            # Before photos: can take when to_approve or approved (for re-documentation)
            record.can_take_before_photos = (
                record.state in ['to_approve', 'approved'] and
                self.env.user.has_group('hr.group_hr_user')
            )

            # After photos: can take when approved (ready to return)
            record.can_take_after_photos = (
                record.state == 'approved' and
                self.env.user.has_group('hr.group_hr_user')
            )

    @api.depends('state')
    def _compute_image_requirements(self):
        """Compute whether images are required"""
        for record in self:
            # Before images are required for approval workflow
            record.requires_before_images = record.state in ['to_approve', 'approved', 'returned']

            # After images are required for return workflow
            record.requires_after_images = record.state in ['returned']

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
        """The function validate the return
        date to ensure it is after the request date"""
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

                # ⭐ NEW: Check if property has approvers
                if not property_obj.approver_ids:
                    raise ValidationError(
                        _('Property "%s" has no approvers assigned. Please contact administrator to set up approvers for this property.')
                        % property_obj.name
                    )

    # Email and Reminder Methods - UPDATED: Only for Fixed Return Date
    def mail_reminder(self):
        """ Send return reminder mail for FIXED DATE returns only"""
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()

        # ✅ Send reminders ONLY for fixed date returns that are overdue
        fixed_date_records = self.search([
            ('state', '=', 'approved'),
            ('return_type', '=', 'date'),
            ('return_date', '!=', False)
        ])

        for custody_record in fixed_date_records:
            if custody_record.return_date <= date_now:
                self._send_fixed_date_reminder(custody_record)

        # ❌ REMOVED: No more reminders for flexible and term_end returns

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

    @api.model_create_multi
    def create(self, vals_list):
        """Create a new record for the HrCustody model.
            This method is responsible for creating a new
            record for the HrCustody model with the provided values.
            It automatically generates a unique name for
            the record using the 'ir.sequence'
            and assigns it to the 'name' field."""
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.custody') or 'New'
        return super(HrCustody, self).create(vals_list)

    def sent(self):
        """Move the current record to the 'to_approve' state."""
        self.state = 'to_approve'
        # Send notification to all approvers
        approver_names = ', '.join(self.property_approver_ids.mapped('name'))
        self.message_post(
            body=_('Custody request sent for approval to: %s') % approver_names,
            message_type='notification'
        )

    def send_mail(self):
        """Send email notification using a predefined template."""
        template = self.env.ref('hr_custody.custody_email_notification_template')
        template.send_mail(self.id)
        self.is_mail_send = True

    def set_to_draft(self):
        """Set the current record to the 'draft' state."""
        self.state = 'draft'

    def renew_approve(self):
        """The function Used to renew and approve
        the current custody record."""
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
        """the function used to refuse
        the renewal of the current custody record"""
        self.renew_date = False
        self.state = 'approved'

    # ⭐ NEW: Refuse with reason
    def refuse_with_reason(self):
        """Refuse with reason - open wizard"""
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

    # Action methods for images
    def action_take_before_photos(self):
        """Action to open before photos wizard"""
        self.ensure_one()

        if not self.can_take_before_photos:
            raise UserError(_('Before photos cannot be taken in current state: %s') %
                          dict(self._fields['state'].selection)[self.state])

        return {
            'name': _('📸 Take Before Photos'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.before.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_custody_id': self.id,
                'default_property_name': self.custody_property_id.name,
                'default_employee_name': self.employee_id.name,
            }
        }

    def action_take_after_photos(self):
        """Action to open after photos wizard"""
        self.ensure_one()

        if not self.can_take_after_photos:
            raise UserError(_('After photos cannot be taken in current state: %s') %
                          dict(self._fields['state'].selection)[self.state])

        return {
            'name': _('📸 Take After Photos & Return'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.after.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_custody_id': self.id,
                'default_property_name': self.custody_property_id.name,
                'default_employee_name': self.employee_id.name,
                'default_before_image_count': self.before_image_count,
            }
        }

    def action_view_image_comparison(self):
        """Action to view before/after image comparison"""
        self.ensure_one()

        return {
            'name': _('📸 Image Comparison - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image',
            'view_mode': 'kanban,list',
            'domain': [('custody_id', '=', self.id)],
            'context': {
                'group_by': 'image_type',
                'default_custody_id': self.id,
            }
        }

    def action_view_all_images(self):
        """Action to view all images for this custody"""
        self.ensure_one()

        return {
            'name': _('📸 All Images - %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image',
            'view_mode': 'kanban,list,form',
            'domain': [('custody_id', '=', self.id)],
            'context': {'default_custody_id': self.id}
        }

    # Updated approve method with image validation
    def approve(self):
        """Updated approve method with before photos validation"""
        # ⭐ NEW: Check if before photos are required but missing
        if self.requires_before_images and not self.has_before_images:
            raise UserError(
                _('Before photos are required before approval. Please take before photos first.')
            )

        # ⭐ NEW: Check approval permissions
        if (self.env.user not in self.custody_property_id.approver_ids and
            not self.env.user.has_group('hr.group_hr_manager')):
            allowed_names = ', '.join(self.custody_property_id.approver_ids.mapped('name'))
            raise UserError(
                _("Only these users can approve this request: %s") % allowed_names
            )

        # Check property availability
        for custody in self.env['hr.custody'].search([
            ('custody_property_id', '=', self.custody_property_id.id),
            ('id', '!=', self.id)
        ]):
            if custody.state == "approved":
                raise UserError(_("Custody is not available now"))

        # Set approval info
        self.approved_by_id = self.env.user
        self.approved_date = fields.Datetime.now()

        # Update property status
        if self.custody_property_id.property_status == 'available':
            self.custody_property_id.property_status = 'in_use'

        self.state = 'approved'

        # Post message with image info
        message_body = _('✅ Request approved by %s') % self.env.user.name
        if self.has_before_images:
            message_body += _(' with %d before photos documented.') % self.before_image_count

        self.message_post(
            body=message_body,
            message_type='notification'
        )

    # Updated return method with image validation
    def set_to_return(self):
        """Updated return method with after photos validation"""
        # ⭐ NEW: Check if after photos are required but missing
        if self.requires_after_images and not self.has_after_images:
            raise UserError(
                _('After photos are required before accepting return. Please take after photos first.')
            )

        # Update property status
        if self.custody_property_id.property_status == 'in_use':
            self.custody_property_id.property_status = 'available'

        self.state = 'returned'

        # Don't automatically set return_date for flexible returns
        if self.return_type == 'date':
            self.return_date = fields.Date.today()

        # Post message with image info
        message_body = _('📦 Equipment returned')
        if self.has_after_images:
            message_body += _(' with %d after photos documented.') % self.after_image_count

        self.message_post(
            body=message_body,
            message_type='notification'
        )

    # ⭐ NEW: Helper method for approvals
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
