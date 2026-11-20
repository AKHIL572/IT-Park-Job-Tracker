import os
import io
import csv
import datetime
from flask import Flask, render_template, request, jsonify, send_file
from config import BASE_DIR, SOURCES
from database import (
    init_db, get_connection, upsert_job, update_job_status,
    update_job_notes, record_scrape_run, get_all_skills,
    add_skill, delete_skill, get_summary_counts, apply_auto_expiry,
    parse_date_to_standard, normalize_date_str
)
from skills_matcher import annotate_jobs_with_skills
from scrapers.runner import run_scrapers, start_background_scrape, get_scrape_state
from resume_parser import extract_text_from_file, extract_skills_from_text, auto_categorize_skill, TECH_SKILLS_CATALOG

app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static")
)

# Initialize database schema on startup
init_db()

def format_display_date(date_str: str) -> str:
    """Format any date string to DD-MM-YYYY for display."""
    if not date_str:
        return ""
    d = parse_date_to_standard(date_str)
    return d.strftime("%d-%m-%Y") if d else date_str

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/summary")
def api_summary():
    apply_auto_expiry()
    counts = get_summary_counts()

    # Calculate new matches count (active jobs with matching skills)
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT title FROM jobs WHERE status IN ('New', 'Saved')")
    rows = cursor.fetchall()
    conn.close()

    skills = get_all_skills()
    new_matches = 0
    from skills_matcher import match_skills_for_title
    for r in rows:
        level, matched = match_skills_for_title(r["title"], skills)
        if len(matched) > 0:
            new_matches += 1

    counts["new_matches"] = new_matches
    return jsonify(counts)

@app.route("/api/jobs")
def api_jobs():
    apply_auto_expiry()

    tab = request.args.get("tab", "all").strip().lower()
    source = request.args.get("source", "").strip()
    location = request.args.get("location", "").strip()
    deadline_filter = request.args.get("deadline", "").strip().lower()
    posted_filter = request.args.get("posted", "").strip().lower()
    skill_filter = request.args.get("skill_match", "").strip().lower()
    search = request.args.get("search", "").strip()
    sort_order = request.args.get("sort_order", "desc").strip().lower()

    page = max(1, int(request.args.get("page", 1)))
    per_page = max(5, min(100, int(request.args.get("per_page", 25))))

    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    # Tab handling
    if tab == "new_matches":
        query += " AND status IN ('New', 'Saved')"
    elif tab == "saved":
        query += " AND status = 'Saved'"
    elif tab == "applied":
        query += " AND status = 'Applied'"
    elif tab == "expired":
        query += " AND status = 'Expired'"
    elif tab == "ignored":
        query += " AND status = 'Ignored'"

    # Sidebar filters
    if source:
        query += " AND source_name LIKE ?"
        params.append(f"%{source}%")

    if location:
        query += " AND (location LIKE ? OR park_or_city LIKE ?)"
        params.extend([f"%{location}%", f"%{location}%"])

    if search:
        query += " AND (title LIKE ? OR company_name LIKE ? OR location LIKE ? OR notes LIKE ?)"
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    cursor.execute(query, params)
    raw_jobs = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Annotate skill matches
    skills_list = get_all_skills()
    annotated = annotate_jobs_with_skills(raw_jobs, skills_list)

    today = datetime.date.today()

    # In-memory filtering for dates & skills
    filtered = []
    for j in annotated:
        matched_count = len(j.get("matched_skills", []))

        if tab == "new_matches" and matched_count == 0:
            continue

        if skill_filter and skill_filter != "all":
            if skill_filter == "has_match" and matched_count == 0:
                continue
            elif skill_filter == "no_match" and matched_count > 0:
                continue
            elif skill_filter in ("high", "possible", "low"):
                if j["skill_match"].lower() != skill_filter:
                    continue

        # Deadline filter
        if deadline_filter and deadline_filter != "all":
            d_str = j.get("deadline", "")
            d_obj = parse_date_to_standard(d_str)
            if deadline_filter == "none":
                if d_obj is not None:
                    continue
            elif deadline_filter == "expired":
                if not d_obj or d_obj >= today:
                    continue
            elif deadline_filter == "week":
                if not d_obj or d_obj < today or (d_obj - today).days > 7:
                    continue
            elif deadline_filter == "month":
                if not d_obj or d_obj < today or (d_obj - today).days > 30:
                    continue

        # Posted filter
        if posted_filter and posted_filter != "all":
            p_str = j.get("date_posted", "")
            p_obj = parse_date_to_standard(p_str)
            if not p_obj:
                continue
            delta = (today - p_obj).days
            if posted_filter == "today" and delta > 0:
                continue
            elif posted_filter == "3days" and delta > 3:
                continue
            elif posted_filter == "7days" and delta > 7:
                continue
            elif posted_filter == "30days" and delta > 30:
                continue

        # Add display dates in DD-MM-YYYY format
        j["date_posted_display"] = format_display_date(j.get("date_posted", ""))
        j["deadline_display"] = format_display_date(j.get("deadline", ""))
        filtered.append(j)

    # STRICT SORTING: Exclusively based on Date Posted (latest to oldest)
    reverse = (sort_order != "asc")
    filtered.sort(
        key=lambda x: (x.get("date_posted") or "1970-01-01", x.get("id") or 0),
        reverse=reverse
    )

    total_count = len(filtered)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    page_items = filtered[start_idx:end_idx]
    total_pages = max(1, (total_count + per_page - 1) // per_page)

    return jsonify({
        "jobs": page_items,
        "total": total_count,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "sort_by": "date_posted",
        "sort_order": "desc" if reverse else "asc"
    })

@app.route("/api/jobs/<int:job_id>/status", methods=["POST"])
def api_update_status(job_id):
    data = request.get_json() or {}
    new_status = data.get("status")
    if not new_status:
        return jsonify({"error": "Status is required"}), 400

    updated = update_job_status(job_id, new_status)
    if not updated:
        return jsonify({"error": "Job not found"}), 404
    return jsonify({"success": True, "job": updated})

@app.route("/api/jobs/<int:job_id>/notes", methods=["POST"])
def api_update_notes(job_id):
    data = request.get_json() or {}
    notes = data.get("notes", "")
    update_job_notes(job_id, notes)
    return jsonify({"success": True, "notes": notes})

@app.route("/api/skills", methods=["GET", "POST"])
def api_skills():
    if request.method == "POST":
        data = request.get_json() or {}
        name = data.get("name", "").strip()
        is_core = bool(data.get("is_core", False))
        category = data.get("category")
        if not name:
            return jsonify({"error": "Skill name required"}), 400
        ok = add_skill(name, is_core=is_core, category=category)
        if not ok:
            return jsonify({"error": "Could not add skill"}), 400
        return jsonify({"success": True, "category": auto_categorize_skill(name)})
    else:
        return jsonify(get_all_skills())

@app.route("/api/skills/bulk-add", methods=["POST"])
def api_bulk_add_skills():
    data = request.get_json() or {}
    skills_to_add = data.get("skills", [])
    added = 0
    for s in skills_to_add:
        name = s.get("name", "").strip()
        is_core = bool(s.get("is_core", False))
        if name:
            if add_skill(name, is_core=is_core):
                added += 1
    return jsonify({"success": True, "added": added})

@app.route("/api/skills/extract-from-resume", methods=["POST"])
def api_extract_from_resume():
    if "resume" not in request.files:
        return jsonify({"error": "No resume file provided"}), 400
    file = request.files["resume"]
    if not file.filename:
        return jsonify({"error": "Empty filename"}), 400

    file_bytes = file.read()
    text = extract_text_from_file(file.filename, file_bytes)
    if not text:
        return jsonify({
            "error": "Could not extract text from file. Please ensure it is a valid PDF, DOCX, or TXT file."
        }), 400

    existing_skills = [s["name"] for s in get_all_skills()]
    extracted = extract_skills_from_text(text, existing_skills)

    return jsonify({
        "success": True,
        "filename": file.filename,
        "extracted": extracted,
        "total_extracted": len(extracted)
    })

@app.route("/api/skills/<int:skill_id>", methods=["DELETE"])
def api_delete_skill(skill_id):
    delete_skill(skill_id)
    return jsonify({"success": True})

@app.route("/api/scrape", methods=["POST"])
def api_trigger_scrape():
    data = request.get_json() or {}
    source = data.get("source")
    background = data.get("background", True)

    state = get_scrape_state()
    if state["is_running"]:
        return jsonify({"status": "busy", "message": "Scrape already running."})

    if background:
        start_background_scrape(source)
        return jsonify({"status": "started", "message": "Background scrape started."})
    else:
        summary = run_scrapers(source)
        return jsonify(summary)

@app.route("/api/scrape/status")
def api_scrape_status():
    state = get_scrape_state()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM scrape_runs ORDER BY id DESC LIMIT 5")
    runs = [dict(r) for r in cursor.fetchall()]
    conn.close()

    # Format run timestamps to DD-MM-YYYY HH:MM
    for r in runs:
        if r.get("run_time"):
            try:
                dt = datetime.datetime.strptime(r["run_time"], "%Y-%m-%d %H:%M:%S")
                r["run_time_display"] = dt.strftime("%d-%m-%Y %I:%M %p")
            except Exception:
                r["run_time_display"] = r["run_time"]

    return jsonify({
        "state": state,
        "recent_runs": runs
    })

@app.route("/api/stats")
def api_stats():
    """Provides actionable aggregations and in-demand skills analytics for the Profile Hub."""
    apply_auto_expiry()
    conn = get_connection()
    cursor = conn.cursor()

    # 1. Jobs by IT park source
    cursor.execute("SELECT source_name, COUNT(*) FROM jobs GROUP BY source_name")
    by_source = {r[0]: r[1] for r in cursor.fetchall()}

    # 2. Status Breakdown
    cursor.execute("SELECT status, COUNT(*) FROM jobs GROUP BY status")
    status_breakdown = {r[0]: r[1] for r in cursor.fetchall()}

    # 3. Top In-Demand Skills in Current Job Openings
    cursor.execute("SELECT title FROM jobs")
    all_titles = [r[0].lower() for r in cursor.fetchall()]

    import re
    skill_counts = {}
    for skill_name in TECH_SKILLS_CATALOG.keys():
        low = skill_name.lower()
        if re.search(r'[#\+\.]', skill_name):
            pattern = rf'(?:^|[\s,/\-\(\)\[\]]){re.escape(low)}(?:$|[\s,/\-\(\)\[\]])'
        else:
            pattern = rf'\b{re.escape(low)}\b'

        count = sum(1 for t in all_titles if re.search(pattern, t))
        if count > 0:
            skill_counts[skill_name] = count

    # Top 10 in-demand skills sorted by frequency
    sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)[:10]
    in_demand_skills = [{"skill": s[0], "count": s[1]} for s in sorted_skills]

    # 4. Recent applied jobs
    cursor.execute("""
        SELECT id, title, company_name, source_name, applied_date, job_url 
        FROM jobs WHERE status = 'Applied' 
        ORDER BY applied_date DESC LIMIT 15
    """)
    recent_applied = []
    for r in cursor.fetchall():
        item = dict(r)
        if item.get("applied_date"):
            try:
                dt = datetime.datetime.strptime(item["applied_date"], "%Y-%m-%d %H:%M:%S")
                item["applied_date_display"] = dt.strftime("%d-%m-%Y")
            except Exception:
                item["applied_date_display"] = item["applied_date"][:10]
        recent_applied.append(item)

    # 5. Recent Scraper runs
    cursor.execute("SELECT * FROM scrape_runs ORDER BY id DESC LIMIT 10")
    recent_runs = []
    for r in cursor.fetchall():
        item = dict(r)
        if item.get("run_time"):
            try:
                dt = datetime.datetime.strptime(item["run_time"], "%Y-%m-%d %H:%M:%S")
                item["run_time_display"] = dt.strftime("%d-%m-%Y %I:%M %p")
            except Exception:
                item["run_time_display"] = item["run_time"]
        recent_runs.append(item)

    counts = get_summary_counts()
    conn.close()

    return jsonify({
        "by_source": by_source,
        "status_breakdown": status_breakdown,
        "in_demand_skills": in_demand_skills,
        "recent_applied": recent_applied,
        "recent_runs": recent_runs,
        "summary": counts
    })

@app.route("/export/csv")
def export_csv():
    """
    Export CSV containing:
    - First row as header
    - Only the columns: Date posted, Exact Job Title, Company Name, Location, Application Deadline, Direct Job url
    - Dates formatted as DD-MM-YYYY
    """
    tab = request.args.get("tab", "all").strip().lower()
    source = request.args.get("source", "").strip()
    location = request.args.get("location", "").strip()
    deadline_filter = request.args.get("deadline", "").strip().lower()
    posted_filter = request.args.get("posted", "").strip().lower()
    skill_filter = request.args.get("skill_match", "").strip().lower()
    search = request.args.get("search", "").strip()
    sort_order = request.args.get("sort_order", "desc").strip().lower()

    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM jobs WHERE 1=1"
    params = []

    if tab == "new_matches":
        query += " AND status IN ('New', 'Saved')"
    elif tab == "saved":
        query += " AND status = 'Saved'"
    elif tab == "applied":
        query += " AND status = 'Applied'"
    elif tab == "expired":
        query += " AND status = 'Expired'"
    elif tab == "ignored":
        query += " AND status = 'Ignored'"

    if source:
        query += " AND source_name LIKE ?"
        params.append(f"%{source}%")
    if location:
        query += " AND (location LIKE ? OR park_or_city LIKE ?)"
        params.extend([f"%{location}%", f"%{location}%"])
    if search:
        query += " AND (title LIKE ? OR company_name LIKE ? OR location LIKE ? OR notes LIKE ?)"
        search_pattern = f"%{search}%"
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    cursor.execute(query, params)
    raw_jobs = [dict(r) for r in cursor.fetchall()]
    conn.close()

    skills_list = get_all_skills()
    annotated = annotate_jobs_with_skills(raw_jobs, skills_list)
    today = datetime.date.today()

    filtered = []
    for j in annotated:
        matched_count = len(j.get("matched_skills", []))
        if tab == "new_matches" and matched_count == 0:
            continue
        if skill_filter and skill_filter != "all":
            if skill_filter == "has_match" and matched_count == 0:
                continue
            elif skill_filter == "no_match" and matched_count > 0:
                continue
            elif skill_filter in ("high", "possible", "low"):
                if j["skill_match"].lower() != skill_filter:
                    continue

        if deadline_filter and deadline_filter != "all":
            d_obj = parse_date_to_standard(j.get("deadline"))
            if deadline_filter == "none" and d_obj is not None:
                continue
            elif deadline_filter == "expired" and (not d_obj or d_obj >= today):
                continue
            elif deadline_filter == "week" and (not d_obj or d_obj < today or (d_obj - today).days > 7):
                continue
            elif deadline_filter == "month" and (not d_obj or d_obj < today or (d_obj - today).days > 30):
                continue

        if posted_filter and posted_filter != "all":
            p_obj = parse_date_to_standard(j.get("date_posted"))
            if not p_obj:
                continue
            delta = (today - p_obj).days
            if posted_filter == "today" and delta > 0:
                continue
            elif posted_filter == "3days" and delta > 3:
                continue
            elif posted_filter == "7days" and delta > 7:
                continue
            elif posted_filter == "30days" and delta > 30:
                continue

        filtered.append(j)

    # Sort strictly by date posted
    reverse = (sort_order != "asc")
    filtered.sort(
        key=lambda x: (x.get("date_posted") or "1970-01-01", x.get("id") or 0),
        reverse=reverse
    )

    # Generate CSV with EXACT columns requested:
    # "Date posted, Exact Job Title, Company Name, Location, Application Deadline, then Direct Job url (as Link)"
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Date posted",
        "Exact Job Title",
        "Company Name",
        "Location",
        "Application Deadline",
        "Direct Job url"
    ])

    for item in filtered:
        writer.writerow([
            format_display_date(item.get("date_posted", "")),
            item.get("title", ""),
            item.get("company_name", ""),
            item.get("location", ""),
            format_display_date(item.get("deadline", "")),
            item.get("job_url", "")
        ])

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"jobs_export_{timestamp}.csv"
    mem_file = io.BytesIO()
    mem_file.write(output.getvalue().encode('utf-8'))
    mem_file.seek(0)

    return send_file(
        mem_file,
        mimetype="text/csv",
        as_attachment=True,
        download_name=filename
    )

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
