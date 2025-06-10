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
        string='Expected Return Date',
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

    # ===== RETURN TRACKING FIELDS =====
    actual_return_date = fields.Date(
        string='Actual Return Date',
        readonly=True,
        tracking=True,
        help='The actual date when the property was returned'
    )

    returned_by_id = fields.Many2one(
        'res.users',
        string='Returned By',
        readonly=True,
        tracking=True,
        help='User who processed the return'
    )

    return_notes = fields.Text(
        string='Return Notes',
        readonly=True,
        help='Notes about the return condition and process'
    )

    # ✅ FIXED: Computed fields with store=True for search compatibility
    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_overdue_status',
        store=True,
        help='True if return is overdue (for fixed date returns)'
    )

    days_overdue = fields.Integer(
        string='Days Overdue',
        compute='_compute_overdue_status',
        store=True,
        help='Number of days overdue (negative if not due yet)'
    )

    # ✅ FIXED: Change field label to be unique
    renew_date = fields.Date(
        string='Renewed Return Date',  # ← เปลี่ยนจาก 'Renewal Return Date'
        tracking=True,
        help="Return date for the renewal",
        readonly=True,
        copy=False
    )

    notes = fields.Html(
        string='Notes',
        help='Note for Custody'
    )

    # ✅ FIXED: Change field label to be unique  
    is_renew_return_date = fields.Boolean(
        string='Is Renewal Rejected',  # ← เปลี่ยนจาก 'Renewal Return Date'
        default=False,
        copy=False,
        help='Rejected Renew Date'
    )

    is_renew_reject = fields.Boolean(
        string='Renewal Rejected',
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
    @api.depends('return_type', 'return_date', 'expected_return_period', 'state', 'actual_return_date')
    def _compute_return_status_display(self):
        """Compute return status display in readable format"""
        for record in self:
            if record.state == 'returned':
                if record.actual_return_date:
                    return_str = f'Returned: {record.actual_return_date.strftime("%d/%m/%Y")}'
                    # Check if returned late
                    if (record.return_type == 'date' and
                        record.return_date and
                        record.actual_return_date > record.return_date):
                        days_late = (record.actual_return_date - record.return_date).days
                        return_str += f' ({days_late} days late)'
                    record.return_status_display = return_str
                else:
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

    @api.depends('return_type', 'return_date', 'actual_return_date', 'state')
    def _compute_overdue_status(self):
        """Compute overdue status for fixed date returns"""
        today = fields.Date.today()

        for record in self:
            if (record.return_type == 'date' and
                record.return_date and
                record.state != 'returned'):

                # Calculate days difference
                delta = (today - record.return_date).days
                record.days_overdue = delta
                record.is_overdue = delta > 0
            else:
                record.days_overdue = 0
                record.is_overdue = False

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

    @api.depends('state')
    def _compute_image_permissions(self):
        """Compute whether images can be taken in current state"""
        for record in self:
            record.can_take_before_photos = (
                record.state in ['to_approve', 'approved'] and
                (self.env.user.has_group('hr.group_hr_user') or
                 self.env.user in record.custody_property_id.approver_ids)
            )

            record.can_take_after_photos = (
                record.state == 'approved' and
                (self.env.user.has_group('hr.group_hr_user') or
                 self.env.user in record.custody_property_id.approver_ids)
            )

    @api.depends('state')
    def _compute_image_requirements(self):
        """Compute whether images are required"""
        for record in self:
            record.requires_before_images = False
            record.requires_after_images = record.state == 'returned'

    # Constraint and validation methods
    @api.constrains('return_type', 'return_date', 'expected_return_period', 'date_request')
    def _check_return_requirements(self):
        """Validate required fields based on return type"""
        for record in self:
            if record.return_type == 'date':
                if not record.return_date:
                    raise ValidationError('Please specify return date when selecting "Fixed Return Date"')
                if record.return_date < record.date_request:
                    raise ValidationError('Return date must not be before request date')
            elif record.return_type in ['flexible', 'term_end']:
                if not record.expected_return_period:
                    raise ValidationError('Please specify expected return period')

    @api.constrains('custody_property_id')
    def _check_property_availability(self):
        """Check if property is available for custody"""
        for record in self:
            if record.custody_property_id:
                property_obj = record.custody_property_id
                if property_obj.property_status != 'available':
                    status_name = dict(property_obj._fields['property_status'].selection)[property_obj.property_status]
                    raise ValidationError(
                        _('Cannot request custody for %s. Property status is: %s. Only Available properties can be requested.')
                        % (property_obj.name, status_name)
                    )
                if not property_obj.approver_ids:
                    raise ValidationError(
                        _('Property "%s" has no approvers assigned. Please contact administrator to set up approvers for this property.')
                        % property_obj.name
                    )

    # CRUD methods
    @api.model_create_multi
    def create(self, vals_list):
        """Create a new record for the HrCustody model."""
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.custody') or 'New'
        return super(HrCustody, self).create(vals_list)

    def write(self, vals):
        """Override write method to handle state changes"""
        result = super(HrCustody, self).write(vals)
        if any(field in vals for field in ['return_date', 'return_type', 'state', 'actual_return_date']):
            self._compute_overdue_status()
        if 'state' in vals:
            for record in self:
                record.message_post(
                    body=_('Custody state changed to %s') % dict(record._fields['state'].selection)[record.state]
                )
        return result

    def unlink(self):
        """Override unlink to prevent deletion of approved records"""
        for record in self:
            if record.state == 'approved':
                raise UserError(_('You cannot delete approved custody records'))
        return super(HrCustody, self).unlink()

    # Business logic methods
    def sent(self):
        """Move the current record to the 'to_approve' state."""
        self.state = 'to_approve'
        approver_names = ', '.join(self.property_approver_ids.mapped('name'))
        self.message_post(
            body=_('Custody request sent for approval to: %s') % approver_names,
            message_type='notification'
        )

    def approve(self):
        """Approve custody request"""
        if (self.env.user not in self.custody_property_id.approver_ids and
            not self.env.user.has_group('hr.group_hr_manager')):
            allowed_names = ', '.join(self.custody_property_id.approver_ids.mapped('name'))
            raise UserError(_("Only these users can approve this request: %s") % allowed_names)

        for custody in self.env['hr.custody'].search([
            ('custody_property_id', '=', self.custody_property_id.id),
            ('id', '!=', self.id)
        ]):
            if custody.state == "approved":
                raise UserError(_("Custody is not available now"))

        self.approved_by_id = self.env.user
        self.approved_date = fields.Datetime.now()

        if self.custody_property_id.property_status == 'available':
            self.custody_property_id.property_status = 'in_use'

        self.state = 'approved'

        message_body = _('✅ Request approved by %s') % self.env.user.name
        if self.has_before_images:
            message_body += _(' with %d before photos documented.') % self.before_image_count
        else:
            message_body += _(' (Before photos can be taken later)')

        self.message_post(body=message_body, message_type='notification')

    # ✅ FIXED: Add missing refuse_with_reason method
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

    # ✅ FIXED: Add missing set_to_draft method
    def set_to_draft(self):
        """Set the current record to the 'draft' state."""
        self.state = 'draft'
        self.message_post(
            body=_('Custody request set back to draft'),
            message_type='notification'
        )

    def set_to_return(self):
        """Process equipment return"""
        if self.requires_after_images and not self.has_after_images:
            raise UserError(_('After photos are required before accepting return. Please take after photos first.'))

        if self.custody_property_id.property_status == 'in_use':
            self.custody_property_id.property_status = 'available'

        self.actual_return_date = fields.Date.today()
        self.returned_by_id = self.env.user
        self.state = 'returned'

        message_body = _('📦 Equipment returned on %s by %s') % (
            self.actual_return_date.strftime('%d/%m/%Y'),
            self.env.user.name
        )

        if self.has_after_images:
            message_body += _(' with %d after photos documented.') % self.after_image_count

        if (self.return_type == 'date' and
            self.return_date and
            self.actual_return_date > self.return_date):
            days_late = (self.actual_return_date - self.return_date).days
            message_body += _(' ⚠️ Returned %d days late.') % days_late

        self.message_post(body=message_body, message_type='notification')

    # ✅ FIXED: Add missing image action methods
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

    # ===== NEW: Multiple Image Upload Actions =====
    def action_upload_before_images(self):
        """Action to open multiple before images upload wizard"""
        self.ensure_one()
        if not self.can_take_before_photos:
            raise UserError(_('Before photos cannot be taken in current state: %s') %
                          dict(self._fields['state'].selection)[self.state])

        return {
            'name': _('📸 Upload Multiple Before Images'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_custody_id': self.id,
                'default_image_type': 'before',
            }
        }

    def action_upload_after_images(self):
        """Action to open multiple after images upload wizard"""
        self.ensure_one()
        if not self.can_take_after_photos:
            raise UserError(_('After photos cannot be taken in current state: %s') %
                          dict(self._fields['state'].selection)[self.state])

        return {
            'name': _('📸 Upload Multiple After Images'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_custody_id': self.id,
                'default_image_type': 'after',
            }
        }

    def action_upload_damage_images(self):
        """Action to open multiple damage images upload wizard"""
        self.ensure_one()
        if self.state not in ['approved', 'returned']:
            raise UserError(_('Damage photos can only be uploaded when custody is approved or returned'))

        return {
            'name': _('📸 Upload Multiple Damage Images'),
            'type': 'ir.actions.act_window',
            'res_model': 'custody.image.upload.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_custody_id': self.id,
                'default_image_type': 'damage',
            }
        }

    # Helper methods
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
                ('name', operator, name),
                ('employee_id.name', operator, name),
                ('custody_property_id.name', operator, name),
                ('purpose', operator, name),
                ('custody_property_id.property_code', operator, name),
                ('approved_by_id.name', operator, name)
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
