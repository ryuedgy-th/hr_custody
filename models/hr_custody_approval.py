from odoo import api, fields, models, _
from odoo.exceptions import UserError


class HrCustodyApproval(models.AbstractModel):
    """
    Approval-related functionality for Hr Custody.
    """
    _name = 'hr.custody.approval'
    _description = 'Hr Custody Approval Mixin'

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

    @api.depends('property_approver_ids', 'category_approver_ids')
    def _compute_effective_approvers(self):
        """Combine all approvers for this custody request"""
        for record in self:
            # Combine property approvers and category approvers
            record.effective_approver_ids = record.property_approver_ids | record.category_approver_ids

    def sent(self):
        """Move the current record to the 'to_approve' state."""
        self.state = 'to_approve'
        # Send notification to all approvers
        approver_names = ', '.join(self.property_approver_ids.mapped('name'))
        self.message_post(
            body=_('Custody request sent for approval to: %s') % approver_names,
            message_type='notification'
        )

    def approve(self):
        """Approve the current custody record.
        
        Validates user permissions, checks property availability,
        records approval metadata, and updates property status.
        """
        # Check if current user is in effective approvers or is HR Manager
        current_user = self.env.user
        is_hr_manager = current_user.has_group('hr.group_hr_manager')
        
        for record in self:
            # Refresh approvers to ensure we have the latest
            record._compute_effective_approvers()
            
            # Check approval permissions
            if not is_hr_manager and current_user not in record.effective_approver_ids:
                raise UserError(
                    _("You don't have permission to approve this request. Authorized approvers are: %s")
                    % (', '.join(record.effective_approver_ids.mapped('name')))
                )

            # Check property availability
            for custody in self.env['hr.custody'].search([
                ('custody_property_id', '=', record.custody_property_id.id),
                ('id', '!=', record.id)
            ]):
                if custody.state == "approved":
                    raise UserError(_("Custody is not available now"))

            # Record approval information
            record.approved_by_id = current_user
            record.approved_date = fields.Datetime.now()

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

    @api.model
    def get_pending_approvals(self, user_id=None):
        """Get custody requests pending approval for specific user"""
        if not user_id:
            user_id = self.env.user.id

        return self.search([
            ('custody_property_id.approver_ids', 'in', [user_id]),
            ('state', '=', 'to_approve')
        ])