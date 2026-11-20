import os
import unittest
import datetime
import io

os.environ["TESTING"] = "1"
import config
config.DB_PATH = config.DATA_DIR / "test_jobs.db"
if config.DB_PATH.exists():
    config.DB_PATH.unlink()

from database import (
    init_db, get_connection, upsert_job, update_job_status,
    update_job_notes, apply_auto_expiry, get_all_skills,
    add_skill, delete_skill, parse_date_to_standard, normalize_date_str
)
from skills_matcher import match_skills_for_title
from resume_parser import auto_categorize_skill, extract_skills_from_text, extract_text_from_file

class TestJobTracker(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        conn = get_connection()
        conn.execute("DELETE FROM jobs")
        conn.execute("DELETE FROM scrape_runs")
        conn.commit()
        conn.close()

    def test_database_initialization(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [r[0] for r in cursor.fetchall()]
        conn.close()
        self.assertIn("jobs", tables)
        self.assertIn("scrape_runs", tables)
        self.assertIn("skills", tables)

    def test_date_posted_normalization_and_sorting(self):
        # Insert jobs with varied dates
        job_old = {
            "source_name": "Cyberpark Kozhikode",
            "title": "Junior Python Django Developer",
            "date_posted": "July 2, 2026",
            "job_url": "https://test.com/job-old",
        }
        job_new = {
            "source_name": "Infopark",
            "title": "Senior Cloud Engineer",
            "date_posted": "20-11-2026",
            "job_url": "https://test.com/job-new",
        }
        job_mid = {
            "source_name": "Cyberpark Kozhikode",
            "title": "Backend Architect",
            "date_posted": "November 12, 2026",
            "job_url": "https://test.com/job-mid",
        }
        upsert_job(job_old)
        upsert_job(job_new)
        upsert_job(job_mid)

        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT title, date_posted FROM jobs ORDER BY date_posted DESC")
        rows = c.fetchall()
        conn.close()

        # Most recent should be Nov 20, then Nov 12, then July 02
        self.assertEqual(rows[0]["date_posted"], "2026-11-20")
        self.assertEqual(rows[0]["title"], "Senior Cloud Engineer")

        self.assertEqual(rows[1]["date_posted"], "2026-11-12")
        self.assertEqual(rows[1]["title"], "Backend Architect")

        self.assertEqual(rows[2]["date_posted"], "2026-07-02")
        self.assertEqual(rows[2]["title"], "Junior Python Django Developer")

    def test_auto_categorization_of_skills(self):
        self.assertEqual(auto_categorize_skill("Python"), "Programming Language")
        self.assertEqual(auto_categorize_skill("Java"), "Programming Language")
        self.assertEqual(auto_categorize_skill("MySQL"), "Database")
        self.assertEqual(auto_categorize_skill("PostgreSQL"), "Database")
        self.assertEqual(auto_categorize_skill("React"), "Framework & Web")
        self.assertEqual(auto_categorize_skill("Docker"), "DevOps & Cloud")
        self.assertEqual(auto_categorize_skill("Figma"), "Design & UI/UX")
        self.assertEqual(auto_categorize_skill("Selenium"), "Testing & QA")

    def test_core_skill_handling(self):
        add_skill("Golang", is_core=True)
        skills = get_all_skills()
        golang = next((s for s in skills if s["name"] == "Golang"), None)
        self.assertIsNotNone(golang)
        self.assertEqual(golang["is_core"], 1)
        self.assertEqual(golang["priority"], 2)
        self.assertEqual(golang["category"], "Programming Language")

    def test_resume_skill_extraction(self):
        sample_resume_text = """
        Experienced Full Stack Developer with 4 years building scalable web applications.
        Proficient in Python, Django, PostgreSQL, and Docker.
        Familiar with React, TypeScript, and AWS cloud deployments.
        Experienced with automated unit testing and Git.
        """
        extracted = extract_skills_from_text(sample_resume_text, existing_skills=["Python"])
        extracted_names = [e["name"] for e in extracted]

        # Python should be skipped because it was in existing_skills
        self.assertNotIn("Python", extracted_names)
        # Other skills should be detected
        self.assertIn("Django", extracted_names)
        self.assertIn("PostgreSQL", extracted_names)
        self.assertIn("Docker", extracted_names)
        self.assertIn("React", extracted_names)
        self.assertIn("AWS", extracted_names)

    def test_auto_expiry_never_touches_applied(self):
        past_date = (datetime.date.today() - datetime.timedelta(days=10)).strftime("%Y-%m-%d")
        upsert_job({
            "source_name": "Technopark",
            "title": "Applied Role",
            "deadline": past_date,
            "job_url": "https://test.com/applied1"
        })
        conn = get_connection()
        c = conn.cursor()
        c.execute("SELECT id FROM jobs WHERE job_url = 'https://test.com/applied1'")
        job_id = c.fetchone()["id"]
        update_job_status(job_id, "Applied")

        # Run auto-expiry
        apply_auto_expiry()

        c.execute("SELECT status FROM jobs WHERE id = ?", (job_id,))
        self.assertEqual(c.fetchone()["status"], "Applied")
        conn.close()

    def test_csv_export_format(self):
        from app import app
        client = app.test_client()

        upsert_job({
            "source_name": "Technopark Thiruvananthapuram",
            "title": "Python Developer",
            "company_name": "Acme Inc",
            "location": "Thiruvananthapuram",
            "date_posted": "2026-11-20",
            "deadline": "2026-12-05",
            "job_url": "https://technopark.in/job-details/123",
        })

        resp = client.get("/export/csv")
        self.assertEqual(resp.status_code, 200)
        lines = resp.data.decode("utf-8").strip().splitlines()
        header = lines[0].split(",")
        expected_header = [
            "Date posted",
            "Exact Job Title",
            "Company Name",
            "Location",
            "Application Deadline",
            "Direct Job url"
        ]
        self.assertEqual(header, expected_header)
        # Check first row has 6 values
        self.assertIn("Python Developer", lines[1])

if __name__ == "__main__":
    unittest.main()
