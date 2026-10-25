import json
from collections import Counter
from sqlalchemy import text
from app.core.database import SessionLocal

def main():
    db = SessionLocal()

    # 1. Total article count, earliest and latest date
    q_range = text("""
        SELECT
            count(*),
            min(published_at),
            max(published_at),
            min(event_date),
            max(event_date)
        FROM events
    """)
    total, min_pub, max_pub, min_evt, max_evt = db.execute(q_range).fetchone()
    print("=== ARTICLE ARCHIVE STATS ===")
    print(f"Total articles: {total}")
    print(f"Publication date range: {min_pub} to {max_pub}")
    print(f"Event date range: {min_evt} to {max_evt}")

    # 2. Count by month across publication date
    q_month = text("""
        SELECT
            TO_CHAR(COALESCE(published_at, event_date), 'YYYY-MM') AS yr_mo,
            count(*)
        FROM events
        GROUP BY yr_mo
        ORDER BY yr_mo
    """)
    month_counts = db.execute(q_month).fetchall()
    print("\n=== ARTICLE COUNT BY MONTH ===")
    for ym, count in month_counts:
        print(f"  {ym}: {count}")

    # 3. Count by domain / category
    q_domain = text("""
        SELECT domain, count(*)
        FROM events
        GROUP BY domain
        ORDER BY count(*) DESC
    """)
    domain_counts = db.execute(q_domain).fetchall()
    print("\n=== ARTICLE COUNT BY DOMAIN ===")
    for dom, count in domain_counts:
        print(f"  {dom}: {count}")

    # 4. Count by source
    q_source = text("""
        SELECT s.name, count(e.id)
        FROM events e
        JOIN sources s ON e.source_id = s.id
        GROUP BY s.name
        ORDER BY count(e.id) DESC
        LIMIT 15
    """)
    source_counts = db.execute(q_source).fetchall()
    print("\n=== TOP 15 SOURCES BY ARTICLE COUNT ===")
    for src, count in source_counts:
        print(f"  {src}: {count}")

    # 5. Language breakdown
    q_lang = text("""
        SELECT
            CASE
                WHEN title ~ '[\u0B80-\u0BFF]' THEN 'Tamil (Unicode)'
                ELSE 'English / Other'
            END as lang,
            count(*)
        FROM events
        GROUP BY lang
    """)
    lang_counts = db.execute(q_lang).fetchall()
    print("\n=== LANGUAGE BREAKDOWN ===")
    for lang, count in lang_counts:
        print(f"  {lang}: {count}")

    # 6. Non-exam domain breakdown (Cinema, Crime, Gossip, Entertainment, Lifestyle)
    non_exam_domains = ('Entertainment', 'Crime', 'Lifestyle', 'Gossip', 'Cinema')
    q_non_exam = text("""
        SELECT id, domain, title, why_it_matters
        FROM events
        WHERE domain IN ('Entertainment', 'Crime', 'Lifestyle', 'Gossip', 'Cinema')
        LIMIT 8
    """)
    non_exam_samples = db.execute(q_non_exam).fetchall()
    print("\n=== SAMPLES OF EXCLUDED NON-EXAM DOMAIN ARTICLES ===")
    for row in non_exam_samples:
        print(f"  [{row[1]}] ID {row[0]}: {row[2][:80]}")

    # 7. Check for potential legal/policy articles categorized as Crime or Government
    q_legal = text("""
        SELECT id, domain, title
        FROM events
        WHERE (title ILIKE '%court%' OR title ILIKE '%judgment%' OR title ILIKE '%verdict%' OR title ILIKE '%bill%')
        LIMIT 5
    """)
    legal_samples = db.execute(q_legal).fetchall()
    print("\n=== SAMPLES OF LEGAL / JUDICIARY ARTICLES (EXAM RELEVANT) ===")
    for row in legal_samples:
        print(f"  [{row[1]}] ID {row[0]}: {row[2][:80]}")

    # 8. Duplicate count
    q_dup = text("""
        SELECT count(*) FROM (
            SELECT dedup_hash, count(*)
            FROM events
            WHERE dedup_hash IS NOT NULL
            GROUP BY dedup_hash
            HAVING count(*) > 1
        ) sub
    """)
    dup_hashes = db.execute(q_dup).scalar()
    print(f"\nDuplicate hashes in events table: {dup_hashes}")

    db.close()

if __name__ == '__main__':
    main()
