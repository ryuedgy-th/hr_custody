def migrate(cr, version):
    """
    Migration script for Phase 4: Add hierarchical categories and related functionality
    """
    # Create property_category table first if it doesn't exist
    cr.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = 'property_category'
        )
    """)
    
    if not cr.fetchone()[0]:
        cr.execute("""
            CREATE TABLE property_category (
                id SERIAL PRIMARY KEY,
                name VARCHAR NOT NULL,
                complete_name VARCHAR,
                parent_id INTEGER REFERENCES property_category(id) ON DELETE CASCADE,
                parent_path VARCHAR,
                description TEXT,
                image BYTEA,
                active BOOLEAN DEFAULT TRUE,
                color INTEGER,
                sequence INTEGER DEFAULT 10,
                property_count INTEGER DEFAULT 0,
                total_property_count INTEGER DEFAULT 0,
                active_custody_count INTEGER DEFAULT 0,
                responsible_department_id INTEGER REFERENCES hr_department(id) ON DELETE SET NULL,
                create_uid INTEGER REFERENCES res_users(id) ON DELETE SET NULL,
                create_date TIMESTAMP DEFAULT NOW(),
                write_uid INTEGER REFERENCES res_users(id) ON DELETE SET NULL,
                write_date TIMESTAMP DEFAULT NOW()
            )
        """)
        
        # Create indexes
        cr.execute("CREATE INDEX property_category_parent_id_index ON property_category (parent_id)")
        cr.execute("CREATE INDEX property_category_parent_path_index ON property_category (parent_path)")
        cr.execute("CREATE INDEX property_category_complete_name_index ON property_category (complete_name)")
        
        # Create many2many table for category approvers
        cr.execute("""
            CREATE TABLE category_approver_rel (
                category_id INTEGER NOT NULL REFERENCES property_category(id) ON DELETE CASCADE,
                user_id INTEGER NOT NULL REFERENCES res_users(id) ON DELETE CASCADE,
                PRIMARY KEY (category_id, user_id)
            )
        """)
        
        print("✅ Property category tables created")
    
    # Now add category_id column to custody.property (allow NULL initially)
    cr.execute("""
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='custody_property' AND column_name='category_id'
    """)
    
    if not cr.fetchone():
        # Add the category_id column as nullable first
        cr.execute("""
            ALTER TABLE custody_property 
            ADD COLUMN category_id INTEGER REFERENCES property_category(id) ON DELETE SET NULL
        """)
        
        # Create index for better performance
        cr.execute("""
            CREATE INDEX custody_property_category_id_index 
            ON custody_property (category_id)
        """)
        
        print("✅ Added category_id column to custody_property")
    
    print("✅ Phase 4 Migration completed: Hierarchical categories infrastructure created")
