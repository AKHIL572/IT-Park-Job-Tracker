import threading
import datetime
from typing import Dict, Any, Optional
from scrapers.technopark import TechnoparkScraper
from scrapers.infopark import InfoparkScraper
from scrapers.cyberpark import CyberparkScraper
from scrapers.ulcyberpark import ULCyberparkScraper
from database import upsert_job, record_scrape_run, apply_auto_expiry, init_db

_scrape_lock = threading.Lock()
_scrape_state = {
    "is_running": False,
    "current_source": None,
    "last_run": None,
    "last_result": None,
    "error": None
}

def get_scrape_state() -> Dict[str, Any]:
    state = dict(_scrape_state)
    # If last_run not set in memory, check database
    if not state["last_run"]:
        try:
            from database import get_connection
            conn = get_connection()
            c = conn.cursor()
            c.execute("SELECT run_time FROM scrape_runs ORDER BY id DESC LIMIT 1")
            row = c.fetchone()
            conn.close()
            if row and row[0]:
                state["last_run"] = row[0]
                _scrape_state["last_run"] = row[0]
        except Exception:
            pass

    # Calculate recommended timing
    if state["last_run"]:
        try:
            last_dt = datetime.datetime.strptime(state["last_run"], "%Y-%m-%d %H:%M:%S")
            next_dt = last_dt + datetime.timedelta(hours=3)
            now = datetime.datetime.now()
            state["next_recommended_run"] = next_dt.strftime("%Y-%m-%d %H:%M:%S")
            state["next_recommended_time_str"] = next_dt.strftime("%I:%M %p")
            state["last_run_time_str"] = last_dt.strftime("%I:%M %p")
            if now >= next_dt:
                state["can_run_recommendation"] = "Ready Now (Rate limit safe)"
                state["is_rate_safe"] = True
            else:
                diff = next_dt - now
                mins = int(diff.total_seconds() // 60)
                hours = mins // 60
                remain_mins = mins % 60
                time_desc = f"{hours}h {remain_mins}m" if hours > 0 else f"{mins}m"
                state["can_run_recommendation"] = f"Next optimal scrape at {next_dt.strftime('%I:%M %p')} (in {time_desc})"
                state["is_rate_safe"] = False
        except Exception:
            state["can_run_recommendation"] = "Ready"
            state["is_rate_safe"] = True
    else:
        state["can_run_recommendation"] = "Ready Now"
        state["is_rate_safe"] = True

    return state

def run_scrapers(specific_source: Optional[str] = None) -> Dict[str, Any]:
    """
    Executes scrapers sequentially with polite pauses, updates database,
    and returns a summary dictionary.
    """
    init_db()
    if not _scrape_lock.acquire(blocking=False):
        return {
            "status": "busy",
            "message": "A scrape job is already in progress. Please wait."
        }

    _scrape_state["is_running"] = True
    _scrape_state["error"] = None
    results = {}
    total_found = 0
    total_new = 0
    total_updated = 0

    scrapers_map = {
        "technopark": TechnoparkScraper(),
        "infopark": InfoparkScraper(),
        "cyberpark": CyberparkScraper(),
        "ulcyberpark": ULCyberparkScraper(),
    }

    targets = [specific_source] if specific_source and specific_source in scrapers_map else list(scrapers_map.keys())

    try:
        for key in targets:
            scraper = scrapers_map[key]
            _scrape_state["current_source"] = scraper.name
            print(f"[Engine] Starting scrape for: {scraper.name}...")

            found = 0
            new = 0
            updated = 0
            err_msg = ""
            status = "success"

            try:
                jobs = scraper.scrape()
                found = len(jobs)
                for j in jobs:
                    is_new, is_updated = upsert_job(j)
                    if is_new:
                        new += 1
                    elif is_updated:
                        updated += 1
            except Exception as e:
                status = "failed"
                err_msg = str(e)
                print(f"[Engine] Scrape error for {scraper.name}: {e}")

            record_scrape_run(
                source_name=scraper.name,
                status=status,
                found=found,
                new=new,
                updated=updated,
                message=err_msg
            )

            results[key] = {
                "source": scraper.name,
                "status": status,
                "found": found,
                "new": new,
                "updated": updated,
                "error": err_msg
            }
            total_found += found
            total_new += new
            total_updated += updated

        # Automatically check and apply deadline expiries after scrape
        expired_count = apply_auto_expiry()

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        _scrape_state["last_run"] = now_str
        summary = {
            "status": "completed",
            "timestamp": now_str,
            "total_found": total_found,
            "total_new": total_new,
            "total_updated": total_updated,
            "expired_updated": expired_count,
            "details": results
        }
        _scrape_state["last_result"] = summary
        return summary

    finally:
        _scrape_state["is_running"] = False
        _scrape_state["current_source"] = None
        _scrape_lock.release()

def start_background_scrape(specific_source: Optional[str] = None):
    t = threading.Thread(target=run_scrapers, args=(specific_source,), daemon=True)
    t.start()
    return t
