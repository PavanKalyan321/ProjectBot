#!/usr/bin/env python3
"""
Supabase Setup Verification Script
Checks that all Supabase integration files are in place
"""

import os
import sys
from pathlib import Path

# Fix Unicode output on Windows
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def check_file_exists(filepath, description):
    """Check if a file exists and report status"""
    exists = os.path.isfile(filepath)
    status = "✓" if exists else "✗"
    print(f"  {status} {description}: {filepath}")
    return exists

def check_directory_exists(dirpath, description):
    """Check if a directory exists and report status"""
    exists = os.path.isdir(dirpath)
    status = "✓" if exists else "✗"
    print(f"  {status} {description}: {dirpath}")
    return exists

def verify_env_file():
    """Verify .env file has required credentials"""
    print("\n" + "="*70)
    print("CHECKING .ENV FILE")
    print("="*70)

    if not os.path.isfile(".env"):
        print("  ✗ .env file not found!")
        return False

    print("  ✓ .env file exists")

    required_vars = [
        "DB_HOST",
        "DB_PORT",
        "DB_NAME",
        "DB_USER",
        "DB_PASSWORD",
        "DB_SSL_MODE",
        "SUPABASE_URL",
        "SUPABASE_API_KEY"
    ]

    env_content = open(".env").read()
    all_present = True

    for var in required_vars:
        if f"{var}=" in env_content:
            print(f"  ✓ {var} is set")
        else:
            print(f"  ✗ {var} is MISSING")
            all_present = False

    return all_present

def verify_config_file():
    """Verify config.py is updated for Supabase"""
    print("\n" + "="*70)
    print("CHECKING CONFIG FILE")
    print("="*70)

    config_file = "backend/database/config.py"

    if not os.path.isfile(config_file):
        print(f"  ✗ {config_file} not found!")
        return False

    content = open(config_file).read()

    checks = [
        ("from dotenv import load_dotenv", "dotenv import"),
        ("load_dotenv()", "load_dotenv() call"),
        ("zofojiubrykbtmstfhzx.supabase.co", "Supabase host"),
        ("os.getenv(", "Environment variable loading"),
    ]

    all_good = True
    for check_str, description in checks:
        if check_str in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} NOT FOUND")
            all_good = False

    return all_good

def verify_requirements():
    """Verify requirements.txt has needed packages"""
    print("\n" + "="*70)
    print("CHECKING REQUIREMENTS.TXT")
    print("="*70)

    if not os.path.isfile("requirements.txt"):
        print("  ✗ requirements.txt not found!")
        return False

    content = open("requirements.txt").read()

    required_packages = [
        ("python-dotenv", "python-dotenv"),
        ("sqlalchemy", "sqlalchemy"),
        ("psycopg2-binary", "psycopg2-binary"),
    ]

    all_good = True
    for package_name, description in required_packages:
        if package_name in content:
            print(f"  ✓ {description} is in requirements.txt")
        else:
            print(f"  ✗ {description} is MISSING from requirements.txt")
            all_good = False

    return all_good

def verify_gitignore():
    """Verify .gitignore has .env"""
    print("\n" + "="*70)
    print("CHECKING .GITIGNORE")
    print("="*70)

    if not os.path.isfile(".gitignore"):
        print("  ✗ .gitignore not found!")
        return False

    content = open(".gitignore").read()

    if ".env" in content:
        print("  ✓ .env is in .gitignore (credentials will be protected)")
        return True
    else:
        print("  ✗ .env is NOT in .gitignore (SECURITY RISK!)")
        return False

def verify_schema_file():
    """Verify schema.sql exists"""
    print("\n" + "="*70)
    print("CHECKING SCHEMA FILE")
    print("="*70)

    schema_file = "backend/database/schema.sql"
    if not os.path.isfile(schema_file):
        print(f"  ✗ {schema_file} not found!")
        return False

    print(f"  ✓ {schema_file} exists")

    content = open(schema_file).read()

    # Check for key schema elements
    checks = [
        ("CREATE TABLE bot_vm_registration", "bot_vm_registration table"),
        ("CREATE TABLE crash_game_rounds", "crash_game_rounds table"),
        ("CREATE TABLE analytics_round_multipliers", "analytics_round_multipliers table"),
        ("CREATE TABLE analytics_round_signals", "analytics_round_signals table"),
        ("CREATE TABLE analytics_round_outcomes", "analytics_round_outcomes table"),
        ("CREATE TABLE session_logs", "session_logs table"),
        ("CREATE TABLE error_logs", "error_logs table"),
        ("CREATE TABLE ocr_validation_logs", "ocr_validation_logs table"),
        ("CREATE TYPE game_type", "ENUM types"),
        ("CREATE INDEX", "Index definitions"),
    ]

    all_good = True
    for check_str, description in checks:
        if check_str in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} NOT FOUND")
            all_good = False

    return all_good

def verify_models_file():
    """Verify models.py exists and has SQLAlchemy models"""
    print("\n" + "="*70)
    print("CHECKING MODELS FILE")
    print("="*70)

    models_file = "backend/database/models.py"
    if not os.path.isfile(models_file):
        print(f"  ✗ {models_file} not found!")
        return False

    print(f"  ✓ {models_file} exists")

    content = open(models_file).read()

    # Check for key model classes
    checks = [
        ("class BotVMRegistration", "BotVMRegistration model"),
        ("class CrashGameRound", "CrashGameRound model"),
        ("class AnalyticsRoundMultiplier", "AnalyticsRoundMultiplier model"),
        ("Base = declarative_base", "SQLAlchemy Base"),
    ]

    all_good = True
    for check_str, description in checks:
        if check_str in content:
            print(f"  ✓ {description}")
        else:
            print(f"  ✗ {description} NOT FOUND")
            all_good = False

    return all_good

def main():
    """Main verification function"""
    print("\n" + "="*70)
    print("SUPABASE SETUP VERIFICATION")
    print("="*70)

    checks = [
        ("Environment File", verify_env_file),
        ("Config File", verify_config_file),
        ("Requirements", verify_requirements),
        ("Gitignore", verify_gitignore),
        ("Schema File", verify_schema_file),
        ("Models File", verify_models_file),
    ]

    results = {}
    for check_name, check_func in checks:
        results[check_name] = check_func()

    # Summary
    print("\n" + "="*70)
    print("SUMMARY")
    print("="*70)

    all_passed = True
    for check_name, result in results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {check_name}")
        if not result:
            all_passed = False

    print("\n" + "="*70)
    if all_passed:
        print("✓ ALL CHECKS PASSED!")
        print("="*70)
        print("\nNext steps:")
        print("1. Create schema in Supabase SQL Editor (copy backend/database/schema.sql)")
        print("2. Install dependencies: pip install -r requirements.txt")
        print("3. Test connection: python migrate_to_supabase.py")
        print("4. Start using bot: python backend/bot.py")
        print("="*70 + "\n")
        return 0
    else:
        print("✗ SOME CHECKS FAILED")
        print("="*70)
        print("\nPlease review the errors above and fix them.")
        print("See SUPABASE_SETUP_GUIDE.md for help.")
        print("="*70 + "\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())
