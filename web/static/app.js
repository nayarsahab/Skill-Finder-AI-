// Skill Finder AI Frontend logic
document.addEventListener("DOMContentLoaded", () => {
    // Current state variables
    let currentCurriculum = null;
    let selectedWeek = 1;
    let checkedActivities = {}; // Maps query_week_index -> boolean

    // Elements
    const form = document.getElementById("generator-form");
    const queryInput = document.getElementById("skill-query");
    const generateBtn = document.getElementById("generate-btn");
    const cacheList = document.getElementById("cache-list");
    const visualizer = document.getElementById("workflow-visualizer");
    const toast = document.getElementById("toast");
    const toastMessage = document.getElementById("toast-message");

    // Screens
    const idleState = document.querySelector(".idle-state");
    const loadingState = document.querySelector(".loading-state");
    const blockedState = document.querySelector(".blocked-state");
    const successState = document.querySelector(".success-state");

    // Graph Nodes & Connectors
    const nodeStart = document.getElementById("node-start");
    const nodeBouncer = document.getElementById("node-bouncer");
    const nodeSearch = document.getElementById("node-search");
    const nodePathfinder = document.getElementById("node-pathfinder");
    const nodeRemediation = document.getElementById("node-remediation");
    const conn1 = document.getElementById("conn-1");
    const conn2 = document.getElementById("conn-2");
    
    const svgBranchYes = document.querySelector(".branch-yes");
    const svgBranchNo = document.querySelector(".branch-no");

    // Loading stages text
    const loaderTitle = document.getElementById("loader-stage-title");
    const loaderDesc = document.getElementById("loader-stage-desc");

    // Safety toggle
    const toggleSafety = document.getElementById("toggle-safety");
    const safetyList = document.getElementById("safety-checklist-list");
    const toggleIcon = toggleSafety.querySelector(".toggle-icon");

    // Initialize Cache History
    loadCacheHistory();

    // Suggestion chips handler
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            queryInput.value = chip.dataset.query;
            triggerGeneration(chip.dataset.query);
        });
    });

    // Form submission handler
    form.addEventListener("submit", (e) => {
        e.preventDefault();
        const query = queryInput.value.trim();
        if (query) {
            triggerGeneration(query);
        }
    });

    // Toggle safety checklist
    toggleSafety.addEventListener("click", () => {
        safetyList.classList.toggle("collapsed");
        toggleIcon.classList.toggle("rotated");
    });

    // Export markdown click handler
    document.getElementById("export-md-btn").addEventListener("click", async () => {
        if (!currentCurriculum) return;
        
        try {
            const res = await fetch("/api/export", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ curriculum: currentCurriculum })
            });
            const data = await res.json();
            if (data.status === "success") {
                showToast(`Markdown file successfully created: ${data.filename}`);
            } else {
                showToast("Failed to export markdown file", true);
            }
        } catch (e) {
            showToast("Error exporting markdown", true);
        }
    });

    // Week tabs click handler
    document.querySelectorAll(".tab-btn").forEach(btn => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            selectedWeek = parseInt(btn.dataset.week);
            renderSelectedWeek();
        });
    });

    // Load Alternative button click handler
    document.getElementById("load-alternative-btn").addEventListener("click", () => {
        const alt = document.getElementById("alternative-title").innerText;
        queryInput.value = alt;
        triggerGeneration(alt);
    });

    // Fetch and render the history list
    async function loadCacheHistory() {
        try {
            const response = await fetch("/api/cache");
            const data = await response.json();
            
            cacheList.innerHTML = "";
            if (!data.history || data.history.length === 0) {
                cacheList.innerHTML = `<div class="badge" style="margin: 20px auto; display: block; text-align: center;">No history cached yet</div>`;
                return;
            }

            data.history.forEach(item => {
                const isCurriculum = item.type === "curriculum";
                const card = document.createElement("div");
                card.className = `cache-item ${isCurriculum ? "" : "blocked"}`;
                
                card.innerHTML = `
                    <div class="cache-icon-box">
                        <i class="fa-solid ${isCurriculum ? "fa-book" : "fa-shield-halved"}"></i>
                    </div>
                    <div class="cache-info">
                        <h4 class="cache-title" title="${item.title}">${item.title}</h4>
                        <div class="cache-meta">
                            <span class="status-indicator ${isCurriculum ? "status-approved" : "status-blocked"}"></span>
                            <span>${isCurriculum ? "Approved" : "Blocked"}</span>
                            <span style="opacity: 0.5">•</span>
                            <span style="font-size: 0.65rem;">${item.query}</span>
                        </div>
                    </div>
                `;

                card.addEventListener("click", () => {
                    queryInput.value = item.query;
                    triggerGeneration(item.query);
                });

                cacheList.appendChild(card);
            });
        } catch (e) {
            console.error("Error loading cache history", e);
            cacheList.innerHTML = `<div class="badge" style="color: var(--danger);">Failed to load cache registry</div>`;
        }
    }

    // Trigger workflow generation
    async function triggerGeneration(query) {
        // Clear previous state
        currentCurriculum = null;
        selectedWeek = 1;
        document.querySelectorAll(".tab-btn").forEach(b => {
            b.classList.remove("active");
            if (b.dataset.week === "1") b.classList.add("active");
        });

        // Hide screens & Show visualizer + Loading state
        hideAllScreens();
        loadingState.classList.remove("hidden");
        visualizer.classList.remove("hidden");
        resetGraphVisuals();

        // 1. Initial State: START node active
        setNodeState("node-start", "active", "Initiated");
        
        // Short artificial steps to showcase the Multi-Agent graph execution (Total ~2.5s)
        await delay(500);
        
        // 2. Active: Security Bouncer Node
        setNodeState("node-start", "completed-success", "Passed");
        setConnectorState("conn-1", true);
        setNodeState("node-bouncer", "active", "Evaluating safety...");
        loaderTitle.innerText = "Shift-Left Security Gate Active";
        loaderDesc.innerText = "Security Bouncer analyzing prompt for hazard classes & injection vectors...";
        
        // Perform backend request in parallel to the visual steps
        let backendPromise = fetch("/api/generate", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ query: query })
        }).then(r => r.json());

        await delay(800);

        try {
            const data = await backendPromise;
            
            // Evaluated safety check
            const bouncer = data.bouncer;
            
            if (bouncer.approved) {
                // Safety Bouncer approved!
                setNodeState("node-bouncer", "completed-success", "Approved");
                svgBranchYes.classList.add("active");
                svgBranchNo.classList.remove("active");
                
                // Active: Web Search Node
                setNodeState("node-search", "active", "Crawling resources...");
                loaderTitle.innerText = "Web Search Indexing";
                loaderDesc.innerText = "Retrieving educational tutorials, textbooks, and video stubs...";
                
                await delay(800);
                
                setNodeState("node-search", "completed-success", "Crawled");
                setConnectorState("conn-2", true);
                
                // Active: Pathfinder Agent
                setNodeState("node-pathfinder", "active", "Compiling 4-week map...");
                loaderTitle.innerText = "Pathfinder Generator Node";
                loaderDesc.innerText = "Writing interactive 4-week structured curriculum & practical capstone projects...";
                
                await delay(600);
                
                setNodeState("node-pathfinder", "completed-success", "Compiled");
                
                // Load success screen
                currentCurriculum = data.curriculum;
                renderCurriculum(data);
            } else {
                // Safety Bouncer blocked!
                setNodeState("node-bouncer", "completed-failed", "Blocked");
                svgBranchYes.classList.remove("active");
                svgBranchNo.classList.add("active");
                
                // Active: Remediation Node
                setNodeState("node-remediation", "active", "Steering alternative...");
                loaderTitle.innerText = "Remediation & Steering Guard";
                loaderDesc.innerText = "Curriculum generation blocked. Finding suitable alternative learning path...";
                
                await delay(800);
                
                setNodeState("node-remediation", "completed-failed", "Remediated");
                
                // Load blocked screen
                renderBlocked(data);
            }
            
            // Reload sidebar list
            loadCacheHistory();

        } catch (e) {
            console.error(e);
            showToast("Failed to communicate with workflow server", true);
            hideAllScreens();
            idleState.classList.remove("hidden");
            resetGraphVisuals();
            visualizer.classList.add("hidden");
        }
    }

    // Render approved Curriculum to UI
    function renderCurriculum(data) {
        hideAllScreens();
        successState.classList.remove("hidden");

        const curriculum = data.curriculum;
        document.getElementById("curriculum-title").innerText = curriculum.skill_title.toUpperCase();
        document.getElementById("curriculum-source").innerText = data.source === "cache" 
            ? "⚡ Loaded from Cache database" 
            : `🛰️ Live Gemini Run (Saved: ${data.filename})`;

        // Render Safety checklist list
        safetyList.innerHTML = "";
        curriculum.safety_checklist.forEach(rule => {
            const li = document.createElement("li");
            li.innerText = rule;
            safetyList.appendChild(li);
        });

        renderSelectedWeek();
    }

    // Render Selected Week info
    function renderSelectedWeek() {
        if (!currentCurriculum) return;
        const week = currentCurriculum.four_week_plan.find(w => w.week_number === selectedWeek);
        const card = document.getElementById("week-content-card");

        if (!week) return;

        // Render week structure
        card.innerHTML = `
            <div class="week-main-header">
                <h3>Week ${week.week_number}: ${week.objective}</h3>
                <div class="week-objective"><i class="fa-solid fa-graduation-cap"></i> Target Milestone</div>
            </div>

            <div class="week-grid">
                <!-- Activities Checkbox list -->
                <div class="week-activities-section">
                    <h4 class="section-title"><i class="fa-solid fa-list-check"></i> Interactive Syllabus Checklist</h4>
                    <ul class="activities-list" id="week-activities-ul">
                        <!-- Items rendered here -->
                    </ul>
                </div>

                <!-- Labs list -->
                <div class="week-labs-section">
                    <h4 class="section-title"><i class="fa-solid fa-flask"></i> Hands-on Labs & Simulations</h4>
                    <ul class="labs-list" id="week-labs-ul">
                        <!-- Items rendered here -->
                    </ul>
                </div>
            </div>

            <!-- Resource Cards section -->
            <div class="resources-list-wrapper">
                <h4 class="section-title"><i class="fa-solid fa-circle-play"></i> Curated Learning Materials</h4>
                <div class="resources-grid" id="week-resources-grid">
                    <!-- Cards rendered here -->
                </div>
            </div>
        `;

        // 1. Render Activities list
        const activitiesUl = document.getElementById("week-activities-ul");
        week.activities.forEach((act, index) => {
            const key = `${currentCurriculum.skill_title}_w${selectedWeek}_idx${index}`;
            const isChecked = !!checkedActivities[key];

            const li = document.createElement("li");
            li.className = `activity-item ${isChecked ? "checked" : ""}`;
            li.innerHTML = `
                <div class="checkbox-box">
                    <i class="fa-solid fa-check"></i>
                </div>
                <span class="activity-text">${act}</span>
            `;

            li.addEventListener("click", () => {
                const newVal = !checkedActivities[key];
                checkedActivities[key] = newVal;
                li.classList.toggle("checked", newVal);
            });

            activitiesUl.appendChild(li);
        });

        // 2. Render Labs list
        const labsUl = document.getElementById("week-labs-ul");
        week.labs.forEach(lab => {
            const li = document.createElement("li");
            li.className = "lab-item";
            li.innerHTML = `
                <div class="lab-badge">
                    <i class="fa-solid fa-laptop-code"></i>
                </div>
                <div class="lab-content">
                    <h5>Lab Milestone</h5>
                    <p>${lab}</p>
                </div>
            `;
            labsUl.appendChild(li);
        });

        // 3. Render Resource cards
        const resourcesGrid = document.getElementById("week-resources-grid");
        week.resources.forEach(res => {
            const card = document.createElement("a");
            card.className = "resource-card";
            card.href = res.url;
            card.target = "_blank";
            
            let iconClass = "fa-book-open";
            if (res.type.toLowerCase().includes("video") || res.type.toLowerCase().includes("youtube")) {
                iconClass = "fa-circle-play";
            } else if (res.type.toLowerCase().includes("course") || res.type.toLowerCase().includes("academy")) {
                iconClass = "fa-graduation-cap";
            }

            card.innerHTML = `
                <div class="resource-icon">
                    <i class="fa-solid ${iconClass}"></i>
                </div>
                <div class="resource-meta">
                    <h6>${res.title}</h6>
                    <span class="resource-type">${res.type}</span>
                </div>
            `;
            resourcesGrid.appendChild(card);
        });
    }

    // Render Blocked remediation panel
    function renderBlocked(data) {
        hideAllScreens();
        blockedState.classList.remove("hidden");

        const bouncer = data.bouncer;
        document.getElementById("blocked-risk-level").innerText = `Risk Level: ${bouncer.risk_level.toUpperCase()}`;
        document.getElementById("blocked-reason-text").innerText = bouncer.reason;

        const alternativeCard = document.getElementById("alternative-card");
        if (bouncer.recommended_alternative) {
            alternativeCard.classList.remove("hidden");
            document.getElementById("alternative-title").innerText = bouncer.recommended_alternative;
        } else {
            alternativeCard.classList.add("hidden");
        }
    }

    // Helper functions
    function hideAllScreens() {
        idleState.classList.add("hidden");
        loadingState.classList.add("hidden");
        blockedState.classList.add("hidden");
        successState.classList.add("hidden");
    }

    function setNodeState(nodeId, stateClass, statusText) {
        const node = document.getElementById(nodeId);
        if (!node) return;
        
        node.className = "node"; // reset classes
        if (stateClass) {
            node.classList.add(stateClass);
        }
        node.querySelector(".node-status").innerText = statusText;
    }

    function setConnectorState(connId, isActive) {
        const conn = document.getElementById(connId);
        if (conn) {
            conn.classList.toggle("active", isActive);
        }
    }

    function resetGraphVisuals() {
        setNodeState("node-start", "", "Waiting");
        setNodeState("node-bouncer", "", "Waiting");
        setNodeState("node-search", "", "Waiting");
        setNodeState("node-pathfinder", "", "Waiting");
        setNodeState("node-remediation", "", "Waiting");

        setConnectorState("conn-1", false);
        setConnectorState("conn-2", false);

        svgBranchYes.classList.remove("active");
        svgBranchNo.classList.remove("active");
    }

    function delay(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }

    function showToast(message, isError = false) {
        toastMessage.innerText = message;
        toast.className = `toast ${isError ? "blocked" : ""}`;
        if (isError) {
            toast.style.borderColor = "var(--danger)";
            toast.style.boxShadow = "0 5px 25px rgba(255, 93, 115, 0.2)";
            toast.querySelector(".toast-icon").className = "fa-solid fa-triangle-exclamation toast-icon";
            toast.querySelector(".toast-icon").style.color = "var(--danger)";
        } else {
            toast.style.borderColor = "var(--success)";
            toast.style.boxShadow = "0 5px 25px rgba(6, 214, 160, 0.2)";
            toast.querySelector(".toast-icon").className = "fa-solid fa-circle-check toast-icon";
            toast.querySelector(".toast-icon").style.color = "var(--success)";
        }
        toast.classList.remove("hidden");

        setTimeout(() => {
            toast.classList.add("hidden");
        }, 4000);
    }
});
