from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class HrCustody(models.Model):
    """
    Complete HR Custody Management with Professional Photo Management
    Odoo 18 Compliant Version with Security and Performance Improvements
    """
    _name = 'hr.custody'
    _description = 'HR Custody Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_request desc'
    _rec_name = 'name'
    _check_company_auto = True

    # Constants for better maintainability
    MAX_HIGH_QUALITY_SIZE = 2 * 1024 * 1024  # 2MB
    MIN_GOOD_QUALITY_SIZE = 500 * 1024       # 500KB

    # Basic Field definitions with Odoo 18 best practices
    name = fields.Char(
        string='Reference',
        copy=False,
        readonly=True,
        index=True,
        help="Unique reference number for custody request"
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
        required=True,
        index=True,
        default=lambda self: self.env.company,
        help="Company where the custody request is made"
    )

    rejected_reason = fields.Text(
        string='Rejection Reason',
        copy=False,
        readonly=True,
        help="Reason provided when rejecting the custody request"
    )

    date_request = fields.Date(
        string='Request Date',
        required=True,
        tracking=True,
        index=True,
        default=fields.Date.today,
        help="Date when the custody request was made"
    )

    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
        default=lambda self: self.env.user.employee_id,
        help="Employee requesting custody of the property"
    )

    purpose = fields.Char(
        string='Purpose/Reason',
        tracking=True,
        required=True,
        help="Business reason for requesting custody"
    )

    custody_property_id = fields.Many2one(
        'custody.property',
        string='Property',
        required=True,
        ondelete='restrict',
        index=True,
        tracking=True,
        help="Property/asset being requested for custody"
    )

    # Approval tracking with proper constraints
    approved_by_id = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        tracking=True,
        index=True,
        help="User who approved the custody request"
    )

    approved_date = fields.Datetime(
        string='Approval Date',
        readonly=True,
        index=True,
        help="Date and time when the request was approved"
    )

    # Return date management with validation
    return_type = fields.Selection([
        ('date', 'Fixed Return Date'),
        ('flexible', 'Flexible Return'),
        ('term_end', 'Return at Term/Project End')
    ], string='Return Type', 
       default='date', 
       required=True, 
       tracking=True,
       help="Type of return arrangement for the property")

    return_date = fields.Date(
        string='Expected Return Date',
        tracking=True,
        index=True,
        help="Expected date for returning the property"
    )

    expected_return_period = fields.Char(
        string='Expected Return Period',
        help="Description of expected return timeframe"
    )

    return_status_display = fields.Char(
        string='Return Status',
        compute='_compute_return_status_display',
        store=False,
        help="Current return status display"
    )

    # Return tracking with proper indexing
    actual_return_date = fields.Date(
        string='Actual Return Date',
        readonly=True,
        tracking=True,
        index=True,
        help="Actual date when the property was returned"
    )

    returned_by_id = fields.Many2one(
        'res.users',
        string='Returned By',
        readonly=True,
        tracking=True,
        help="User who processed the return"
    )

    return_notes = fields.Text(
        string='Return Notes',
        readonly=True,
        help="Notes from the return process"
    )

    notes = fields.Html(
        string='Additional Notes',
        help="Additional notes and comments"
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('to_approve', 'Waiting For Approval'),
        ('approved', 'Approved'),
        ('returned', 'Returned'),
        ('rejected', 'Rejected')
    ],
    string='Status',
    default='draft',
    tracking=True,
    index=True,
    required=True,
    help="Current status of the custody request"
    )

    # 📸 PHOTO MANAGEMENT SYSTEM - Optimized for Odoo 18
    
    attachment_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=[('res_model', '=', 'hr.custody')],
        string='All Attachments',
        help="All attachments related to this custody"
    )

    handover_photo_ids = fields.One2many(
        'ir.attachment',
        'res_id',
        domain=[('res_model', '=', 'hr.custody'), 
                ('custody_photo_type', 'in', ['handover_overall', 'handover_detail', 'handover_serial'])],
        string='Handover Photos',
        help="Photos taken during property handover"
    )

    return_photo_ids = fields.One2many(
        'ir.attachment',
        'res_id', 
        domain=[('res_model', '=', 'hr.custody'), 
                ('custody_photo_type', 'in', ['return_overall', 'return_detail', 'return_damage', 'maintenance'])],
        string='Return Photos',
        help="Photos taken during property return"
    )

    # Optimized computed fields for photo counts
    photo_counts = fields.Text(
        string='Photo Summary',
        compute='_compute_photo_counts',
        store=False,
        help="Summary of photos by type"
    )

    photo_status = fields.Char(
        string='Photo Documentation Status',
        compute='_compute_photo_status',
        store=False,
        help="Overall photo documentation status"
    )

    handover_photo_count = fields.Integer(
        string='Handover Photos',
        compute='_compute_handover_photo_count',
        store=False,
        help='Number of handover photos'
    )

    return_photo_count = fields.Integer(
        string='Return Photos',
        compute='_compute_return_photo_count',
        store=False,
        help='Number of return photos'
    )

    total_photo_count = fields.Integer(
        string='Total Photos',
        compute='_compute_total_photo_count',
        store=False,
        help='Total number of photos'
    )

    # Boolean fields for view conditions
    has_handover_photos = fields.Boolean(
        string='Has Handover Photos',
        compute='_compute_has_handover_photos',
        store=False,
        help='Whether this custody has handover photos'
    )

    has_return_photos = fields.Boolean(
        string='Has Return Photos',
        compute='_compute_has_return_photos',
        store=False,
        help='Whether this custody has return photos'
    )

    has_photos = fields.Boolean(
        string='Has Photos',
        compute='_compute_has_photos',
        store=False,
        help='Whether this custody has any photos'
    )

    # ✅ FIX: Add missing photos_complete field
    photos_complete = fields.Boolean(
        string='Photos Complete',
        compute='_compute_photos_complete',
        store=False,
        help='Whether photo documentation is complete for current state'
    )

    # Additional photo quality and status fields
    photo_quality_status = fields.Char(
        string='Photo Quality Status',
        compute='_compute_photo_quality_status',
        store=False,
        help='Overall photo quality assessment'
    )

    photos_required = fields.Boolean(
        string='Photos Required',
        compute='_compute_photos_required',
        store=False,
        help='Whether photos are required for current state'
    )

    # 🔧 COMPUTED METHODS - Optimized for Performance

    @api.depends('return_type', 'return_date', 'expected_return_period', 'state', 'actual_return_date')
    def _compute_return_status_display(self) -> None:
        """Compute return status display with proper formatting"""
        for record in self:
            if record.state == 'returned':
                if record.actual_return_date:
                    record.return_status_display = _('Returned: %s') % record.actual_return_date.strftime("%d/%m/%Y")
                else:
                    record.return_status_display = _('Returned')
            elif record.return_type == 'date' and record.return_date:
                record.return_status_display = _('Due: %s') % record.return_date.strftime("%d/%m/%Y")
            elif record.return_type == 'flexible':
                period = record.expected_return_period or _('No fixed date')
                record.return_status_display = _('Flexible (%s)') % period
            elif record.return_type == 'term_end':
                period = record.expected_return_period or _('End of term')
                record.return_status_display = _('Return %s') % period
            else:
                record.return_status_display = _('Pending')

    @api.depends('attachment_ids.custody_photo_type')
    def _compute_photo_counts(self) -> None:
        """Compute photo counts by type efficiently"""
        for record in self:
            if not record.attachment_ids:
                record.photo_counts = _("No photos")
                continue
                
            counts = {}
            for attachment in record.attachment_ids:
                if attachment.custody_photo_type:
                    counts[attachment.custody_photo_type] = counts.get(attachment.custody_photo_type, 0) + 1
            
            if counts:
                count_list = [f"{key}: {value}" for key, value in counts.items()]
                record.photo_counts = ", ".join(count_list)
            else:
                record.photo_counts = _("No categorized photos")

    @api.depends('handover_photo_ids')
    def _compute_handover_photo_count(self) -> None:
        """Compute handover photo count efficiently"""
        for record in self:
            record.handover_photo_count = len(record.handover_photo_ids)

    @api.depends('return_photo_ids')
    def _compute_return_photo_count(self) -> None:
        """Compute return photo count efficiently"""
        for record in self:
            record.return_photo_count = len(record.return_photo_ids)

    @api.depends('attachment_ids.mimetype')
    def _compute_total_photo_count(self) -> None:
        """Compute total photo count with proper filtering"""
        for record in self:
            image_attachments = record.attachment_ids.filtered(
                lambda a: a.mimetype and a.mimetype.startswith('image/')
            )
            record.total_photo_count = len(image_attachments)

    @api.depends('handover_photo_ids')
    def _compute_has_handover_photos(self) -> None:
        """Compute whether custody has handover photos"""
        for record in self:
            record.has_handover_photos = len(record.handover_photo_ids) > 0

    @api.depends('return_photo_ids')
    def _compute_has_return_photos(self) -> None:
        """Compute whether custody has return photos"""
        for record in self:
            record.has_return_photos = len(record.return_photo_ids) > 0

    @api.depends('attachment_ids.mimetype')
    def _compute_has_photos(self) -> None:
        """Compute whether custody has any photos"""
        for record in self:
            image_attachments = record.attachment_ids.filtered(
                lambda a: a.mimetype and a.mimetype.startswith('image/')
            )
            record.has_photos = len(image_attachments) > 0

    @api.depends('state', 'handover_photo_ids', 'return_photo_ids')
    def _compute_photos_complete(self) -> None:
        """Compute whether photo documentation is complete for current state"""
        for record in self:
            handover_count = len(record.handover_photo_ids)
            return_count = len(record.return_photo_ids)
            
            if record.state in ['draft', 'to_approve']:
                # Draft states don't require photos
                record.photos_complete = True
            elif record.state == 'approved':
                # Approved state should have handover photos
                record.photos_complete = handover_count > 0
            elif record.state == 'returned':
                # Returned state should have both handover and return photos
                record.photos_complete = handover_count > 0 and return_count > 0
            else:
                # Rejected or other states
                record.photos_complete = True

    @api.depends('state')
    def _compute_photos_required(self) -> None:
        """Compute whether photos are required for current state"""
        for record in self:
            record.photos_required = record.state in ['approved', 'returned']

    @api.depends('attachment_ids.custody_photo_type', 'attachment_ids.is_high_quality')
    def _compute_photo_quality_status(self) -> None:
        """Compute overall photo quality status"""
        for record in self:
            if not record.attachment_ids:
                record.photo_quality_status = _("No photos")
                continue
            
            image_attachments = record.attachment_ids.filtered(
                lambda a: a.mimetype and a.mimetype.startswith('image/')
            )
            
            if not image_attachments:
                record.photo_quality_status = _("No photos")
                continue
            
            high_quality_count = len(image_attachments.filtered('is_high_quality'))
            total_count = len(image_attachments)
            quality_percentage = (high_quality_count / total_count) * 100
            
            if quality_percentage >= 80:
                record.photo_quality_status = _("High Quality (%d%%)") % quality_percentage
            elif quality_percentage >= 50:
                record.photo_quality_status = _("Good Quality (%d%%)") % quality_percentage
            else:
                record.photo_quality_status = _("Low Quality (%d%%)") % quality_percentage

    @api.depends('attachment_ids.custody_photo_type', 'state')
    def _compute_photo_status(self) -> None:
        """Compute comprehensive photo status"""
        for record in self:
            handover_count = len(record.handover_photo_ids)
            return_count = len(record.return_photo_ids)
            
            if record.state == 'returned':
                if handover_count > 0 and return_count > 0:
                    record.photo_status = _("Complete (%d handover, %d return)") % (handover_count, return_count)
                elif handover_count > 0:
                    record.photo_status = _("Partial (%d handover only)") % handover_count
                else:
                    record.photo_status = _("No photos")
            elif record.state == 'approved':
                if handover_count > 0:
                    record.photo_status = _("Handover documented (%d photos)") % handover_count
                else:
                    record.photo_status = _("No handover photos")
            else:
                record.photo_status = _("Pending documentation")

    # 🔒 CONSTRAINT METHODS - Odoo 18 Best Practices

    @api.constrains('return_date', 'date_request')
    def _check_return_date(self) -> None:
        """Validate return date is after request date"""
        for record in self:
            if record.return_date and record.return_date <= record.date_request:
                raise ValidationError(_("Return date must be after request date"))

    @api.constrains('state', 'approved_by_id', 'approved_date')
    def _check_approval_requirements(self) -> None:
        """Validate approval requirements"""
        for record in self:
            if record.state == 'approved':
                if not record.approved_by_id:
                    raise ValidationError(_("Approved records must have an approver"))
                if not record.approved_date:
                    raise ValidationError(_("Approved records must have approval date"))

    @api.constrains('state', 'returned_by_id', 'actual_return_date')
    def _check_return_requirements(self) -> None:
        """Validate return requirements"""
        for record in self:
            if record.state == 'returned':
                if not record.returned_by_id:
                    raise ValidationError(_("Returned records must have return processor"))
                if not record.actual_return_date:
                    raise ValidationError(_("Returned records must have actual return date"))

    @api.constrains('employee_id', 'company_id')
    def _check_employee_company(self) -> None:
        """Validate employee belongs to the same company"""
        for record in self:
            if record.employee_id.company_id and record.employee_id.company_id != record.company_id:
                raise ValidationError(_("Employee must belong to the same company as the custody request"))

    # 🚀 PHOTO MANAGEMENT METHODS - Enhanced

    def action_assign_handover_photo_types(self) -> Dict[str, Any]:
        """Assign photo types for handover with improved feedback"""
        self.ensure_one()
        untyped_attachments = self.attachment_ids.filtered(
            lambda a: not a.custody_photo_type and a.mimetype and a.mimetype.startswith('image/')
        )
        
        if not untyped_attachments:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': _('No untyped photos found to assign'),
                    'sticky': False,
                }
            }
        
        success = self._auto_assign_photo_types('handover')
        if success:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _('✅ Assigned handover photo types to %d photos') % len(untyped_attachments),
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _('Failed to assign photo types'),
                    'sticky': False,
                }
            }

    def action_assign_return_photo_types(self) -> Dict[str, Any]:
        """Assign photo types for return with improved feedback"""
        self.ensure_one()
        untyped_attachments = self.attachment_ids.filtered(
            lambda a: not a.custody_photo_type and a.mimetype and a.mimetype.startswith('image/')
        )
        
        if not untyped_attachments:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'info',
                    'message': _('No untyped photos found to assign'),
                    'sticky': False,
                }
            }
        
        success = self._auto_assign_photo_types('return')
        if success:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'success',
                    'message': _('✅ Assigned return photo types to %d photos') % len(untyped_attachments),
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'type': 'warning',
                    'message': _('Failed to assign photo types'),
                    'sticky': False,
                }
            }

    def _auto_assign_photo_types(self, photo_category: str = 'handover') -> bool:
        """Auto-assign photo types with error handling"""
        try:
            untyped_attachments = self.attachment_ids.filtered(
                lambda a: not a.custody_photo_type and a.mimetype and a.mimetype.startswith('image/')
            )
            
            if not untyped_attachments:
                return False
            
            # Determine default type based on category
            default_type = 'handover_overall' if photo_category == 'handover' else 'return_overall'
            
            # Update attachments efficiently
            untyped_attachments.write({
                'custody_photo_type': default_type,
                'res_model': 'hr.custody',
                'res_id': self.id,
            })
            
            # Post message to chatter
            self.message_post(
                body=_('📸 Auto-assigned %s photo types to %d photos') % (
                    photo_category, len(untyped_attachments)
                )
            )
            
            return True
            
        except Exception as e:
            # Log error and return False
            self.env['ir.logging'].create({
                'name': 'hr.custody',
                'type': 'server',
                'level': 'ERROR',
                'message': f'Error in _auto_assign_photo_types: {str(e)}',
                'func': '_auto_assign_photo_types',
                'line': '1',
            })
            return False

    # 📊 BUSINESS LOGIC METHODS - Enhanced

    @api.model_create_multi
    def create(self, vals_list: List[Dict[str, Any]]) -> 'HrCustody':
        """Create method with enhanced sequence generation"""
        for vals in vals_list:
            if not vals.get('name'):
                try:
                    vals['name'] = self.env['ir.sequence'].next_by_code('hr.custody')
                    if not vals['name']:
                        vals['name'] = _('New')
                except Exception:
                    vals['name'] = _('New')
        
        records = super().create(vals_list)
        
        # Auto-assign photo types for attachments created during record creation
        for record in records:
            if record.attachment_ids:
                record._auto_assign_photo_types('handover')
        
        return records

    def write(self, vals: Dict[str, Any]) -> bool:
        """Enhanced write method with state change tracking"""
        result = super().write(vals)
        
        if 'state' in vals:
            for record in self:
                state_label = dict(record._fields['state'].selection).get(record.state, record.state)
                record.message_post(
                    body=_('Custody state changed to: %s') % state_label
                )
        
        # Auto-assign photo types when attachments are added
        if 'attachment_ids' in vals:
            for record in self:
                if record.state == 'approved':
                    record._auto_assign_photo_types('handover')
                elif record.state == 'returned':
                    record._auto_assign_photo_types('return')
        
        return result

    def unlink(self) -> bool:
        """Enhanced unlink with proper validation"""
        for record in self:
            if record.state in ('approved', 'returned'):
                raise UserError(_('You cannot delete approved or returned custody records'))
        return super().unlink()

    # 🎯 WORKFLOW METHODS - Enhanced & Backward Compatible

    def sent(self) -> None:
        """Legacy method name for backward compatibility with views"""
        return self.action_send_for_approval()

    def approve(self) -> None:
        """Legacy method name for backward compatibility with views"""
        return self.action_approve()

    def refuse_with_reason(self) -> Dict[str, Any]:
        """Legacy method name for backward compatibility with views"""
        return self.action_refuse_with_reason()

    def set_to_draft(self) -> None:
        """Legacy method name for backward compatibility with views"""
        return self.action_set_to_draft()

    def set_to_return(self) -> None:
        """Legacy method name for backward compatibility with views"""
        return self.action_return_equipment()

    def action_send_for_approval(self) -> None:
        """Send custody request for approval"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft requests can be sent for approval'))
        
        self.state = 'to_approve'
        self.message_post(
            body=_('Custody request sent for approval'),
            message_type='notification'
        )

    def action_approve(self) -> None:
        """Approve custody request with validation"""
        self.ensure_one()
        if self.state != 'to_approve':
            raise UserError(_('Only pending requests can be approved'))
        
        # Check if property is available
        if self.custody_property_id.property_status != 'available':
            raise UserError(_('Property is not available for custody'))
        
        self.write({
            'approved_by_id': self.env.user.id,
            'approved_date': fields.Datetime.now(),
            'state': 'approved'
        })
        
        # Update property status
        self.custody_property_id.property_status = 'in_use'
        
        self.message_post(
            body=_('✅ Request approved by %s') % self.env.user.name,
            message_type='notification'
        )

    def action_refuse_with_reason(self) -> Dict[str, Any]:
        """Open wizard to refuse with reason"""
        self.ensure_one()
        if self.state != 'to_approve':
            raise UserError(_('Only pending requests can be rejected'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Rejection Reason'),
            'res_model': 'property.return.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_reason': '',
                'model_id': 'hr.custody',
                'reject_id': self.id,
            }
        }

    def action_set_to_draft(self) -> None:
        """Reset to draft state"""
        self.ensure_one()
        if self.state not in ('rejected', 'to_approve'):
            raise UserError(_('Only rejected or pending requests can be reset to draft'))
        
        self.state = 'draft'
        self.message_post(
            body=_('Custody request reset to draft'),
            message_type='notification'
        )

    def action_return_equipment(self) -> None:
        """Process equipment return"""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Only approved custody can be returned'))
        
        # Update property status
        if self.custody_property_id.property_status == 'in_use':
            self.custody_property_id.property_status = 'available'
        
        self.write({
            'actual_return_date': fields.Date.today(),
            'returned_by_id': self.env.user.id,
            'state': 'returned'
        })
        
        self.message_post(
            body=_('📦 Equipment returned on %s by %s') % (
                self.actual_return_date.strftime('%d/%m/%Y'),
                self.env.user.name
            ),
            message_type='notification'
        )

    def name_get(self) -> List[tuple]:
        """Enhanced name display with context"""
        result = []
        for record in self:
            name = f"{record.name or _('New')} - {record.employee_id.name}"
            if record.custody_property_id:
                name += f" ({record.custody_property_id.name})"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name: str = '', args: Optional[List] = None, operator: str = 'ilike', 
                     limit: int = 100, name_get_uid: Optional[int] = None) -> List[int]:
        """Enhanced search supporting reference and employee name"""
        args = args or []
        if name:
            domain = ['|', '|',
                      ('name', operator, name),
                      ('employee_id.name', operator, name),
                      ('custody_property_id.name', operator, name)]
            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
        return super()._name_search(name, args, operator, limit, name_get_uid)


class IrAttachment(models.Model):
    """Enhanced ir.attachment with custody photo categorization and quality assessment"""
    _inherit = 'ir.attachment'

    # Photo categorization system
    custody_photo_type = fields.Selection([
        ('handover_overall', 'Handover - Overall View'),
        ('handover_detail', 'Handover - Detail View'), 
        ('handover_serial', 'Handover - Serial Number'),
        ('return_overall', 'Return - Overall View'),
        ('return_detail', 'Return - Detail View'),
        ('return_damage', 'Return - Damage Documentation'),
        ('maintenance', 'Maintenance Record'),
    ], string='Photo Type', 
       index=True,
       help="Categorizes photos for custody workflow")

    # Enhanced quality scoring
    quality_score = fields.Integer(
        string='Quality Score',
        compute='_compute_quality_score',
        store=True,
        help="Automatic quality assessment (0-100) based on file size and format"
    )

    is_high_quality = fields.Boolean(
        string='High Quality',
        compute='_compute_quality_score',
        store=True,
        help="Whether this attachment meets high quality criteria"
    )

    @api.depends('file_size', 'mimetype')
    def _compute_quality_score(self) -> None:
        """Enhanced quality scoring with better criteria"""
        for attachment in self:
            if not attachment.mimetype or not attachment.mimetype.startswith('image/'):
                attachment.quality_score = 0
                attachment.is_high_quality = False
                continue
            
            if not attachment.file_size:
                attachment.quality_score = 30
                attachment.is_high_quality = False
                continue
            
            # Enhanced quality scoring based on file size and format
            score = 0
            
            # Size-based scoring
            if attachment.file_size > HrCustody.MAX_HIGH_QUALITY_SIZE:  # > 2MB
                score += 50
            elif attachment.file_size > HrCustody.MIN_GOOD_QUALITY_SIZE:  # > 500KB
                score += 35
            else:
                score += 20
            
            # Format-based scoring
            if 'jpeg' in attachment.mimetype or 'jpg' in attachment.mimetype:
                score += 25
            elif 'png' in attachment.mimetype:
                score += 30
            elif 'webp' in attachment.mimetype:
                score += 20
            else:
                score += 10
            
            # Name-based quality hints
            if attachment.name:
                name_lower = attachment.name.lower()
                if any(keyword in name_lower for keyword in ['hd', 'high', 'quality', 'hq']):
                    score += 15
                elif any(keyword in name_lower for keyword in ['thumb', 'small', 'compressed']):
                    score -= 10
            
            attachment.quality_score = min(score, 100)
            attachment.is_high_quality = score >= 70
