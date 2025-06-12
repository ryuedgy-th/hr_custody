{
    'name': 'Advanced HR Custody Management',
    'version': '18.0.1.2.0',  # 🔄 RESTORED: Pre-refactor stable version
    'category': 'Human Resources',
    'summary': """Complete HR custody management with professional photo documentation""",
    'description': """
        🚀 Advanced HR Custody Management - Odoo 18.0 (Pre-Refactor Stable)

        A comprehensive solution for managing company assets and property custody with 
        advanced photo documentation, approval workflows, and professional UI/UX.

        ✨ KEY FEATURES (WORKING STABLE VERSION):
        • Complete Photo Management System with professional galleries
        • Smart photo type assignment (handover/return with 7 categories)
        • Professional UI/UX with working image URLs (raw_value fix applied)
        • Multi-level approval workflow system
        • Real-time photo upload and gallery display
        • Mobile-responsive design

        📸 PHOTO MANAGEMENT:
        • Professional photo galleries with thumbnails and badges
        • Photo categorization: handover_overall, handover_detail, handover_serial
        • Return photos: return_overall, return_detail, return_damage, maintenance
        • Quality scoring and analytics
        • Side-by-side photo comparison
        • Manual photo type assignment buttons

        🔧 TECHNICAL STATUS:
        • Odoo 18.0 compatibility verified
        • URL comma issue fixed (using raw_value)
        • XML syntax errors resolved
        • All photo features working correctly
        • No module loading errors

        This is the stable version before modular refactoring, containing the complete
        working photo management system in a single, well-tested codebase.
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

        # Core models and views (working stable version)
        'views/hr_custody_views_complete.xml',          # Main monolithic view file (pre-refactor)
        'views/custody_property_views.xml',
        'views/property_category_views.xml',
        'views/hr_employee_views.xml',
        
        # Reports
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
