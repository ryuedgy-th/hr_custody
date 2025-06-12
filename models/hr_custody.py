from datetime import date, datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrCustody(models.Model):
    """
    Complete HR Custody Management with Professional Photo Management
    Pre-refactor stable version with all working features
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

    # 📸 COMPLETE PHOTO MANAGEMENT SYSTEM (PRE-REFACTOR STABLE)
    
    # Main attachment field for photo upload
    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=[('res_model', '=', 'hr.custody')],
        string='All Attachments'
    )

    # Photo categorization fields with computed domains
    handover_photo_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=[('res_model', '=', 'hr.custody'), ('custody_photo_type', 'in', ['handover_overall', 'handover_detail', 'handover_serial'])],
        string='Handover Photos'
    )

    return_photo_ids = fields.One2many(
        'ir.attachment',
        'res_id', 
        domain=[('res_model', '=', 'hr.custody'), ('custody_photo_type', 'in', ['return_overall', 'return_detail', 'return_damage', 'maintenance'])],
        string='Return Photos'
    )

    # Photo counts for UI display
    photo_counts = fields.Text(
        string='Photo Counts',
        compute='_compute_photo_counts',
        store=False
    )

    photo_status = fields.Char(
        string='Photo Status',
        compute='_compute_photo_status',
        store=False
    )

    # ✅ FIX: Add missing handover_photo_count field
    handover_photo_count = fields.Integer(
        string='Handover Photo Count',
        compute='_compute_handover_photo_count',
        store=False,
        help='Count of handover photos for this custody'
    )

    # Add return photo count for consistency
    return_photo_count = fields.Integer(
        string='Return Photo Count',
        compute='_compute_return_photo_count',
        store=False,
        help='Count of return photos for this custody'
    )

    # 🔧 COMPUTED METHODS FOR PHOTO MANAGEMENT

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

    @api.depends('attachment_ids', 'attachment_ids.custody_photo_type')
    def _compute_photo_counts(self):
        """Compute photo counts by type for display"""
        for record in self:
            counts = {}
            for attachment in record.attachment_ids:
                photo_type = attachment.custody_photo_type
                if photo_type:
                    counts[photo_type] = counts.get(photo_type, 0) + 1
            
            # Create display string
            if counts:
                count_list = [f"{k}: {v}" for k, v in counts.items()]
                record.photo_counts = ", ".join(count_list)
            else:
                record.photo_counts = "No photos"

    @api.depends('handover_photo_ids')
    def _compute_handover_photo_count(self):
        """Compute count of handover photos"""
        for record in self:
            record.handover_photo_count = len(record.handover_photo_ids)

    @api.depends('return_photo_ids')
    def _compute_return_photo_count(self):
        """Compute count of return photos"""
        for record in self:
            record.return_photo_count = len(record.return_photo_ids)

    @api.depends('attachment_ids', 'state')
    def _compute_photo_status(self):
        """Compute overall photo status"""
        for record in self:
            handover_count = len([a for a in record.attachment_ids if a.custody_photo_type in ['handover_overall', 'handover_detail', 'handover_serial']])
            return_count = len([a for a in record.attachment_ids if a.custody_photo_type in ['return_overall', 'return_detail', 'return_damage', 'maintenance']])
            
            if record.state == 'returned':
                if handover_count > 0 and return_count > 0:
                    record.photo_status = f"Complete ({handover_count} handover, {return_count} return)"
                elif handover_count > 0:
                    record.photo_status = f"Partial ({handover_count} handover only)"
                else:
                    record.photo_status = "No photos"
            elif record.state == 'approved':
                if handover_count > 0:
                    record.photo_status = f"Handover documented ({handover_count} photos)"
                else:
                    record.photo_status = "No handover photos"
            else:
                record.photo_status = "Pending"

    # 🚀 PHOTO MANAGEMENT ACTION METHODS

    def action_assign_handover_photo_types(self):
        """Manually assign photo types for handover photos"""
        untyped_attachments = self.attachment_ids.filtered(lambda a: not a.custody_photo_type and a.mimetype and a.mimetype.startswith('image/'))
        
        if not untyped_attachments:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': 'No untyped photos found to assign',
                    'sticky': False,
                }
            }
        
        result = self._auto_assign_photo_types('handover')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': f'✅ Assigned handover photo types to {len(untyped_attachments)} photos',
                'sticky': False,
            }
        }

    def action_assign_return_photo_types(self):
        """Manually assign photo types for return photos"""
        untyped_attachments = self.attachment_ids.filtered(lambda a: not a.custody_photo_type and a.mimetype and a.mimetype.startswith('image/'))
        
        if not untyped_attachments:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': 'No untyped photos found to assign',
                    'sticky': False,
                }
            }
        
        result = self._auto_assign_photo_types('return')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': f'✅ Assigned return photo types to {len(untyped_attachments)} photos',
                'sticky': False,
            }
        }

    def _auto_assign_photo_types(self, photo_category='handover'):
        """Auto-assign photo types based on custody state and category"""
        untyped_attachments = self.attachment_ids.filtered(
            lambda a: not a.custody_photo_type and a.mimetype and a.mimetype.startswith('image/')
        )
        
        if not untyped_attachments:
            return False
        
        # Assign default photo type based on category and state
        if photo_category == 'handover':
            default_type = 'handover_overall'
        else:  # return
            default_type = 'return_overall'
        
        # Update attachments with photo type
        for attachment in untyped_attachments:
            attachment.write({
                'custody_photo_type': default_type,
                'res_model': 'hr.custody',
                'res_id': self.id,
            })
        
        # Post message to chatter
        self.message_post(
            body=f'📸 Auto-assigned {photo_category} photo types to {len(untyped_attachments)} photos'
        )
        
        return True

    # 📊 BUSINESS LOGIC METHODS

    @api.model_create_multi
    def create(self, vals_list):
        """Create method with sequence generation and photo processing"""
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('hr.custody') or 'New'
        
        records = super(HrCustody, self).create(vals_list)
        
        # Auto-assign photo types for any attachments created during record creation
        for record in records:
            if record.attachment_ids:
                record._auto_assign_photo_types('handover')
        
        return records

    def write(self, vals):
        """Override write to handle state changes and photo assignments"""
        result = super(HrCustody, self).write(vals)
        
        if 'state' in vals:
            for record in self:
                record.message_post(
                    body=_('Custody state changed to %s') % dict(record._fields['state'].selection)[record.state]
                )
        
        # Auto-assign photo types when attachments are added
        if 'attachment_ids' in vals:
            for record in self:
                if record.state == 'approved':
                    record._auto_assign_photo_types('handover')
                elif record.state == 'returned':
                    record._auto_assign_photo_types('return')
        
        return result

    def unlink(self):
        """Override unlink to prevent deletion of approved records"""
        for record in self:
            if record.state == 'approved':
                raise UserError(_('You cannot delete approved custody records'))
        return super(HrCustody, self).unlink()

    # 🎯 WORKFLOW METHODS

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


class IrAttachment(models.Model):
    """Extended ir.attachment with custody photo categorization"""
    _inherit = 'ir.attachment'

    # 📸 PHOTO CATEGORIZATION SYSTEM
    custody_photo_type = fields.Selection([
        ('handover_overall', 'Handover - Overall View'),
        ('handover_detail', 'Handover - Detail View'), 
        ('handover_serial', 'Handover - Serial Number'),
        ('return_overall', 'Return - Overall View'),
        ('return_detail', 'Return - Detail View'),
        ('return_damage', 'Return - Damage Documentation'),
        ('maintenance', 'Maintenance Record'),
    ], string='Photo Type', help="Categorizes photos for custody workflow")

    # Quality scoring (optional enhancement)
    quality_score = fields.Integer(
        string='Quality Score',
        compute='_compute_quality_score',
        store=True,
        help="Automatic quality assessment based on file size and resolution"
    )

    is_high_quality = fields.Boolean(
        string='High Quality',
        compute='_compute_quality_score',
        store=True
    )

    @api.depends('file_size', 'mimetype')
    def _compute_quality_score(self):
        """Compute photo quality score based on file size and type"""
        for attachment in self:
            if attachment.mimetype and attachment.mimetype.startswith('image/'):
                # Basic quality scoring based on file size
                if attachment.file_size:
                    if attachment.file_size > 2000000:  # > 2MB
                        attachment.quality_score = 90
                        attachment.is_high_quality = True
                    elif attachment.file_size > 500000:  # > 500KB
                        attachment.quality_score = 70
                        attachment.is_high_quality = True
                    else:
                        attachment.quality_score = 50
                        attachment.is_high_quality = False
                else:
                    attachment.quality_score = 30
                    attachment.is_high_quality = False
            else:
                attachment.quality_score = 0
                attachment.is_high_quality = False
