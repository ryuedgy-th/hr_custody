# -*- coding: utf-8 -*-
#############################################################################
#    A part of Open HRMS Project <https://www.openhrms.com>
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions(<https://www.cybrosys.com>)
#
#    You can modify it under the terms of the GNU LESSER
#    GENERAL PUBLIC LICENSE (LGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU LESSER GENERAL PUBLIC LICENSE (LGPL v3) for more details.
#
#    You should have received a copy of the GNU LESSER GENERAL PUBLIC LICENSE
#    (LGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
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

    # Email and Reminder Methods
    def mail_reminder(self):
        """ Use this function to send return reminder mail"""
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()

        # Send reminders for fixed date returns
        fixed_date_records = self.search([
            ('state', '=', 'approved'),
            ('return_type', '=', 'date'),
            ('return_date', '!=', False)
        ])

        for custody_record in fixed_date_records:
            if custody_record.return_date <= date_now:
                self._send_fixed_date_reminder(custody_record)

        # Send reminders for flexible returns (every 30 days)
        flexible_records = self.search([
            ('state', '=', 'approved'),
            ('return_type', 'in', ['flexible', 'term_end'])
        ])

        for record in flexible_records:
            if self._should_send_flexible_reminder(record):
                self._send_flexible_reminder(record)

    def _send_fixed_date_reminder(self, custody_record):
        """Send reminder for fixed date returns"""
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

    def _should_send_flexible_reminder(self, record):
        """Check if should send flexible reminder (every 30 days)"""
        last_message = self.env['mail.message'].search([
            ('model', '=', 'hr.custody'),
            ('res_id', '=', record.id),
            ('subject', 'ilike', 'reminder'),
        ], order='date desc', limit=1)

        if not last_message:
            return True

        days_since_last = (fields.Date.today() - last_message.date.date()).days
        return days_since_last >= 30

    def _send_flexible_reminder(self, record):
        """Send reminder for flexible return date items"""
        mail_content = _(
            'Hi %s,<br/>'
            'This is a reminder about the %s you borrowed on %s.<br/>'
            'Return Type: %s<br/>'
            'Expected Return Period: %s<br/><br/>'
            'If you can return it now, please contact HR department.<br/>'
            'If you still need to use it, please inform us.<br/><br/>'
            'Best regards,<br/>%s'
        ) % (
            record.employee_id.name,
            record.custody_property_id.name,
            record.date_request,
            dict(record._fields['return_type'].selection)[record.return_type],
            record.expected_return_period or 'Not specified',
            record.company_id.name or 'HR Department'
        )

        main_content = {
            'subject': _('Custody Reminder: %s') % record.custody_property_id.name,
            'author_id': self.env.user.partner_id.id,
            'body_html': mail_content,
            'email_to': record.employee_id.work_email,
        }

        mail_id = self.env['mail.mail'].create(main_content)
        mail_id.send()

        # Post message for tracking
        record.message_post(
            body=_('Flexible return reminder sent to %s') % record.employee_id.name,
            message_type='notification'
        )

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

    def approve(self):
        """The function used to approve the current custody record."""
        for custody in self.env['hr.custody'].search([
            ('custody_property_id', '=', self.custody_property_id.id),
            ('id', '!=', self.id)
        ]):
            if custody.state == "approved":
                raise UserError(_("Custody is not available now"))

        # Update property status to 'in_use' when approved
        if self.custody_property_id.property_status == 'available':
            self.custody_property_id.property_status = 'in_use'

        self.state = 'approved'

    def set_to_return(self):
        """The function used to set the current custody record to the 'returned' state"""
        # Update property status to 'available' when returned
        if self.custody_property_id.property_status == 'in_use':
            self.custody_property_id.property_status = 'available'

        self.state = 'returned'
        # Don't automatically set return_date for flexible returns
        if self.return_type == 'date':
            self.return_date = fields.Date.today()

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

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        """Override name_search to search in multiple fields"""
        if args is None:
            args = []

        if name:
            domain = [
                '|', '|', '|', '|',
                ('name', operator, name),  # Code
                ('employee_id.name', operator, name),  # Employee name
                ('custody_property_id.name', operator, name),  # Property name
                ('purpose', operator, name),  # Reason
                ('custody_property_id.property_code', operator, name)  # Property code
            ]
            records = self.search(domain + args, limit=limit)
            return records.name_get()

        return super(HrCustody, self).name_search(name, args, operator, limit)
