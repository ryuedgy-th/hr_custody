def migrate(cr, version):
    """
    Migration script for fixing Phase 4: Update foreign key constraint to SET NULL
    """
    # Check if category_id column exists and has wrong constraint
    cr.execute("""
        SELECT tc.constraint_name 
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu 
        ON tc.constraint_name = ccu.constraint_name
        WHERE tc.table_name = 'custody_property' 
        AND ccu.column_name = 'category_id'
        AND tc.constraint_type = 'FOREIGN KEY'
    """)
    
    constraint_result = cr.fetchone()
    if constraint_result:
        constraint_name = constraint_result[0]
        
        # Drop the existing constraint and recreate with SET NULL
        cr.execute(f"""
            ALTER TABLE custody_property 
            DROP CONSTRAINT IF EXISTS {constraint_name}
        """)
        
        cr.execute("""
            ALTER TABLE custody_property 
            ADD CONSTRAINT custody_property_category_id_fkey 
            FOREIGN KEY (category_id) REFERENCES property_category(id) ON DELETE SET NULL
        """)
        
        print("✅ Fixed foreign key constraint to SET NULL")
    else:
        # If no constraint found, just add the correct one
        cr.execute("""
            ALTER TABLE custody_property 
            ADD CONSTRAINT custody_property_category_id_fkey 
            FOREIGN KEY (category_id) REFERENCES property_category(id) ON DELETE SET NULL
        """)
        print("✅ Added foreign key constraint with SET NULL")
    
    print("✅ Phase 4 Migration Fix completed: Foreign key constraint updated")
