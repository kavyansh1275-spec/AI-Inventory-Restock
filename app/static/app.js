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
    <tr>
      <td>${esc(p.name)}</td><td>${p.current_stock}</td><td>${p.average_daily_sales}</td>
      <td>${p.days_remaining == null ? "—" : p.days_remaining}</td><td>${p.reorder_point}</td>
      <td>${p.suggested_reorder_quantity}</td>
      <td><span class="badge ${esc(p.urgency)}">${esc(p.urgency)}</span></td>
    </tr>`).join("") : '<tr><td colspan="7" class="empty">No products found.</td></tr>';
}

async function analyze() {
  if (!products.length) { setMessage("Load sample data or import a CSV first."); return; }
  setMessage("Analyzing inventory...");
  try {
    const response = await fetch("/predict", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({products})});
    if (!response.ok) throw new Error(await response.text());
    render(await response.json());
    setMessage("Analysis complete.");
  } catch (error) { setMessage(`Analysis failed: ${error.message}`); }
}

$("sampleBtn").addEventListener("click", () => { products = structuredClone(sampleProducts); render({products: [], summary: {}}); setMessage("Sample data loaded. Click Analyze inventory."); });
$("analyzeBtn").addEventListener("click", analyze);
$("csvInput").addEventListener("change", async event => {
  const file = event.target.files[0];
  if (!file) return;
  const form = new FormData(); form.append("file", file);
  setMessage("Reading CSV...");
  try {
    const response = await fetch("/predict/csv", {method: "POST", body: form});
    if (!response.ok) throw new Error(await response.text());
    render(await response.json());
    setMessage("CSV analyzed successfully.");
  } catch (error) { setMessage(`CSV import failed: ${error.message}`); }
});
