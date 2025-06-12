"""
HR Custody Module Hooks for Odoo 18
"""

import logging
from odoo import api, SUPERUSER_ID

_logger = logging.getLogger(__name__)


def _pre_init_hook(cr):
    """
    Pre-initialization hook
    Executed before module installation
    """
    _logger.info("HR Custody: Starting pre-initialization...")
    
    # Check if required tables exist to prevent conflicts during upgrade
    cr.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_name = 'hr_custody'
    """)
    
    if cr.fetchone():
        _logger.info("HR Custody: Existing installation detected, preparing for upgrade...")
        # Add any upgrade preparation logic here
    else:
        _logger.info("HR Custody: Fresh installation detected")


def _post_init_hook(cr, registry):
    """
    Post-initialization hook
    Executed after module installation/upgrade
    """
    _logger.info("HR Custody: Starting post-initialization...")
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    try:
        # Create default sequences if they don't exist
        sequence_model = env['ir.sequence']
        existing_sequence = sequence_model.search([('code', '=', 'hr.custody')], limit=1)
        
        if not existing_sequence:
            sequence_model.create({
                'name': 'HR Custody Sequence',
                'code': 'hr.custody',
                'prefix': 'CUST',
                'padding': 5,
                'number_increment': 1,
                'implementation': 'standard',
            })
            _logger.info("HR Custody: Default sequence created")
        
        # Set up default property categories if none exist
        category_model = env['property.category']
        if not category_model.search_count([]):
            default_categories = [
                {'name': 'IT Equipment', 'description': 'Computers, laptops, phones, tablets'},
                {'name': 'Office Furniture', 'description': 'Desks, chairs, cabinets'},
                {'name': 'Vehicles', 'description': 'Company cars, motorcycles, bicycles'},
                {'name': 'Tools & Equipment', 'description': 'Professional tools and equipment'},
                {'name': 'Electronics', 'description': 'Electronic devices and accessories'},
            ]
            
            for category_data in default_categories:
                category_model.create(category_data)
            
            _logger.info("HR Custody: Default property categories created")
        
        # Update existing attachments to have proper custody photo types if needed
        attachment_model = env['ir.attachment']
        untyped_custody_attachments = attachment_model.search([
            ('res_model', '=', 'hr.custody'),
            ('custody_photo_type', '=', False),
            ('mimetype', 'like', 'image%')
        ])
        
        if untyped_custody_attachments:
            # Auto-assign default photo types based on custody state
            for attachment in untyped_custody_attachments:
                if attachment.res_id:
                    custody = env['hr.custody'].browse(attachment.res_id)
                    if custody.exists():
                        default_type = 'handover_overall' if custody.state in ['draft', 'to_approve', 'approved'] else 'return_overall'
                        attachment.custody_photo_type = default_type
            
            _logger.info("HR Custody: Updated %d existing attachments with photo types", len(untyped_custody_attachments))
        
        # Ensure all custody records have proper company_id
        custody_model = env['hr.custody']
        custody_without_company = custody_model.search([('company_id', '=', False)])
        if custody_without_company:
            default_company = env['res.company'].search([], limit=1)
            if default_company:
                custody_without_company.write({'company_id': default_company.id})
                _logger.info("HR Custody: Updated %d records with default company", len(custody_without_company))
        
        _logger.info("HR Custody: Post-initialization completed successfully")
        
    except Exception as e:
        _logger.error("HR Custody: Error during post-initialization: %s", str(e))
        raise


def _uninstall_hook(cr, registry):
    """
    Uninstallation hook
    Executed before module uninstallation
    """
    _logger.info("HR Custody: Starting uninstallation cleanup...")
    
    env = api.Environment(cr, SUPERUSER_ID, {})
    
    try:
        # Clean up custody photo types from attachments
        attachment_model = env['ir.attachment']
        custody_attachments = attachment_model.search([
            ('res_model', '=', 'hr.custody'),
            ('custody_photo_type', '!=', False)
        ])
        
        if custody_attachments:
            custody_attachments.write({'custody_photo_type': False})
            _logger.info("HR Custody: Cleaned up %d attachment photo types", len(custody_attachments))
        
        # Update property status back to available for active custody
        property_model = env['custody.property']
        in_use_properties = property_model.search([('property_status', '=', 'in_use')])
        if in_use_properties:
            in_use_properties.write({'property_status': 'available'})
            _logger.info("HR Custody: Reset %d properties to available status", len(in_use_properties))
        
        _logger.info("HR Custody: Uninstallation cleanup completed")
        
    except Exception as e:
        _logger.error("HR Custody: Error during uninstallation: %s", str(e))
        # Don't raise error during uninstall to avoid blocking the process
