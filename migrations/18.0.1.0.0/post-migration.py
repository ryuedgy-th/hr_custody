# migrations/18.0.1.0.0/post-migration.py

def migrate(cr, version):
    """Post-migration script for hr_custody module to Odoo 18."""

    # 1. Update field references that changed in Odoo 18
    # Remove deprecated fields and update field types
    try:
        # Remove deprecated image fields (image_medium, image_small)
        cr.execute("""
            ALTER TABLE custody_property
            DROP COLUMN IF EXISTS image_medium;
        """)
        cr.execute("""
            ALTER TABLE custody_property
            DROP COLUMN IF EXISTS image_small;
        """)
    except Exception:
        pass  # Fields might not exist

    # 2. Update tracking field references
    # Replace track_visibility with tracking
    cr.execute("""
        UPDATE ir_model_fields
        SET tracking = TRUE
        WHERE model = 'hr.custody'
        AND name IN ('date_request', 'purpose', 'return_date', 'renew_date', 'state')
    """)

    # 3. Update view references
    # Update tree views to list views
    cr.execute("""
        UPDATE ir_ui_view
        SET arch_db = REPLACE(arch_db, '<tree', '<list')
        WHERE model = 'hr.custody'
        AND arch_db LIKE '%<tree%'
    """)

    cr.execute("""
        UPDATE ir_ui_view
        SET arch_db = REPLACE(arch_db, '</tree>', '</list>')
        WHERE model = 'hr.custody'
        AND arch_db LIKE '%</tree>%'
    """)

    # Do the same for custody.property
    cr.execute("""
        UPDATE ir_ui_view
        SET arch_db = REPLACE(arch_db, '<tree', '<list')
        WHERE model = 'custody.property'
        AND arch_db LIKE '%<tree%'
    """)

    cr.execute("""
        UPDATE ir_ui_view
        SET arch_db = REPLACE(arch_db, '</tree>', '</list>')
        WHERE model = 'custody.property'
        AND arch_db LIKE '%</tree>%'
    """)

    # 4. Update cron job records for Odoo 18
    cr.execute("""
        SELECT id FROM ir_cron
        WHERE name = 'HR Custody Return Notification'
    """)
    cron_ids = cr.fetchall()

    if cron_ids:
        for cron_id in cron_ids:
            # Update cron job configuration for Odoo 18
            cr.execute("""
                UPDATE ir_cron
                SET active = true,
                    interval_number = 1,
                    interval_type = 'days',
                    state = 'code',
                    code = 'model.mail_reminder()'
                WHERE id = %s
            """, (cron_id[0],))

    # 5. Update sequence generation
    # Ensure all custody records have proper sequence numbers
    cr.execute("""
        UPDATE hr_custody
        SET name = 'CR' || LPAD(id::text, 4, '0')
        WHERE name IS NULL OR name = '' OR name = 'New'
    """)

    # 6. Update company references to use env.company instead of env.user.company_id
    cr.execute("""
        UPDATE hr_custody
        SET company_id = (
            SELECT company_id
            FROM res_users
            WHERE id = (
                SELECT create_uid
                FROM hr_custody AS hc
                WHERE hc.id = hr_custody.id
            )
            LIMIT 1
        )
        WHERE company_id IS NULL
    """)

    cr.execute("""
        UPDATE custody_property
        SET company_id = (
            SELECT company_id
            FROM res_users
            WHERE id = (
                SELECT create_uid
                FROM custody_property AS cp
                WHERE cp.id = custody_property.id
            )
            LIMIT 1
        )
        WHERE company_id IS NULL
    """)

    # 7. Update mail template references
    cr.execute("""
        UPDATE mail_template
        SET email_from = '{{object.company_id.email or \'\'}}'
        WHERE model_id IN (
            SELECT id FROM ir_model WHERE model = 'hr.custody'
        )
    """)

    # 8. Update action references for Odoo 18
    # Update view_mode from tree to list
    cr.execute("""
        UPDATE ir_actions_act_window
        SET view_mode = REPLACE(view_mode, 'tree', 'list')
        WHERE res_model IN ('hr.custody', 'custody.property', 'report.custody')
    """)

    # 9. Clean up old field references in views
    # Remove references to deprecated fields
    cr.execute("""
        UPDATE ir_ui_view
        SET arch_db = REPLACE(
            REPLACE(arch_db, 'track_visibility="always"', 'tracking="True"'),
            'track_visibility=''always''', 'tracking="True"'
        )
        WHERE model IN ('hr.custody', 'custody.property')
    """)

    # 10. Update invisible conditions for Odoo 18 syntax
    cr.execute("""
        UPDATE ir_ui_view
        SET arch_db = REPLACE(
            REPLACE(
                REPLACE(arch_db, 'invisible=" ', 'invisible="'),
                'invisible=\' ', 'invisible="'),
            ' "', '"'
        )
        WHERE model IN ('hr.custody', 'custody.property')
    """)

    # 11. Ensure proper field types for Odoo 18
    # Update boolean field defaults
    cr.execute("""
        UPDATE hr_custody
        SET is_renew_return_date = FALSE
        WHERE is_renew_return_date IS NULL
    """)

    cr.execute("""
        UPDATE hr_custody
        SET is_renew_reject = FALSE
        WHERE is_renew_reject IS NULL
    """)

    cr.execute("""
        UPDATE hr_custody
        SET is_mail_send = FALSE
        WHERE is_mail_send IS NULL
    """)

    # 12. Update menu sequence and structure
    cr.execute("""
        UPDATE ir_ui_menu
        SET sequence = 20
        WHERE name = 'Custody'
        AND parent_id IS NULL
    """)

    # 13. Clean up old security records
    try:
        # Remove duplicate access records if any
        cr.execute("""
            DELETE FROM ir_model_access
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM ir_model_access
                GROUP BY name, model_id, group_id
            )
        """)
    except Exception:
        pass

    # 14. Update report configurations
    cr.execute("""
        UPDATE ir_actions_act_window
        SET help = '<p class="o_view_nocontent_smiling_face">Create your first custody request!</p><p>Track company assets and equipment assigned to employees.</p>'
        WHERE res_model = 'hr.custody'
    """)

    # 15. Ensure proper state values
    cr.execute("""
        UPDATE hr_custody
        SET state = 'draft'
        WHERE state IS NULL OR state = ''
    """)

    # 16. Update computed field dependencies
    # This will be handled by the ORM when the module loads

    # 17. Log migration completion
    cr.execute("""
        INSERT INTO ir_logging (name, level, message, path, line, func, create_date, create_uid)
        VALUES ('hr_custody.migration', 'INFO', 'Successfully migrated hr_custody to Odoo 18.0',
                'migrations/18.0.1.0.0/post-migration.py', 0, 'migrate', NOW(), 1)
    """)

    print("HR Custody module successfully migrated to Odoo 18.0")
