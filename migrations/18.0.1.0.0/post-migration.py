def migrate(cr, version):
    """Post-migration script for hr_custody module to Odoo 18."""

    # Update cron job records - remove numbercall field if exists
    cr.execute("""
        SELECT id FROM ir_cron
        WHERE name = 'HR Custody Return Notification'
    """)
    cron_ids = cr.fetchall()

    if cron_ids:
        for cron_id in cron_ids:
            # Ensure cron job is active and properly configured
            cr.execute("""
                UPDATE ir_cron
                SET active = true,
                    interval_number = 1,
                    interval_type = 'days',
                    state = 'code',
                    code = 'model.mail_reminder()'
                WHERE id = %s
            """, (cron_id[0],))

    # Ensure all custody records have proper sequence numbers
    cr.execute("""
        UPDATE hr_custody
        SET name = 'CR' || LPAD(id::text, 4, '0')
        WHERE name IS NULL OR name = ''
    """)

    # Update company_id references to use env.company
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
        )
        WHERE company_id IS NULL
    """)

    # Update custody_property company_id as well
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
        )
        WHERE company_id IS NULL
    """)
