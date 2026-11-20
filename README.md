# Kerala IT Parks Job Tracker (100% Free, Private & Local)

A clean, free, private, and fully local job tracker built to monitor official job boards across Kerala IT Parks:
- **Technopark Thiruvananthapuram**
- **Infopark** (Kochi / Cherthala / Thrissur)
- **Cyberpark Kozhikode**
- **UL Cyberpark Kozhikode**

---

## 🔒 100% Free, Private & Local Principles
- **No Paid Services / No Cloud**: Runs completely on your own laptop.
- **Zero API Keys & Subscriptions**: Uses zero cloud databases or external SaaS.
- **Local SQLite Database**: All data is stored in `data/jobs.db`.
- **Offline Analytics**: Uses vendored Chart.js and vanilla CSS for zero external CDN dependency.
- **Polite & Ethical Scraping**:
  - Scrapes **only publicly visible** job postings from official IT-park boards.
  - No scraping behind logins or bypassing security.
  - No personal details collected.
  - **No automated job description scraping** (you can manually paste requirements using the Notes button).
  - Respects `robots.txt`, terms of use, and implements polite delay pauses between requests.
  - Safe to run on-demand or a few times per day.

---

## 🌟 Updated Features

1. **Strict Date Posted Sorting**:
   - All job posting dates and deadlines are normalized to standard ISO `YYYY-MM-DD`.
   - The jobs list is **strictly sorted by Date Posted (Latest to Oldest)**.
   - Includes a one-click toggle button to switch between *Latest First ↓* and *Oldest First ↑*.

2. **Top Bar Status Tabs & Cleaner Sidebar**:
   - Status filters are consolidated into the top bar: **All Jobs**, **New Matches**, **Saved**, **Applied**, **Expired**, and **Ignored** (with live count badges).
   - The redundant status filter dropdown in the sidebar has been removed for a cleaner view.

3. **Scraper Indicator & Rate Limit Hover Info**:
   - The top bar **"Scraper Ready"** indicator circle glows green when ready.
   - Hovering over the indicator displays exact timing details:
     - Last scrape time
     - Recommended next scrape time to respect official server limits.
   - When scraping is active, the indicator pulses amber with live progress text.

4. **Streamlined "Manage Skills" & Auto-Categorization**:
   - No need to manually guess or select categories or priority levels.
   - Simply enter a skill name (e.g. `Python`, `MySQL`, `React`, `Docker`, `Figma`) and choose whether it's a **⭐ Core Skill**.
   - The system **automatically assigns the category** (`Programming Language`, `Database`, `Framework & Web`, `DevOps & Cloud`, `Design & UI/UX`, `Testing & QA`, etc.).
   - Skills are neatly organized and displayed grouped by category with a `⭐ Core` tag.

5. **Resume Upload & Skill Auto-Extraction**:
   - Inside the **Manage Skills** modal, you can upload your resume (`.pdf`, `.docx`, or `.txt`).
   - The system locally scans your resume, detects technical skills you haven't added yet, and presents a checklist so you can add them to your profile with one click.
   - **100% Private**: Your resume never leaves your computer.

6. **Targeted CSV Export**:
   - The **Export CSV** button exports the currently filtered results.
   - Header is always included as the first row.
   - Contains only the exact requested columns:
     1. `Date posted`
     2. `Exact Job Title`
     3. `Company Name`
     4. `Location`
     5. `Application Deadline`
     6. `Direct Job url`

7. **Smart Deduplication & Workflow State Protection**:
   - **Save**: Changes status to `Saved` and records `saved_date`.
   - **Apply**: Changes status to `Applied` and records `applied_date`.
   - **Ignore**: Changes status to `Ignored`.
   - **Restore**: Restores any job back to `New`.
   - **Auto-Expiry**: Automatically marks jobs as `Expired` once their deadline passes. **Applied jobs are never changed automatically.**
   - Re-scraping updates `last_seen_date` without ever overwriting your saved status, applied dates, or manual notes.

---

## 🚀 How to Run

1. Open your terminal in this directory:
   ```bash
   cd /home/akhil/Desktop/Job_Search
   ```

2. Run the launcher script:
   ```bash
   chmod +x run.sh
   ./run.sh
   ```

3. Open your browser to:
   ```
   http://127.0.0.1:5000
   ```

---

## 🧪 Running Automated Tests

Run the full test suite at any time:
```bash
python3 -m unittest discover -s tests
```
