import json

TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Signal Router | Fireworks</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap">
<style>
  :root {
    --bg: #f7f7f8; --panel: #ffffff; --ink: #16181d; --muted: #6b7280; --line: #e4e4e7;
    --accent: #6726fe; --accent-soft: #f0eaff; --good: #157f4b; --good-soft: #e6f4ec;
    --warn: #a15c07; --warn-soft: #fbf0df; --cold: #55606e; --cold-soft: #eef0f3;
    --mono: "Favorit", "SF Mono", ui-monospace, Menlo, Consolas, monospace;
  }
  * { box-sizing: border-box; }
  body { margin: 0; background: var(--bg); color: var(--ink);
         font-size: 14px; line-height: 1.45;
         font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }
  .wrap { max-width: 1240px; margin: 0 auto; padding: 0 24px 64px; }
  header { background: var(--ink); color: #fff; border-bottom: 3px solid var(--accent); margin: 0 -24px;
           padding: 30px 24px; display: flex; flex-direction: column; align-items: center; text-align: center; gap: 12px; }
  h1 { margin: 0; font-size: 24px; font-weight: 600; letter-spacing: -0.02em; color: #fff;
       display: inline-flex; align-items: center; gap: 12px; }
  h1::before { content: ""; width: 14px; height: 14px; background: var(--accent); }
  .controls { display: flex; align-items: center; justify-content: space-between; gap: 16px; flex-wrap: wrap;
              margin: 24px 0 16px; padding: 12px; background: var(--panel); border: 1px solid var(--line); }
  .tabs, .chips { display: flex; gap: 6px; align-items: center; }
  .tab, .chip { border: 1px solid var(--line); background: var(--panel); color: var(--ink);
                padding: 8px 14px; cursor: pointer; font-family: var(--mono); font-size: 11px; font-weight: 600;
                text-transform: uppercase; letter-spacing: .06em; display: inline-flex; align-items: center; gap: 8px; }
  .tab.on { background: var(--ink); color: #fff; border-color: var(--ink); }
  .chip { padding: 6px 11px; }
  .chip.on { background: var(--accent-soft); border-color: var(--accent); color: var(--accent); }
  .chiplabel { font-family: var(--mono); font-size: 10px; text-transform: uppercase; letter-spacing: .08em; color: var(--muted); margin: 0 2px 0 10px; }
  .chiplabel:first-child { margin-left: 0; }
  .count { font-size: 10px; opacity: .75; }
  select { font: inherit; padding: 7px 10px; border: 1px solid var(--line); background: var(--panel); }
  label.viewas { display: inline-flex; align-items: center; gap: 8px; color: var(--muted);
                 font-family: var(--mono); font-size: 11px; text-transform: uppercase; letter-spacing: .06em; }

  .layout { display: grid; grid-template-columns: minmax(0, 1fr) 380px; gap: 20px; align-items: start; }
  @media (max-width: 1000px) { .layout { grid-template-columns: 1fr; } .side { position: static !important; } }

  .card { background: var(--panel); border: 1px solid var(--line); padding: 16px 18px; margin-bottom: 12px; }
  .card.sel { border-color: var(--accent); box-shadow: 0 0 0 3px var(--accent-soft); }
  .head { display: grid; grid-template-columns: 64px minmax(0, 1fr) auto; gap: 14px; align-items: center; cursor: pointer; }
  .score { width: 64px; height: 64px; display: flex; flex-direction: column; align-items: center; justify-content: center; }
  .score b { font-size: 22px; line-height: 1; font-weight: 600; }
  .score small { font-family: var(--mono); font-size: 9px; margin-top: 4px; letter-spacing: .08em; text-transform: uppercase; }
  .hot { background: var(--accent-soft); color: var(--accent); }
  .warm { background: var(--warn-soft); color: var(--warn); }
  .cool { background: var(--cold-soft); color: var(--cold); }
  .title h3 { margin: 0; font-size: 16px; font-weight: 600; letter-spacing: -0.01em; display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
  .rank { color: var(--muted); font-weight: 500; font-size: 13px; }
  .meta { color: var(--muted); font-size: 13px; margin-top: 2px; }
  .owner { text-align: right; font-size: 12px; color: var(--muted); }
  .owner b { display: block; color: var(--ink); font-size: 14px; }

  .signals { list-style: none; margin: 12px 0 0; padding: 0; display: grid; gap: 6px; }
  .signals li { display: grid; grid-template-columns: 150px minmax(0, 1fr) 56px 56px; gap: 10px; align-items: center;
                padding: 7px 10px; background: var(--bg); }
  .signals li.match { background: var(--accent-soft); box-shadow: inset 2px 0 0 var(--accent); }
  .type { font-family: var(--mono); font-size: 10px; text-transform: uppercase; letter-spacing: .06em; color: var(--accent); font-weight: 600; text-align: center;
          background: var(--accent-soft); padding: 3px 6px; }
  .sigscore { text-align: right; color: var(--muted); font-variant-numeric: tabular-nums; }
  .sigdate { text-align: right; color: var(--muted); font-size: 13px; white-space: nowrap; }

  .flags { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
  .flag { font-family: var(--mono); font-size: 10px; text-transform: uppercase; letter-spacing: .05em;
          background: var(--warn-soft); color: var(--warn); padding: 4px 8px; }

  .actions { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 12px; justify-content: flex-start; }
  .btn { border: 1px solid var(--line); background: var(--panel); padding: 8px 14px; cursor: pointer;
         font-family: var(--mono); font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: .06em;
         color: var(--ink); text-decoration: none; display: inline-flex; align-items: center; gap: 8px; }
  .btn:hover { border-color: var(--ink); }
  .btn.on { background: var(--accent); color: #fff; border-color: var(--accent); }
  .btn.primary { background: var(--accent); color: #fff; border-color: var(--accent); }

  .panel { margin-top: 12px; border-top: 1px solid var(--line); padding-top: 12px; }
  table.why { width: 100%; border-collapse: collapse; }
  table.why td { padding: 6px 8px; vertical-align: top; border-bottom: 1px dashed var(--line); }
  table.why td.pts { width: 70px; text-align: right; font-weight: 600; font-variant-numeric: tabular-nums; }
  table.why td.pts.neg { color: #b42318; }
  table.why .rule { color: var(--muted); font-size: 12px; }
  table.why .parts { color: var(--muted); font-size: 12px; margin-top: 3px; }
  table.why tr.total td { border-bottom: 0; border-top: 2px solid var(--ink); font-weight: 700; }
  .route { color: var(--muted); font-size: 13px; margin-top: 10px; }
  .brief { margin: 0; }
  .email label { display: block; font-size: 12px; color: var(--muted); margin: 6px 0 4px; }
  .email input, .email textarea { width: 100%; font: inherit; border: 1px solid var(--line); padding: 8px 10px; background: var(--bg); }
  .email textarea { min-height: 170px; resize: vertical; }
  .email .actions { justify-content: flex-end; }
  .empty { text-align: center; color: var(--muted); padding: 48px 0; background: var(--panel); border: 1px dashed var(--line); }

  .side { position: sticky; top: 16px; display: grid; gap: 16px; }
  .slack { background: #1a1d21; color: #d1d2d3; border-radius: 12px; overflow: hidden; border: 1px solid #2c2d30; }
  .slack .bar { background: #3f0e40; color: #fff; padding: 10px 14px; font-weight: 600; display: flex; justify-content: space-between; align-items: center; }
  .slack .bar span { font-weight: 400; opacity: .7; font-size: 12px; }
  .slack .msg { display: grid; grid-template-columns: 36px minmax(0, 1fr); gap: 10px; padding: 14px; }
  @keyframes slackpop {
    0% { opacity: 0; transform: translateY(-16px) scale(.95); }
    60% { opacity: 1; transform: translateY(3px) scale(1.01); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
  }
  .slack .msg.pop { animation: slackpop .45s cubic-bezier(.2, .9, .3, 1.15); transform-origin: top center; }
  .slack .avatar { width: 36px; height: 36px; border-radius: 8px; background: var(--accent); display: flex; align-items: center; justify-content: center; color: #fff; font-weight: 700; }
  .slack .who { color: #fff; font-weight: 700; }
  .slack .who small { color: #9a9b9e; font-weight: 400; margin-left: 6px; }
  .slack .attach { border-left: 4px solid var(--accent); padding: 4px 0 4px 10px; margin-top: 8px; }
  .slack .attach b { color: #fff; }
  .slack .fields { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 12px; margin-top: 8px; font-size: 12px; }
  .slack .fields div span { display: block; color: #9a9b9e; }
  .slack .sbtns { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 10px; }
  .slack .sbtn { border: 1px solid #565856; color: #fff; background: transparent; border-radius: 6px; padding: 5px 10px; font: inherit; font-size: 12px; cursor: pointer; text-decoration: none;
                 display: inline-flex; align-items: center; gap: 6px; }
  .slack .sbtn.go { background: #007a5a; border-color: #007a5a; }
  .slack .note { font-size: 11px; color: #9a9b9e; padding: 0 14px 12px; text-align: center; }

</style>
</head>
<body>
<div class="wrap">
  <header>
    <h1>Signal Router</h1>
  </header>

  <div class="controls">
    <div class="tabs" id="tabs"></div>
    <div class="chips" id="chips"></div>
    <label class="viewas">Viewing as <select id="seller"></select></label>
  </div>

  <div class="layout">
    <main id="list"></main>
    <aside class="side">
      <div class="slack" id="slack"></div>
    </aside>
  </div>
</div>

<script>
const DATA = __DATA__;
const state = { list: "customer", segment: "all", sigType: "all", seller: "all", selected: null, open: {}, pop: false };
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"']/g, (c) => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));
const heat = (score) => score >= 8 ? "hot" : score >= 6.5 ? "warm" : "cool";
const fmtDate = (iso) => new Date(iso).toLocaleDateString("en-US", { month: "short", day: "numeric", timeZone: "UTC" });
const pts = (p) => (p >= 0 ? "+" : "\u2212") + Math.abs(p).toFixed(1);
const TYPE = { usage_spike: "Usage spike", competitor_evaluation: "Competitor", intent_topic: "Intent", job_change: "Job change", funding_event: "Funding" };
const SF_LOGO = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" aria-hidden="true" focusable="false"><path fill="#00A1E0" d="M10.9 6.1a4.6 4.6 0 0 1 4.4-2.6 5 5 0 0 1 4.7 3.2 4.2 4.2 0 0 1 1.7 8H6.4a3.9 3.9 0 0 1-1.6-7.4 4.9 4.9 0 0 1 6.1-1.2z"/></svg>`;
const SEGMENTS = [["all", "All"], ["AI-Native", "AI-Native"], ["Enterprise-Expansion", "Enterprise Expansion"], ["Unknown", "Not in CRM"]];
const SIG_TYPES = [["all", "All"], ["usage_spike", "Usage spike"], ["competitor_evaluation", "Competitor"], ["intent_topic", "Intent"], ["job_change", "Job change"], ["funding_event", "Funding"]];

function visible(list) {
  return DATA.cards.filter((c) =>
    c.list === list &&
    (state.seller === "all" || (c.owner && c.owner.id === state.seller)) &&
    (state.segment === "all" || c.segment === state.segment) &&
    (state.sigType === "all" || c.signals.some((s) => s.type === state.sigType)));
}

function renderControls() {
  $("tabs").innerHTML = [["customer", "Customers"], ["prospect", "Prospects"]].map(([k, label]) =>
    `<button class="tab ${state.list === k ? "on" : ""}" data-list="${k}">${label} <span class="count">${visible(k).length}</span></button>`).join("");
  $("chips").innerHTML = `<span class="chiplabel">Segment</span>` + SEGMENTS.map(([k, label]) =>
    `<button class="chip ${state.segment === k ? "on" : ""}" data-seg="${k}">${label}</button>`).join("") +
    `<span class="chiplabel">Signal</span>` + SIG_TYPES.map(([k, label]) =>
    `<button class="chip ${state.sigType === k ? "on" : ""}" data-sig="${k}">${label}</button>`).join("");
  const opts = [`<option value="all">All sellers</option>`].concat(DATA.sellers.map((s) =>
    `<option value="${s.id}" ${state.seller === s.id ? "selected" : ""}>${esc(s.name)} (${s.cards})${s.status !== "active" ? " - " + s.status : ""}</option>`));
  $("seller").innerHTML = opts.join("");
}

function whyPanel(c) {
  const rows = c.breakdown.map((l) => `
    <tr><td class="pts ${l.points < 0 ? "neg" : ""}">${pts(l.points)}</td>
      <td>${esc(l.label)}<div class="rule">${esc(l.rule)}</div>
        ${l.parts.length ? `<div class="parts">${l.parts.map((p) => `${esc(p.label)} <b>${pts(p.points)}</b>`).join(" &middot; ")}</div>` : ""}
      </td></tr>`).join("");
  return `<table class="why">${rows}
    <tr class="total"><td class="pts">${c.score_100.toFixed(1)}</td><td>Total out of 100, shown as ${c.score.toFixed(1)} / 10</td></tr></table>`;
}

function emailPanel(c) {
  return `<div class="email">
    <label>Subject</label><input value="${esc(c.email.subject)}" readonly>
    <label>Body</label><textarea readonly>${esc(c.email.body)}</textarea>
    <div class="actions">
      <button class="btn" data-copy="${esc(c.key)}">Copy email</button>
      <a class="btn primary" href="${esc(c.email.mailto)}">Open in mail</a>
    </div></div>`;
}

function cardHtml(c) {
  const open = state.open[c.key];
  const meta = c.account_id
    ? [c.region, c.tier, c.segment, c.industry, c.arr_band + " ARR"].join(" &middot; ")
    : [c.region, esc(c.domain), "not in CRM"].join(" &middot; ");
  const signals = c.signals.map((s) => `<li class="${state.sigType !== "all" && s.type === state.sigType ? "match" : ""}"><span class="type">${TYPE[s.type] || s.type}</span><span>${esc(s.headline)}</span><time class="sigdate" datetime="${s.timestamp}">${fmtDate(s.timestamp)}</time><span class="sigscore" title="What this signal added to the ${c.score.toFixed(1)} score, after stacking and blending">+${(s.contribution / 10).toFixed(1)}</span></li>`).join("");
  const flags = c.flags.length ? `<div class="flags">${c.flags.map((f) => `<span class="flag">${esc(f)}</span>`).join("")}</div>` : "";
  const btn = (k, label) => `<button class="btn ${open === k ? "on" : ""}" data-open="${k}" data-key="${esc(c.key)}">${label}</button>`;
  let panel = "";
  if (open === "why") panel = whyPanel(c);
  if (open === "brief") panel = `<p class="brief">${esc(c.brief)}</p><div class="route">Routing: ${esc(c.route_reason)}</div>`;
  if (open === "email") panel = emailPanel(c);
  return `<article class="card ${state.selected === c.key ? "sel" : ""}" id="card-${esc(c.key)}">
    <div class="head" data-select="${esc(c.key)}">
      <div class="score ${heat(c.score)}"><b>${c.score.toFixed(1)}</b><small>score</small></div>
      <div class="title"><h3><span class="rank">#${c.rank}</span>${esc(c.name)}</h3><div class="meta">${meta}</div></div>
      <div class="owner">Owner<b>${c.owner ? esc(c.owner.name) : "Hold queue"}</b></div>
    </div>
    <ul class="signals">${signals}</ul>
    ${flags}
    <div class="actions">
      ${btn("why", "Why this score")}${btn("brief", "Research brief")}${btn("email", "Draft email")}
      <a class="btn" href="${esc(c.salesforce_url)}" target="_blank" rel="noopener">${SF_LOGO}${c.account_id ? "Open in Salesforce" : "Create in Salesforce"}</a>
    </div>
    ${panel ? `<div class="panel">${panel}</div>` : ""}
  </article>`;
}

function renderList() {
  const cards = visible(state.list);
  if (cards.length && !cards.some((c) => c.key === state.selected)) state.selected = cards[0].key;
  $("list").innerHTML = cards.length ? cards.map(cardHtml).join("") : `<div class="empty">No ${state.list === "customer" ? "customer" : "prospect"} cards for this filter.</div>`;
}

function renderSlack() {
  const c = DATA.cards.find((x) => x.key === state.selected);
  if (!c) { $("slack").innerHTML = `<div class="bar">Slack preview</div><div class="note">Select a card to preview its alert.</div>`; return; }
  const channel = c.owner ? "@" + c.owner.name.split(" ")[0].toLowerCase() : "#signals-hold";
  $("slack").innerHTML = `
    <div class="bar">${esc(channel)} <span>Slack preview (mock)</span></div>
    <div class="msg${state.pop ? " pop" : ""}">
      <div class="avatar">SR</div>
      <div>
        <div class="who">Signal Router <small>APP &middot; 9:02 AM</small></div>
        <div class="attach">
          <b>${esc(c.name)}</b> &middot; ${c.score.toFixed(1)} / 10 &middot; ${c.list === "customer" ? "Customer" : "Prospect"}
          <div style="margin-top:6px">${esc(c.signals[0].headline)}${c.signals.length > 1 ? ` <i>(+${c.signals.length - 1} more)</i>` : ""}</div>
          <div style="margin-top:6px">${esc(c.play)}</div>
          <div class="fields">
            <div><span>Owner</span>${c.owner ? esc(c.owner.name) : "Hold queue"}</div>
            <div><span>Region / tier</span>${esc(c.region)} &middot; ${esc(c.tier)}</div>
            <div><span>Top driver</span>${esc(c.signals[0].headline)} (+${(c.breakdown[0].points / 10).toFixed(1)})</div>
            <div><span>Fit</span>${c.components.fit.toFixed(0)} / 100</div>
          </div>
          <div class="sbtns">
            <button class="sbtn go" data-jump="${esc(c.key)}">Open in dashboard</button>
            <button class="sbtn" data-jump="${esc(c.key)}" data-then="email">Draft email</button>
            <a class="sbtn" href="${esc(c.salesforce_url)}" target="_blank" rel="noopener">${SF_LOGO}Salesforce</a>
          </div>
        </div>
      </div>
    </div>
    <div class="note">In production this posts as a DM to the owner. Here it previews the selected card.</div>`;
  state.pop = false;
}

function render() { renderControls(); renderList(); renderSlack(); }

document.addEventListener("click", (e) => {
  const t = e.target.closest("[data-list],[data-seg],[data-sig],[data-open],[data-select],[data-copy],[data-jump]");
  if (!t) return;
  if (t.dataset.list) { state.list = t.dataset.list; state.selected = null; }
  else if (t.dataset.seg) { state.segment = t.dataset.seg; state.selected = null; }
  else if (t.dataset.sig) { state.sigType = t.dataset.sig; state.selected = null; }
  else if (t.dataset.open) {
    const k = t.dataset.key;
    state.open[k] = state.open[k] === t.dataset.open ? null : t.dataset.open;
    if (state.selected !== k) state.pop = true;
    state.selected = k;
  }
  else if (t.dataset.select) { state.pop = true; state.selected = t.dataset.select; }
  else if (t.dataset.copy) {
    const c = DATA.cards.find((x) => x.key === t.dataset.copy);
    navigator.clipboard && navigator.clipboard.writeText(`Subject: ${c.email.subject}\n\n${c.email.body}`);
    t.textContent = "Copied";
    return;
  }
  else if (t.dataset.jump) {
    const c = DATA.cards.find((x) => x.key === t.dataset.jump);
    state.list = c.list;
    if (state.selected !== c.key) state.pop = true;
    state.selected = c.key;
    if (state.seller !== "all" && (!c.owner || c.owner.id !== state.seller)) state.seller = "all";
    if (state.segment !== "all" && c.segment !== state.segment) state.segment = "all";
    if (t.dataset.then) state.open[c.key] = t.dataset.then;
    render();
    document.getElementById("card-" + c.key).scrollIntoView({ behavior: "smooth", block: "center" });
    return;
  }
  render();
});
$("seller").addEventListener("change", (e) => {
  state.seller = e.target.value; state.selected = null;
  const other = state.list === "customer" ? "prospect" : "customer";
  if (!visible(state.list).length && visible(other).length) state.list = other;
  render();
});

render();
</script>
</body>
</html>
"""


def render_html(output) -> str:
    payload = json.dumps(output).replace("</", "<\\/")
    return TEMPLATE.replace("__DATA__", payload)
