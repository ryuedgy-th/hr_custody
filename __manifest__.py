{
    'name': 'Simple HR Custody Management',
    'version': '18.0.1.0.0',
    'category': 'Human Resources',
    'summary': """Simple and clean custody management system""",
    'description': """
        🎯 Simple HR Custody Management - Odoo 18.0

        A clean and simple solution for managing company assets and property custody.

        ✨ KEY FEATURES:
        • 📋 Basic Custody Request Management
        • ✅ Multi-Level Approval System
        • 📸 Simple Photo Upload
        • 📅 Return Date Tracking
        • ⚠️ Overdue Detection
        • 🔍 Smart Search & Filters

        🎯 WORKFLOW:
        • Request → Approval → Usage → Return
        • Photo documentation during handover/return
        • Automatic overdue tracking
        • Email notifications

        Clean, simple, and effective custody management.
    """,
    'author': 'ryuedgy-th',
    'website': "https://github.com/ryuedgy-th/hr_custody",
    'depends': ['hr', 'mail', 'base'],
    
    # 📁 MINIMAL DATA FILES - ONLY ESSENTIAL
    'data': [
        # 🔐 Security & Access Control
        'security/custody_security.xml',
        'security/ir.model.access.csv',

        # 📊 Core Data & Sequences
        'data/custody_sequence_data.xml',

        # 🧙‍♂️ Only Essential Wizard
        'wizard/property_return_reason_views.xml',

        # 📋 HR CUSTODY VIEWS (Core Only)
        'views/hr_custody/hr_custody_views_basic.xml',     # Core form & list views
        'views/hr_custody/hr_custody_views_photo.xml',     # Simple photo management
        'views/hr_custody/hr_custody_views_search.xml',    # Search & filters
        'views/hr_custody/hr_custody_views_actions.xml',   # Actions & menus
        
        # 🏢 Property Management
        'views/custody_property_views.xml',
        'views/property_category_views.xml',
        
        # 👤 Employee Integration
        'views/hr_employee_views.xml',
    ],
    
    # ⚙️ Configuration
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 85,
}