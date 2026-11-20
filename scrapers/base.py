import time
import urllib.request
import urllib.parse
import ssl
from typing import Optional, Dict, Any
from config import DEFAULT_HEADERS, REQUEST_DELAY_SECONDS, REQUEST_TIMEOUT_SECONDS

class BaseScraper:
    def __init__(self, source_key: str, name: str, park_or_city: str):
        self.source_key = source_key
        self.name = name
        self.park_or_city = park_or_city
        self.headers = DEFAULT_HEADERS.copy()

    def fetch(self, url: str, data: Optional[bytes] = None, extra_headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Fetch URL with rate-limiting delay and polite headers."""
        time.sleep(REQUEST_DELAY_SECONDS)
        headers = self.headers.copy()
        if extra_headers:
            headers.update(extra_headers)

        req = urllib.request.Request(url, data=data, headers=headers)
        # Create context that handles standard SSL certificates
        ctx = ssl.create_default_context()

        try:
            with urllib.request.urlopen(req, context=ctx, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                return resp.read().decode('utf-8', errors='ignore')
        except urllib.error.HTTPError as e:
            print(f"[{self.name}] HTTP {e.code} error fetching {url}")
            return None
        except Exception as e:
            # Fallback for sites with hostname mismatches or non-critical SSL chain quirks
            try:
                unverified_ctx = ssl._create_unverified_context()
                with urllib.request.urlopen(req, context=unverified_ctx, timeout=REQUEST_TIMEOUT_SECONDS) as resp:
                    return resp.read().decode('utf-8', errors='ignore')
            except Exception as e2:
                print(f"[{self.name}] Error fetching {url}: {e2}")
                return None

    def clean_text(self, text: Optional[str]) -> str:
        if not text:
            return ""
        return " ".join(text.split()).strip()

