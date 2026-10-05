// SAMPLE DATA ONLY. pnl is null while a trade is still open.
// premium = total dollars collected (per-share premium x 100 x contracts).
const trades = [
  { opened: "2026-01-06", ticker: "AAPL", type: "Cash-Secured Put", strike: 205, expiry: "2026-01-23", contracts: 1, premium: 210, status: "Closed", pnl: 210 },
  { opened: "2026-01-12", ticker: "MSFT", type: "Cash-Secured Put", strike: 400, expiry: "2026-01-30", contracts: 1, premium: 320, status: "Closed", pnl: 320 },
  { opened: "2026-01-20", ticker: "KO",   type: "Cash-Secured Put", strike: 60,  expiry: "2026-02-06", contracts: 3, premium: 195, status: "Closed", pnl: 195 },
  { opened: "2026-01-27", ticker: "AAPL", type: "Cash-Secured Put", strike: 200, expiry: "2026-02-13", contracts: 1, premium: 185, status: "Closed", pnl: -340 },
  { opened: "2026-02-03", ticker: "JNJ",  type: "Cash-Secured Put", strike: 150, expiry: "2026-02-20", contracts: 2, premium: 260, status: "Closed", pnl: 260 },
  { opened: "2026-02-10", ticker: "MSFT", type: "Cash-Secured Put", strike: 395, expiry: "2026-02-27", contracts: 1, premium: 290, status: "Closed", pnl: 290 },
  { opened: "2026-02-17", ticker: "AAPL", type: "Covered Call",     strike: 205, expiry: "2026-03-06", contracts: 1, premium: 150, status: "Closed", pnl: 150 },
  { opened: "2026-02-24", ticker: "KO",   type: "Cash-Secured Put", strike: 61,  expiry: "2026-03-13", contracts: 3, premium: 210, status: "Closed", pnl: 210 },
  { opened: "2026-03-03", ticker: "V",    type: "Cash-Secured Put", strike: 330, expiry: "2026-03-20", contracts: 1, premium: 340, status: "Closed", pnl: 340 },
  { opened: "2026-03-10", ticker: "JNJ",  type: "Cash-Secured Put", strike: 152, expiry: "2026-03-27", contracts: 2, premium: 245, status: "Closed", pnl: 245 },
  { opened: "2026-03-17", ticker: "AAPL", type: "Covered Call",     strike: 210, expiry: "2026-04-03", contracts: 1, premium: 140, status: "Closed", pnl: 140 },
  { opened: "2026-03-24", ticker: "MSFT", type: "Cash-Secured Put", strike: 390, expiry: "2026-04-10", contracts: 1, premium: 310, status: "Closed", pnl: -520 },
  { opened: "2026-04-01", ticker: "V",    type: "Cash-Secured Put", strike: 325, expiry: "2026-04-17", contracts: 1, premium: 305, status: "Closed", pnl: 305 },
  { opened: "2026-04-08", ticker: "KO",   type: "Covered Call",     strike: 64,  expiry: "2026-04-24", contracts: 3, premium: 120, status: "Closed", pnl: 120 },
  { opened: "2026-04-15", ticker: "JNJ",  type: "Cash-Secured Put", strike: 155, expiry: "2026-05-01", contracts: 2, premium: 230, status: "Closed", pnl: 230 },
  { opened: "2026-04-22", ticker: "MSFT", type: "Covered Call",     strike: 405, expiry: "2026-05-08", contracts: 1, premium: 260, status: "Closed", pnl: 260 },
  { opened: "2026-05-04", ticker: "AAPL", type: "Cash-Secured Put", strike: 208, expiry: "2026-05-22", contracts: 1, premium: 195, status: "Closed", pnl: 195 },
  { opened: "2026-05-12", ticker: "V",    type: "Covered Call",     strike: 340, expiry: "2026-05-29", contracts: 1, premium: 220, status: "Closed", pnl: 220 },
  { opened: "2026-05-19", ticker: "KO",   type: "Cash-Secured Put", strike: 62,  expiry: "2026-06-05", contracts: 3, premium: 200, status: "Closed", pnl: 200 },
  { opened: "2026-06-02", ticker: "JNJ",  type: "Covered Call",     strike: 160, expiry: "2026-06-19", contracts: 2, premium: 190, status: "Closed", pnl: 190 },
  { opened: "2026-06-09", ticker: "AAPL", type: "Cash-Secured Put", strike: 210, expiry: "2026-06-26", contracts: 1, premium: 205, status: "Closed", pnl: 205 },
  { opened: "2026-09-08", ticker: "MSFT", type: "Cash-Secured Put", strike: 410, expiry: "2026-09-25", contracts: 1, premium: 330, status: "Closed", pnl: 330 },
  { opened: "2026-09-21", ticker: "V",    type: "Cash-Secured Put", strike: 335, expiry: "2026-10-09", contracts: 1, premium: 315, status: "Open",   pnl: null },
  { opened: "2026-09-28", ticker: "KO",   type: "Covered Call",     strike: 66,  expiry: "2026-10-16", contracts: 3, premium: 135, status: "Open",   pnl: null },
];

const fmt = n => (n < 0 ? "-$" : "$") + Math.abs(n).toLocaleString();
const cls = n => (n > 0 ? "pos" : n < 0 ? "neg" : "");
const byId = id => document.getElementById(id);

let cumChart, tickerChart;

function getFiltered() {
  const t = byId("fTicker").value, s = byId("fType").value, st = byId("fStatus").value;
  return trades.filter(x => (!t || x.ticker === t) && (!s || x.type === s) && (!st || x.status === st));
}

function renderKpis(data) {
  const closed = data.filter(x => x.status === "Closed");
  const totalPnl = closed.reduce((a, x) => a + x.pnl, 0);
  const premium = data.reduce((a, x) => a + x.premium, 0);
  const wins = closed.filter(x => x.pnl > 0).length;
  const winRate = closed.length ? Math.round((wins / closed.length) * 100) : 0;
  const open = data.filter(x => x.status === "Open").length;
  const items = [
    ["Realized P&L", `<span class="${cls(totalPnl)}">${fmt(totalPnl)}</span>`],
    ["Premium collected", fmt(premium)],
    ["Win rate", closed.length ? winRate + "%" : "n/a"],
    ["Closed trades", closed.length],
    ["Open positions", open],
  ];
  byId("kpis").innerHTML = items
    .map(([l, v]) => `<div class="kpi"><div class="label">${l}</div><div class="value">${v}</div></div>`)
    .join("");
}

function renderCharts(data) {
  const closed = data.filter(x => x.status === "Closed").sort((a, b) => a.expiry.localeCompare(b.expiry));
  let run = 0;
  const labels = closed.map(x => x.expiry);
  const cum = closed.map(x => (run += x.pnl));

  const perTicker = {};
  closed.forEach(x => (perTicker[x.ticker] = (perTicker[x.ticker] || 0) + x.pnl));
  const tLabels = Object.keys(perTicker);
  const tVals = tLabels.map(k => perTicker[k]);

  const style = getComputedStyle(document.documentElement);
  const accent = style.getPropertyValue("--accent").trim();
  const green = style.getPropertyValue("--green").trim();
  const red = style.getPropertyValue("--red").trim();
  const muted = style.getPropertyValue("--muted").trim();
  const grid = style.getPropertyValue("--border").trim();
  const scales = {
    x: { ticks: { color: muted }, grid: { color: grid } },
    y: { ticks: { color: muted, callback: v => "$" + v }, grid: { color: grid } },
  };

  if (cumChart) cumChart.destroy();
  if (tickerChart) tickerChart.destroy();

  cumChart = new Chart(byId("cumChart"), {
    type: "line",
    data: { labels, datasets: [{ data: cum, borderColor: accent, backgroundColor: accent + "33", fill: true, tension: 0.25, pointRadius: 2 }] },
    options: { plugins: { legend: { display: false } }, scales },
  });
  tickerChart = new Chart(byId("tickerChart"), {
    type: "bar",
    data: { labels: tLabels, datasets: [{ data: tVals, backgroundColor: tVals.map(v => (v >= 0 ? green : red)) }] },
    options: { plugins: { legend: { display: false } }, scales },
  });
}

function renderTable(data) {
  const sorted = [...data].sort((a, b) => b.opened.localeCompare(a.opened));
  byId("rows").innerHTML = sorted
    .map(x => `<tr>
      <td>${x.opened}</td><td><strong>${x.ticker}</strong></td><td>${x.type}</td>
      <td>$${x.strike}</td><td>${x.expiry}</td><td>${x.contracts}</td>
      <td>${fmt(x.premium)}</td><td>${x.status}</td>
      <td class="${x.pnl === null ? "" : cls(x.pnl)}">${x.pnl === null ? "-" : fmt(x.pnl)}</td>
    </tr>`)
    .join("");
}

function render() {
  const data = getFiltered();
  renderKpis(data);
  renderCharts(data);
  renderTable(data);
}

[...new Set(trades.map(t => t.ticker))].sort().forEach(t => {
  const o = document.createElement("option");
  o.textContent = t;
  byId("fTicker").appendChild(o);
});
["fTicker", "fType", "fStatus"].forEach(id => byId(id).addEventListener("change", render));
render();
