.. image:: https://img.shields.io/badge/license-LGPL--3-green.svg
    :target: https://www.gnu.org/licenses/lgpl-3.0-standalone.html
    :alt: License: LGPL-3

.. image:: https://img.shields.io/badge/version-18.0.1.0.0-blue.svg
    :alt: Version: 18.0.1.0.0

.. image:: https://img.shields.io/badge/enhanced-version-orange.svg
    :alt: Enhanced Version


Enhanced HR Custody Management
==============================

**Professional Asset & Equipment Custody Management System for Odoo 18**

An enhanced and security-hardened version of the OpenHRMS Custody module, featuring role-based approval workflows, advanced security controls, and streamlined user experience. Perfect for organizations requiring professional asset management with robust approval processes.

🔗 **Based on**: `OpenHRMS hr_custody module <https://github.com/CybroOdoo/OpenHRMS/tree/17.0/hr_custody>`_

🚀 **Key Enhancements**
-----------------------

**Security & Compliance**
* **Role-Based Approval System** - Three-tier permission structure (User/Officer/Manager)
* **Enhanced Security Groups** - Proper separation of concerns and access controls
* **Asset Management Category** - Dedicated category for custody roles
* **OAuth2 Compatibility** - Resolved authentication conflicts

**User Experience Improvements**
* **Streamlined Interface** - Removed complex custom approver configurations
* **Dynamic Warranty Years** - Auto-calculated dropdown (current year ±5/+15 years)
* **Simplified Approval Workflow** - Clear role-based permissions
* **Clean UI/UX** - Removed unnecessary complexity while maintaining functionality

**Technical Improvements**
* **Odoo 18.0 Compatibility** - Fully compatible with latest Odoo version
* **Code Quality** - PEP8 compliant, proper error handling, optimized queries
* **Performance Optimizations** - Reduced N+1 queries, efficient database operations
* **Translation Ready** - Proper _() wrappers for internationalization

📋 **Core Features**
-------------------

**Property & Asset Management**
* Complete property lifecycle management
* Categories, tags, and detailed property information
* Warranty tracking with intelligent year selection
* Maintenance history and status tracking
* Image documentation with batch upload capabilities

**Custody Request Workflow**
* Employee self-service custody requests
* Role-based approval system (Officer/Manager levels)
* Flexible return types (fixed date, flexible, term-end)
* Comprehensive status tracking
* Email notifications and reminders

**Advanced Image Management**
* Multiple image upload with wizard
* Before/after condition comparison
* Fullscreen image viewing with zoom
* Batch image management and deletion
* Image categorization (checkout/return)

**Reporting & Analytics**
* Comprehensive custody reports
* Property utilization tracking
* Overdue item monitoring
* Maintenance scheduling
* User activity reports

👥 **Role-Based Access Control**
-------------------------------

**Custody User** (View-Only)
  * View own custody records
  * Check borrowed items and due dates
  * Read-only access to ensure data integrity

**Custody Officer** (Management)
  * All User permissions
  * Approve/reject custody requests
  * Manage properties and categories
  * Cannot delete critical records

**Custody Manager** (Full Access)
  * All Officer permissions
  * Delete records and complete administration
  * Access to all system settings
  * Full property lifecycle management

💼 **Enterprise Features**
-------------------------

* **Multi-company Support** - Proper company-wise data separation
* **Advanced Security** - Role-based access with inheritance
* **Scalable Architecture** - Optimized for large organizations
* **Integration Ready** - Compatible with other Odoo modules
* **Audit Trail** - Complete activity tracking and logging

📦 **Installation & Setup**
--------------------------

**Requirements**
* Odoo 18.0+
* Python 3.8+
* Dependencies: hr, mail, base

**Quick Installation**
1. Download and extract the module to your addons directory
2. Update the app list in Odoo
3. Install "Enhanced HR Custody Management"
4. Assign users to appropriate custody roles
5. Configure properties and begin managing assets

**Post-Installation Configuration**
* Assign users to Custody User/Officer/Manager roles
* Create property categories and items
* Configure email notifications (optional)
* Set up maintenance schedules (optional)

🔧 **Technical Specifications**
------------------------------

* **Framework**: Odoo 18.0
* **License**: LGPL-3 (Open Source)
* **Language**: Python 3.8+
* **Database**: PostgreSQL
* **Frontend**: Odoo Web Framework
* **Security**: Role-based access control

💰 **Commercial Support & Services**
-----------------------------------

**Available Services**
* Custom implementation and configuration
* User training and documentation
* Technical support and maintenance
* Custom feature development
* Integration with existing systems

**Pricing Options**
* Implementation Service: $1,000 - $3,000 USD
* Annual Support: $500 - $1,500 USD
* Custom Development: Contact for quote

📞 **Contact for Commercial Services**
* **Email**: Contact for commercial inquiries
* **Implementation**: Professional setup and configuration
* **Training**: User and administrator training available
* **Support**: Ongoing technical support options

⚖️ **License & Legal**
---------------------

This module is licensed under LGPL-3 and is an enhanced version of the original OpenHRMS hr_custody module. 

**Compliance Notes**
* Source code modifications are available upon request
* Original attribution to Cybrosys Techno Solutions maintained
* Enhanced version developed independently
* Commercial use permitted under LGPL-3 terms

**Original Credits**
* **Base Module**: Cybrosys Techno Solutions
* **Original Authors**: Mily Shajan (V15), Aiswarya M (V16), Janish Babu EK (V17)
* **Enhancement**: Independent development for Odoo 18.0

🔄 **Version History**
---------------------

**18.0.1.0.0** (Current - Enhanced Version)
* Complete Odoo 18.0 compatibility
* Role-based approval system implementation
* Security enhancements and OAuth2 fixes
* UI/UX improvements and code optimization
* Dynamic warranty year selection
* Streamlined configuration process

🐛 **Support & Bug Reports**
---------------------------

For technical issues or feature requests:
* Check existing documentation
* Review configuration settings
* Contact support for commercial installations

**Note**: This is an independently enhanced version. For the original OpenHRMS module support, please contact Cybrosys Techno Solutions.

---

*This enhanced version provides enterprise-grade asset management capabilities while maintaining the open-source flexibility of the original OpenHRMS module.*