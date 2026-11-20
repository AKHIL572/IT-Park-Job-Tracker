from bs4 import BeautifulSoup
from typing import List, Dict, Any
from scrapers.base import BaseScraper
from config import SOURCES

class InfoparkScraper(BaseScraper):
    def __init__(self):
        cfg = SOURCES["infopark"]
        super().__init__("infopark", cfg["name"], cfg["city"])
        self.base_url = "https://infopark.in"

    def scrape(self, max_pages: int = 5) -> List[Dict[str, Any]]:
        """Scrapes Infopark Kochi/Cherthala/Thrissur public job table."""
        jobs = []
        for page in range(1, max_pages + 1):
            if page == 1:
                url = "https://infopark.in/companies/job-search"
            else:
                url = f"https://infopark.in/companies-job?page={page}"

            html = self.fetch(url)
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")
            table = soup.find("table")
            if not table:
                break

            rows = table.find_all("tr")
            if len(rows) <= 1:
                break

            for tr in rows[1:]:
                tds = tr.find_all("td")
                if len(tds) < 4:
                    continue

                date_posted = self.clean_text(tds[0].get_text(strip=True))
                title = self.clean_text(tds[1].get_text(strip=True))
                company_name = self.clean_text(tds[2].get_text(strip=True))
                deadline = self.clean_text(tds[3].get_text(strip=True))

                direct_url = ""
                if len(tds) > 4:
                    link_tag = tds[4].find("a", href=True)
                    if link_tag:
                        href = link_tag["href"].strip()
                        if href.startswith("http"):
                            direct_url = href
                        else:
                            direct_url = f"{self.base_url}{href}"

                if not title:
                    continue

                jobs.append({
                    "source_name": self.name,
                    "source_type": "IT Park",
                    "park_or_city": self.park_or_city,
                    "title": title,
                    "company_name": company_name,
                    "location": "Kochi / Cherthala / Thrissur",
                    "date_posted": date_posted,
                    "deadline": deadline,
                    "job_url": direct_url or url,
                })

        return jobs

