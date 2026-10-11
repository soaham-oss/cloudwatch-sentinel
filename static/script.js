let timer = null;
const $ = (id) => document.getElementById(id);

// ---------- charts ----------
const axis = (max) => ({ ticks: { color: "#8a9bb4" }, grid: { color: "#233246" }, beginAtZero: true, max });
function lineChart(id, color, max) {
  return new Chart($(id), {
    type: "line",
    data: { labels: [], datasets: [{ data: [], borderColor: color, backgroundColor: color + "22", fill: true, tension: 0.3, pointRadius: 0 }] },
    options: { responsive: true, maintainAspectRatio: false, animation: false, plugins: { legend: { display: false } },
      scales: { x: { ticks: { color: "#8a9bb4", maxTicksLimit: 5 }, grid: { color: "#233246" } }, y: axis(max) } }
  });
}
const cpuChart = lineChart("chCpu", "#ff9900", 100);
const memChart = lineChart("chMem", "#6cb6ff", 100);
const netChart = lineChart("chNet", "#2ecc71");
const aiChart = new Chart($("chAi"), {
  type: "scatter",
  data: { datasets: [
    { label: "Normal", data: [], backgroundColor: "#2ecc71" },
    { label: "Anomaly", data: [], backgroundColor: "#ff4d4f", pointRadius: 6 }] },
  options: { responsive: true, maintainAspectRatio: false, animation: false,
    plugins: { legend: { labels: { color: "#e6edf5" } } },
    scales: { x: { title: { display: true, text: "CPU %", color: "#8a9bb4" }, ticks: { color: "#8a9bb4" }, grid: { color: "#233246" } },
              y: { title: { display: true, text: "Response time (ms)", color: "#8a9bb4" }, ticks: { color: "#8a9bb4" }, grid: { color: "#233246" } } } }
});

function setLine(chart, labels, values) {
  chart.data.labels = labels;
  chart.data.datasets[0].data = values;
  chart.update();
}

// ---------- one update cycle: ask Flask for new data ----------
async function tick() {
  const [m, l, a] = await Promise.all([
    fetch("/metrics").then(r => r.json()),
    fetch("/logs").then(r => r.json()),
    fetch("/anomaly").then(r => r.json())
  ]);
  const n = m.latest, h = m.history, labels = h.map(x => x.time);

  $("cCpu").textContent = n.cpu + "%";
  $("cMem").textContent = n.memory + "%";
  $("cNet").textContent = n.network + " MB/s";
  $("cReq").textContent = n.requests.toLocaleString();
  $("cRt").textContent = n.response_time + " ms";
  $("cAlerts").textContent = m.active_alerts;
  $("cAlerts").parentElement.classList.toggle("alert", m.active_alerts > 0);

  setLine(cpuChart, labels, h.map(x => x.cpu));
  setLine(memChart, labels, h.map(x => x.memory));
  setLine(netChart, labels, h.map(x => x.network));

  $("alertList").innerHTML = m.alerts.length
    ? m.alerts.map(x => `<li><b>🔴 ${x.name.toUpperCase()}</b><br>${x.message} <span class="hint">${x.time}</span></li>`).join("")
    : '<li class="empty">No alarms yet. Try "Simulate High CPU".</li>';

  $("logBox").innerHTML = l.map(x => `<div class="${x.level}">${x.time} [${x.level}] ${x.message}</div>`).join("");

  const bad = a.status === "Anomaly";
  $("status").className = "status " + (bad ? "bad" : "ok");
  $("status").textContent = bad ? "🔴 Anomaly Detected" : "🟢 System Status: Normal";
  $("aCount").textContent = a.count;
  $("aLatest").textContent = a.latest
    ? `${a.latest.time} (CPU ${a.latest.cpu}%, Memory ${a.latest.memory}%, ${a.latest.requests} req, ${a.latest.response_time} ms)`
    : "None yet";
  aiChart.data.datasets[0].data = a.points.filter(p => !p.anomaly);
  aiChart.data.datasets[1].data = a.points.filter(p => p.anomaly);
  aiChart.update();
}

// ---------- controls ----------
function start() {
  if (timer) return;
  tick();
  timer = setInterval(tick, 2000);
  $("monitorState").textContent = "Monitoring";
  $("monitorState").className = "pill on";
}
function stop() {
  clearInterval(timer);
  timer = null;
  $("monitorState").textContent = "Stopped";
  $("monitorState").className = "pill";
}
$("btnStart").onclick = start;
$("btnStop").onclick = stop;
document.querySelectorAll("[data-sim]").forEach(btn => {
  btn.onclick = async () => {
    await fetch("/simulate", { method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: btn.dataset.sim }) });
    if (timer) tick();
  };
});
start();
