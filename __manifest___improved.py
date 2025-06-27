{
    'name': 'HR Custody Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources/Equipment',
    'summary': 'Comprehensive company asset and equipment custody management system',
    'description': '''
HR Custody Management System
============================

A comprehensive solution for managing company assets and equipment custody with:

**Core Features:**
* Multi-category asset tracking with tags and categorization
* Employee custody request workflow with approval system
* Flexible return date management (fixed date, flexible, term-based)
* Visual condition documentation with before/after images
* Maintenance scheduling with automated reminders
* Role-based access control with custody-specific permissions

**Advanced Capabilities:**
* Property status tracking (Available, In Use, Maintenance, Damaged, Retired)
* Multi-image support for comprehensive documentation
* Automated email notifications and overdue reminders  
* Warranty tracking and status monitoring
* Technical specifications tracking (IP, MAC, Serial numbers)
* Maintenance history with scheduled maintenance workflows
* Department-based property management
* Multi-company support with proper data isolation

**User Roles:**
* Custody Users: View own custody records
* Custody Officers: Approve requests and manage properties
* Custody Managers: Full administrative access

**Integration:**
* Seamless HR module integration
* Mail activity tracking and notifications
* Product catalog integration for equipment specifications
* Department-based responsibility assignment

Perfect for organizations managing laptops, mobile devices, vehicles, 
keys, and other company assets with proper accountability and tracking.
    ''',
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': 'https://www.cybrosys.com',
    'depends': ['hr', 'mail'],  # Removed unnecessary 'base' dependency
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
        'wizard/multi_images_upload_views.xml',
        'wizard/record_maintenance_views.xml',
        # Main views with menu structure - must come before dependent views
        'views/custody_property_views.xml',
        'views/custody_image_views.xml',
        'views/maintenance_history_views.xml',
        'views/hr_custody_views.xml',
        # Category and Tag views that depend on menus from hr_custody_views.xml
        'views/custody_category_views.xml',
        'views/custody_tag_views.xml',
        # Employee views
        'views/hr_employee_views.xml',
        # Reports last
        'reports/report_custody_views.xml',
    ],
    'demo': ['data/demo_data.xml'],
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,  # Changed from True - this is a feature module, not an app
    'sequence': 95,  # Added sequence for proper module ordering
    'assets': {
        'web.assets_backend': [
            'hr_custody/static/src/scss/custody.scss',
        ],
    },
    # Added external dependencies documentation
    'external_dependencies': {
        'python': [],  # No external Python dependencies
        'bin': [],     # No external binary dependencies
    },
    # Added price and currency for Odoo Apps store (if publishing)
    # 'price': 0.00,
    # 'currency': 'EUR',
    # 'support': 'support@cybrosys.com',
}