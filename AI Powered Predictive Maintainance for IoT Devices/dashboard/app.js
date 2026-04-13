const DEFAULT_SCENARIOS = [
  {
    name: "Stable baseline",
    payload: {
      type: "L",
      air_temperature: 295.8,
      process_temperature: 306.1,
      rotational_speed: 1680,
      torque: 34.2,
      tool_wear: 12,
    },
  },
  {
    name: "Medium stress",
    payload: {
      type: "M",
      air_temperature: 298.4,
      process_temperature: 309.0,
      rotational_speed: 1450,
      torque: 41.8,
      tool_wear: 65,
    },
  },
  {
    name: "High risk",
    payload: {
      type: "H",
      air_temperature: 310.5,
      process_temperature: 325.0,
      rotational_speed: 1900,
      torque: 55.2,
      tool_wear: 220,
    },
  },
  {
    name: "Wear spike",
    payload: {
      type: "L",
      air_temperature: 303.2,
      process_temperature: 313.4,
      rotational_speed: 1205,
      torque: 28.6,
      tool_wear: 150,
    },
  },
];

const state = {
  charts: {},
  data: null,
  history: JSON.parse(localStorage.getItem("predictguard-history") || "[]"),
};

const $ = (selector) => document.querySelector(selector);

function formatCount(value) {
  return new Intl.NumberFormat("en-US").format(value);
}

function roundPercent(value) {
  return Number(Number(value).toFixed(2));
}

function easeOutCubic(t) {
  return 1 - Math.pow(1 - t, 3);
}

function animateCount(element, target, decimals = 2, duration = 900) {
  const start = Number(element.textContent.replace(/[^0-9.-]/g, "")) || 0;
  const startTime = performance.now();
  function tick(now) {
    const progress = Math.min((now - startTime) / duration, 1);
    const value = start + (target - start) * easeOutCubic(progress);
    element.textContent = value.toFixed(decimals);
    if (progress < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

function setStatus(text) {
  $("#statusChip").textContent = text;
}

function riskColor(level) {
  if (level === "HIGH") return "var(--danger)";
  if (level === "MEDIUM") return "var(--warn)";
  return "var(--good)";
}

function updateRing(probability, level) {
  const percent = Math.max(0, Math.min(probability * 100, 100));
  $("#meterFill").style.width = `${percent}%`;
  $("#riskValue").textContent = `${percent.toFixed(1)}%`;
  $("#riskLabel").textContent = level ? `${level} risk` : "Awaiting input";
  $("#riskProbability").textContent = level ? `Probability ${(probability * 100).toFixed(1)}%` : "Awaiting prediction";
  $("#resultRiskLevel").textContent = level || "--";
  $("#resultRiskLevel").style.color = riskColor(level);
}

function saveHistory(entry) {
  state.history.unshift(entry);
  state.history = state.history.slice(0, 5);
  localStorage.setItem("predictguard-history", JSON.stringify(state.history));
  renderHistory();
}

function renderHistory() {
  const container = $("#predictionHistory");
  if (!state.history.length) {
    container.innerHTML = `<div class="history-item"><div class="history-dot" style="background: var(--muted)"></div><div><div class="history-title">No recent predictions</div><div class="history-meta">Submit a sample to start building history.</div></div><div class="history-meta">--</div></div>`;
    return;
  }

  container.innerHTML = state.history.map((item) => `
    <div class="history-item">
      <div class="history-dot" style="background: ${riskColor(item.riskLevel)}"></div>
      <div>
        <div class="history-title">${item.riskLevel} - ${item.action}</div>
        <div class="history-meta">${item.type} | ${item.probability} | ${item.timestamp}</div>
      </div>
      <div class="history-meta">${item.prediction}</div>
    </div>
  `).join("");
}

function renderFeatureImportance(items) {
  const container = $("#featureImportance");
  if (!items?.length) {
    container.innerHTML = `<div class="history-meta">Feature importance will appear after the model bundle is loaded.</div>`;
    return;
  }

  const max = Math.max(...items.map((item) => item.importance), 0.0001);
  container.innerHTML = items.map((item) => `
    <div class="feature-row">
      <div class="feature-row-head">
        <span>${item.feature}</span>
        <strong>${(item.importance * 100).toFixed(1)}%</strong>
      </div>
      <div class="feature-track">
        <div class="feature-fill" style="width:${(item.importance / max) * 100}%"></div>
      </div>
    </div>
  `).join("");
}

function destroyChart(key) {
  if (state.charts[key]) state.charts[key].destroy();
}

function updateDoughnutChart(id, labels, values, colors) {
  const chart = state.charts[id];
  if (!chart) {
    createDoughnutChart(id, labels, values, colors);
    return;
  }

  chart.data.labels = labels;
  chart.data.datasets[0].data = values;
  chart.data.datasets[0].backgroundColor = colors;
  chart.update("none");
}

function createDoughnutChart(id, labels, values, colors) {
  destroyChart(id);
  state.charts[id] = new Chart(document.getElementById(id), {
    type: "doughnut",
    data: { labels, datasets: [{ data: values, backgroundColor: colors, borderWidth: 0, hoverOffset: 10 }] },
    options: {
      responsive: true,
      cutout: "72%",
      plugins: { legend: { labels: { color: "#c9d7f2" } } },
      animation: { duration: 1200, easing: "easeOutQuart" },
    },
  });
}

function createBarChart(id, labels, values, color, horizontal = false) {
  destroyChart(id);
  state.charts[id] = new Chart(document.getElementById(id), {
    type: "bar",
    data: { labels, datasets: [{ data: values, backgroundColor: color, borderRadius: 10 }] },
    options: {
      indexAxis: horizontal ? "y" : "x",
      responsive: true,
      plugins: { legend: { display: false } },
      scales: {
        x: { ticks: { color: "#8ea2c5" }, grid: { color: "rgba(255,255,255,0.06)" } },
        y: { ticks: { color: "#8ea2c5" }, grid: { color: "rgba(255,255,255,0.06)" } },
      },
      animation: { duration: 1100, easing: "easeOutCubic" },
    },
  });
}

function createGroupedMetricChart(id, labels, validation, test) {
  destroyChart(id);
  state.charts[id] = new Chart(document.getElementById(id), {
    type: "bar",
    data: {
      labels,
      datasets: [
        { label: "Validation", data: validation, backgroundColor: "rgba(138, 125, 255, 0.82)", borderRadius: 10 },
        { label: "Test", data: test, backgroundColor: "rgba(81, 208, 255, 0.82)", borderRadius: 10 },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#c9d7f2" } } },
      scales: {
        x: { ticks: { color: "#8ea2c5" }, grid: { color: "rgba(255,255,255,0.06)" } },
        y: { ticks: { color: "#8ea2c5" }, grid: { color: "rgba(255,255,255,0.06)" }, suggestedMax: 1 },
      },
      animation: { duration: 1200, easing: "easeOutQuart" },
    },
  });
}

function createRadarChart(id, labels, healthyValues, failureValues) {
  destroyChart(id);
  state.charts[id] = new Chart(document.getElementById(id), {
    type: "radar",
    data: {
      labels,
      datasets: [
        {
          label: "Healthy",
          data: healthyValues,
          borderColor: "rgba(72, 227, 154, 0.9)",
          backgroundColor: "rgba(72, 227, 154, 0.16)",
          pointBackgroundColor: "rgba(72, 227, 154, 1)",
        },
        {
          label: "Failure",
          data: failureValues,
          borderColor: "rgba(255, 107, 129, 0.9)",
          backgroundColor: "rgba(255, 107, 129, 0.14)",
          pointBackgroundColor: "rgba(255, 107, 129, 1)",
        },
      ],
    },
    options: {
      responsive: true,
      plugins: { legend: { labels: { color: "#c9d7f2" } } },
      scales: {
        r: {
          angleLines: { color: "rgba(255,255,255,0.08)" },
          grid: { color: "rgba(255,255,255,0.08)" },
          pointLabels: { color: "#c9d7f2" },
          ticks: { color: "#8ea2c5", backdropColor: "transparent" },
        },
      },
      animation: { duration: 1300, easing: "easeOutQuart" },
    },
  });
}

function createScatterChart(id, points) {
  destroyChart(id);
  const healthy = points.filter((p) => p.label === 0);
  const failure = points.filter((p) => p.label === 1);

  state.charts[id] = new Chart(document.getElementById(id), {
    type: "scatter",
    data: {
      datasets: [
        { label: "Healthy", data: healthy.map((p) => ({ x: p.x, y: p.y })), borderColor: "rgba(72, 227, 154, 1)", backgroundColor: "rgba(72, 227, 154, 0.75)", pointRadius: 4 },
        { label: "Failure", data: failure.map((p) => ({ x: p.x, y: p.y })), borderColor: "rgba(255, 107, 129, 1)", backgroundColor: "rgba(255, 107, 129, 0.75)", pointRadius: 4 },
      ],
    },
    options: {
      plugins: { legend: { labels: { color: "#c9d7f2" } } },
      scales: {
        x: { title: { display: true, text: "Air temperature [K]", color: "#c9d7f2" }, ticks: { color: "#8ea2c5" }, grid: { color: "rgba(255,255,255,0.06)" } },
        y: { title: { display: true, text: "Torque [Nm]", color: "#c9d7f2" }, ticks: { color: "#8ea2c5" }, grid: { color: "rgba(255,255,255,0.06)" } },
      },
      animation: { duration: 1000, easing: "easeOutQuart" },
    },
  });
}

function populateHeader(data) {
  $("#modelName").textContent = data.model.name;
  $("#modelThreshold").textContent = data.model.threshold.toFixed(2);
  const failureRate = data.dataset.alert_failure_rate ?? data.dataset.failure_rate;
  const datasetRows = data.dataset.alert_total ?? data.dataset.rows;
  $("#failureRate").textContent = `${Number(failureRate).toFixed(2)}%`;
  $("#datasetRows").textContent = formatCount(datasetRows);
  $("#statusChip").textContent = `Model ready: ${data.model.name}`;
  $("#snapshotText").textContent = data.insights.join(" ");
}

function populateKpis(data) {
  const validation = data.metrics.validation_details || {};
  const test = data.metrics.test_details || {};
  animateCount($("[data-count-up='validationF1']"), Number(validation.f1 || 0), 2);
  animateCount($("[data-count-up='testRecall']"), Number(test.recall || 0), 2);
  animateCount($("[data-count-up='testPRAUC']"), Number(test.average_precision || 0), 2);
  animateCount($("[data-count-up='failureCount']"), Number(data.dataset.failure_count || 0), 0);
}

function labelsFromSensorProfile(profile) {
  return Object.keys(profile).map((key) => key.replace(/_/g, " "));
}

function valuesFromSensorProfile(profile) {
  return Object.values(profile);
}

function populateCharts(data) {
  const failure = data.dataset.alert_target_distribution || data.dataset.target_distribution;
  createDoughnutChart("failureChart", failure.map((item) => item.label), failure.map((item) => item.count), ["rgba(72, 227, 154, 0.95)", "rgba(255, 107, 129, 0.95)"]);

  const types = data.dataset.type_distribution;
  createBarChart("typeChart", types.map((item) => item.label), types.map((item) => item.count), "rgba(81, 208, 255, 0.9)");

  const labels = data.metrics.labels;
  createGroupedMetricChart("metricsChart", labels, data.metrics.validation, data.metrics.test);

  const healthyProfile = data.dataset.normalized_sensor_profiles.healthy;
  const failureProfile = data.dataset.normalized_sensor_profiles.failure;
  createRadarChart("profileChart", labelsFromSensorProfile(healthyProfile), valuesFromSensorProfile(healthyProfile), valuesFromSensorProfile(failureProfile));

  createScatterChart("scatterChart", data.dataset.scatter_points);
  renderPredictionLog(data.prediction_log);
}

function renderFeatureImportance(items) {
  const container = $("#featureImportance");
  if (!items?.length) {
    container.innerHTML = `<div class="history-meta">Feature importance will appear after the model bundle is loaded.</div>`;
    return;
  }

  const max = Math.max(...items.map((item) => item.importance), 0.0001);
  container.innerHTML = items.map((item) => `
    <div class="feature-row">
      <div class="feature-row-head">
        <span>${item.feature}</span>
        <strong>${(item.importance * 100).toFixed(1)}%</strong>
      </div>
      <div class="feature-track">
        <div class="feature-fill" style="width:${(item.importance / max) * 100}%"></div>
      </div>
    </div>
  `).join("");
}

function renderFeatureBars(data) {
  renderFeatureImportance(data.feature_importance);
}

function renderPredictionLog(logData, options = {}) {
  const countPill = $("#logCountPill");
  const tbody = $("#predictionLogBody");
  const recent = logData?.recent || [];
  const distribution = logData?.risk_distribution || [];
  const { updateChart = true } = options;

  countPill.textContent = `${formatCount(logData?.total || 0)} logs`;
  if (updateChart) {
    createDoughnutChart(
      "logRiskChart",
      distribution.map((item) => item.label),
      distribution.map((item) => item.count),
      ["rgba(72, 227, 154, 0.95)", "rgba(255, 190, 85, 0.95)", "rgba(255, 107, 129, 0.95)"]
    );
  } else {
    updateDoughnutChart(
      "logRiskChart",
      distribution.map((item) => item.label),
      distribution.map((item) => item.count),
      ["rgba(72, 227, 154, 0.95)", "rgba(255, 190, 85, 0.95)", "rgba(255, 107, 129, 0.95)"]
    );
  }

  if (!recent.length) {
    tbody.innerHTML = `<tr><td colspan="6">No predictions have been logged yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = recent.map((row) => {
    const riskClass = row.risk_level === "HIGH" ? "risk-high" : row.risk_level === "MEDIUM" ? "risk-medium" : "risk-low";
    const probability = Number(row.risk_probability || 0);
    const timestamp = String(row.timestamp_utc || "").replace("T", " ").replace("Z", "");
    return `
      <tr>
        <td>${timestamp}</td>
        <td>${row.type || "--"}</td>
        <td><span class="risk-pill ${riskClass}">${row.risk_level || "--"}</span></td>
        <td>${(probability * 100).toFixed(1)}%</td>
        <td>${Number(row.failure_prediction) === 1 ? "Failure" : "Healthy"}</td>
        <td>${row.action || "--"}</td>
      </tr>
    `;
  }).join("");
}

function syncLiveDashboardFromPrediction(payload, result) {
  if (!state.data) return;

  const dataset = state.data.dataset || {};
  const predictionLog = state.data.prediction_log || {
    total: 0,
    recent: [],
    risk_distribution: [
      { label: "LOW", count: 0 },
      { label: "MEDIUM", count: 0 },
      { label: "HIGH", count: 0 },
    ],
  };

  predictionLog.total = Number(predictionLog.total || 0) + 1;
  predictionLog.recent = [
    {
      timestamp_utc: new Date().toISOString(),
      batch_id: "",
      sample_index: "",
      type: payload.type,
      risk_probability: result.risk_probability,
      risk_level: result.risk_level,
      failure_prediction: result.failure_prediction,
      action: result.action,
    },
    ...(predictionLog.recent || []),
  ].slice(0, 15);

  const riskCounts = new Map((predictionLog.risk_distribution || []).map((item) => [item.label, Number(item.count || 0)]));
  riskCounts.set(result.risk_level, (riskCounts.get(result.risk_level) || 0) + 1);
  predictionLog.risk_distribution = ["LOW", "MEDIUM", "HIGH"].map((label) => ({
    label,
    count: riskCounts.get(label) || 0,
  }));

  const baseline = Array.isArray(dataset.alert_target_distribution)
    ? dataset.alert_target_distribution.map((item) => ({ ...item }))
    : [
        { label: "Healthy", count: Number(dataset.healthy_count || 0) },
        { label: "Failure", count: Number(dataset.failure_count || 0) },
      ];

  const healthyItem = baseline.find((item) => item.label === "Healthy");
  const failureItem = baseline.find((item) => item.label === "Failure");

  if (Number(result.failure_prediction) === 1 && failureItem) {
    failureItem.count += 1;
    dataset.logged_failure_alerts = Number(dataset.logged_failure_alerts || 0) + 1;
  }

  const total = baseline.reduce((sum, item) => sum + Number(item.count || 0), 0);
  const failureCount = Number(failureItem?.count || 0);

  dataset.alert_target_distribution = baseline.map((item) => ({
    label: item.label,
    count: Number(item.count || 0),
    share: total > 0 ? roundPercent((Number(item.count || 0) / total) * 100) : 0,
  }));
  dataset.alert_total = total;
  dataset.alert_failure_rate = total > 0 ? roundPercent((failureCount / total) * 100) : 0;
  state.data.dataset = dataset;
  state.data.prediction_log = predictionLog;

  updateDoughnutChart(
    "failureChart",
    baseline.map((item) => item.label),
    baseline.map((item) => Number(item.count || 0)),
    ["rgba(72, 227, 154, 0.95)", "rgba(255, 107, 129, 0.95)"]
  );
  updateDoughnutChart(
    "logRiskChart",
    predictionLog.risk_distribution.map((item) => item.label),
    predictionLog.risk_distribution.map((item) => item.count),
    ["rgba(72, 227, 154, 0.95)", "rgba(255, 190, 85, 0.95)", "rgba(255, 107, 129, 0.95)"]
  );
  renderPredictionLog(predictionLog, { updateChart: false });
  $("#failureRate").textContent = `${Number(dataset.alert_failure_rate || 0).toFixed(2)}%`;
  $("#datasetRows").textContent = formatCount(Number(dataset.alert_total || 0));
  $("#statusChip").textContent = "Live prediction recorded";
}

function applyScenario(sample) {
  const form = $("#predictForm");
  form.type.value = sample.type;
  form.air_temperature.value = sample.air_temperature;
  form.process_temperature.value = sample.process_temperature;
  form.rotational_speed.value = sample.rotational_speed;
  form.torque.value = sample.torque;
  form.tool_wear.value = sample.tool_wear;
}

function readFormPayload(form) {
  return {
    type: form.type.value,
    air_temperature: Number(form.air_temperature.value),
    process_temperature: Number(form.process_temperature.value),
    rotational_speed: Number(form.rotational_speed.value),
    torque: Number(form.torque.value),
    tool_wear: Number(form.tool_wear.value),
  };
}

async function submitPrediction(payload) {
  $("#apiState").textContent = "Predicting...";
  try {
    const response = await fetch("/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!response.ok) {
      const errorBody = await response.json().catch(() => ({}));
      throw new Error(errorBody.detail || "Prediction failed");
    }
    const result = await response.json();
    updateRing(result.risk_probability, result.risk_level);
    $("#resultAction").textContent = result.action;
    $("#predictionValue").textContent = result.failure_prediction === 1 ? "Failure" : "Healthy";
    $("#resultRiskLevel").style.color = riskColor(result.risk_level);
    $("#apiState").textContent = "Prediction complete";

    saveHistory({
      type: payload.type,
      probability: `${(result.risk_probability * 100).toFixed(1)}%`,
      prediction: result.failure_prediction === 1 ? "Failure" : "Healthy",
      riskLevel: result.risk_level,
      action: result.action,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    });

    syncLiveDashboardFromPrediction(payload, result);
  } catch (error) {
    $("#apiState").textContent = "Prediction failed";
    setStatus(error.message);
    alert(error.message);
  }
}

async function loadDashboard() {
  try {
    const response = await fetch("/api/dashboard-data");
    if (!response.ok) throw new Error("Unable to load dashboard data");
    const data = await response.json();
    state.data = data;
    populateHeader(data);
    populateKpis(data);
    populateCharts(data);
    renderFeatureBars(data);
    renderHistory();
    setStatus("Connected and healthy");
    updateRing(0, null);
  } catch (error) {
    setStatus("Dashboard data unavailable");
    $("#snapshotText").textContent = error.message;
  }
}

function wireUI() {
  const form = $("#predictForm");
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    await submitPrediction(readFormPayload(form));
  });

  $("#resetBtn").addEventListener("click", () => {
    applyScenario(DEFAULT_SCENARIOS[0].payload);
    updateRing(0, null);
    $("#resultAction").textContent = "Submit a sample to get an action recommendation.";
    $("#resultRiskLevel").textContent = "--";
    $("#predictionValue").textContent = "--";
    $("#riskProbability").textContent = "Awaiting prediction";
    $("#meterFill").style.width = "0%";
  });

  $("#randomizeBtn").addEventListener("click", () => {
    const sample = DEFAULT_SCENARIOS[Math.floor(Math.random() * DEFAULT_SCENARIOS.length)];
    applyScenario(sample.payload);
    $("#apiState").textContent = `Loaded ${sample.name}`;
  });

  $("#clearHistoryBtn").addEventListener("click", () => {
    state.history = [];
    localStorage.removeItem("predictguard-history");
    renderHistory();
  });
}

window.addEventListener("DOMContentLoaded", async () => {
  wireUI();
  applyScenario(DEFAULT_SCENARIOS[0].payload);
  renderHistory();
  await loadDashboard();
});
