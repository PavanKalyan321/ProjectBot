#!/usr/bin/env python3
"""
Supabase Migration Script
Migrates database schema from DigitalOcean to Supabase
"""

import sys
import os
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from database.connection import DatabaseConnection
from database.models import Base
from sqlalchemy import text, inspect

def test_connection():
    """Test database connection to Supabase"""
    print("\n" + "="*70)
    print("TESTING SUPABASE CONNECTION")
    print("="*70)

    try:
        DatabaseConnection.initialize()
        with DatabaseConnection.get_session() as session:
            result = session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✓ Connected to Supabase")
            print(f"✓ PostgreSQL Version: {version}")
        return True
    except Exception as e:
        print(f"✗ Connection failed: {str(e)}")
        return False

def create_schema():
    """Create all tables in Supabase"""
    print("\n" + "="*70)
    print("CREATING SCHEMA")
    print("="*70)

    try:
        DatabaseConnection.initialize()

        # Create all tables
        print("Creating tables...")
        Base.metadata.create_all(DatabaseConnection._engine)
        print("✓ Schema created successfully")

        # List created tables
        inspector = inspect(DatabaseConnection._engine)
        tables = inspector.get_table_names()

        print(f"\n✓ Created {len(tables)} tables:")
        for table in sorted(tables):
            columns = inspector.get_columns(table)
            print(f"  - {table} ({len(columns)} columns)")

        return True
    except Exception as e:
        print(f"✗ Schema creation failed: {str(e)}")
        return False

def verify_schema():
    """Verify schema was created correctly"""
    print("\n" + "="*70)
    print("VERIFYING SCHEMA")
    print("="*70)

    required_tables = [
        'bot_vm_registration',
        'game_platform_config',
        'crash_game_rounds',
        'analytics_round_multipliers',
        'analytics_round_signals',
        'analytics_round_outcomes',
        'session_logs',
        'error_logs',
        'ocr_validation_logs',
    ]

    try:
        inspector = inspect(DatabaseConnection._engine)
        existing_tables = set(inspector.get_table_names())

        print(f"Expected {len(required_tables)} tables...")

        all_present = True
        for table in required_tables:
            if table in existing_tables:
                columns = inspector.get_columns(table)
                print(f"✓ {table} ({len(columns)} columns)")
            else:
                print(f"✗ {table} MISSING")
                all_present = False

        if all_present:
            print(f"\n✓ All {len(required_tables)} tables verified!")
            return True
        else:
            print("\n✗ Some tables are missing")
            return False

    except Exception as e:
        print(f"✗ Verification failed: {str(e)}")
        return False

def main():
    """Main migration function"""
    print("\n" + "="*70)
    print("SUPABASE MIGRATION SCRIPT")
    print("="*70)

    # Step 1: Test connection
    if not test_connection():
        print("\n✗ Migration aborted: Cannot connect to Supabase")
        return False

    # Step 2: Create schema
    if not create_schema():
        print("\n✗ Migration aborted: Schema creation failed")
        return False

    # Step 3: Verify schema
    if not verify_schema():
        print("\n✗ Migration aborted: Schema verification failed")
        return False

    print("\n" + "="*70)
    print("✓ MIGRATION COMPLETED SUCCESSFULLY!")
    print("="*70)
    print("\nNext steps:")
    print("1. Your Supabase database is ready")
    print("2. Update your application configuration if needed")
    print("3. Start using the database logger in your bot")
    print("\nYou can now run:")
    print("  - python run_dashboard.py (for the dashboard)")
    print("  - python backend/bot.py (for the bot)")
    print("="*70 + "\n")

    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
