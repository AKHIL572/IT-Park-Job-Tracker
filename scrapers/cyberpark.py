import json
import urllib.parse
from bs4 import BeautifulSoup
from typing import List, Dict, Any
from scrapers.base import BaseScraper
from config import SOURCES

class CyberparkScraper(BaseScraper):
    def __init__(self):
        cfg = SOURCES["cyberpark"]
        super().__init__("cyberpark", cfg["name"], cfg["city"])
        self.ajax_url = cfg["ajax_url"]

    def scrape(self, max_pages: int = 4) -> List[Dict[str, Any]]:
        """Scrapes Cyberpark Kozhikode jobs via public WP Job Manager AJAX."""
        jobs = []
        for page in range(1, max_pages + 1):
            post_data = urllib.parse.urlencode({
                "per_page": 20,
                "page": page,
                "show_pagination": "false"
            }).encode("utf-8")

            extra_headers = {
                "X-Requested-With": "XMLHttpRequest",
                "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                "Referer": "https://cyberparks.in/careers/"
            }

            raw = self.fetch(self.ajax_url, data=post_data, extra_headers=extra_headers)
            if not raw:
                break

            try:
                res = json.loads(raw)
            except Exception as e:
                print(f"[{self.name}] JSON parse error on page {page}: {e}")
                break

            html = res.get("html", "")
            if not html:
                break

            soup = BeautifulSoup(html, "html.parser")
            listings = soup.find_all("li", class_=lambda c: c and "job_listing" in c)
            if not listings:
                # Fallback to any li with link
                listings = [li for li in soup.find_all("li") if li.find("a", href=True)]

            if not listings:
                break

            for li in listings:
                link_tag = li.find("a", href=True)
                direct_url = link_tag["href"].strip() if link_tag else ""

                title_tag = li.find("h3") or li.find(class_="job_listing-title") or link_tag
                title = self.clean_text(title_tag.get_text(strip=True)) if title_tag else ""

                comp_tag = li.find(class_="company")
                # Sometimes company tag contains duplicated inner text, clean it
                company_name = self.clean_text(comp_tag.get_text(strip=True)) if comp_tag else ""
                if company_name and len(company_name) > 60:
                    # Clean repeated company text if present
                    parts = company_name.split()
                    if len(parts) >= 4 and parts[:len(parts)//2] == parts[len(parts)//2:]:
                        company_name = " ".join(parts[:len(parts)//2])

                loc_tag = li.find(class_="location")
                location = self.clean_text(loc_tag.get_text(strip=True)) if loc_tag else "Kozhikode"

                date_tag = li.find("time") or li.find(class_="date")
                date_str = self.clean_text(date_tag.get_text(strip=True)) if date_tag else ""
                # Strip "Posted on " prefix if present
                if date_str.lower().startswith("posted on"):
                    date_str = date_str[9:].strip()

                if not title:
                    continue

                jobs.append({
                    "source_name": self.name,
                    "source_type": "IT Park",
                    "park_or_city": self.park_or_city,
                    "title": title,
                    "company_name": company_name,
                    "location": location,
                    "date_posted": date_str,
                    "deadline": "",  # Cyberpark card doesn't include deadline
                    "job_url": direct_url,
                })

            max_num_pages = res.get("max_num_pages", page)
            if page >= max_num_pages:
                break

        return jobs

