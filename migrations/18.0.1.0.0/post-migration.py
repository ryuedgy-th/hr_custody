# migrations/18.0.1.0.1/pre-migration.py

def migrate(cr, version):
    """Pre-migration script to add new fields to hr_custody table"""

    # 1. Add actual_return_date column
    try:
        cr.execute("""
            ALTER TABLE hr_custody
            ADD COLUMN IF NOT EXISTS actual_return_date DATE;
        """)
        print("✅ Added actual_return_date column")
    except Exception as e:
        print(f"❌ Error adding actual_return_date: {e}")

    # 2. Add returned_by_id column
    try:
        cr.execute("""
            ALTER TABLE hr_custody
            ADD COLUMN IF NOT EXISTS returned_by_id INTEGER;
        """)
        print("✅ Added returned_by_id column")
    except Exception as e:
        print(f"❌ Error adding returned_by_id: {e}")

    # 3. Add return_notes column
    try:
        cr.execute("""
            ALTER TABLE hr_custody
            ADD COLUMN IF NOT EXISTS return_notes TEXT;
        """)
        print("✅ Added return_notes column")
    except Exception as e:
        print(f"❌ Error adding return_notes: {e}")

    # 4. Add is_overdue column (computed field, but we need it for SQL queries)
    try:
        cr.execute("""
            ALTER TABLE hr_custody
            ADD COLUMN IF NOT EXISTS is_overdue BOOLEAN DEFAULT FALSE;
        """)
        print("✅ Added is_overdue column")
    except Exception as e:
        print(f"❌ Error adding is_overdue: {e}")

    # 5. Add days_overdue column
    try:
        cr.execute("""
            ALTER TABLE hr_custody
            ADD COLUMN IF NOT EXISTS days_overdue INTEGER DEFAULT 0;
        """)
        print("✅ Added days_overdue column")
    except Exception as e:
        print(f"❌ Error adding days_overdue: {e}")

    # 6. Add return_type column if not exists
    try:
        cr.execute("""
            ALTER TABLE hr_custody
            ADD COLUMN IF NOT EXISTS return_type VARCHAR;
        """)
        # Set default values for existing records
        cr.execute("""
            UPDATE hr_custody
            SET return_type = 'date'
            WHERE return_type IS NULL;
        """)
        print("✅ Added return_type column")
    except Exception as e:
        print(f"❌ Error adding return_type: {e}")

    # 7. Add expected_return_period column
    try:
        cr.execute("""
            ALTER TABLE hr_custody
            ADD COLUMN IF NOT EXISTS expected_return_period VARCHAR;
        """)
        print("✅ Added expected_return_period column")
    except Exception as e:
        print(f"❌ Error adding expected_return_period: {e}")

    # 8. Create foreign key constraints
    try:
        # Add foreign key for returned_by_id
        cr.execute("""
            ALTER TABLE hr_custody
            ADD CONSTRAINT IF NOT EXISTS hr_custody_returned_by_id_fkey
            FOREIGN KEY (returned_by_id) REFERENCES res_users(id);
        """)
        print("✅ Added foreign key constraints")
    except Exception as e:
        print(f"❌ Error adding foreign keys: {e}")

    # 9. Update existing returned records with actual return date
    try:
        cr.execute("""
            UPDATE hr_custody
            SET actual_return_date = CURRENT_DATE
            WHERE state = 'returned' AND actual_return_date IS NULL;
        """)
        print("✅ Updated existing returned records")
    except Exception as e:
        print(f"❌ Error updating existing records: {e}")

    print("🎉 Migration completed successfully!")
