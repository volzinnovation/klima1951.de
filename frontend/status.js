const statusLabels = {
  ok: "OK",
  warn: "Warnung",
  missing: "Fehlt",
  error: "Fehler",
};

const metricLabels = {
  hurs: "Relative Luftfeuchte",
  pr: "Niederschlag",
  tas: "Temperatur",
  tasmax: "Tagesmaximum",
  tasmin: "Tagesminimum",
};

const numberFormatter = new Intl.NumberFormat("de-DE");
const dateFormatter = new Intl.DateTimeFormat("de-DE", {
  dateStyle: "medium",
  timeStyle: "short",
  timeZone: "Europe/Berlin",
});

function text(id, value) {
  document.getElementById(id).textContent = value;
}

function bytes(value) {
  if (!Number.isFinite(value)) {
    return "n/a";
  }
  if (value >= 1024 * 1024 * 1024) {
    return `${(value / (1024 * 1024 * 1024)).toFixed(2)} GiB`;
  }
  if (value >= 1024 * 1024) {
    return `${(value / (1024 * 1024)).toFixed(1)} MiB`;
  }
  if (value >= 1024) {
    return `${(value / 1024).toFixed(1)} KiB`;
  }
  return `${value} B`;
}

function formatDate(value) {
  if (!value) {
    return "n/a";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return "n/a";
  }
  return `${dateFormatter.format(date)} Uhr`;
}

function chip(status) {
  const normalized = statusLabels[status] ? status : "warn";
  const element = document.createElement("span");
  element.className = `status-chip ${normalized}`;
  element.textContent = statusLabels[normalized];
  return element;
}

function statusRow(status, title, detail) {
  const row = document.createElement("div");
  row.className = "status-row";
  row.append(chip(status));

  const body = document.createElement("div");
  const heading = document.createElement("strong");
  heading.textContent = title;
  const paragraph = document.createElement("p");
  paragraph.textContent = detail;
  body.append(heading, paragraph);
  row.append(body);
  return row;
}

function renderOverview(payload) {
  const city = payload.city_outputs || {};
  const hyras = payload.hyras || {};
  const checks = payload.checks || [];
  const configured = city.configured_cities || 0;
  const complete = city.complete_city_outputs || 0;
  const ratio = configured > 0 ? Math.round((complete / configured) * 100) : 0;
  const overall = checks.some((check) => check.status === "missing")
    ? "error"
    : checks.some((check) => check.status !== "ok")
      ? "warn"
      : "ok";

  text("generated-at", formatDate(payload.generated_at_utc));
  text("city-complete", `${numberFormatter.format(complete)} / ${numberFormatter.format(configured)}`);
  text("city-total", `${ratio}% vollstaendig`);
  text("year-span", `${city.stats_min_year || "n/a"}-${city.stats_max_year || "n/a"}`);
  text("hyras-count", numberFormatter.format(hyras.hyras_file_count || 0));
  text("payload-size", bytes(city.all_years_total_bytes || 0));

  const status = document.getElementById("overall-status");
  status.className = `status-chip ${overall}`;
  status.textContent = overall === "ok" ? "Alle Pruefungen OK" : statusLabels[overall];
  document.getElementById("completion-fill").style.width = `${ratio}%`;
}

function renderFreshness(payload) {
  const freshness = payload.freshness || {};
  const status = statusLabels[freshness.status] ? freshness.status : "warn";
  const statusElement = document.getElementById("freshness-status");
  statusElement.className = `status-chip ${status}`;
  statusElement.textContent = status === "ok" ? "Aktuell" : statusLabels[status];

  text("freshness-detail", freshness.detail || "Noch keine Aktualitaetsdaten im Statuspayload.");
  text("freshness-expected", freshness.expected_latest_complete_year || "n/a");
  text("freshness-stats", freshness.stats_latest_complete_year || "n/a");
  text("freshness-hyras", freshness.hyras_latest_complete_year || "n/a");

  const staleMetrics = freshness.stale_hyras_metrics || [];
  const filesBehind = freshness.stats_files_behind_expected_year || 0;
  if (status === "ok") {
    text("freshness-note", "Der aktuelle Jahrgang laeuft weiter; erwartet wird nur das letzte abgeschlossene Jahr.");
    return;
  }

  const notes = [];
  if (filesBehind > 0) {
    notes.push(`${numberFormatter.format(filesBehind)} Stadt-CSV-Dateien hinter Erwartung`);
  }
  if (staleMetrics.length > 0) {
    notes.push(`HYRAS: ${staleMetrics.join(", ")}`);
  }
  text("freshness-note", notes.join(" / ") || "Bitte ETL-Ausgabe pruefen.");
}

function renderChecks(payload) {
  const list = document.getElementById("checks-list");
  list.replaceChildren();
  for (const check of payload.checks || []) {
    list.append(statusRow(check.status, check.name, check.detail));
  }
}

function renderMetrics(payload) {
  const body = document.getElementById("metric-table-body");
  body.replaceChildren();
  const metrics = payload.hyras?.metrics || {};
  for (const [metric, summary] of Object.entries(metrics).sort()) {
    const row = document.createElement("tr");
    const name = document.createElement("td");
    const files = document.createElement("td");
    const years = document.createElement("td");
    name.textContent = metricLabels[metric] || metric;
    files.textContent = numberFormatter.format(summary.file_count || 0);
    years.textContent = `${summary.min_year || "n/a"}-${summary.max_year || "n/a"}`;
    row.append(name, files, years);
    body.append(row);
  }
}

function renderFiles(payload) {
  const list = document.getElementById("files-list");
  list.replaceChildren();

  const fileEntries = Object.values(payload.files || {});
  for (const fileInfo of payload.hyras?.files || []) {
    fileEntries.push(fileInfo);
  }

  for (const fileInfo of fileEntries) {
    const detail = `${bytes(fileInfo.bytes)} - geaendert ${formatDate(fileInfo.modified_at_utc)}`;
    const row = statusRow(fileInfo.exists ? "ok" : "missing", fileInfo.path || "Unbekannte Datei", detail);
    row.querySelector("strong").classList.add("file-path");
    list.append(row);
  }
}

function renderMissing(payload) {
  const list = document.getElementById("missing-list");
  const missing = payload.city_outputs?.missing_examples || [];
  list.replaceChildren();

  if (missing.length === 0) {
    list.append(statusRow("ok", "Keine fehlenden Ausgaben", "Alle konfigurierten Staedte haben all-years.json und stats.csv."));
    return;
  }

  for (const entry of missing) {
    const missingFiles = (entry.missing || []).join(", ");
    list.append(statusRow("warn", entry.city || "Unbekannte Stadt", missingFiles));
  }
}

async function loadStatus() {
  try {
    const response = await fetch("data-status.json", { cache: "no-cache" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const payload = await response.json();
    renderOverview(payload);
    renderFreshness(payload);
    renderChecks(payload);
    renderMetrics(payload);
    renderFiles(payload);
    renderMissing(payload);
  } catch (error) {
    const status = document.getElementById("overall-status");
    status.className = "status-chip error";
    status.textContent = "Status nicht ladbar";
    document.getElementById("checks-list").replaceChildren(
      statusRow("error", "data-status.json", error.message),
    );
  }
}

document.addEventListener("DOMContentLoaded", loadStatus);
