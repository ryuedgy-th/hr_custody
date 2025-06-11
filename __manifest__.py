{
    'name': 'Advanced HR Custody Management',
    'version': '18.0.1.3.0',  # 🚀 MAJOR RELEASE: Complete UX redesign and feature enhancement
    'category': 'Human Resources',
    'summary': """Modern enterprise-grade custody management with smart workflows and hierarchical categories""",
    'description': """
        🚀 Advanced HR Custody Management - Odoo 18.0

        A comprehensive solution for managing company assets and property custody with 
        advanced approval workflows, real-time tracking, and modern UX design.

        ✨ KEY FEATURES:
        • Smart Workflow Management with unified interface
        • Hierarchical Property Categories with inheritance
        • Advanced Multi-Level Approval System
        • Comprehensive Tracking with overdue detection
        • Modern responsive UX with smart filters
        • Real-time notifications and analytics

        🎯 SMART FILTERS & WORKFLOW:
        • 🔔 Waiting My Approval (priority view)
        • 📋 My Requests
        • ✅ Approved by Me  
        • ⚠️ Overdue Items
        • 🕐 Due This Week
        • 📊 Comprehensive status and date filters

        🏗️ ENTERPRISE FEATURES:
        • Hierarchical category organization
        • Property-specific and category-default approvers
        • Flexible return management (fixed/flexible/term-end)
        • Complete audit trail and approval history
        • Mobile-responsive design
        • Multi-company support

        Based on the original Open HRMS Custody module by Cybrosys Techno Solutions,
        extensively redesigned and enhanced for modern enterprise requirements.
    """,
    'author': 'Enhanced by ryuedgy-th',
    'company': 'Based on Cybrosys Techno Solutions',
    'maintainer': 'ryuedgy-th',
    'website': "https://github.com/ryuedgy-th/hr_custody",
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

        # 🔧 PERFECT DEPENDENCY ORDER - External ID resolution
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
    'external_dependencies': {
        'python': [],
    },
    'support': 'https://github.com/ryuedgy-th/hr_custody/issues',
    'live_test_url': False,
    'price': 0.0,
    'currency': 'USD',
}
