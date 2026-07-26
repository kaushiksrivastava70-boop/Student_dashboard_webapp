const dropzone = document.getElementById("dropzone");
const fileInput = document.getElementById("fileInput");
const sampleBtn = document.getElementById("sampleBtn");
const errorBanner = document.getElementById("errorBanner");
const uploadSection = document.getElementById("uploadSection");
const dashboard = document.getElementById("dashboard");
const statRow = document.getElementById("statRow");
const resetBtn = document.getElementById("resetBtn");
const tableSearch = document.getElementById("tableSearch");
const themeToggle = document.getElementById("themeToggle");

let subjectChart, distributionChart;
let currentTableRows = [];
let currentColumns = [];
let lastPayload = null;

// ---------- Theme ----------
const THEME_COLORS = {
  light: { ink: "#1B2340", inkSoft: "#3A4266", gold: "#C9932F", teal: "#3F6B63", rose: "#B5533C", gridLine: "#E4DCC9" },
  dark: { ink: "#EFE9DA", inkSoft: "#B7AF9C", gold: "#E3B04E", teal: "#6FB3A4", rose: "#E28A72", gridLine: "#2B2F3A" },
};

function getTheme() {
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

function applyTheme(theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("gradeline-theme", theme);
  if (lastPayload) {
    renderSubjectChart(lastPayload.subjects);
    renderDistributionChart(lastPayload.distribution);
  }
}

themeToggle.addEventListener("click", () => {
  applyTheme(getTheme() === "dark" ? "light" : "dark");
});

dropzone.addEventListener("click", () => fileInput.click());
dropzone.addEventListener("dragover", (e) => {
  e.preventDefault();
  dropzone.classList.add("drag-over");
});
dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-over"));
dropzone.addEventListener("drop", (e) => {
  e.preventDefault();
  dropzone.classList.remove("drag-over");
  if (e.dataTransfer.files.length) uploadFile(e.dataTransfer.files[0]);
});
fileInput.addEventListener("change", () => {
  if (fileInput.files.length) uploadFile(fileInput.files[0]);
});
sampleBtn.addEventListener("click", async (e) => {
  e.stopPropagation();
  showError(null);
  const res = await fetch("/sample");
  const blob = await res.blob();
  const file = new File([blob], "sample_students.csv", { type: "text/csv" });
  uploadFile(file);
});
resetBtn.addEventListener("click", () => {
  dashboard.hidden = true;
  uploadSection.hidden = false;
  fileInput.value = "";
  showError(null);
  window.scrollTo({ top: 0, behavior: "smooth" });
});
tableSearch.addEventListener("input", () => renderTable(tableSearch.value));

function showError(message) {
  if (!message) {
    errorBanner.hidden = true;
    errorBanner.textContent = "";
    return;
  }
  errorBanner.hidden = false;
  errorBanner.textContent = message;
}

async function uploadFile(file) {
  if (!file.name.toLowerCase().endsWith(".csv")) {
    showError("Please upload a .csv file.");
    return;
  }
  showError(null);

  const formData = new FormData();
  formData.append("file", file);

  try {
    const res = await fetch("/upload", { method: "POST", body: formData });
    const data = await res.json();
    if (!res.ok) {
      showError(data.error || "Something went wrong processing that file.");
      return;
    }
    renderDashboard(data);
  } catch (err) {
    showError("Could not reach the server. Please try again.");
  }
}

function renderDashboard(data) {
  uploadSection.hidden = true;
  dashboard.hidden = false;

  renderStats(data.summary);
  renderSubjectChart(data.subjects);
  renderDistributionChart(data.distribution);

  currentTableRows = data.table;
  currentColumns = data.table_columns;
  lastPayload = data;
  buildTableHead(currentColumns);
  renderTable("");

  window.scrollTo({ top: 0, behavior: "smooth" });
}

function renderStats(summary) {
  const cards = [
    { tag: "Roster", label: "Total Students", value: summary.total_students, cls: "" },
    { tag: "Overall", label: "Average Marks", value: summary.average_marks, cls: "" },
    { tag: "Ceiling", label: "Highest Marks", value: summary.highest_marks, cls: "teal" },
    { tag: "Floor", label: "Lowest Marks", value: summary.lowest_marks, cls: "rose" },
    { tag: "Watch", label: "At-Risk Students", value: summary.at_risk_count, cls: "rose" },
  ];

  statRow.innerHTML = cards
    .map(
      (c) => `
    <div class="stat-card" data-tag="${c.tag}">
      <p class="stat-label">${c.label}</p>
      <p class="stat-value ${c.cls}">${c.value}</p>
    </div>`
    )
    .join("");

  if (summary.top_performer) {
    statRow.innerHTML += `
    <div class="stat-card" data-tag="Top Mark">
      <p class="stat-label">Top Performer</p>
      <p class="stat-value" style="font-size:22px;">${summary.top_performer.name}</p>
      <p class="stat-sub">${summary.top_performer.average} average</p>
    </div>`;
  }
}

function renderSubjectChart(subjects) {
  const c = THEME_COLORS[getTheme()];
  const ctx = document.getElementById("subjectChart");
  if (subjectChart) subjectChart.destroy();
  subjectChart = new Chart(ctx, {
    type: "bar",
    data: {
      labels: subjects.map((s) => s.subject),
      datasets: [
        {
          label: "Average",
          data: subjects.map((s) => s.average),
          backgroundColor: c.ink,
          borderRadius: 3,
        },
        {
          label: "Highest",
          data: subjects.map((s) => s.highest),
          backgroundColor: c.gold,
          borderRadius: 3,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom",
          labels: { font: { family: "Inter" }, color: c.ink },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          max: 100,
          grid: { color: c.gridLine },
          ticks: { color: c.inkSoft },
        },
        x: {
          grid: { display: false },
          ticks: { color: c.inkSoft },
        },
      },
    },
  });
}

function renderDistributionChart(distribution) {
  const c = THEME_COLORS[getTheme()];
  const ctx = document.getElementById("distributionChart");
  if (distributionChart) distributionChart.destroy();
  const labels = Object.keys(distribution);
  const values = Object.values(distribution);
  distributionChart = new Chart(ctx, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: [c.rose, "#D97757", c.gold, c.teal, c.ink],
          borderColor: getTheme() === "dark" ? "#15181F" : "#F6F2E9",
          borderWidth: 3,
        },
      ],
    },
    options: {
      responsive: true,
      plugins: {
        legend: {
          position: "bottom",
          labels: { font: { family: "Inter" }, boxWidth: 14, color: c.ink },
        },
      },
    },
  });
}

function buildTableHead(columns) {
  const thead = document.querySelector("#dataTable thead");
  thead.innerHTML = `<tr>${columns.map((c) => `<th>${c}</th>`).join("")}</tr>`;
}

function renderTable(filterText) {
  const tbody = document.querySelector("#dataTable tbody");
  const filter = filterText.trim().toLowerCase();
  const nameCol = currentColumns[0];

  const rows = currentTableRows.filter((row) => {
    if (!filter) return true;
    const nameVal = String(row[nameCol] ?? "").toLowerCase();
    return nameVal.includes(filter);
  });

  tbody.innerHTML = rows
    .map((row) => {
      const cells = currentColumns
        .map((col, i) => {
          const val = row[col];
          const display = val === null || val === undefined || Number.isNaN(val) ? "—" : val;
          if (i === 0) return `<td class="name-cell">${display}</td>`;
          const isLow = typeof val === "number" && val < 60;
          return `<td class="${isLow ? "at-risk" : ""}">${display}</td>`;
        })
        .join("");
      return `<tr>${cells}</tr>`;
    })
    .join("");

  if (!rows.length) {
    tbody.innerHTML = `<tr><td colspan="${currentColumns.length}" style="text-align:center; padding:24px; color:#3A4266;">No matching students.</td></tr>`;
  }
}
