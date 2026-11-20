// Kerala IT Parks Job Tracker - Clean SaaS Frontend Application
document.addEventListener("DOMContentLoaded", () => {
    // State
    const state = {
        tab: "all",
        page: 1,
        perPage: 25,
        sortOrder: "desc", // Latest date posted first
        search: "",
        source: "",
        location: "",
        skillMatch: "all",
        deadline: "all",
        posted: "all",
        activeJobForNotes: null,
        scrapeInterval: null,
        charts: {},
        extractedResumeSkills: []
    };

    // DOM Elements
    const elements = {
        tbody: document.getElementById("jobs-tbody"),
        lblShowing: document.getElementById("lbl-showing-count"),
        currentPageNum: document.getElementById("current-page-num"),
        totalPagesNum: document.getElementById("total-pages-num"),
        btnPrevPage: document.getElementById("btn-prev-page"),
        btnNextPage: document.getElementById("btn-next-page"),
        btnToggleSortOrder: document.getElementById("btn-toggle-sort-order"),
        sortOrderText: document.getElementById("sort-order-text"),
        filterSearch: document.getElementById("filter-search"),
        filterSource: document.getElementById("filter-source"),
        filterLocation: document.getElementById("filter-location"),
        filterSkillMatch: document.getElementById("filter-skill-match"),
        filterDeadline: document.getElementById("filter-deadline"),
        filterPosted: document.getElementById("filter-posted"),
        btnResetFilters: document.getElementById("btn-reset-filters"),
        btnManualRefresh: document.getElementById("btn-manual-refresh"),
        btnExportCsv: document.getElementById("btn-export-csv"),
        btnOpenProfile: document.getElementById("btn-open-profile"),
        scrapeStatusText: document.getElementById("scrape-status-text"),
        scrapeStatusIndicator: document.getElementById("scrape-status-indicator"),

        // Navigation Tabs Count Badges
        badgeAll: document.getElementById("tab-badge-all"),
        badgeMatches: document.getElementById("tab-badge-matches"),
        badgeSaved: document.getElementById("tab-badge-saved"),
        badgeApplied: document.getElementById("tab-badge-applied"),
        badgeExpired: document.getElementById("tab-badge-expired"),
        badgeIgnored: document.getElementById("tab-badge-ignored"),

        // Profile Hub Elements
        modalProfile: document.getElementById("modal-profile"),
        btnCloseProfile: document.getElementById("btn-close-profile"),
        btnDoneProfile: document.getElementById("btn-done-profile"),
        pkpiTotal: document.getElementById("pkpi-total"),
        pkpiMatches: document.getElementById("pkpi-matches"),
        pkpiSaved: document.getElementById("pkpi-saved"),
        pkpiApplied: document.getElementById("pkpi-applied"),
        pkpiExpired: document.getElementById("pkpi-expired"),
        pkpiIgnored: document.getElementById("pkpi-ignored"),
        skillsCategorizedWrapper: document.getElementById("skills-categorized-wrapper"),
        inputNewSkill: document.getElementById("input-new-skill"),
        checkIsCore: document.getElementById("check-is-core"),
        btnAddSkill: document.getElementById("btn-add-skill"),
        resumeFileInput: document.getElementById("resume-file-input"),
        btnSelectResume: document.getElementById("btn-select-resume"),
        selectedResumeName: document.getElementById("selected-resume-name"),
        btnUploadResume: document.getElementById("btn-upload-resume"),
        resumeExtractedContainer: document.getElementById("resume-extracted-container"),
        extractedCountLbl: document.getElementById("extracted-count-lbl"),
        extractedSkillsList: document.getElementById("extracted-skills-list"),
        btnAddAllExtracted: document.getElementById("btn-add-all-extracted"),
        tableRecentApplied: document.querySelector("#table-recent-applied tbody"),
        scrapeRunsContainer: document.getElementById("scrape-runs-container"),

        // Notes Modal
        modalNotes: document.getElementById("modal-notes"),
        notesTextarea: document.getElementById("notes-textarea"),
        notesModalTitle: document.getElementById("notes-modal-title"),
        btnSaveNotes: document.getElementById("btn-save-notes"),
        btnCancelNotes: document.getElementById("btn-cancel-notes"),
        btnCloseNotes: document.getElementById("btn-close-notes"),

        toast: document.getElementById("toast")
    };

    // Standard Clean Inline SVG Icons
    const ICONS = {
        externalLink: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>`,
        save: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m19 21-7-4-7 4V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2v16z"/></svg>`,
        apply: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>`,
        ignore: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" y1="2" x2="22" y2="22"/></svg>`,
        restore: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="1 4 1 10 7 10"/><path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/></svg>`,
        notes: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>`
    };

    // Helper: Toast message
    function showToast(message) {
        elements.toast.textContent = message;
        elements.toast.classList.add("show");
        setTimeout(() => {
            elements.toast.classList.remove("show");
        }, 3000);
    }

    // Helper: Debounce
    function debounce(func, delay = 300) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func(...args), delay);
        };
    }

    function escapeHtml(text) {
        if (!text) return "";
        return String(text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    // Fetch Scraper Status & Rate Limit Timing for Hover Tooltip
    async function checkScraperStatus() {
        try {
            const res = await fetch("/api/scrape/status");
            if (!res.ok) return;
            const data = await res.json();
            const state = data.state || {};

            if (state.is_running) {
                elements.scrapeStatusIndicator.className = "status-indicator running";
                elements.scrapeStatusText.textContent = state.current_source ? `Scraping ${state.current_source}...` : "Scraping...";
                elements.scrapeStatusIndicator.title = "Scrape currently active in background. Please wait...";
            } else {
                elements.scrapeStatusIndicator.className = "status-indicator ready";
                elements.scrapeStatusText.textContent = "Scraper Ready";

                let tooltip = "Scraper ready to check official IT park boards.";
                if (state.last_run_time_str) {
                    tooltip += `\n• Last run: ${state.last_run_time_str}`;
                }
                if (state.can_run_recommendation) {
                    tooltip += `\n• Status: ${state.can_run_recommendation}`;
                }
                tooltip += "\n• Respects rate limits & polite delays.";
                elements.scrapeStatusIndicator.title = tooltip;
            }
        } catch (e) {
            console.error("Error checking scraper status:", e);
        }
    }

    // Fetch Summary Counts for Top Navigation Tabs
    async function fetchSummary() {
        try {
            const res = await fetch("/api/summary");
            if (!res.ok) return;
            const data = await res.json();

            // Tab Badges
            elements.badgeAll.textContent = data.total || 0;
            elements.badgeMatches.textContent = data.new_matches || 0;
            elements.badgeSaved.textContent = data.saved || 0;
            elements.badgeApplied.textContent = data.applied || 0;
            elements.badgeExpired.textContent = data.expired || 0;
            elements.badgeIgnored.textContent = data.ignored || 0;

            // Profile Hub KPI stats
            if (elements.pkpiTotal) elements.pkpiTotal.textContent = data.total || 0;
            if (elements.pkpiMatches) elements.pkpiMatches.textContent = data.new_matches || 0;
            if (elements.pkpiSaved) elements.pkpiSaved.textContent = data.saved || 0;
            if (elements.pkpiApplied) elements.pkpiApplied.textContent = data.applied || 0;
            if (elements.pkpiExpired) elements.pkpiExpired.textContent = data.expired || 0;
            if (elements.pkpiIgnored) elements.pkpiIgnored.textContent = data.ignored || 0;

            checkScraperStatus();
        } catch (e) {
            console.error("Error fetching summary:", e);
        }
    }

    // Build URL Query Params for Jobs
    function buildQueryParams() {
        const params = new URLSearchParams();
        params.set("tab", state.tab);
        params.set("page", state.page);
        params.set("per_page", state.perPage);
        // STRICT SORTING: always by Date Posted
        params.set("sort_order", state.sortOrder);

        if (state.search) params.set("search", state.search);
        if (state.source) params.set("source", state.source);
        if (state.location) params.set("location", state.location);
        if (state.skillMatch && state.skillMatch !== "all") params.set("skill_match", state.skillMatch);
        if (state.deadline && state.deadline !== "all") params.set("deadline", state.deadline);
        if (state.posted && state.posted !== "all") params.set("posted", state.posted);

        return params.toString();
    }

    // Fetch and Render Jobs Table
    async function loadJobs() {
        elements.tbody.innerHTML = `<tr><td colspan="8" class="table-loading-cell">Loading jobs...</td></tr>`;

        try {
            const query = buildQueryParams();
            const res = await fetch(`/api/jobs?${query}`);
            if (!res.ok) throw new Error("Failed to load jobs");
            const data = await res.json();

            renderTable(data.jobs);
            elements.lblShowing.textContent = data.total;
            elements.currentPageNum.textContent = data.page;
            elements.totalPagesNum.textContent = data.total_pages;

            elements.btnPrevPage.disabled = data.page <= 1;
            elements.btnNextPage.disabled = data.page >= data.total_pages;

            fetchSummary();
        } catch (err) {
            console.error(err);
            elements.tbody.innerHTML = `<tr><td colspan="8" class="table-loading-cell">Error loading jobs. Please try refreshing.</td></tr>`;
        }
    }

    // Render HTML Rows (With Matched Skills Chips & Standard SVG Action Buttons)
    function renderTable(jobs) {
        if (!jobs || jobs.length === 0) {
            elements.tbody.innerHTML = `
                <tr>
                    <td colspan="8" class="table-loading-cell" style="padding: 3rem 1rem;">
                        <strong style="color: var(--text-heading); font-size: 0.95rem;">No jobs found matching your criteria.</strong>
                        <p class="text-muted" style="font-size: 0.8rem; margin-top: 0.35rem;">Try adjusting your sidebar filters or click "Refresh" to scrape the latest openings.</p>
                    </td>
                </tr>
            `;
            return;
        }

        const rowsHtml = jobs.map(j => {
            const statusClass = (j.status || "new").toLowerCase();

            // Render Exact Matched Skills Chips (instead of generic Low/High)
            let matchedSkillsHtml = "";
            const matchedList = j.matched_skills || [];
            const isHighMatch = j.skill_match === "High";

            if (matchedList.length > 0) {
                matchedSkillsHtml = `<div class="matched-skills-cell">` +
                    matchedList.slice(0, 3).map(s => `<span class="tech-chip ${isHighMatch ? 'core-match' : ''}">${escapeHtml(s)}</span>`).join("") +
                    (matchedList.length > 3 ? `<span class="tech-chip">+${matchedList.length - 3}</span>` : "") +
                    `</div>`;
            } else {
                matchedSkillsHtml = `<span class="no-match-text">—</span>`;
            }

            // Action buttons using clean SVG icons with tooltips
            let actionButtons = "";
            const isApplied = j.status === "Applied";
            const isSaved = j.status === "Saved";
            const isExpired = j.status === "Expired";
            const isIgnored = j.status === "Ignored";

            // Save icon button
            if (!isSaved && !isApplied) {
                actionButtons += `<button class="btn-row-action act-save" data-action="save" data-id="${j.id}" title="Save Job">${ICONS.save}</button>`;
            }

            // Apply icon button
            if (!isApplied) {
                actionButtons += `<button class="btn-row-action act-apply" data-action="apply" data-id="${j.id}" title="Mark as Applied">${ICONS.apply}</button>`;
            }

            // Restore icon button
            if (isSaved || isApplied || isExpired || isIgnored) {
                actionButtons += `<button class="btn-row-action act-restore" data-action="restore" data-id="${j.id}" title="Restore to Active">${ICONS.restore}</button>`;
            }

            // Ignore icon button
            if (!isIgnored && !isApplied) {
                actionButtons += `<button class="btn-row-action act-ignore" data-action="ignore" data-id="${j.id}" title="Ignore / Hide">${ICONS.ignore}</button>`;
            }

            // Notes icon button
            const hasNotes = !!(j.notes && j.notes.trim());
            actionButtons += `<button class="btn-row-action act-notes ${hasNotes ? 'has-notes' : ''}" data-action="notes" data-id="${j.id}" title="${hasNotes ? 'View / Edit Notes' : 'Add Note'}">${ICONS.notes}</button>`;

            // Display dates formatted in DD-MM-YYYY
            const postedDisplay = j.date_posted_display || j.date_posted || "-";
            const deadlineDisplay = j.deadline_display || (j.deadline ? j.deadline : "—");

            return `
                <tr data-job-id="${j.id}">
                    <td>
                        <a href="${escapeHtml(j.job_url)}" target="_blank" rel="noopener noreferrer" class="job-title-link">
                            <span>${escapeHtml(j.title)}</span>
                            ${ICONS.externalLink}
                        </a>
                    </td>
                    <td>
                        <span class="company-title">${escapeHtml(j.company_name || 'N/A')}</span>
                    </td>
                    <td>
                        <span class="source-badge">${escapeHtml(j.source_name)}</span>
                        <div class="location-subtext">${escapeHtml(j.location || j.park_or_city || '')}</div>
                    </td>
                    <td><span class="date-text">${escapeHtml(postedDisplay)}</span></td>
                    <td>
                        <span class="date-text" style="${isExpired ? 'color: var(--color-rose); font-weight: 600;' : ''}">
                            ${escapeHtml(deadlineDisplay)}
                        </span>
                    </td>
                    <td>${matchedSkillsHtml}</td>
                    <td>
                        <span class="status-pill ${statusClass}">${j.status}</span>
                    </td>
                    <td class="col-actions">
                        <div class="row-actions-group">
                            ${actionButtons}
                        </div>
                    </td>
                </tr>
            `;
        }).join("");

        elements.tbody.innerHTML = rowsHtml;
    }

    // Action clicks (Event Delegation)
    elements.tbody.addEventListener("click", async (e) => {
        const btn = e.target.closest(".btn-row-action");
        if (!btn) return;

        const action = btn.dataset.action;
        const jobId = btn.dataset.id;
        if (!jobId) return;

        if (action === "save") {
            await updateStatus(jobId, "Saved");
        } else if (action === "apply") {
            await updateStatus(jobId, "Applied");
        } else if (action === "ignore") {
            await updateStatus(jobId, "Ignored");
        } else if (action === "restore") {
            await updateStatus(jobId, "New");
        } else if (action === "notes") {
            openNotesModal(jobId);
        }
    });

    async function updateStatus(jobId, newStatus) {
        try {
            const res = await fetch(`/api/jobs/${jobId}/status`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ status: newStatus })
            });
            if (!res.ok) throw new Error("Failed to update status");
            showToast(`Status updated to ${newStatus}`);
            loadJobs();
        } catch (e) {
            console.error(e);
            showToast("Error updating job status.");
        }
    }

    // Toggle Sort Order (Latest First vs Oldest First)
    elements.btnToggleSortOrder.addEventListener("click", () => {
        if (state.sortOrder === "desc") {
            state.sortOrder = "asc";
            elements.sortOrderText.textContent = "Oldest First ↑";
        } else {
            state.sortOrder = "desc";
            elements.sortOrderText.textContent = "Latest First ↓";
        }
        state.page = 1;
        loadJobs();
    });

    // Notes Modal
    async function openNotesModal(jobId) {
        state.activeJobForNotes = jobId;
        elements.notesTextarea.value = "Loading notes...";
        elements.modalNotes.classList.add("open");

        try {
            const row = document.querySelector(`tr[data-job-id="${jobId}"]`);
            const title = row ? row.querySelector(".job-title-link span").textContent.trim() : `Job #${jobId}`;
            elements.notesModalTitle.textContent = `Notes: ${title}`;

            const res = await fetch(`/api/jobs?search=&tab=all&page=1&per_page=100`);
            const data = await res.json();
            const job = data.jobs.find(j => j.id == jobId);
            elements.notesTextarea.value = (job && job.notes) ? job.notes : "";
        } catch (e) {
            elements.notesTextarea.value = "";
        }
    }

    elements.btnSaveNotes.addEventListener("click", async () => {
        if (!state.activeJobForNotes) return;
        const notes = elements.notesTextarea.value;
        try {
            const res = await fetch(`/api/jobs/${state.activeJobForNotes}/notes`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ notes })
            });
            if (!res.ok) throw new Error("Failed to save notes");
            showToast("Notes saved.");
            elements.modalNotes.classList.remove("open");
            loadJobs();
        } catch (e) {
            showToast("Error saving notes.");
        }
    });

    elements.btnCancelNotes.addEventListener("click", () => elements.modalNotes.classList.remove("open"));
    elements.btnCloseNotes.addEventListener("click", () => elements.modalNotes.classList.remove("open"));

    // Profile Hub Modal
    elements.btnOpenProfile.addEventListener("click", () => {
        elements.modalProfile.classList.add("open");
        loadProfileAnalytics();
        loadSkillsList();
    });

    elements.btnCloseProfile.addEventListener("click", () => elements.modalProfile.classList.remove("open"));
    elements.btnDoneProfile.addEventListener("click", () => {
        elements.modalProfile.classList.remove("open");
        loadJobs();
    });

    // Profile Internal Tab Switching
    document.querySelectorAll(".profile-tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".profile-tab-btn").forEach(b => b.classList.remove("active"));
            document.querySelectorAll(".profile-tab-content").forEach(c => c.classList.remove("active"));

            btn.classList.add("active");
            const targetId = `ptab-${btn.dataset.ptab}`;
            const targetContent = document.getElementById(targetId);
            if (targetContent) targetContent.classList.add("active");

            if (btn.dataset.ptab === "analytics") {
                loadProfileAnalytics();
            } else if (btn.dataset.ptab === "skills") {
                loadSkillsList();
            }
        });
    });

    // Load Profile Hub Analytics & Animated Charts
    async function loadProfileAnalytics() {
        try {
            const res = await fetch("/api/stats");
            const data = await res.json();

            // Populate KPIs
            const s = data.summary || {};
            if (elements.pkpiTotal) elements.pkpiTotal.textContent = s.total || 0;
            if (elements.pkpiMatches) elements.pkpiMatches.textContent = s.new_matches || 0;
            if (elements.pkpiSaved) elements.pkpiSaved.textContent = s.saved || 0;
            if (elements.pkpiApplied) elements.pkpiApplied.textContent = s.applied || 0;
            if (elements.pkpiExpired) elements.pkpiExpired.textContent = s.expired || 0;
            if (elements.pkpiIgnored) elements.pkpiIgnored.textContent = s.ignored || 0;

            renderProfileCharts(data);
            renderAppliedLog(data.recent_applied || []);
            renderScraperHistory(data.recent_runs || []);
        } catch (e) {
            console.error("Profile analytics err:", e);
        }
    }

    function renderProfileCharts(data) {
        if (typeof Chart === "undefined") return;

        // Chart 1: Jobs by IT Park Source (Animated Doughnut with Numbers in Tooltip/Legend)
        const ctxSource = document.getElementById("chart-by-source");
        if (ctxSource) {
            if (state.charts.source) state.charts.source.destroy();
            const sourceKeys = Object.keys(data.by_source || {});
            const sourceVals = Object.values(data.by_source || {});
            const totalJobs = sourceVals.reduce((a, b) => a + b, 0);

            // Labels with exact numbers
            const formattedLabels = sourceKeys.map((k, idx) => {
                const count = sourceVals[idx];
                const pct = totalJobs ? Math.round((count / totalJobs) * 100) : 0;
                return `${k}: ${count} (${pct}%)`;
            });

            state.charts.source = new Chart(ctxSource, {
                type: "doughnut",
                data: {
                    labels: formattedLabels,
                    datasets: [{
                        data: sourceVals,
                        backgroundColor: ["#2563eb", "#10b981", "#8b5cf6", "#f59e0b", "#64748b"],
                        borderWidth: 2,
                        borderColor: "#ffffff"
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        animateScale: true,
                        animateRotate: true,
                        duration: 900,
                        easing: "easeOutQuart"
                    },
                    plugins: {
                        legend: { position: "bottom", labels: { boxWidth: 12, font: { size: 11 } } },
                        tooltip: {
                            callbacks: {
                                label: (ctx) => ` ${ctx.label}`
                            }
                        }
                    }
                }
            });
        }

        // Chart 2: Top In-Demand Skills in Current Openings (Animated Horizontal Bar)
        const ctxDemand = document.getElementById("chart-in-demand");
        if (ctxDemand) {
            if (state.charts.demand) state.charts.demand.destroy();
            const inDemand = data.in_demand_skills || [];
            const skillLabels = inDemand.map(item => item.skill);
            const skillCounts = inDemand.map(item => item.count);

            state.charts.demand = new Chart(ctxDemand, {
                type: "bar",
                data: {
                    labels: skillLabels,
                    datasets: [{
                        label: "Openings Requesting Skill",
                        data: skillCounts,
                        backgroundColor: "#3b82f6",
                        borderRadius: 4
                    }]
                },
                options: {
                    indexAxis: "y",
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: {
                        duration: 900,
                        easing: "easeOutQuart"
                    },
                    scales: {
                        x: { beginAtZero: true, grid: { color: "#f1f5f9" } },
                        y: { grid: { display: false }, ticks: { font: { size: 11 } } }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        }

        // Chart 3: Pipeline Status Breakdown
        const ctxStatus = document.getElementById("chart-status-breakdown");
        if (ctxStatus) {
            if (state.charts.status) state.charts.status.destroy();
            const statusMap = data.status_breakdown || {};
            const labels = ["New", "Saved", "Applied", "Expired", "Ignored"];
            const values = labels.map(l => statusMap[l] || 0);

            state.charts.status = new Chart(ctxStatus, {
                type: "bar",
                data: {
                    labels: labels,
                    datasets: [{
                        label: "Jobs",
                        data: values,
                        backgroundColor: ["#3b82f6", "#8b5cf6", "#10b981", "#ef4444", "#94a3b8"],
                        borderRadius: 4
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    animation: { duration: 900, easing: "easeOutQuart" },
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: "#f1f5f9" } },
                        x: { grid: { display: false } }
                    }
                }
            });
        }
    }

    function renderAppliedLog(list) {
        if (!elements.tableRecentApplied) return;
        if (!list || list.length === 0) {
            elements.tableRecentApplied.innerHTML = `<tr><td colspan="5" class="text-center text-muted" style="padding: 1.5rem;">No applied jobs yet. Click the send icon on any job card to record an application.</td></tr>`;
            return;
        }

        elements.tableRecentApplied.innerHTML = list.map(item => `
            <tr>
                <td><strong>${escapeHtml(item.title)}</strong></td>
                <td>${escapeHtml(item.company_name || 'N/A')}</td>
                <td><span class="source-badge">${escapeHtml(item.source_name)}</span></td>
                <td><span class="date-text">${escapeHtml(item.applied_date_display || '-')}</span></td>
                <td>
                    <a href="${escapeHtml(item.job_url)}" target="_blank" rel="noopener noreferrer" class="job-title-link">
                        ${ICONS.externalLink}
                    </a>
                </td>
            </tr>
        `).join("");
    }

    function renderScraperHistory(runs) {
        if (!elements.scrapeRunsContainer) return;
        if (!runs || runs.length === 0) {
            elements.scrapeRunsContainer.innerHTML = `<em>No scraper runs recorded yet.</em>`;
            return;
        }

        elements.scrapeRunsContainer.innerHTML = runs.map(r => `
            <div class="scrape-history-item">
                <div>
                    <strong>${escapeHtml(r.source_name)}</strong>
                    <div class="scrape-history-meta">${escapeHtml(r.run_time_display || r.run_time)} • Found: ${r.jobs_found} • New: ${r.new_jobs}</div>
                </div>
                <span class="status-pill ${r.status === 'success' ? 'applied' : 'expired'}">
                    ${r.status}
                </span>
            </div>
        `).join("");
    }

    // Skills Management: Load & Group
    async function loadSkillsList() {
        if (!elements.skillsCategorizedWrapper) return;
        elements.skillsCategorizedWrapper.innerHTML = `<em>Loading skills...</em>`;
        try {
            const res = await fetch("/api/skills");
            const skills = await res.json();

            if (skills.length === 0) {
                elements.skillsCategorizedWrapper.innerHTML = `<em>No skills configured. Add your first skill above or scan a resume!</em>`;
                return;
            }

            const grouped = {};
            for (const s of skills) {
                const cat = s.category || "General";
                if (!grouped[cat]) grouped[cat] = [];
                grouped[cat].push(s);
            }

            let html = "";
            for (const [catName, skillItems] of Object.entries(grouped)) {
                html += `
                    <div class="category-block">
                        <div class="category-block-title">${escapeHtml(catName)} (${skillItems.length})</div>
                        <div class="category-chips-flow">
                            ${skillItems.map(s => `
                                <div class="profile-skill-chip ${s.is_core ? 'core' : ''}">
                                    ${s.is_core ? '<span title="Core Skill" style="color: #059669;">●</span>' : ''}
                                    <span>${escapeHtml(s.name)}</span>
                                    <button class="btn-remove-skill" data-id="${s.id}" title="Remove skill">✕</button>
                                </div>
                            `).join("")}
                        </div>
                    </div>
                `;
            }

            elements.skillsCategorizedWrapper.innerHTML = html;
        } catch (e) {
            elements.skillsCategorizedWrapper.innerHTML = `<em>Failed to load skills.</em>`;
        }
    }

    // Add Skill (with Auto-categorization)
    elements.btnAddSkill.addEventListener("click", async () => {
        const name = elements.inputNewSkill.value.trim();
        const is_core = elements.checkIsCore.checked;
        if (!name) return;

        try {
            const res = await fetch("/api/skills", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ name, is_core })
            });
            if (!res.ok) {
                const err = await res.json();
                showToast(err.error || "Error adding skill.");
                return;
            }
            const data = await res.json();
            elements.inputNewSkill.value = "";
            elements.checkIsCore.checked = false;
            showToast(`Added '${name}' (${data.category})`);
            loadSkillsList();
        } catch (e) {
            showToast("Error adding skill.");
        }
    });

    // Delete Skill Click
    elements.skillsCategorizedWrapper.addEventListener("click", async (e) => {
        const delBtn = e.target.closest(".btn-remove-skill");
        if (!delBtn) return;
        const id = delBtn.dataset.id;
        try {
            await fetch(`/api/skills/${id}`, { method: "DELETE" });
            loadSkillsList();
        } catch (e) {
            showToast("Error removing skill.");
        }
    });

    // Resume Upload & Extraction Handlers
    elements.btnSelectResume.addEventListener("click", () => {
        elements.resumeFileInput.click();
    });

    elements.resumeFileInput.addEventListener("change", () => {
        const file = elements.resumeFileInput.files[0];
        if (file) {
            elements.selectedResumeName.textContent = file.name;
            elements.btnUploadResume.style.display = "inline-flex";
        } else {
            elements.selectedResumeName.textContent = "No file selected";
            elements.btnUploadResume.style.display = "none";
        }
    });

    elements.btnUploadResume.addEventListener("click", async () => {
        const file = elements.resumeFileInput.files[0];
        if (!file) return;

        elements.btnUploadResume.disabled = true;
        elements.btnUploadResume.textContent = "Extracting...";
        showToast("Scanning resume for technical skills...");

        const formData = new FormData();
        formData.append("resume", file);

        try {
            const res = await fetch("/api/skills/extract-from-resume", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            elements.btnUploadResume.disabled = false;
            elements.btnUploadResume.textContent = "Extract Skills";

            if (!res.ok) {
                showToast(data.error || "Failed to scan resume.");
                return;
            }

            state.extractedResumeSkills = data.extracted || [];
            if (state.extractedResumeSkills.length === 0) {
                showToast("No new skills detected.");
                elements.resumeExtractedContainer.style.display = "none";
                return;
            }

            elements.extractedCountLbl.innerHTML = `<strong>${state.extractedResumeSkills.length}</strong> skills detected:`;
            elements.extractedSkillsList.innerHTML = state.extractedResumeSkills.map((s, idx) => `
                <label class="chk-skill-label">
                    <input type="checkbox" class="chk-extracted-skill" data-idx="${idx}" checked>
                    <span>${escapeHtml(s.name)}</span>
                    <small style="color: #64748b;">(${escapeHtml(s.category)})</small>
                </label>
            `).join("");

            elements.resumeExtractedContainer.style.display = "block";
            showToast(`Found ${state.extractedResumeSkills.length} skills in resume!`);
        } catch (e) {
            elements.btnUploadResume.disabled = false;
            elements.btnUploadResume.textContent = "Extract Skills";
            showToast("Error processing resume.");
        }
    });

    elements.btnAddAllExtracted.addEventListener("click", async () => {
        const checkedInputs = elements.extractedSkillsList.querySelectorAll(".chk-extracted-skill:checked");
        if (checkedInputs.length === 0) {
            showToast("Please select at least one skill.");
            return;
        }

        const selectedSkills = [];
        checkedInputs.forEach(input => {
            const idx = parseInt(input.dataset.idx, 10);
            if (state.extractedResumeSkills[idx]) {
                selectedSkills.push(state.extractedResumeSkills[idx]);
            }
        });

        try {
            const res = await fetch("/api/skills/bulk-add", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ skills: selectedSkills })
            });
            const data = await res.json();
            showToast(`Added ${data.added || selectedSkills.length} skills to profile!`);
            elements.resumeExtractedContainer.style.display = "none";
            elements.resumeFileInput.value = "";
            elements.selectedResumeName.textContent = "No file selected";
            elements.btnUploadResume.style.display = "none";
            loadSkillsList();
        } catch (e) {
            showToast("Error adding extracted skills.");
        }
    });

    // Top Navigation Tabs (All Jobs, New Matches, Saved, Applied, Expired, Ignored)
    document.querySelectorAll(".nav-tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".nav-tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");

            state.tab = btn.dataset.tab;
            state.page = 1;
            loadJobs();
        });
    });

    // Sidebar Filter Listeners
    elements.filterSearch.addEventListener("input", debounce(() => {
        state.search = elements.filterSearch.value.trim();
        state.page = 1;
        loadJobs();
    }, 350));

    elements.filterSource.addEventListener("change", () => {
        state.source = elements.filterSource.value;
        state.page = 1;
        loadJobs();
    });

    elements.filterLocation.addEventListener("change", () => {
        state.location = elements.filterLocation.value;
        state.page = 1;
        loadJobs();
    });

    elements.filterSkillMatch.addEventListener("change", () => {
        state.skillMatch = elements.filterSkillMatch.value;
        state.page = 1;
        loadJobs();
    });

    elements.filterDeadline.addEventListener("change", () => {
        state.deadline = elements.filterDeadline.value;
        state.page = 1;
        loadJobs();
    });

    elements.filterPosted.addEventListener("change", () => {
        state.posted = elements.filterPosted.value;
        state.page = 1;
        loadJobs();
    });

    elements.btnResetFilters.addEventListener("click", () => {
        elements.filterSearch.value = "";
        elements.filterSource.value = "";
        elements.filterLocation.value = "";
        elements.filterSkillMatch.value = "all";
        elements.filterDeadline.value = "all";
        elements.filterPosted.value = "all";

        state.search = "";
        state.source = "";
        state.location = "";
        state.skillMatch = "all";
        state.deadline = "all";
        state.posted = "all";
        state.sortOrder = "desc";
        elements.sortOrderText.textContent = "Latest First ↓";
        state.page = 1;

        loadJobs();
    });

    // Pagination
    elements.btnPrevPage.addEventListener("click", () => {
        if (state.page > 1) {
            state.page--;
            loadJobs();
        }
    });

    elements.btnNextPage.addEventListener("click", () => {
        state.page++;
        loadJobs();
    });

    // Manual Refresh Scraper Trigger
    elements.btnManualRefresh.addEventListener("click", async () => {
        elements.btnManualRefresh.disabled = true;
        showToast("Triggering job scraper...");

        try {
            const res = await fetch("/api/scrape", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ background: true })
            });
            const data = await res.json();

            if (data.status === "busy") {
                showToast("Scraper is already running in background.");
            } else {
                showToast("Background scraping started...");
                startScrapePolling();
            }
        } catch (e) {
            showToast("Failed to start scraper.");
            elements.btnManualRefresh.disabled = false;
        }
    });

    function startScrapePolling() {
        elements.scrapeStatusIndicator.className = "status-indicator running";
        elements.scrapeStatusText.textContent = "Scraping...";

        if (state.scrapeInterval) clearInterval(state.scrapeInterval);

        state.scrapeInterval = setInterval(async () => {
            try {
                const res = await fetch("/api/scrape/status");
                const data = await res.json();

                if (data.state && data.state.is_running) {
                    const current = data.state.current_source || "job boards";
                    elements.scrapeStatusText.textContent = `Scraping ${current}...`;
                } else {
                    clearInterval(state.scrapeInterval);
                    state.scrapeInterval = null;
                    elements.btnManualRefresh.disabled = false;

                    const summary = data.state.last_result;
                    if (summary) {
                        showToast(`Scrape finished! Found ${summary.total_found} jobs (+${summary.total_new} new).`);
                    } else {
                        showToast("Scraping completed.");
                    }

                    checkScraperStatus();
                    fetchSummary();
                    loadJobs();
                }
            } catch (e) {
                console.error("Scrape poll err:", e);
            }
        }, 2000);
    }

    // Export CSV with exact requested columns
    elements.btnExportCsv.addEventListener("click", () => {
        const query = buildQueryParams();
        window.location.href = `/export/csv?${query}`;
    });

    // Initial Load
    fetchSummary();
    loadJobs();
});
