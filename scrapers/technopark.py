import json
import urllib.parse
from typing import List, Dict, Any
from scrapers.base import BaseScraper
from config import SOURCES

class TechnoparkScraper(BaseScraper):
    def __init__(self):
        cfg = SOURCES["technopark"]
        super().__init__("technopark", cfg["name"], cfg["city"])
        self.api_url = cfg["api_url"]

    def scrape(self, max_pages: int = 5) -> List[Dict[str, Any]]:
        """Scrapes Technopark job vacancies politely."""
        jobs = []
        for page in range(1, max_pages + 1):
            url = f"{self.api_url}?page={page}&search=&type="
            raw = self.fetch(url)
            if not raw:
                break

            try:
                data = json.loads(raw)
            except Exception as e:
                print(f"[{self.name}] JSON parse error on page {page}: {e}")
                break

            items = data.get("data", [])
            if not items:
                break

            for item in items:
                job_id = item.get("id")
                raw_title = item.get("job_title", "")
                title = self.clean_text(raw_title)
                if not title:
                    continue

                company_info = item.get("company") or {}
                company_name = self.clean_text(company_info.get("company", ""))
                date_posted = self.clean_text(item.get("posted_date", ""))
                deadline = self.clean_text(item.get("closing_date", ""))

                # Build official direct job details link
                encoded_title = urllib.parse.quote(title)
                direct_url = f"https://technopark.in/job-details/{job_id}?job={encoded_title}"

                jobs.append({
                    "source_name": self.name,
                    "source_type": "IT Park",
                    "park_or_city": self.park_or_city,
                    "title": title,
                    "company_name": company_name,
                    "location": "Thiruvananthapuram",
                    "date_posted": date_posted,
                    "deadline": deadline,
                    "job_url": direct_url,
                })

            current_page = data.get("current_page", page)
            last_page = data.get("last_page", page)
            if current_page >= last_page:
                break

        return jobs

