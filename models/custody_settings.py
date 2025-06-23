from odoo import api, fields, models, _


class CustodySettings(models.TransientModel):
    """
    Configuration settings for HR Custody module.
    Manages global approval settings and default approvers.
    """
    _name = 'custody.settings'
    _description = 'Custody Settings'
    _inherit = 'res.config.settings'

    # Global Approval Settings - stored as config parameters
    default_approver_group_ids = fields.Char(
        string='Default Approver Groups',
        help='Comma-separated list of group IDs that can approve custody requests by default',
        config_parameter='hr_custody.default_approver_groups'
    )

    default_approver_user_ids = fields.Char(
        string='Default Approver Users', 
        help='Comma-separated list of user IDs that can approve custody requests globally',
        config_parameter='hr_custody.default_approver_users'
    )

    # Display fields for UI
    default_approver_groups = fields.Many2many(
        'res.groups',
        string='Default Approver Groups Display',
        help='Select which user groups can approve custody requests by default',
        domain="[('category_id.name', 'in', ['Human Resources', 'Asset Management', 'Extra Rights'])]",
        compute='_compute_default_approvers',
        inverse='_inverse_default_approver_groups'
    )

    default_approver_users = fields.Many2many(
        'res.users',
        string='Default Approver Users Display',
        help='Specific users who can approve custody requests globally',
        domain="[('share', '=', False)]",
        compute='_compute_default_approvers',
        inverse='_inverse_default_approver_users'
    )

    # Approval workflow settings
    require_approval = fields.Boolean(
        string='Require Approval',
        default=True,
        help='Whether custody requests require approval before being granted',
        config_parameter='hr_custody.require_approval'
    )

    auto_approve_same_department = fields.Boolean(
        string='Auto-approve Same Department',
        default=False,
        help='Automatically approve requests from same department manager',
        config_parameter='hr_custody.auto_approve_same_department'
    )

    # Notification settings
    notify_approvers = fields.Boolean(
        string='Notify Approvers',
        default=True,
        help='Send email notifications to approvers when new requests are submitted',
        config_parameter='hr_custody.notify_approvers'
    )

    reminder_frequency = fields.Selection([
        ('never', 'Never'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], string='Return Reminder Frequency', default='weekly',
    help='How often to send return reminders for overdue items',
    config_parameter='hr_custody.reminder_frequency')

    maintenance_reminder_days = fields.Integer(
        string='Maintenance Reminder Days',
        default=7,
        help='Number of days before maintenance due date to send reminders',
        config_parameter='hr_custody.maintenance_reminder_days'
    )

    @api.depends('default_approver_group_ids', 'default_approver_user_ids')
    def _compute_default_approvers(self):
        """Compute Many2many fields from stored config parameters"""
        for record in self:
            # Groups
            group_ids = []
            if record.default_approver_group_ids:
                try:
                    group_ids = [int(gid) for gid in record.default_approver_group_ids.split(',') if gid.strip()]
                except (ValueError, TypeError):
                    group_ids = []
            record.default_approver_groups = [(6, 0, group_ids)]
            
            # Users  
            user_ids = []
            if record.default_approver_user_ids:
                try:
                    user_ids = [int(uid) for uid in record.default_approver_user_ids.split(',') if uid.strip()]
                except (ValueError, TypeError):
                    user_ids = []
            record.default_approver_users = [(6, 0, user_ids)]

    def _inverse_default_approver_groups(self):
        """Store Many2many groups as comma-separated config parameter"""
        for record in self:
            group_ids = ','.join(str(gid) for gid in record.default_approver_groups.ids)
            record.default_approver_group_ids = group_ids

    def _inverse_default_approver_users(self):
        """Store Many2many users as comma-separated config parameter"""
        for record in self:
            user_ids = ','.join(str(uid) for uid in record.default_approver_users.ids)
            record.default_approver_user_ids = user_ids

    @api.model
    def get_default_approver_groups(self):
        """Get the default approver groups from settings"""
        settings = self.env['ir.config_parameter'].sudo()
        group_ids = settings.get_param('hr_custody.default_approver_groups', '')
        if group_ids:
            return [int(gid) for gid in group_ids.split(',') if gid.strip()]
        return []

    @api.model
    def get_default_approver_users(self):
        """Get the default approver users from settings"""
        settings = self.env['ir.config_parameter'].sudo()
        user_ids = settings.get_param('hr_custody.default_approver_users', '')
        if user_ids:
            return [int(uid) for uid in user_ids.split(',') if uid.strip()]
        return []

    @api.model
    def get_effective_approvers(self, property_id=None):
        """
        Get effective approvers for a custody request.
        Priority: Property custom approvers > Global settings > Default HR groups
        """
        approvers = []
        
        # 1. Check property-specific approvers first
        if property_id:
            property_obj = self.env['custody.property'].browse(property_id)
            if property_obj.approver_ids:
                return property_obj.approver_ids
        
        # 2. Get global default groups
        group_ids = self.get_default_approver_groups()
        if group_ids:
            groups = self.env['res.groups'].browse(group_ids)
            for group in groups:
                approvers.extend(group.users.ids)
        
        # 3. Get global default users
        user_ids = self.get_default_approver_users()
        if user_ids:
            approvers.extend(user_ids)
        
        # 4. Fallback to HR Manager group if no settings
        if not approvers:
            hr_manager_group = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
            if hr_manager_group:
                approvers.extend(hr_manager_group.users.ids)
        
        # Remove duplicates and return users
        unique_approver_ids = list(set(approvers))
        return self.env['res.users'].browse(unique_approver_ids)

