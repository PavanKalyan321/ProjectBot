"""
Test Database Connection Script
Tests DigitalOcean PostgreSQL connection using psycopg2
"""

import sys
import os
from datetime import datetime

print("=" * 80)
print("  DATABASE CONNECTION TEST - PostgreSQL Direct Connection")
print("=" * 80)

# Test 1: Check if psycopg2 is installed
print("\n[STEP 1] Checking psycopg2 installation...")
try:
    import psycopg2
    print("[OK] psycopg2 is installed")
except ImportError:
    print("[ERROR] psycopg2 not installed")
    print("       Install with: pip install psycopg2-binary")
    sys.exit(1)

# Test 2: Get connection details
print("\n[STEP 2] Setting up connection details...")
connection_params = {
    "host": "db-main-do-user-28557476-0.h.db.ondigitalocean.com",
    "port": 25060,
    "database": "defaultdb",
    "user": "pk",
    "password": os.getenv("DB_PASSWORD", "YOUR_PASSWORD_HERE"),
    "sslmode": "require"
}

print(f"[INFO] Host: {connection_params['host']}")
print(f"[INFO] Port: {connection_params['port']}")
print(f"[INFO] Database: {connection_params['database']}")
print(f"[INFO] User: {connection_params['user']}")
print(f"[INFO] SSL Mode: {connection_params['sslmode']}")

# Check if password is set
if connection_params['password'] == "YOUR_PASSWORD_HERE":
    print("\n[ERROR] Password not set!")
    print("       Options:")
    print("       1. Set environment variable: DB_PASSWORD='your_password'")
    print("       2. Edit this script and set password directly")
    print("       3. Use: python -c \"import os; os.environ['DB_PASSWORD']='...'\" then run")
    sys.exit(1)

print("[OK] Connection parameters ready")

# Test 3: Attempt connection
print("\n[STEP 3] Attempting database connection...")
try:
    conn = psycopg2.connect(
        host=connection_params['host'],
        port=connection_params['port'],
        database=connection_params['database'],
        user=connection_params['user'],
        password=connection_params['password'],
        sslmode=connection_params['sslmode'],
        connect_timeout=10
    )
    print("[OK] Connection successful!")

    # Get connection info
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()[0]
    print(f"\n[INFO] PostgreSQL Version:")
    print(f"       {version}")

except psycopg2.OperationalError as e:
    print(f"[ERROR] Connection failed: {e}")
    print("\nCommon causes:")
    print("  1. Wrong password")
    print("  2. Database server not running")
    print("  3. Network/firewall blocking port 25060")
    print("  4. Invalid host address")
    sys.exit(1)

except psycopg2.DatabaseError as e:
    print(f"[ERROR] Database error: {e}")
    sys.exit(1)

except Exception as e:
    print(f"[ERROR] Unexpected error: {e}")
    sys.exit(1)

# Test 4: List tables
print("\n[STEP 4] Querying database tables...")
try:
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;
    """)

    tables = cursor.fetchall()
    if tables:
        print(f"[OK] Found {len(tables)} tables:\n")
        for i, (table_name,) in enumerate(tables, 1):
            print(f"     {i}. {table_name}")
    else:
        print("[WARN] No tables found in public schema")

except Exception as e:
    print(f"[ERROR] Failed to query tables: {e}")
    conn.close()
    sys.exit(1)

# Test 5: Check for data
print("\n[STEP 5] Checking table row counts...")
try:
    table_counts = {}
    for (table_name,) in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cursor.fetchone()[0]
        table_counts[table_name] = count

    print("[OK] Table row counts:\n")
    total_rows = 0
    for table_name in sorted(table_counts.keys()):
        count = table_counts[table_name]
        status = "[OK]" if count > 0 else "[EMPTY]"
        print(f"     {status} {table_name:40} | {count:5} row(s)")
        total_rows += count

    print(f"\n[INFO] Total rows across all tables: {total_rows}")

except Exception as e:
    print(f"[ERROR] Failed to count rows: {e}")

# Test 6: Verify analytics tables exist
print("\n[STEP 6] Verifying analytics tables (for ML training)...")
try:
    analytics_tables = [
        "analytics_round_multipliers",
        "analytics_round_signals",
        "analytics_round_outcomes"
    ]

    for table in analytics_tables:
        if table in table_counts:
            status = "OK" if table_counts[table] > 0 else "EMPTY"
            print(f"     [{status}] {table} - {table_counts[table]} records")
        else:
            print(f"     [MISSING] {table}")

except Exception as e:
    print(f"[ERROR] Failed to verify analytics tables: {e}")

# Test 7: Sample query
print("\n[STEP 7] Running sample query...")
try:
    cursor.execute("""
        SELECT
            COUNT(*) as total_rounds,
            SUM(CASE WHEN round_outcome = 'WIN' THEN 1 ELSE 0 END) as wins,
            ROUND(100.0 * SUM(CASE WHEN round_outcome = 'WIN' THEN 1 ELSE 0 END) /
                  NULLIF(COUNT(*), 0), 2) as win_rate_percent,
            SUM(profit_loss_amount) as total_profit
        FROM crash_game_rounds;
    """)

    result = cursor.fetchone()
    if result and result[0] and result[0] > 0:
        total_rounds, wins, win_rate, total_profit = result
        print(f"[OK] Sample query result:")
        print(f"     Total Rounds: {total_rounds}")
        print(f"     Wins: {wins}")
        print(f"     Win Rate: {win_rate}%")
        print(f"     Total Profit: {total_profit}")
    else:
        print("[EMPTY] No rounds in database (this is ok for fresh setup)")

except Exception as e:
    print(f"[WARN] Sample query failed: {e}")
    print("       (This is ok if crash_game_rounds table doesn't exist yet)")

# Cleanup
print("\n[STEP 8] Closing connection...")
try:
    cursor.close()
    conn.close()
    print("[OK] Connection closed")
except:
    pass

# Final status
print("\n" + "=" * 80)
print("  FINAL STATUS: DATABASE CONNECTION SUCCESSFUL")
print("=" * 80)
print("\nYour database is accessible and working!")
print(f"\nTimestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("\nNext steps:")
print("  1. Connect with DBeaver using same credentials")
print("  2. Start logging data from your bot")
print("  3. Query analytics tables for ML training")
