from odoo import api, fields, models, _


class CustodySettings(models.TransientModel):
    """
    Configuration settings for HR Custody module.
    Manages global approval settings and default approvers.
    """
    _name = 'custody.settings'
    _description = 'Custody Settings'
    _inherit = 'res.config.settings'

    # Global Approval Settings
    default_approver_groups = fields.Many2many(
        'res.groups',
        'custody_settings_groups_rel',
        'settings_id',
        'group_id',
        string='Default Approver Groups',
        help='Select which user groups can approve custody requests by default',
        domain="[('category_id.name', 'in', ['Human Resources', 'Asset Management', 'Extra Rights'])]"
    )

    # Custom default approvers (individual users)
    default_approver_users = fields.Many2many(
        'res.users',
        'custody_settings_users_rel',
        'settings_id',
        'user_id',
        string='Default Approver Users',
        help='Specific users who can approve custody requests globally',
        domain="[('share', '=', False)]"
    )

    # Approval workflow settings
    require_approval = fields.Boolean(
        string='Require Approval',
        default=True,
        help='Whether custody requests require approval before being granted'
    )

    auto_approve_same_department = fields.Boolean(
        string='Auto-approve Same Department',
        default=False,
        help='Automatically approve requests from same department manager'
    )

    # Notification settings
    notify_approvers = fields.Boolean(
        string='Notify Approvers',
        default=True,
        help='Send email notifications to approvers when new requests are submitted'
    )

    reminder_frequency = fields.Selection([
        ('never', 'Never'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly')
    ], string='Return Reminder Frequency', default='weekly',
    help='How often to send return reminders for overdue items')

    maintenance_reminder_days = fields.Integer(
        string='Maintenance Reminder Days',
        default=7,
        help='Number of days before maintenance due date to send reminders'
    )

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

    def set_values(self):
        """Save the settings"""
        super(CustodySettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_custody.default_approver_groups',
            ','.join(str(gid) for gid in self.default_approver_groups.ids)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_custody.default_approver_users',
            ','.join(str(uid) for uid in self.default_approver_users.ids)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_custody.require_approval', str(self.require_approval)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_custody.auto_approve_same_department', str(self.auto_approve_same_department)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_custody.notify_approvers', str(self.notify_approvers)
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_custody.reminder_frequency', self.reminder_frequency
        )
        self.env['ir.config_parameter'].sudo().set_param(
            'hr_custody.maintenance_reminder_days', str(self.maintenance_reminder_days)
        )

    @api.model
    def get_values(self):
        """Load the settings"""
        res = super(CustodySettings, self).get_values()
        
        # Load group settings
        group_ids = self.get_default_approver_groups()
        if group_ids:
            res['default_approver_groups'] = [(6, 0, group_ids)]
        
        # Load user settings
        user_ids = self.get_default_approver_users()
        if user_ids:
            res['default_approver_users'] = [(6, 0, user_ids)]
        
        # Load other settings
        settings = self.env['ir.config_parameter'].sudo()
        res.update({
            'require_approval': settings.get_param('hr_custody.require_approval', 'True') == 'True',
            'auto_approve_same_department': settings.get_param('hr_custody.auto_approve_same_department', 'False') == 'True',
            'notify_approvers': settings.get_param('hr_custody.notify_approvers', 'True') == 'True',
            'reminder_frequency': settings.get_param('hr_custody.reminder_frequency', 'weekly'),
            'maintenance_reminder_days': int(settings.get_param('hr_custody.maintenance_reminder_days', '7')),
        })
        
        return res