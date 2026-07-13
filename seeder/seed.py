"""
TMU MDM Seeder Service
Waits for PostgreSQL to be ready, then applies DDL and seed scripts in order.
Idempotent: safe to re-run (DDL uses CREATE TABLE IF NOT EXISTS, seed uses ON CONFLICT DO NOTHING).
"""
import os
import sys
import time
import glob
import psycopg2

DB_HOST = os.getenv("POSTGRES_HOST", "postgres")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "tmu_mdm")
DB_USER = os.getenv("POSTGRES_USER", "tmu_admin")
DB_PASSWORD = os.getenv("POSTGRES_PASSWORD", "tmu_password")
SQL_DIR = os.getenv("SQL_DIR", "/sql")
MAX_RETRIES = int(os.getenv("MAX_RETRIES", "30"))
RETRY_DELAY = int(os.getenv("RETRY_DELAY_SECONDS", "2"))


def wait_for_postgres():
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            conn = psycopg2.connect(
                host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
                user=DB_USER, password=DB_PASSWORD,
            )
            conn.close()
            print(f"[seeder] PostgreSQL is ready (attempt {attempt}).")
            return
        except psycopg2.OperationalError as e:
            print(f"[seeder] PostgreSQL not ready yet (attempt {attempt}/{MAX_RETRIES}): {e}")
            time.sleep(RETRY_DELAY)
    print("[seeder] ERROR: PostgreSQL did not become ready in time.")
    sys.exit(1)


def run_sql_file(conn, filepath):
    print(f"[seeder] Applying {filepath} ...")
    with open(filepath, "r", encoding="utf-8") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"[seeder] Done: {filepath}")


def main():
    wait_for_postgres()
    conn = psycopg2.connect(
        host=DB_HOST, port=DB_PORT, dbname=DB_NAME,
        user=DB_USER, password=DB_PASSWORD,
    )
    try:
        sql_files = sorted(glob.glob(os.path.join(SQL_DIR, "*.sql")))
        if not sql_files:
            print(f"[seeder] No SQL files found in {SQL_DIR}.")
            sys.exit(1)
        for filepath in sql_files:
            run_sql_file(conn, filepath)
        print("[seeder] All scripts applied successfully. MDM schema is ready.")
    except Exception as e:
        conn.rollback()
        print(f"[seeder] ERROR while applying scripts: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
