{
    'name': 'Advanced HR Custody Management',
    'version': '18.0.2.0.2',  # 🚨 HOTFIX: Fixed asset file references
    'category': 'Human Resources',
    'summary': """Modern enterprise-grade custody management with modular architecture and photo documentation""",
    'description': """
        🚀 Advanced HR Custody Management - Odoo 18.0

        A comprehensive solution for managing company assets and property custody with 
        advanced approval workflows, photo documentation, real-time tracking, and modular architecture.

        ✨ KEY FEATURES:
        • 📸 Complete Photo Management System (inspired by hr_expense)
        • Smart Workflow Management with unified interface
        • Hierarchical Property Categories with inheritance
        • Advanced Multi-Level Approval System
        • Comprehensive Tracking with overdue detection
        • Modern responsive UX with smart filters
        • Modular XML architecture for better maintainability

        📁 IMPROVED ARCHITECTURE:
        • Modular file structure for better code organization
        • Separated concerns (basic forms, photos, search, actions)
        • Easier maintenance and debugging
        • Better team collaboration with reduced merge conflicts
        • Improved performance with focused file loading

        📸 PHOTO MANAGEMENT SYSTEM:
        • 📸 Handover Photos - Document initial condition
        • 📦 Return Photos - Document final condition  
        • 🔍 Photo Comparison - Side-by-side view
        • 📊 Quality Analysis - Automatic quality scoring
        • 🏷️ Photo Categorization - By type and purpose
        • 🎨 Gallery View - Beautiful photo browsing

        🎯 SMART FILTERS & WORKFLOW:
        • 🔔 Waiting My Approval (priority view)
        • 📋 My Requests
        • ✅ Approved by Me  
        • ⚠️ Overdue Items
        • 🕐 Due This Week
        • 📸 Photo Status filters

        Based on the original Open HRMS Custody module by Cybrosys Techno Solutions,
        extensively redesigned for modern enterprise requirements with modular architecture.
    """,
    'author': 'Enhanced by ryuedgy-th',
    'company': 'Based on Cybrosys Techno Solutions',
    'maintainer': 'ryuedgy-th',
    'website': "https://github.com/ryuedgy-th/hr_custody",
    'depends': ['hr', 'mail', 'base'],
    
    # 📁 MODULAR DATA FILES - Fixed File Paths
    'data': [
        # 🔐 Security & Access Control
        'security/custody_security.xml',
        'security/ir.model.access.csv',

        # 📊 Core Data & Sequences
        'data/custody_sequence_data.xml',
        'data/ir_cron_data.xml',
        'data/mail_custody_notification_data.xml',

        # 🧙‍♂️ Wizards (must be loaded before views that reference them)
        'wizard/property_return_reason_views.xml',
        'wizard/property_return_date_views.xml',
        'views/custody_photo_wizard_views.xml',

        # 📋 HR CUSTODY VIEWS (Modular Structure)
        'views/hr_custody/hr_custody_views_basic.xml',     # Core form & list views
        'views/hr_custody/hr_custody_views_photo.xml',     # Photo management system
        'views/hr_custody/hr_custody_views_search.xml',    # Search & filters
        'views/hr_custody/hr_custody_views_actions.xml',   # Actions & menus
        
        # 🏢 Property Management - FIXED PATHS
        'views/custody_property_views.xml',
        'views/property_category_views.xml',
        
        # 📎 Attachment & Photo Management - FIXED PATHS
        'views/ir_attachment_custody_views.xml',
        
        # 👤 Employee Integration
        'views/hr_employee_views.xml',
        
        # 📊 Reports & Analytics
        'reports/report_custody_views.xml',
    ],
    
    # 🎨 Assets (CSS/JS) - FIXED ASSET PATHS
    'assets': {
        'web.assets_backend': [
            'hr_custody/static/src/css/custody_image_upload.css',
            'hr_custody/static/src/js/custody_image_upload.js',
        ],
    },
    
    # 📦 Demo Data
    'demo': ['data/demo_data.xml'],
    
    # 🖼️ Images & Branding
    'images': ['static/description/banner.jpg'],
    
    # ⚙️ Configuration
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 85,
    
    # 🔧 Dependencies
    'external_dependencies': {
        'python': [],
    },
    
    # 📞 Support & Info
    'support': 'https://github.com/ryuedgy-th/hr_custody/issues',
    'live_test_url': False,
    'price': 0.0,
    'currency': 'USD',
}