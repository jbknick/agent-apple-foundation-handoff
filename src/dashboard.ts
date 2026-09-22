import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import type { DashboardSnapshot } from './store.js';

function safeJson(value: unknown): string {
  return JSON.stringify(value).replace(/</g, '\\u003c');
}

export function renderDashboard(data: DashboardSnapshot): string {
  const initial = safeJson(data);
  return `<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark"><title>Apple Offload Usage</title>
<link rel="icon" href="data:image/svg+xml,%3Csvg viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23070a0e'/%3E%3Cpath d='M18 43 31 14h5l11 29h-8l-2-6H27l-2 6zm11-12h6l-3-9z' fill='%236de8ff'/%3E%3C/svg%3E">
<style>
:root{--bg:#070a0e;--panel:#0d131a;--line:#26323e;--ink:#edf7ff;--muted:#8ba0b2;--cyan:#6de8ff;--lime:#b9ff66;--amber:#ffcc66;--red:#ff7383}*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at 85% -10%,#163544 0,transparent 34rem),var(--bg);color:var(--ink);font:14px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace}main{width:min(1180px,calc(100% - 32px));margin:auto;padding:40px 0 72px}header{display:flex;justify-content:space-between;gap:24px;align-items:flex-end;border-bottom:1px solid var(--line);padding-bottom:24px}h1{font:700 clamp(32px,6vw,68px)/.95 system-ui,sans-serif;letter-spacing:-.055em;margin:8px 0}.eyebrow,.label{color:var(--cyan);text-transform:uppercase;letter-spacing:.14em;font-size:11px}.muted{color:var(--muted)}button{border:1px solid var(--line);border-radius:99px;background:#111a23;color:var(--ink);padding:9px 14px;font:inherit;cursor:pointer}button:hover{border-color:var(--cyan)}.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:12px;margin-top:24px}.metric,.panel{background:color-mix(in srgb,var(--panel) 92%,transparent);border:1px solid var(--line);border-radius:14px}.metric{grid-column:span 3;padding:18px;min-height:126px;display:flex;flex-direction:column;justify-content:space-between}.value{font:650 34px/1 system-ui,sans-serif;letter-spacing:-.04em}.panel{grid-column:span 12;padding:20px;overflow:auto}h2{font:650 19px system-ui,sans-serif;margin:0 0 14px}table{width:100%;border-collapse:collapse;min-width:700px;text-align:left}th{color:var(--muted);font-size:11px;text-transform:uppercase;letter-spacing:.08em}th,td{padding:11px 10px;border-bottom:1px solid var(--line)}tbody tr:last-child td{border-bottom:0}.status{display:inline-flex;align-items:center;gap:7px}.status:before{content:'';width:7px;height:7px;border-radius:50%;background:var(--amber)}.status.ready:before{background:var(--lime)}.status.needs_codex:before,.status.blocked:before{background:var(--red)}.bar{height:5px;background:#1b2732;border-radius:9px;overflow:hidden;margin-top:7px}.bar>i{display:block;height:100%;background:linear-gradient(90deg,var(--cyan),var(--lime))}.empty{padding:36px 10px;color:var(--muted);text-align:center}footer{margin-top:18px;color:var(--muted);font-size:12px}@media(max-width:760px){main{width:min(100% - 20px,1180px);padding-top:24px}header{align-items:flex-start;flex-direction:column}.metric{grid-column:span 6}.value{font-size:28px}}@media(max-width:420px){.metric{grid-column:span 12}}
</style></head><body><main><header><div><div class="eyebrow">Local Foundation Models / private snapshot</div><h1>Apple Offload<br>Usage</h1><div class="muted" id="stamp"></div></div><button onclick="location.reload()" aria-label="Reload this published snapshot">Reload snapshot</button></header>
<section class="grid" aria-label="Usage summary"><article class="metric"><span class="label">Total runs</span><strong class="value" id="runs"></strong><span class="muted">Across recorded workspaces</span></article><article class="metric"><span class="label">Ready rate</span><strong class="value" id="rate"></strong><span class="muted">Validated results</span></article><article class="metric"><span class="label">Local model</span><strong class="value" id="local"></strong><span class="muted">On-device route</span></article><article class="metric"><span class="label">Avg latency</span><strong class="value" id="latency"></strong><span class="muted">End-to-end</span></article>
<article class="panel"><h2>Workspaces &amp; worktrees</h2><div id="workspaces"></div></article><article class="panel"><h2>Recent activity</h2><div id="recent"></div></article></section><footer>Aggregated metadata only. No prompts, artifacts, evidence, paths, run IDs, or model responses are included. Refresh requires a new local export and private Site publish.</footer></main>
<script>const d=${initial};const n=new Intl.NumberFormat();const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
stamp.textContent='Generated '+new Date(d.generatedAt).toLocaleString();runs.textContent=n.format(d.totals.runs);rate.textContent=d.totals.runs?Math.round(d.totals.ready/d.totals.runs*100)+'%':'—';local.textContent=n.format(d.totals.local);latency.textContent=d.totals.averageLatencyMs===null?'—':(d.totals.averageLatencyMs/1000).toFixed(1)+'s';
workspaces.innerHTML=d.workspaces.length?'<table><thead><tr><th>Workspace</th><th>Runs</th><th>Ready</th><th>Local</th><th>Shadow</th><th>Needs Codex</th><th>Avg latency</th></tr></thead><tbody>'+d.workspaces.map(w=>'<tr><td><strong>'+esc(w.name)+'</strong><div class="bar"><i style="width:'+(d.totals.runs?w.runs/d.totals.runs*100:0)+'%"></i></div></td><td>'+n.format(w.runs)+'</td><td>'+n.format(w.ready)+'</td><td>'+n.format(w.local)+'</td><td>'+n.format(w.shadow)+'</td><td>'+n.format(w.needsCodex)+'</td><td>'+(w.averageLatencyMs===null?'—':(w.averageLatencyMs/1000).toFixed(1)+'s')+'</td></tr>').join('')+'</tbody></table>':'<div class="empty">No usage recorded yet.</div>';
recent.innerHTML=d.recent.length?'<table><thead><tr><th>When</th><th>Workspace</th><th>Task</th><th>Mode</th><th>Route</th><th>Status</th><th>Latency</th></tr></thead><tbody>'+d.recent.map(r=>'<tr><td>'+esc(new Date(r.createdAt).toLocaleString())+'</td><td>'+esc(r.workspace)+'</td><td>'+esc(r.task)+'</td><td>'+esc(r.mode)+'</td><td>'+esc(r.route||'—')+'</td><td><span class="status '+esc(r.status)+'">'+esc(r.status)+'</span></td><td>'+(r.latencyMs/1000).toFixed(1)+'s</td></tr>').join('')+'</tbody></table>':'<div class="empty">No recent activity.</div>';</script></body></html>`;
}

export async function writeDashboard(outputDir: string, data: DashboardSnapshot): Promise<string> {
  const root = path.resolve(outputDir);
  await mkdir(path.join(root, 'dist'), { recursive: true, mode: 0o700 });
  await mkdir(path.join(root, '.openai'), { recursive: true, mode: 0o700 });
  const manifest = path.join(root, '.openai', 'hosting.json');
  try {
    await writeFile(path.join(root, 'dist', 'index.html'), renderDashboard(data), { mode: 0o600 });
    await writeFile(manifest, JSON.stringify({ static: { directory: 'dist' } }, null, 2) + '\n', { flag: 'wx', mode: 0o600 });
  } catch (error) {
    if (!(error instanceof Error) || !('code' in error) || error.code !== 'EEXIST') throw error;
    await writeFile(path.join(root, 'dist', 'index.html'), renderDashboard(data), { mode: 0o600 });
  }
  return path.join(root, 'dist', 'index.html');
}
