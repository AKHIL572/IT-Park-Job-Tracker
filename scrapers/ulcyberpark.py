import re
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from scrapers.base import BaseScraper
from config import SOURCES

class ULCyberparkScraper(BaseScraper):
    def __init__(self):
        cfg = SOURCES["ulcyberpark"]
        super().__init__("ulcyberpark", cfg["name"], cfg["city"])
        self.jobs_url = cfg["url"]

    def scrape(self) -> List[Dict[str, Any]]:
        """Scrapes UL Cyberpark Kozhikode jobs page."""
        jobs = []
        html = self.fetch(self.jobs_url)
        if not html:
            return jobs

        soup = BeautifulSoup(html, "html.parser")
        table = soup.find("div", class_="table-job") or soup.find("table")
        if not table:
            return jobs

        rows = table.find_all("tr")
        for tr in rows:
            tds = tr.find_all("td")
            if len(tds) < 2:
                continue

            # First TD has title and closing date
            first_td = tds[0]
            title_tag = first_td.find("a")
            title = self.clean_text(title_tag.get_text(strip=True)) if title_tag else ""

            span_tag = first_td.find("span")
            span_text = span_tag.get_text(strip=True) if span_tag else ""
            deadline_match = re.search(r'closing\s*date\s*:\s*([0-9\-\./]+)', span_text, re.IGNORECASE)
            deadline = deadline_match.group(1).strip() if deadline_match else ""

            # Second TD has company name
            second_td = tds[1]
            comp_tag = second_td.find("a") or second_td
            company_name = self.clean_text(comp_tag.get_text(strip=True))

            # Third TD has direct URL
            direct_url = self.jobs_url
            if len(tds) > 2:
                view_link = tds[2].find("a", href=True)
                if view_link:
                    href = view_link["href"].strip()
                    if href.startswith("http"):
                        direct_url = href
                    else:
                        direct_url = f"https://www.ulcyberpark.com{href}"

            if not title:
                continue

            jobs.append({
                "source_name": self.name,
                "source_type": "IT Park",
                "park_or_city": self.park_or_city,
                "title": title,
                "company_name": company_name,
                "location": "Kozhikode",
                "date_posted": "",  # UL Cyberpark doesn't show posted date on listing
                "deadline": deadline,
                "job_url": direct_url,
            })

        return jobs

