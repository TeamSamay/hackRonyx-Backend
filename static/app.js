// ============================================================================
// VERDICT AI - CLIENT-SIDE INTERACTIVITY & LIVE API INTEGRATION
// ============================================================================

const API_BASE = ""; // Relative API path for seamless Vercel / local routing

document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  loadDashboardData();
});

function initEventListeners() {
  const btnSeed = document.getElementById("btn-seed");
  const btnRefresh = document.getElementById("btn-refresh");

  if (btnSeed) {
    btnSeed.addEventListener("click", async () => {
      btnSeed.innerText = "⏳ Seeding...";
      try {
        const res = await fetch(`${API_BASE}/api/demo/seed`, { method: "POST" });
        if (res.ok) {
          alert("Demo Cases Seeded Successfully!");
          loadDashboardData();
        } else {
          alert("Notice: Using client-side rich demo cache.");
        }
      } catch (err) {
        console.warn("Backend seed fallback:", err);
      } finally {
        btnSeed.innerText = "⚡ Seed Demo Cases";
      }
    });
  }

  if (btnRefresh) {
    btnRefresh.addEventListener("click", () => {
      loadDashboardData();
    });
  }

  // Case item selection
  const caseItems = document.querySelectorAll(".case-item");
  caseItems.forEach((item) => {
    item.addEventListener("click", () => {
      caseItems.forEach((c) => c.classList.remove("active"));
      item.classList.add("active");
      const caseId = item.getAttribute("data-id");
      updateInspector(caseId);
    });
  });
}

async function loadDashboardData() {
  try {
    const res = await fetch(`${API_BASE}/api/cases`);
    if (res.ok) {
      const data = await res.json();
      console.log("Cases loaded from backend:", data);
      document.getElementById("backend-status").innerText = "🟢 Online & Connected";
    }
  } catch (e) {
    console.log("Using cached visual dataset");
  }
}

function updateInspector(caseId) {
  const inspId = document.getElementById("insp-id");
  const inspRisk = document.getElementById("insp-risk");
  const inspVerdict = document.getElementById("insp-verdict");
  const inspAudit = document.getElementById("insp-audit");

  if (caseId === "CASE-TX92831") {
    inspId.innerText = "CASE-TX92831";
    inspRisk.innerText = "91.0%";
    inspRisk.style.color = "var(--accent-rose)";
    inspVerdict.className = "badge badge-conflicting";
    inspVerdict.innerText = "HUMAN_REVIEW_MANDATED";
    inspAudit.innerText = `[GATE] Rule 4: Spatio-Temporal Discrepancy Flagged\n[LOCATION] Mumbai != Delhi (Δt: 8s)\n[ACTION] Automated Clearance Blocked`;
  } else if (caseId === "CASE-CLAIM782") {
    inspId.innerText = "CASE-CLAIM782";
    inspRisk.innerText = "8.0%";
    inspRisk.style.color = "var(--accent-emerald)";
    inspVerdict.className = "badge badge-sufficient";
    inspVerdict.innerText = "AUTO_APPROVED";
    inspAudit.innerText = `[GATE] Rule 1: High Evidence Quality & Complete\n[POLICE FIR] Verified FIR-88219 (Accidental Collision)\n[GARAGE] Verified Authorized Estimate ₹3.2L`;
  } else if (caseId === "CASE-LOAN409") {
    inspId.innerText = "CASE-LOAN409";
    inspRisk.innerText = "35.0%";
    inspRisk.style.color = "var(--accent-amber)";
    inspVerdict.className = "badge badge-incomplete";
    inspVerdict.innerText = "REQUEST_DATA";
    inspAudit.innerText = `[GATE] Rule 2: Incomplete Financial Records\n[MISSING] Q4 GST Tax Reconciliation\n[MISSING] Director Physical Guarantee Proof`;
  } else if (caseId === "CASE-KYC501") {
    inspId.innerText = "CASE-KYC501";
    inspRisk.innerText = "68.0%";
    inspRisk.style.color = "var(--accent-purple)";
    inspVerdict.className = "badge badge-low-quality";
    inspVerdict.innerText = "REQUEST_BETTER_SOURCES";
    inspAudit.innerText = `[GATE] Rule 3: Low Quality Submissions\n[OCR CONFIDENCE] 42% (Glare & Blur Detected)\n[RECENCY] Address Bill Dated 2021 (>90 Days Expired)`;
  }
}
