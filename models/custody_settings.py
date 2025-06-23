from odoo import api, fields, models, _


class CustodySettings(models.TransientModel):
    """
    Configuration settings for HR Custody module.
    Manages global approval settings and default approvers.
    """
    _name = 'custody.settings'
    _description = 'Custody Settings'
    _inherit = 'res.config.settings'



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


    @api.model
    def get_default_approver_groups(self):
        """Get the default approver groups from predefined security groups"""
        # Return predefined custody and HR groups that have approval permissions
        custody_officer = self.env.ref('hr_custody.group_custody_officer', raise_if_not_found=False)
        custody_manager = self.env.ref('hr_custody.group_custody_manager', raise_if_not_found=False)
        hr_manager = self.env.ref('hr.group_hr_manager', raise_if_not_found=False)
        
        group_ids = []
        if custody_officer:
            group_ids.append(custody_officer.id)
        if custody_manager:
            group_ids.append(custody_manager.id)
        if hr_manager:
            group_ids.append(hr_manager.id)
        
        return group_ids

    @api.model
    def get_default_approver_users(self):
        """Get the default approver users from predefined security groups"""
        # Get all users from the default approver groups
        group_ids = self.get_default_approver_groups()
        if group_ids:
            groups = self.env['res.groups'].browse(group_ids)
            user_ids = []
            for group in groups:
                user_ids.extend(group.users.ids)
            return list(set(user_ids))  # Remove duplicates
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

