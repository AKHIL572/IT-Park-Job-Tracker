import sqlite3
import hashlib
import datetime
import re
from typing import List, Dict, Optional, Tuple, Any
from config import DB_PATH
from resume_parser import auto_categorize_skill

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def parse_date_to_standard(date_str: Optional[str]) -> Optional[datetime.date]:
    """Parse various date string formats into standard datetime.date."""
    if not date_str:
        return None
    cleaned = date_str.strip()
    if not cleaned:
        return None

    # Strip prefixes like "Posted on "
    if cleaned.lower().startswith("posted on"):
        cleaned = cleaned[9:].strip()

    formats = [
        "%Y-%m-%d",       # 2026-11-20
        "%d-%m-%Y",       # 20-11-2026
        "%d/%m/%Y",       # 20/11/2026
        "%Y/%m/%d",       # 2026/11/20
        "%d %b %Y",       # 20 Nov 2026
        "%d %B %Y",       # 20 November 2026
        "%b %d, %Y",      # Nov 20, 2026
        "%B %d, %Y",      # November 20, 2026
        "%B %d %Y",       # November 20 2026
    ]
    for fmt in formats:
        try:
            return datetime.datetime.strptime(cleaned, fmt).date()
        except ValueError:
            continue

    # Regex fallback for "Month DD, YYYY" or "Month DD YYYY"
    match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s*(\d{4})', cleaned)
    if match:
        m, d, y = match.groups()
        try:
            return datetime.datetime.strptime(f"{m} {d} {y}", "%B %d %Y").date()
        except ValueError:
            pass

    # Regex fallback for "DD-MM-YYYY" or "DD/MM/YYYY"
    match2 = re.search(r'(\d{1,2})[-/](\d{1,2})[-/](\d{4})', cleaned)
    if match2:
        d, m, y = match2.groups()
        try:
            return datetime.date(int(y), int(m), int(d))
        except ValueError:
            pass

    return None

def normalize_date_str(date_str: Optional[str], fallback_today: bool = False) -> str:
    """Standardizes date string to YYYY-MM-DD or empty string."""
    d = parse_date_to_standard(date_str)
    if d:
        return d.strftime("%Y-%m-%d")
    if fallback_today:
        return datetime.date.today().strftime("%Y-%m-%d")
    return ""

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    # Jobs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_hash TEXT UNIQUE NOT NULL,
        source_name TEXT NOT NULL,
        source_type TEXT DEFAULT 'IT Park',
        park_or_city TEXT,
        title TEXT NOT NULL,
        company_name TEXT,
        location TEXT,
        date_posted TEXT,
        deadline TEXT,
        job_url TEXT NOT NULL,
        first_seen_date TEXT NOT NULL,
        last_seen_date TEXT NOT NULL,
        status TEXT DEFAULT 'New',
        saved_date TEXT,
        applied_date TEXT,
        notes TEXT
    );
    """)

    # Indexes
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_deadline ON jobs(deadline);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jobs_date_posted ON jobs(date_posted);")

    # Scrape runs table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS scrape_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        run_time TEXT NOT NULL,
        source_name TEXT NOT NULL,
        status TEXT NOT NULL,
        jobs_found INTEGER DEFAULT 0,
        new_jobs INTEGER DEFAULT 0,
        updated_jobs INTEGER DEFAULT 0,
        message TEXT
    );
    """)

    # Skills table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS skills (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        category TEXT DEFAULT 'General',
        priority INTEGER DEFAULT 1,
        is_core INTEGER DEFAULT 0
    );
    """)

    # Migrate is_core column if not exists
    cursor.execute("PRAGMA table_info(skills)")
    cols = [r[1] for r in cursor.fetchall()]
    if "is_core" not in cols:
        cursor.execute("ALTER TABLE skills ADD COLUMN is_core INTEGER DEFAULT 0")

    # Seed default popular skills if empty
    cursor.execute("SELECT COUNT(*) FROM skills")
    if cursor.fetchone()[0] == 0:
        default_skills = [
            ("Python", "Programming Language", 2, 1),
            ("JavaScript", "Programming Language", 1, 0),
            ("TypeScript", "Programming Language", 1, 0),
            ("React", "Framework & Web", 2, 1),
            ("Node", "Framework & Web", 1, 0),
            ("Java", "Programming Language", 1, 0),
            ("Full Stack", "Role", 2, 1),
            ("Frontend", "Frontend", 1, 0),
            ("Backend", "Framework & Web", 1, 0),
            ("UI/UX", "Design & UI/UX", 1, 0),
            ("DevOps", "DevOps & Cloud", 2, 1),
            ("AWS", "DevOps & Cloud", 1, 0),
            ("Docker", "DevOps & Cloud", 1, 0),
            ("SQL", "Database", 1, 0),
            ("PostgreSQL", "Database", 1, 0),
            ("MySQL", "Database", 1, 0),
            ("Data Engineer", "Role", 2, 1),
            ("QA", "Testing & QA", 1, 0),
            ("Automation Engineer", "Testing & QA", 2, 1),
            ("Flutter", "Framework & Web", 1, 0),
            ("Golang", "Programming Language", 1, 0),
        ]
        cursor.executemany(
            "INSERT OR IGNORE INTO skills (name, category, priority, is_core) VALUES (?, ?, ?, ?)",
            default_skills
        )

    conn.commit()
    conn.close()

    # Normalize any legacy dates in existing database
    normalize_all_existing_dates()

def normalize_all_existing_dates():
    """Migrate all dates in the jobs table to standard YYYY-MM-DD format."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, date_posted, deadline, first_seen_date FROM jobs")
    rows = cursor.fetchall()
    updates = []
    for r in rows:
        job_id = r["id"]
        raw_posted = r["date_posted"]
        raw_deadline = r["deadline"]
        first_seen = r["first_seen_date"]

        norm_posted = normalize_date_str(raw_posted)
        if not norm_posted and first_seen:
            # Fallback to first seen date (YYYY-MM-DD)
            norm_posted = first_seen[:10]

        norm_deadline = normalize_date_str(raw_deadline)

        if norm_posted != raw_posted or norm_deadline != raw_deadline:
            updates.append((norm_posted, norm_deadline, job_id))

    if updates:
        cursor.executemany("UPDATE jobs SET date_posted = ?, deadline = ? WHERE id = ?", updates)
        conn.commit()
    conn.close()

def generate_job_hash(url: str, title: str, company: str, posted_date: str) -> str:
    """Generate a stable unique hash for deduplication."""
    clean_url = (url or "").strip().lower()
    if clean_url and len(clean_url) > 10:
        return hashlib.sha256(clean_url.encode('utf-8')).hexdigest()
    
    norm_title = re.sub(r'\s+', ' ', (title or "").lower().strip())
    norm_comp = re.sub(r'\s+', ' ', (company or "").lower().strip())
    norm_date = (posted_date or "").strip()
    key = f"{norm_title}|{norm_comp}|{norm_date}"
    return hashlib.sha256(key.encode('utf-8')).hexdigest()

def upsert_job(job_dict: Dict[str, Any]) -> Tuple[bool, bool]:
    """
    Insert or update a job.
    Normalizes date_posted and deadline to standard YYYY-MM-DD.
    Guarantees user status, notes, saved_date, applied_date are never erased.
    """
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    raw_posted = job_dict.get("date_posted", "")
    norm_posted = normalize_date_str(raw_posted)
    if not norm_posted:
        norm_posted = today_str

    raw_deadline = job_dict.get("deadline", "")
    norm_deadline = normalize_date_str(raw_deadline)

    job_hash = job_dict.get("job_hash") or generate_job_hash(
        job_dict.get("job_url", ""),
        job_dict.get("title", ""),
        job_dict.get("company_name", ""),
        norm_posted
    )

    cursor.execute("SELECT id, status, saved_date, applied_date, notes FROM jobs WHERE job_hash = ?", (job_hash,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE jobs SET
                last_seen_date = ?,
                title = COALESCE(NULLIF(title, ''), ?),
                company_name = COALESCE(NULLIF(company_name, ''), ?),
                location = COALESCE(NULLIF(location, ''), ?),
                date_posted = COALESCE(NULLIF(date_posted, ''), ?),
                deadline = COALESCE(NULLIF(deadline, ''), ?),
                job_url = COALESCE(NULLIF(job_url, ''), ?)
            WHERE job_hash = ?
        """, (
            now_str,
            job_dict.get("title", ""),
            job_dict.get("company_name", ""),
            job_dict.get("location", ""),
            norm_posted,
            norm_deadline,
            job_dict.get("job_url", ""),
            job_hash
        ))
        conn.commit()
        conn.close()
        return False, True
    else:
        cursor.execute("""
            INSERT INTO jobs (
                job_hash, source_name, source_type, park_or_city,
                title, company_name, location, date_posted, deadline,
                job_url, first_seen_date, last_seen_date, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'New', '')
        """, (
            job_hash,
            job_dict.get("source_name", ""),
            job_dict.get("source_type", "IT Park"),
            job_dict.get("park_or_city", ""),
            job_dict.get("title", "").strip(),
            job_dict.get("company_name", "").strip(),
            job_dict.get("location", "").strip(),
            norm_posted,
            norm_deadline,
            job_dict.get("job_url", "").strip(),
            now_str,
            now_str
        ))
        conn.commit()
        conn.close()
        return True, False

def apply_auto_expiry() -> int:
    """
    Mark jobs as Expired if their deadline has passed.
    IMPORTANT: NEVER change Applied jobs automatically!
    """
    conn = get_connection()
    cursor = conn.cursor()
    today_str = datetime.date.today().strftime("%Y-%m-%d")

    cursor.execute("""
        SELECT id, deadline, status FROM jobs 
        WHERE status NOT IN ('Applied', 'Expired') 
        AND deadline IS NOT NULL AND TRIM(deadline) != ''
    """)
    rows = cursor.fetchall()
    expired_count = 0

    for row in rows:
        job_id = row["id"]
        deadline_str = row["deadline"]
        if deadline_str and len(deadline_str) == 10 and deadline_str < today_str:
            cursor.execute("UPDATE jobs SET status = 'Expired' WHERE id = ?", (job_id,))
            expired_count += 1

    conn.commit()
    conn.close()
    return expired_count

def update_job_status(job_id: int, new_status: str) -> Optional[Dict[str, Any]]:
    """Update job status: 'Saved', 'Applied', 'Ignored', 'New'."""
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    job = cursor.fetchone()
    if not job:
        conn.close()
        return None

    if new_status == "Saved":
        cursor.execute("UPDATE jobs SET status = 'Saved', saved_date = ? WHERE id = ?", (now_str, job_id))
    elif new_status == "Applied":
        cursor.execute("UPDATE jobs SET status = 'Applied', applied_date = ? WHERE id = ?", (now_str, job_id))
    elif new_status == "Ignored":
        cursor.execute("UPDATE jobs SET status = 'Ignored' WHERE id = ?", (job_id,))
    elif new_status in ("New", "Restore"):
        cursor.execute("UPDATE jobs SET status = 'New' WHERE id = ?", (job_id,))
    elif new_status == "Expired":
        cursor.execute("UPDATE jobs SET status = 'Expired' WHERE id = ?", (job_id,))

    conn.commit()
    cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
    updated = dict(cursor.fetchone())
    conn.close()
    return updated

def update_job_notes(job_id: int, notes: str) -> bool:
    """Save manual notes for a job."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE jobs SET notes = ? WHERE id = ?", (notes, job_id))
    conn.commit()
    conn.close()
    return True

def record_scrape_run(source_name: str, status: str, found: int = 0, new: int = 0, updated: int = 0, message: str = "") -> int:
    conn = get_connection()
    cursor = conn.cursor()
    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
        INSERT INTO scrape_runs (run_time, source_name, status, jobs_found, new_jobs, updated_jobs, message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (now_str, source_name, status, found, new, updated, message))
    run_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return run_id

def get_all_skills() -> List[Dict[str, Any]]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, category, priority, is_core FROM skills ORDER BY is_core DESC, priority DESC, name ASC")
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def add_skill(name: str, is_core: bool = False, category: Optional[str] = None) -> bool:
    clean_name = name.strip()
    if not clean_name:
        return False
    # Auto-assign category
    cat = category if (category and category != "General") else auto_categorize_skill(clean_name)
    priority = 2 if is_core else 1
    core_val = 1 if is_core else 0

    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO skills (name, category, priority, is_core) 
            VALUES (?, ?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET 
                is_core = excluded.is_core,
                priority = excluded.priority,
                category = excluded.category
        """, (clean_name, cat, priority, core_val))
        conn.commit()
        return True
    except Exception as e:
        print("add_skill error:", e)
        return False
    finally:
        conn.close()

def delete_skill(skill_id: int) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM skills WHERE id = ?", (skill_id,))
    conn.commit()
    conn.close()
    return True

def get_summary_counts() -> Dict[str, int]:
    """Get KPI summary cards count."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
    counts = {r[0]: r[1] for r in cursor.fetchall()}
    cursor.execute("SELECT COUNT(*) FROM jobs")
    total = cursor.fetchone()[0]
    conn.close()

    return {
        "total": total,
        "new": counts.get("New", 0),
        "saved": counts.get("Saved", 0),
        "applied": counts.get("Applied", 0),
        "ignored": counts.get("Ignored", 0),
        "expired": counts.get("Expired", 0)
    }

init_db()
