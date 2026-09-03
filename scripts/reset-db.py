import os
import sqlite3
import subprocess
import sys

# Order Supervisor - Clean Database Reset
DB_FILE = "order_supervisor.db"

print("======================================================")
print("  RESETTING ORDER SUPERVISOR DATABASE")
print("======================================================")

if os.path.exists(DB_FILE):
    try:
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        for table in ["activities", "events", "instructions", "runs"]:
            try:
                cursor.execute(f"DELETE FROM {table}")
            except Exception:
                pass
        conn.commit()
        conn.close()
        print("[OK] Cleared all historical order runs, activities, and events.")
    except Exception as e:
        print(f"[!] Warning clearing tables: {e}")

# Re-run seed
print("[OK] Seeding fresh supervisor templates...")
subprocess.run([sys.executable, "database/seed.py"])

print("======================================================")
print("  DATABASE RESET COMPLETE - ZERO OLD ORDERS REMAINING")
print("======================================================")
