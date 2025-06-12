from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrCustody(models.Model):
    """
        Simple Hr custody contract creation model.
    """
    _name = 'hr.custody'
    _description = 'Hr Custody Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc'
    _rec_name = 'name'

    # Basic Field definitions
    name = fields.Char(
        string='Code',
        copy=False,
        readonly=True
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
        default=lambda self: self.env.company
    )

    rejected_reason = fields.Text(
        string='Rejected Reason',
        copy=False,
        readonly=True
    )

    date_request = fields.Date(
        string='Requested Date',
        required=True,
        tracking=True,
        default=fields.Date.today
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        default=lambda self: self.env.user.employee_id
    )

    purpose = fields.Char(
        string='Reason',
        tracking=True,
        required=True
    )

    custody_property_id = fields.Many2one(
        'custody.property',
        string='Property',
        required=True
    )

    # Approval tracking
    approved_by_id = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        tracking=True
    )

    approved_date = fields.Datetime(
        string='Approved Date',
        readonly=True
    )

    # Return date management
    return_type = fields.Selection([
        ('date', 'Fixed Return Date'),
        ('flexible', 'No Fixed Return Date'),
        ('term_end', 'Return at Term/Project End')
    ], string='Return Type', default='date', required=True, tracking=True)

    return_date = fields.Date(
        string='Expected Return Date',
        tracking=True
    )

    expected_return_period = fields.Char(
        string='Expected Return Period'
    )

    return_status_display = fields.Char(
        string='Return Status',
        compute='_compute_return_status_display',
        store=False
    )

    # Return tracking
    actual_return_date = fields.Date(
        string='Actual Return Date',
        readonly=True,
        tracking=True
    )

    returned_by_id = fields.Many2one(
        'res.users',
        string='Returned By',
        readonly=True,
        tracking=True
    )

    return_notes = fields.Text(
        string='Return Notes',
        readonly=True
    )

    # Simple attachment field
    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        string='Photos & Documents',
        domain=[('res_model', '=', 'hr.custody')]
    )

    notes = fields.Html(
        string='Notes'
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
    tracking=True
    )

    # Simple computed method
    @api.depends('return_type', 'return_date', 'expected_return_period', 'state', 'actual_return_date')
    def _compute_return_status_display(self):
        """Compute return status display"""
        for record in self:
            if record.state == 'returned':
                if record.actual_return_date:
                    record.return_status_display = f'Returned: {record.actual_return_date.strftime("%d/%m/%Y")}'
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

    # Standard create method
    @api.model_create_multi
    def create(self, vals_list):
        """Create method with sequence generation"""
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.custody') or 'New'
        
        records = super(HrCustody, self).create(vals_list)
        return records

    def write(self, vals):
        """Override write to handle state changes"""
        result = super(HrCustody, self).write(vals)
        
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
        self.message_post(
            body=_('Custody request sent for approval'),
            message_type='notification'
        )

    def approve(self):
        """Approve custody request"""
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

        self.message_post(
            body=_('📦 Equipment returned on %s by %s') % (
                self.actual_return_date.strftime('%d/%m/%Y'),
                self.env.user.name
            ),
            message_type='notification'
        )

    def name_get(self):
        """Enhanced name display"""
        result = []
        for record in self:
            name = f"{record.name} - {record.employee_id.name}"
            if record.custody_property_id:
                name += f" ({record.custody_property_id.name})"
            result.append((record.id, name))
        return result
