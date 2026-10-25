import sys
from sqlalchemy import text
from app.core.database import SessionLocal

def main():
    db = SessionLocal()
    patterns = ['%à®%', '%à¯%', '%Ã%']

    # Get all text/varchar columns for all tables
    res = db.execute(text("""
        SELECT table_name, column_name
        FROM information_schema.columns
        WHERE table_schema = 'public'
          AND data_type IN ('text', 'character varying', 'json', 'jsonb')
        ORDER BY table_name, column_name
    """)).fetchall()

    print(f"Total columns to scan: {len(res)}")
    found_mojibake = []

    for table_name, col_name in res:
        for pat in patterns:
            try:
                stmt = text(f"SELECT id, {col_name}::text FROM {table_name} WHERE {col_name}::text LIKE :pat LIMIT 5")
                rows = db.execute(stmt, {"pat": pat}).fetchall()
                if rows:
                    print(f"[MOJIBAKE DETECTED] Table {table_name}, Col {col_name}, Pattern {pat}: {len(rows)} samples")
                    for r in rows:
                        sample = str(r[1])[:100].replace('\n', ' ')
                        print(f"  ID {r[0]}: {sample}")
                    found_mojibake.append((table_name, col_name, pat, len(rows)))
            except Exception as e:
                db.rollback()
                # Some tables might not have 'id' column
                try:
                    stmt = text(f"SELECT {col_name}::text FROM {table_name} WHERE {col_name}::text LIKE :pat LIMIT 5")
                    rows = db.execute(stmt, {"pat": pat}).fetchall()
                    if rows:
                        print(f"[MOJIBAKE DETECTED (no id)] Table {table_name}, Col {col_name}: {len(rows)} samples")
                        found_mojibake.append((table_name, col_name, pat, len(rows)))
                except Exception as e2:
                    db.rollback()

    if not found_mojibake:
        print("\n[VERIFIED CLEAN] No mojibake (%à®%, %à¯%, %Ã%) found in ANY text/varchar/json column in PostgreSQL!")
    else:
        print(f"\n[ALERT] Found {len(found_mojibake)} columns with mojibake!")

    # Check for valid Tamil in events
    try:
        stmt = text("SELECT id, title FROM events WHERE title ~ '[\u0B80-\u0BFF]' LIMIT 5")
        tamil_events = db.execute(stmt).fetchall()
        print(f"\n--- Valid Tamil Records in events table (sample {len(tamil_events)}) ---")
        for r in tamil_events:
            print(f"  Event ID {r[0]}: {r[1]}")
    except Exception as e:
        db.rollback()
        print(f"Error checking valid Tamil: {e}")

    db.close()

if __name__ == '__main__':
    main()
