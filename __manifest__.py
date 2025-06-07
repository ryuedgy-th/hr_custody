{
    'name': 'Open HRMS Custody',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': """Manage the company properties""",
    'description': 'Manage the company properties when it is in '
                   'the custody of an employee',
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

        # ⚠️ สำคัญ: custody_property_views.xml ต้องมาก่อน hr_custody_views.xml
        # เพราะ hr_custody_views.xml อ้างอิง custody_property_action
        'views/custody_property_views.xml',
        'views/hr_custody_views.xml',
        'views/hr_employee_views.xml',

        # Reports last
        'reports/report_custody_views.xml',
    ],
    'demo': ['data/demo_data.xml'],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'web_icon': 'hr_custody,static/description/icon.png',
    'installable': True,
    'auto_install': False,
    'application': True,
}
