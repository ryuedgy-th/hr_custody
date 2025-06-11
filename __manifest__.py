{
    'name': 'Open HRMS Custody',
    'version': '18.0.1.1.1',  # ⭐ NEW: Increment version for migration fix
    'category': 'Human Resources',
    'summary': """Manage the company properties with hierarchical categories and image documentation""",
    'description': """
        Manage the company properties when it is in the custody of an employee.

        Features:
        * Hierarchical property categories for better organization
        * Multiple approvers system with category inheritance
        * Flexible return date management
        * Before/after photo documentation
        * Property status tracking
        * Email notifications
        * Comprehensive reporting
        * Return date tracking with overdue management
        * Performance analytics
        * Category-based property management
        * Default approvers per category
    """,
    'author': 'Cybrosys Techno solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    'depends': ['hr', 'mail', 'base'],
    'data': [
        # Security files first
        'security/custody_security.xml',
        'security/ir.model.access.csv',

        # Data files
        'data/custody_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/mail_custody_notification_data.xml',

        # Wizard views
        'wizard/property_return_reason_views.xml',
        'wizard/property_return_date_views.xml',
        'wizard/custody_before_wizard_views.xml',
        'wizard/custody_after_wizard_views.xml',

        # Main views - ORDER MATTERS!
        'views/property_category_views.xml',  # ⭐ NEW: Categories first
        'views/custody_property_views.xml',  # Must come after categories - references category fields
        'views/hr_custody_views.xml',        # References custody_property_action
        'views/hr_employee_views.xml',
        'views/custody_image_views.xml',     # Image views and history

        # Reports last
        'reports/report_custody_views.xml',
    ],
    'demo': ['data/demo_data.xml'],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
}
