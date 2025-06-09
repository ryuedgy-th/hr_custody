{
    'name': 'Open HRMS Custody',
    'version': '18.0.1.0.1',  # ← เพิ่ม version เพื่อให้ migration ทำงาน
    'category': 'Human Resources',
    'summary': """Manage the company properties with image documentation""",
    'description': """
        Manage the company properties when it is in the custody of an employee.

        Features:
        * Multiple approvers system
        * Flexible return date management
        * Before/after photo documentation
        * Property status tracking
        * Email notifications
        * Comprehensive reporting
        * Return date tracking with overdue management
        * Performance analytics
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
        'views/custody_property_views.xml',  # Must come first - defines custody_property_action
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
