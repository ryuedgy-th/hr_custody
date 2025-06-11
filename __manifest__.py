{
    'name': 'Open HRMS Custody',
    'version': '18.0.1.2.5',  # 🔧 MEGA FIX: Complete external ID dependency chain resolution
    'category': 'Human Resources',
    'summary': """Manage the company properties with hierarchical categories""",
    'description': """
        Manage the company properties when it is in the custody of an employee.

        Features:
        * Hierarchical property categories for better organization
        * Multiple approvers system with category inheritance
        * Flexible return date management
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

        # 🔧 CRITICAL FIX: Perfect dependency chain resolution
        # Based on Odoo 18.0 docs: "Data files are sequentially loaded following their order, 
        # if data A refers to data B, you must make sure that B is loaded before A"
        
        # 1. Main menu structure FIRST (creates all parent menus)
        'views/hr_custody_menu_structure.xml',  # Creates: hr_custody_main_menu, hr_custody_menu_management, hr_custody_menu_config
        
        # 2. Base actions and views (no external menu dependencies)  
        'views/custody_property_views.xml',     # Creates: custody_property_action
        'views/property_category_views.xml',   # Creates: property_category_action, references hr_custody_menu_config
        
        # 3. Main views that reference the above actions
        'views/hr_custody_views.xml',          # References: custody_property_action, hr_custody_menu_management
        'views/hr_employee_views.xml',
        
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
