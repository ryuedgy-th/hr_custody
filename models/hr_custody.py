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

    # เพิ่ม Custody Type
    custody_type = fields.Selection([
        ('temporary', 'Temporary (มีกำหนดคืน)'),
        ('permanent', 'Permanent (ไม่มีกำหนดคืน)'),
        ('until_notice', 'Until Notice (คืนเมื่อได้รับแจ้ง)')
    ], string='Custody Type', default='temporary', required=True,
       tracking=True, help='Type of custody - temporary has return date, permanent does not')

    return_date = fields.Date(
        string='Return Date',
        required=False,  # เปลี่ยนเป็น False เพื่อรองรับ permanent
        tracking=True,
        help='The date when the custody is expected to be returned. Leave empty for permanent custody.'
    )

    # เพิ่มฟิลด์สำหรับ permanent custody
    permanent_reason = fields.Text(
        string='Permanent Custody Reason',
        help='Reason for permanent custody (no return date)'
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

    @api.onchange('custody_type')
    def _onchange_custody_type(self):
        """เมื่อเปลี่ยนประเภทการยืม"""
        if self.custody_type == 'permanent':
            self.return_date = False
            self.permanent_reason = 'Permanent assignment - no return date required'
        elif self.custody_type == 'until_notice':
            self.return_date = False
            self.permanent_reason = 'Return when notified by management'
        else:  # temporary
            if not self.return_date:
                # ตั้งค่าเริ่มต้น 30 วันจากวันที่ขอ
                if self.date_request:
                    self.return_date = self.date_request + timedelta(days=30)
                else:
                    self.return_date = fields.Date.today() + timedelta(days=30)
            self.permanent_reason = False

    def mail_reminder(self):
        """ Use this function to product return reminder mail"""
        now = datetime.now() + timedelta(days=1)
        date_now = now.date()

        # เฉพาะ custody ที่มี return_date เท่านั้น (temporary)
        match = self.search([
            ('state', '=', 'approved'),
            ('custody_type', '=', 'temporary'),  # เฉพาะแบบชั่วคราว
            ('return_date', '!=', False)  # มี return_date
        ])

        for custody_record in match:
            if custody_record.return_date:
                exp_date = custody_record.return_date
                if exp_date <= date_now:
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    url = f"{base_url}/web#id={custody_record.id}&view_type=form&model=hr.custody"

                    mail_content = _(
                        'Hi %s,<br>Your temporary custody of %s (Ref: %s) is due for return on %s. '
                        'Please return the item or request for renewal through the following link: '
                        '<br><br><a href="%s" style="background-color: #875A7B; color: white; '
                        'padding: 10px 15px; text-decoration: none; border-radius: 3px;">View Custody</a>'
                    ) % (
                        custody_record.employee_id.name,
                        custody_record.custody_property_id.name,
                        custody_record.name,
                        custody_record.return_date,
                        url
                    )

                    main_content = {
                        'subject': _('Custody Return Reminder - %s') % custody_record.name,
                        'author_id': self.env.user.partner_id.id,
                        'body_html': mail_content,
                        'email_to': custody_record.employee_id.work_email,
                    }

                    mail_id = self.env['mail.mail'].create(main_content)
                    mail_id.send()

                    if custody_record.employee_id.user_id:
                        mail_id.mail_message_id.write({
                            'partner_ids': [(4, custody_record.employee_id.user_id.partner_id.id)]
                        })

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
        """The function used to approve
        the current custody record."""
        for custody in self.env['hr.custody'].search([
            ('custody_property_id', '=', self.custody_property_id.id),
            ('id', '!=', self.id)
        ]):
            if custody.state == "approved":
                raise UserError(_("Custody is not available now"))

        self.state = 'approved'

    def set_to_return(self):
        """The function used to set the current
        custody record to the 'returned' state"""
        self.state = 'returned'
        # อัปเดต return_date เป็นวันที่จริงที่คืน
        if not self.return_date or self.custody_type != 'temporary':
            self.return_date = fields.Date.today()

    @api.constrains('return_date', 'custody_type', 'date_request')
    def validate_return_date(self):
        """ตรวจสอบ return_date ตาม custody_type"""
        for record in self:
            if record.custody_type == 'temporary':
                # ถ้าเป็นแบบชั่วคราว ต้องมี return_date
                if not record.return_date:
                    raise ValidationError(_('Return date is required for temporary custody'))
                if record.return_date < record.date_request:
                    raise ValidationError(_('Return date must be after request date'))

            # ถ้าเป็น permanent หรือ until_notice ไม่ต้องมี return_date

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

    def name_get(self):
        """แสดงชื่อพร้อมประเภทการยืม"""
        result = []
        for record in self:
            name = record.name or 'New'
            if record.custody_type == 'permanent':
                name += ' (Permanent)'
            elif record.custody_type == 'until_notice':
                name += ' (Until Notice)'
            result.append((record.id, name))
        return result
