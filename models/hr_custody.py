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

    # ===== 📸 PHOTO MANAGEMENT SYSTEM =====
    # Inspired by hr_expense attachment system
    
    # All attachments (photos and documents)
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'hr_custody_attachment_rel',
        'custody_id',
        'attachment_id',
        string='All Attachments',
        help='All photos and documents related to this custody'
    )
    
    # Handover photos (taken when property is handed over)
    handover_photo_ids = fields.Many2many(
        'ir.attachment',
        'hr_custody_handover_photo_rel',
        'custody_id',
        'attachment_id',
        string='Handover Photos',
        domain=[('res_model', '=', 'hr.custody'), ('custody_photo_type', 'in', ['handover_overall', 'handover_detail', 'handover_serial'])],
        help='Photos taken during property handover to document initial condition'
    )
    
    # Return photos (taken when property is returned)
    return_photo_ids = fields.Many2many(
        'ir.attachment',
        'hr_custody_return_photo_rel',
        'custody_id', 
        'attachment_id',
        string='Return Photos',
        domain=[('res_model', '=', 'hr.custody'), ('custody_photo_type', 'in', ['return_overall', 'return_detail', 'return_damage'])],
        help='Photos taken during property return to document final condition'
    )
    
    # Computed fields for photo counts
    handover_photo_count = fields.Integer(
        string='Handover Photos Count',
        compute='_compute_photo_counts',
        help='Number of handover photos'
    )
    
    return_photo_count = fields.Integer(
        string='Return Photos Count', 
        compute='_compute_photo_counts',
        help='Number of return photos'
    )
    
    total_photo_count = fields.Integer(
        string='Total Photos',
        compute='_compute_photo_counts',
        help='Total number of photos'
    )
    
    # ✅ FIXED: Photo status indicators with store=True for search compatibility
    has_handover_photos = fields.Boolean(
        string='Has Handover Photos',
        compute='_compute_photo_status',
        store=True,
        help='True if handover photos are uploaded'
    )
    
    has_return_photos = fields.Boolean(
        string='Has Return Photos',
        compute='_compute_photo_status',
        store=True,
        help='True if return photos are uploaded'
    )
    
    photos_complete = fields.Boolean(
        string='Photos Complete',
        compute='_compute_photo_status',
        store=True,
        help='True if both handover and return photos are available'
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

    # ===== 📸 PHOTO COMPUTED METHODS =====
    
    @api.depends('handover_photo_ids', 'return_photo_ids', 'attachment_ids')
    def _compute_photo_counts(self):
        """Compute photo counts for dashboard display"""
        for record in self:
            record.handover_photo_count = len(record.handover_photo_ids)
            record.return_photo_count = len(record.return_photo_ids)
            # Count only photo attachments (filter by mimetype)
            photo_attachments = record.attachment_ids.filtered(
                lambda att: att.mimetype and att.mimetype.startswith('image/')
            )
            record.total_photo_count = len(photo_attachments)
    
    @api.depends('handover_photo_ids', 'return_photo_ids', 'state')
    def _compute_photo_status(self):
        """Compute photo status indicators"""
        for record in self:
            record.has_handover_photos = bool(record.handover_photo_ids)
            record.has_return_photos = bool(record.return_photo_ids)
            
            # Photos are complete if:
            # - Handover photos exist (for approved+ states)
            # - Return photos exist (for returned state)
            if record.state == 'returned':
                record.photos_complete = record.has_handover_photos and record.has_return_photos
            elif record.state in ['approved']:
                record.photos_complete = record.has_handover_photos
            else:
                record.photos_complete = False

    # ===== 📸 PHOTO MANAGEMENT METHODS =====
    
    def action_view_handover_photos(self):
        """Open handover photos in gallery view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Handover Photos - %s') % self.name,
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', self.handover_photo_ids.ids)],
            'context': {
                'default_res_model': 'hr.custody',
                'default_res_id': self.id,
                'default_custody_photo_type': 'handover_overall',
            },
            'target': 'current'
        }
    
    def action_view_return_photos(self):
        """Open return photos in gallery view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Return Photos - %s') % self.name,
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('id', 'in', self.return_photo_ids.ids)],
            'context': {
                'default_res_model': 'hr.custody',
                'default_res_id': self.id,
                'default_custody_photo_type': 'return_overall',
            },
            'target': 'current'
        }
    
    def action_compare_photos(self):
        """Open photo comparison view"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Photo Comparison - %s') % self.name,
            'res_model': 'hr.custody',
            'view_mode': 'form',
            'res_id': self.id,
            'views': [(False, 'form')],
            'target': 'new',
            'context': {
                'default_view_mode': 'photo_comparison',
                'form_view_ref': 'hr_custody.hr_custody_photo_comparison_view_form'
            }
        }
    
    def get_photos_by_type(self, photo_type):
        """Get photos filtered by type"""
        self.ensure_one()
        return self.attachment_ids.filtered(
            lambda att: att.custody_photo_type == photo_type
        )
    
    def get_handover_photos_summary(self):
        """Get summary of handover photos by type"""
        self.ensure_one()
        summary = {}
        handover_types = ['handover_overall', 'handover_detail', 'handover_serial']
        for photo_type in handover_types:
            photos = self.get_photos_by_type(photo_type)
            summary[photo_type] = {
                'count': len(photos),
                'photos': photos,
                'latest': photos.sorted('create_date', reverse=True)[:1] if photos else False
            }
        return summary
    
    def get_return_photos_summary(self):
        """Get summary of return photos by type"""
        self.ensure_one()
        summary = {}
        return_types = ['return_overall', 'return_detail', 'return_damage']
        for photo_type in return_types:
            photos = self.get_photos_by_type(photo_type)
            summary[photo_type] = {
                'count': len(photos),
                'photos': photos,
                'latest': photos.sorted('create_date', reverse=True)[:1] if photos else False
            }
        return summary

    # Computed Fields (existing)
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
        self.message_post(
            body=_('✅ Request approved by %s') % self.env.user.name,
            message_type='notification'
        )

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

    def set_to_draft(self):
        """Set the current record to the 'draft' state."""
        self.state = 'draft'
        self.message_post(
            body=_('Custody request set back to draft'),
            message_type='notification'
        )

    def set_to_return(self):
        """Process equipment return"""
        if self.custody_property_id.property_status == 'in_use':
            self.custody_property_id.property_status = 'available'

        self.actual_return_date = fields.Date.today()
        self.returned_by_id = self.env.user
        self.state = 'returned'

        message_body = _('📦 Equipment returned on %s by %s') % (
            self.actual_return_date.strftime('%d/%m/%Y'),
            self.env.user.name
        )

        if (self.return_type == 'date' and
            self.return_date and
            self.actual_return_date > self.return_date):
            days_late = (self.actual_return_date - self.return_date).days
            message_body += _(' ⚠️ Returned %d days late.') % days_late

        self.message_post(body=message_body, message_type='notification')

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
