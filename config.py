import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "jobs.db"

# Polite scraping configuration
DEFAULT_HEADERS = {
    "User-Agent": "JobTracker/1.0 (Polite local job aggregator; respecting public listings)",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,application/json,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Request delay between individual page requests in seconds
REQUEST_DELAY_SECONDS = 1.5
REQUEST_TIMEOUT_SECONDS = 15

# Source definitions
SOURCES = {
    "technopark": {
        "name": "Technopark Thiruvananthapuram",
        "type": "IT Park",
        "city": "Thiruvananthapuram",
        "url": "https://technopark.in/job-search",
        "api_url": "https://technopark.in/api/paginated-jobs",
    },
    "infopark": {
        "name": "Infopark",
        "type": "IT Park",
        "city": "Kochi / Cherthala / Thrissur",
        "url": "https://infopark.in/companies/job-search",
    },
    "cyberpark": {
        "name": "Cyberpark Kozhikode",
        "type": "IT Park",
        "city": "Kozhikode",
        "url": "https://cyberparks.in/careers/",
        "ajax_url": "https://cyberparks.in/jm-ajax/get_listings/",
    },
    "ulcyberpark": {
        "name": "UL Cyberpark Kozhikode",
        "type": "IT Park",
        "city": "Kozhikode",
        "url": "https://www.ulcyberpark.com/jobs",
    },
}

