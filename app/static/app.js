const sampleProducts = [
  {name: "Protein Powder", current_stock: 18, minimum_stock: 20, daily_sales: [5,6,5,7,6,8,7], lead_time_days: 4, target_days: 14, supplier: "Fitness Supply Co."},
  {name: "Shaker Bottle", current_stock: 85, minimum_stock: 30, daily_sales: [3,4,3,5,4,3,4], lead_time_days: 5, target_days: 14, supplier: "Fitness Supply Co."},
  {name: "Resistance Band", current_stock: 12, minimum_stock: 15, daily_sales: [4,5,4,6,5,5,7], lead_time_days: 3, target_days: 14, supplier: "Active Gear"},
  {name: "Yoga Mat", current_stock: 70, minimum_stock: 20, daily_sales: [2,2,3,2,3,2,2], lead_time_days: 7, target_days: 14, supplier: "Active Gear"}
];

let products = [];
const $ = id => document.getElementById(id);

function setMessage(text) { $("message").textContent = text; }
function esc(value) { return String(value ?? "").replace(/[&<>\"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c])); }

function render(data) {
  products = data.products || [];
  const summary = data.summary || {};
  $("total").textContent = summary.total_products ?? products.length;
  $("restock").textContent = summary.products_needing_restock ?? 0;
  $("critical").textContent = summary.critical_products ?? 0;
  $("healthy").textContent = products.filter(p => !p.needs_restock).length;
  $("productCount").textContent = `${products.length} product${products.length === 1 ? "" : "s"}`;
  $("tableBody").innerHTML = products.length ? products.map(p => `
    <tr><td>${esc(p.name)}</td><td>${p.current_stock}</td><td>${p.average_daily_sales}</td>
    <td>${p.days_remaining == null ? "—" : p.days_remaining}</td><td>${p.reorder_point}</td>
    <td>${p.suggested_reorder_quantity}</td><td><span class="badge ${esc(p.urgency)}">${esc(p.urgency)}</span></td></tr>`).join("") : '<tr><td colspan="7" class="empty">No products found.</td></tr>';
}

async function postJSON(url) {
  const response = await fetch(url, {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({products})});
  if (!response.ok) throw new Error(await response.text());
  return response.json();
}

async function analyze() {
  if (!products.length) { setMessage("Load sample data or import a CSV first."); return; }
  setMessage("Analyzing inventory...");
  try {
    render(await postJSON("/predict"));
    await refreshIntelligence();
    setMessage("Analysis complete and saved locally.");
  } catch (error) { setMessage(`Analysis failed: ${error.message}`); }
}

async function refreshIntelligence() {
  await Promise.all([loadAlerts(), loadOrders(), loadHistory()]);
}

async function loadAlerts() {
  if (!products.length) return;
  try {
    const data = await postJSON("/alerts");
    const report = data.alerts || {};
    const alerts = report.alerts || [];
    $("alerts").innerHTML = alerts.length ? alerts.map(alert => `
      <div class="alert-card ${esc(alert.urgency)}"><div class="alert-top"><span class="badge ${esc(alert.urgency)}">${esc(alert.urgency)}</span><strong>${esc(alert.product)}</strong></div>
      <p>${esc(alert.action)}</p><small>Suggested order: ${alert.suggested_reorder_quantity} units${alert.supplier ? ` · ${esc(alert.supplier)}` : " · supplier missing"}</small></div>`).join("") : '<p class="empty">No active inventory alerts.</p>';
  } catch (error) { $("alerts").innerHTML = '<p class="empty">Could not load alerts.</p>'; }
}

async function loadOrders() {
  if (!products.length) return;
  try {
    const data = await postJSON("/orders/preview");
    const orders = data.orders || [];
    const missing = data.products_without_supplier || [];
    let html = orders.length ? orders.map(order => `<div class="order-card"><div class="order-head"><strong>${esc(order.supplier)}</strong><span>${order.total_units} units</span></div>
      ${order.items.map(item => `<div class="order-item"><span>${esc(item.product)}</span><span>${item.quantity} · ${esc(item.urgency)}</span></div>`).join("")}<small>Manual confirmation required</small></div>`).join("") : '<p class="empty">No supplier orders are currently needed.</p>';
    if (missing.length) html += `<div class="notice"><strong>Supplier missing</strong><p>${missing.map(esc).join(", ")}</p><small>Add a supplier in the CSV before ordering.</small></div>`;
    $("orders").innerHTML = html;
  } catch (error) { $("orders").innerHTML = '<p class="empty">Could not load order preview.</p>'; }
}

async function loadHistory() {
  try {
    const response = await fetch("/history?limit=10");
    if (!response.ok) throw new Error(await response.text());
    const snapshots = (await response.json()).snapshots || [];
    $("history").innerHTML = snapshots.length ? snapshots.map(s => {
      const saved = s.products || {}; const summary = saved.summary || {};
      return `<div class="history-item"><div><strong>Analysis #${s.id}</strong><small>${esc(s.created_at)}</small></div><span>${Array.isArray(saved.products) ? saved.products.length : 0} products · ${summary.products_needing_restock ?? 0} restock</span></div>`;
    }).join("") : '<p class="empty">No saved analyses yet.</p>';
  } catch (error) { $("history").innerHTML = '<p class="empty">Could not load history.</p>'; }
}

$("sampleBtn").addEventListener("click", () => {
  products = structuredClone(sampleProducts); render({products: [], summary: {}});
  $("alerts").innerHTML = '<p class="empty">Analyze inventory to generate alerts.</p>';
  $("orders").innerHTML = '<p class="empty">Analyze inventory to generate an order preview.</p>';
  setMessage("Sample data loaded. Click Analyze inventory.");
});
$("analyzeBtn").addEventListener("click", analyze);
$("refreshBtn").addEventListener("click", async () => { setMessage("Refreshing dashboard..."); await loadHistory(); if (products.length) await refreshIntelligence(); setMessage("Dashboard refreshed."); });
$("csvInput").addEventListener("change", async event => {
  const file = event.target.files[0]; if (!file) return;
  const form = new FormData(); form.append("file", file); setMessage("Reading CSV...");
  try { const response = await fetch("/predict/csv", {method: "POST", body: form}); if (!response.ok) throw new Error(await response.text()); render(await response.json()); await refreshIntelligence(); setMessage("CSV analyzed and saved successfully."); }
  catch (error) { setMessage(`CSV import failed: ${error.message}`); }
});

loadHistory();
