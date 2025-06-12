def migrate(cr, version):
    """
    Migration script for fixing Phase 4: Update foreign key constraint to SET NULL
    """
    # Check if category_id column exists
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='custody_property' AND column_name='category_id'
    """)
    
    if not cr.fetchone():
        print("⚠️ category_id column not found, skipping constraint fix")
        return
    
    # Check current foreign key constraints on category_id
    cr.execute("""
        SELECT tc.constraint_name, rc.delete_rule
        FROM information_schema.table_constraints tc
        JOIN information_schema.constraint_column_usage ccu 
        ON tc.constraint_name = ccu.constraint_name
        JOIN information_schema.referential_constraints rc
        ON tc.constraint_name = rc.constraint_name
        WHERE tc.table_name = 'custody_property' 
        AND ccu.column_name = 'category_id'
        AND tc.constraint_type = 'FOREIGN KEY'
    """)
    
    constraint_result = cr.fetchone()
    if constraint_result:
        constraint_name, delete_rule = constraint_result
        
        if delete_rule != 'SET NULL':
            # Drop the existing constraint and recreate with SET NULL
            cr.execute(f"""
                ALTER TABLE custody_property 
                DROP CONSTRAINT {constraint_name}
            """)
            
            cr.execute("""
                ALTER TABLE custody_property 
                ADD CONSTRAINT custody_property_category_id_fkey 
                FOREIGN KEY (category_id) REFERENCES property_category(id) ON DELETE SET NULL
            """)
            
            print(f"✅ Updated constraint {constraint_name} from {delete_rule} to SET NULL")
        else:
            print(f"✅ Constraint {constraint_name} already has SET NULL rule")
    else:
        # Check if our desired constraint already exists
        cr.execute("""
            SELECT constraint_name 
            FROM information_schema.table_constraints 
            WHERE table_name = 'custody_property' 
            AND constraint_name = 'custody_property_category_id_fkey'
            AND constraint_type = 'FOREIGN KEY'
        """)
        
        if not cr.fetchone():
            # No constraint exists, create one
            cr.execute("""
                ALTER TABLE custody_property 
                ADD CONSTRAINT custody_property_category_id_fkey 
                FOREIGN KEY (category_id) REFERENCES property_category(id) ON DELETE SET NULL
            """)
            print("✅ Added foreign key constraint with SET NULL")
        else:
            print("✅ Desired constraint already exists")
    
    print("✅ Phase 4 Migration Fix completed: Foreign key constraint verified")
