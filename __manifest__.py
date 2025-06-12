{
    'name': 'Advanced HR Custody Management',
    'version': '18.0.1.3.0',  # 🔄 Updated version for compliance improvements
    'category': 'Human Resources',
    'sequence': 10,
    'summary': """Complete HR custody management with professional photo documentation and enhanced security""",
    'description': """
        🚀 Advanced HR Custody Management - Odoo 18.0 (Compliance Enhanced)

        A comprehensive solution for managing company assets and property custody with 
        advanced photo documentation, approval workflows, enhanced security, and 
        professional UI/UX optimized for Odoo 18.

        ✨ KEY FEATURES (ODOO 18 COMPLIANT):
        • Complete Photo Management System with professional galleries
        • Smart photo type assignment (handover/return with 7 categories)
        • Enhanced security with granular access control and record rules
        • Multi-level approval workflow system with state-based permissions
        • Real-time photo upload and gallery display
        • Mobile-responsive design with modern UI/UX
        • Multi-company support with proper data isolation
        • Department-based access control for managers
        • Performance-optimized computed fields and database queries

        📸 PHOTO MANAGEMENT:
        • Professional photo galleries with thumbnails and quality scoring
        • Photo categorization: handover_overall, handover_detail, handover_serial
        • Return photos: return_overall, return_detail, return_damage, maintenance
        • Enhanced quality scoring and analytics (0-100 score)
        • Side-by-side photo comparison capabilities
        • Automated photo type assignment with error handling

        🔒 SECURITY & COMPLIANCE:
        • Granular record rules for different user levels
        • State-based access control (draft/approved/returned)
        • Department manager access to team requests
        • Property approver permissions
        • Multi-company data isolation
        • Attachment security for custody photos
        • Field-level constraints and validations

        🔧 TECHNICAL IMPROVEMENTS (ODOO 18):
        • Type hints for better code maintainability
        • Enhanced error handling and validation
        • Optimized computed fields with proper dependencies
        • Database indexing for performance
        • Proper ondelete constraints
        • Modern Python coding standards
        • Comprehensive field help documentation

        This version meets all Odoo 18 development standards and best practices
        including security, performance, and code quality requirements.
    """,
    'author': 'Enhanced by ryuedgy-th',
    'company': 'Based on Cybrosys Techno Solutions',
    'maintainer': 'ryuedgy-th',
    'website': "https://github.com/ryuedgy-th/hr_custody",
    'depends': ['hr', 'mail', 'base', 'web'],  # Added 'web' for better JS compatibility
    'data': [
        # Security files first - ORDER MATTERS
        'security/custody_security.xml',
        'security/ir.model.access.csv',

        # Data files
        'data/custody_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/mail_custody_notification_data.xml',

        # Wizard views
        'wizard/property_return_reason_views.xml',
        'wizard/property_return_date_views.xml',

        # Core models and views (Odoo 18 compliant)
        'views/hr_custody_views_complete.xml',
        'views/custody_property_views.xml',
        'views/property_category_views.xml',
        'views/hr_employee_views.xml',
        
        # Reports
        'reports/report_custody_views.xml',
    ],
    'demo': ['data/demo_data.xml'],
    'assets': {
        'web.assets_backend': [
            # Custom CSS and JS assets if needed
        ],
    },
    'images': ['static/description/banner.jpg'],
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'bootstrap': True,  # Better compatibility with Odoo 18
    'external_dependencies': {
        'python': [],
    },
    'cloc_exclude': [
        'static/**/*',  # Exclude static files from line counting
    ],
    'support': 'https://github.com/ryuedgy-th/hr_custody/issues',
    'live_test_url': False,
    'price': 0.0,
    'currency': 'USD',
    
    # Odoo 18 specific metadata with hooks
    'post_init_hook': 'hooks._post_init_hook',
    'uninstall_hook': 'hooks._uninstall_hook', 
    'pre_init_hook': 'hooks._pre_init_hook',
}
