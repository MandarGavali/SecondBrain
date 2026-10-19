"use strict";

/* ==========================================================================
   SecondBrain web UI — vanilla JS, no build step. Served by FastAPI at "/".
   ========================================================================== */

// ---------- small utils ----------
const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
const escapeHtml = (s) => String(s ?? "").replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const icon = (name, cls = "") => `<svg class="${cls}"><use href="#i-${name}"/></svg>`;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));
const pct = (v) => `${Math.round(v * 100)}%`;
const fmtMs = (ms) => (ms >= 1000 ? `${(ms / 1000).toFixed(ms >= 10000 ? 0 : 1)} s` : `${Math.round(ms)} ms`);
const prettyDoc = (name) => (name || "unknown").replace(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_/i, "");
const timeAgo = (ts) => {
  const s = Math.max(1, Math.round((Date.now() - ts) / 1000));
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return new Date(ts).toLocaleDateString();
};

function el(tag, className, html) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (html !== undefined) node.innerHTML = html;
  return node;
}

const store = {
  get(key, fallback) {
    try { const v = localStorage.getItem(key); return v == null ? fallback : JSON.parse(v); } catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* private mode: memory only */ }
  },
};

// ---------- api ----------
async function api(path, options = {}) {
  const res = await fetch(path, options);
  let body = null;
  try { body = await res.json(); } catch { /* non-JSON body */ }
  if (!res.ok) throw new Error(errorMessage(res.status, body));
  return body;
}
const postJson = (path, data) => api(path, {
  method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(data),
});

function errorMessage(status, body) {
  const detail = body?.detail ?? body?.error?.message;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
  if (detail) return String(detail);
  if (status === 503) return "The language model is temporarily unavailable. Please try again later.";
  return `Request failed (HTTP ${status}).`;
}

function toast(text, kind = "info", ms = 3800) {
  const t = el("div", `toast ${kind}`, `${icon(kind === "ok" ? "check" : kind === "err" ? "alert" : "bolt")}<div>${escapeHtml(text)}</div>`);
  $("#toasts").append(t);
  setTimeout(() => { t.classList.add("out"); setTimeout(() => t.remove(), 300); }, ms);
}

// ==========================================================================
// domain knowledge: pipeline nodes, routes, tools
// ==========================================================================
const ROUTES = {
  no_search: { label: "Direct answer", short: "Direct", color: "var(--c-nosearch)", desc: "Small talk or general knowledge: answered by the chat model without touching the vector store." },
  simple: { label: "Quick lookup", short: "Lookup", color: "var(--c-simple)", desc: "Single-fact question: one top-k retrieval, a grounded answer, then verification." },
  complex: { label: "Agent", short: "Agent", color: "var(--c-complex)", desc: "Multi-step reasoning: LO-MCP picks the relevant tools and a tool-calling agent loops until it is done." },
};
const CONF_COLORS = { High: "var(--high)", Medium: "var(--medium)", Low: "var(--low)" };
const GROUP_COLORS = { memory: "var(--c-memory)", route: "var(--c-route)", rag: "var(--c-rag)", agent: "var(--c-agent)", verify: "var(--c-verify)" };

const NODES = {
  recall_memory: { x: 95, y: 320, group: "memory", tag: "P3", title: "Recall memory", metric: "t_memory_ms",
    desc: "Searches the user's Mem0 long-term memory with the question and drops memories AAM marked as deprecated. The survivors are injected into the prompt." },
  classify: { x: 275, y: 320, group: "route", tag: "P1", title: "Classify", metric: "t_classify_ms",
    desc: "Adaptive router. Cheap regex heuristics decide first; only when unsure does a Gemini zero-shot call pick no_search, simple or complex. Any failure falls back to complex." },
  chat: { x: 470, y: 90, group: "agent", tag: "P1", title: "Chat", metric: "t_chat_ms",
    desc: "Direct conversational answer for greetings and general questions. No retrieval, so it costs one LLM call and verification is skipped (confidence N/A)." },
  retrieve: { x: 470, y: 320, group: "rag", tag: "RAG", title: "Retrieve", metric: "t_retrieve_ms",
    desc: "Top-k similarity search in Qdrant with Gemini embeddings (k = SIMPLE_K, or RETRY_K on a retry). Every chunk keeps its similarity score as evidence." },
  generate: { x: 660, y: 320, group: "rag", tag: "RAG", title: "Generate", metric: "t_generate_ms",
    desc: "Gemini writes an answer grounded only in the retrieved chunks, citing pages. The model's own verbal confidence is stripped and replaced by a measured one." },
  rewrite: { x: 660, y: 180, group: "verify", tag: "P4", title: "Rewrite", metric: null,
    desc: "When verification fails, the query is rewritten by Gemini and retrieval runs again with a larger k. Happens at most MAX_RETRIES times." },
  select_tools: { x: 470, y: 510, group: "agent", tag: "P2", title: "Select tools", metric: "t_select_tools_ms",
    desc: "LO-MCP: embeds the query, compares it with cached tool embeddings and binds only the tools near the best score. Fewer schemas means fewer prompt tokens and fewer wrong tool calls." },
  agent: { x: 660, y: 510, group: "agent", tag: "Agent", title: "Agent", metric: "t_agent_",
    desc: "Tool-calling Gemini agent with the selected tools only. It loops with the tool node until it answers or hits MAX_AGENT_STEPS." },
  tools: { x: 660, y: 615, group: "agent", tag: "MCP", title: "Tools", metric: null,
    desc: "Executes the tool calls: search_documents, list_documents, summarize_documents, generate_questions. search_documents returns its chunks as an artifact so they become evidence." },
  collect_evidence: { x: 850, y: 510, group: "verify", tag: "P4", title: "Collect evidence", metric: null,
    desc: "Gathers the chunks every tool call returned during this turn, de-duplicated, so the agent's answer can be verified like a RAG answer." },
  verify: { x: 850, y: 320, group: "verify", tag: "P4", title: "Verify", metric: "t_verify_ms",
    desc: "Measured confidence C = w1·top-score + w2·relevance-ratio + w3·grounded. An LLM judge checks groundedness. The result decides: deliver, retry or abstain." },
  abstain: { x: 1040, y: 180, group: "verify", tag: "P4", title: "Abstain", metric: null,
    desc: "Rather than hallucinate, the system says it could not find reliable evidence and flags the question for review." },
  finalize: { x: 1040, y: 320, group: "route", tag: "Core", title: "Finalize", metric: "t_finalize_ms",
    desc: "Writes the final answer into the checkpointed history, closes any dangling tool calls so Gemini's history stays valid, and (with AAM off) saves memory per turn." },
};
const EDGES = [
  ["recall_memory", "classify"],
  ["classify", "chat", "no_search", [380, 110]],
  ["classify", "retrieve", "simple"],
  ["classify", "select_tools", "complex", [380, 500]],
  ["chat", "finalize", null, [1040, 90]],
  ["retrieve", "generate"],
  ["generate", "verify"],
  ["select_tools", "agent"],
  ["agent", "tools", "tools", [615, 565]],
  ["tools", "agent", null, [705, 565]],
  ["agent", "collect_evidence", "done"],
  ["collect_evidence", "verify"],
  ["verify", "finalize", "deliver"],
  ["verify", "rewrite", "retry", [800, 200]],
  ["rewrite", "retrieve", null, [520, 200]],
  ["verify", "abstain", "abstain", [930, 220]],
  ["abstain", "finalize"],
];
const NODE_W = 150, NODE_H = 52;

const TOOLS = {
  search_documents: "Semantic search over the indexed chunks; returns evidence with scores.",
  list_documents: "Names of every indexed document.",
  summarize_documents: "Retrieves and summarises the knowledge base.",
  generate_questions: "Generates practice or interview questions from the documents.",
};
const MCP_TOOLS = [
  ["ask_secondbrain", "Full adaptive turn, returns the answer"],
  ["search_documents", "Raw semantic search over the knowledge base"],
  ["upload_document", "Index a PDF from a path"],
  ["remember", "Store a fact in long-term memory"],
  ["list_memories", "Active memories (deprecated hidden)"],
  ["forget", "Delete a memory and its AAM status"],
  ["end_session", "Trigger AAM reflection"],
  ["discover_tools", "LO-MCP: only the schemas relevant to a task"],
];

/** The node sequence a turn went through, inferred from its metrics. */
function pathFor(r) {
  if (!r || !r.route) return null;
  const m = r.metrics || {};
  const p = ["recall_memory", "classify"];
  if (r.route === "no_search") p.push("chat");
  else if (r.route === "simple") p.push("retrieve", "generate", "verify");
  else {
    const steps = Math.max(1, Object.keys(m).filter((k) => /^t_agent_\d+_ms$/.test(k)).length);
    p.push("select_tools");
    for (let i = 0; i < steps; i++) { p.push("agent"); if (i < steps - 1) p.push("tools"); }
    p.push("collect_evidence", "verify");
  }
  if (r.route !== "no_search") {
    for (let i = 0; i < (m.retries || 0); i++) p.push("rewrite", "retrieve", "generate", "verify");
  }
  if (r.abstained) p.push("abstain");
  p.push("finalize");
  return p;
}

function nodeTime(name, m) {
  const key = NODES[name]?.metric;
  if (!key || !m) return null;
  if (key === "t_agent_") {
    const vals = Object.entries(m).filter(([k]) => /^t_agent_\d+_ms$/.test(k)).map(([, v]) => v);
    return vals.length ? vals.reduce((a, b) => a + b, 0) : null;
  }
  return typeof m[key] === "number" ? m[key] : null;
}

// ==========================================================================
// state
// ==========================================================================
const state = {
  threads: store.get("sb.threads", []),
  activeId: store.get("sb.active", null),
  userId: store.get("sb.userId", "me"),
  system: null,
  selected: null,           // { threadId, index }
  busy: false,
  view: "chat",
  uploads: store.get("sb.uploads", {}),
  documents: [],
};

const saveThreads = () => { store.set("sb.threads", state.threads); store.set("sb.active", state.activeId); };
const newThreadId = () => Math.floor(100000 + Math.random() * 900000000);
const activeThread = () => state.threads.find((t) => t.id === state.activeId);
const allTurns = () => state.threads.flatMap((t) => t.turns.filter((x) => x.r).map((x, i) => ({ ...x, thread: t })));
const flag = (name) => state.system?.flags?.[name];

function ensureThread() {
  let t = activeThread();
  if (!t) {
    t = { id: newThreadId(), title: "New conversation", created: Date.now(), updated: Date.now(), turns: [] };
    state.threads.unshift(t);
    state.activeId = t.id;
    saveThreads();
  }
  return t;
}

// ==========================================================================
// navigation
// ==========================================================================
const VIEW_TITLES = { chat: "Chat", knowledge: "Knowledge base", memory: "Memory", pipeline: "Pipeline", lab: "Tool Lab", analytics: "Analytics", system: "System" };

function switchView(name) {
  if (!VIEW_TITLES[name]) return;
  state.view = name;
  $$(".rail-btn[data-view]").forEach((b) => b.classList.toggle("active", b.dataset.view === name));
  $$(".view").forEach((v) => v.classList.toggle("active", v.id === `view-${name}`));
  $("#viewTitle").textContent = VIEW_TITLES[name];
  $("#rail").classList.remove("open");
  if (name === "knowledge") loadDocuments();
  if (name === "memory") loadMemory();
  if (name === "pipeline") renderPipelineView();
  if (name === "analytics") renderAnalytics();
  if (name === "system") renderSystem();
  if (name === "chat") $("#input").focus();
}

// ==========================================================================
// markdown (small and safe)
// ==========================================================================
const inline = (s) => escapeHtml(s)
  .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
  .replace(/(^|[^*])\*([^*\s][^*]*?)\*(?!\*)/g, "$1<em>$2</em>")
  .replace(/`([^`]+)`/g, "<code>$1</code>");
const SECTION = /^\s*\**(Answer|Evidence Summary|Source Pages|Sources)\**\s*:\s*\**\s*(.*)$/i;

function renderMarkdown(text) {
  const out = [];
  let para = [], list = null, listType = "ul", code = null;
  const flushPara = () => { if (para.length) { out.push(`<p>${para.map(inline).join("<br>")}</p>`); para = []; } };
  const flushList = () => { if (list) { out.push(`<${listType}>${list.map((li) => `<li>${inline(li)}</li>`).join("")}</${listType}>`); list = null; } };
  for (const raw of String(text || "").split("\n")) {
    const line = raw.trimEnd();
    if (/^```/.test(line.trim())) {
      if (code) { out.push(`<pre>${escapeHtml(code.join("\n"))}</pre>`); code = null; }
      else { flushPara(); flushList(); code = []; }
      continue;
    }
    if (code) { code.push(raw); continue; }
    const section = line.match(SECTION);
    const heading = line.match(/^\s*#{1,6}\s+(.*)$/);
    const bullet = line.match(/^\s*[-*•]\s+(.*)$/);
    const numbered = line.match(/^\s*\d+[.)]\s+(.*)$/);
    if (!line.trim()) { flushPara(); flushList(); }
    else if (section) { flushPara(); flushList(); out.push(`<h4>${escapeHtml(section[1])}</h4>`); if (section[2]) para.push(section[2]); }
    else if (heading) { flushPara(); flushList(); out.push(`<h4>${inline(heading[1].replace(/\*\*/g, ""))}</h4>`); }
    else if (bullet || numbered) {
      flushPara();
      const type = numbered ? "ol" : "ul";
      if (list && listType !== type) flushList();
      listType = type;
      (list ??= []).push((bullet || numbered)[1]);
    } else { flushList(); para.push(line); }
  }
  if (code) out.push(`<pre>${escapeHtml(code.join("\n"))}</pre>`);
  flushPara(); flushList();
  return out.join("");
}
const plainText = (md) => String(md || "").replace(/[*`#>]/g, "").replace(/\n{2,}/g, "\n");

// ==========================================================================
// chat: threads
// ==========================================================================
function renderThreads() {
  const list = $("#threadList");
  const q = $("#threadFilter").value.trim().toLowerCase();
  list.innerHTML = "";
  const items = state.threads.filter((t) => !q || t.title.toLowerCase().includes(q) ||
    t.turns.some((x) => x.q.toLowerCase().includes(q)));
  if (!items.length) {
    list.append(el("li", "empty-note", state.threads.length ? "No matches" : "No conversations yet"));
    return;
  }
  for (const t of items) {
    const routes = [...new Set(t.turns.map((x) => x.r?.route).filter(Boolean))];
    const li = el("li", t.id === state.activeId ? "active" : "", `
      <span class="t-title">${escapeHtml(t.title)}</span>
      <span class="t-meta">${t.turns.length} msg · ${timeAgo(t.updated)} ${routes.map((r) => `<span class="tag ${r}">${ROUTES[r]?.short || r}</span>`).join("")}</span>
      <button class="icon-btn t-del" title="Delete conversation">${icon("trash")}</button>`);
    li.addEventListener("click", () => openThread(t.id));
    $(".t-del", li).addEventListener("click", (e) => { e.stopPropagation(); deleteThread(t.id); });
    list.append(li);
  }
}

function openThread(id) {
  state.activeId = id;
  saveThreads();
  renderThreads();
  renderConversation();
  const t = activeThread();
  const last = t?.turns.map((x, i) => (x.r ? i : -1)).filter((i) => i >= 0).pop();
  if (last != null) selectTurn(t.id, last, false); else renderInspector(null);
}

function deleteThread(id) {
  state.threads = state.threads.filter((t) => t.id !== id);
  if (state.activeId === id) state.activeId = state.threads[0]?.id ?? null;
  if (state.selected?.threadId === id) state.selected = null;
  saveThreads();
  renderThreads();
  renderConversation();
  renderInspector(state.selected ? getTurn(state.selected) : null);
}

function startNewChat() {
  state.activeId = null;
  saveThreads();
  renderThreads();
  renderConversation();
  renderInspector(null);
  switchView("chat");
}

// ==========================================================================
// chat: messages
// ==========================================================================
function renderConversation() {
  const box = $("#messages");
  $$(".msg", box).forEach((m) => m.remove());
  const t = activeThread();
  $("#hero").hidden = !!(t && t.turns.length);
  if (!t) return;
  t.turns.forEach((turn, i) => {
    box.append(userMsg(turn.q));
    const node = el("div", "msg bot");
    box.append(node);
    if (turn.r) fillAnswer(node, t, i, false);
    else if (turn.error) fillError(node, turn.error);
  });
  box.scrollTop = box.scrollHeight;
}

function userMsg(text) {
  const m = el("div", "msg user");
  const b = el("div", "bubble");
  b.textContent = text;
  m.append(b);
  return m;
}

const THINK_STEPS = ["Recalling long-term memory", "Routing the question", "Retrieving evidence / selecting tools", "Generating the answer", "Verifying against the sources"];

function thinkingMsg() {
  const node = el("div", "msg bot");
  node.innerHTML = `<div class="avatar"><i></i></div><div class="bot-body"><div class="answer-card"><div class="thinking">
    ${THINK_STEPS.map((s, i) => `<div class="think-row${i === 0 ? " active" : ""}"><span class="dot"></span>${s}${i === 0 ? '<span class="think-time">0.0 s</span>' : ""}</div>`).join("")}
  </div></div></div>`;
  const rows = $$(".think-row", node);
  const timer = $(".think-time", node);
  const started = performance.now();
  let step = 0;
  const tick = setInterval(() => {
    timer.textContent = `${((performance.now() - started) / 1000).toFixed(1)} s`;
  }, 100);
  const adv = setInterval(() => {
    if (step >= rows.length - 1) return;
    rows[step].classList.replace("active", "done");
    step += 1;
    rows[step].classList.add("active");
    rows[step].append(timer);
  }, 1700);
  node.stop = () => { clearInterval(tick); clearInterval(adv); };
  return node;
}

async function send(text) {
  const query = String(text || "").trim();
  if (!query || state.busy) return;
  switchView("chat");
  state.busy = true;
  $("#sendBtn").disabled = true;
  $("#input").value = "";
  autosize();

  const t = ensureThread();
  if (!t.turns.length) t.title = query.length > 48 ? `${query.slice(0, 46)}…` : query;
  const turn = { q: query, ts: Date.now() };
  t.turns.push(turn);
  t.updated = Date.now();
  saveThreads();
  renderThreads();

  const box = $("#messages");
  $("#hero").hidden = true;
  box.append(userMsg(query));
  const pending = thinkingMsg();
  box.append(pending);
  box.scrollTop = box.scrollHeight;

  try {
    const r = await postJson("/chat", { query, thread_id: t.id, user_id: state.userId || null });
    turn.r = r;
    pending.stop();
    $$(".think-row", pending).forEach((row) => { row.classList.remove("active"); row.classList.add("done"); });
    await sleep(250);
    const idx = t.turns.indexOf(turn);
    fillAnswer(pending, t, idx, true);
    selectTurn(t.id, idx, false);
  } catch (e) {
    pending.stop();
    turn.error = e.message;
    fillError(pending, e.message);
    toast(e.message, "err");
  } finally {
    t.updated = Date.now();
    saveThreads();
    renderThreads();
    state.busy = false;
    $("#sendBtn").disabled = false;
    $("#input").focus();
  }
}

function fillError(node, text) {
  node.className = "msg bot error";
  node.innerHTML = `<div class="avatar"><i></i></div><div class="bot-body"><div class="answer-card"><div class="answer-text">${icon("alert")} ${escapeHtml(text)}</div></div></div>`;
}

function answerPills(r) {
  const pills = [];
  if (r.route) pills.push(`<span class="pill r-${r.route}">${icon("route")}${escapeHtml(ROUTES[r.route]?.label || r.route)}</span>`);
  if (r.confidence) {
    const score = typeof r.confidence_score === "number" ? ` · ${pct(r.confidence_score)}` : "";
    pills.push(`<span class="pill ${escapeHtml(r.confidence)}">${escapeHtml(r.confidence)} confidence${score}</span>`);
  }
  if (r.grounded === true) pills.push(`<span class="pill ok">${icon("check")}Grounded</span>`);
  if (r.grounded === false) pills.push(`<span class="pill bad">${icon("alert")}Not grounded</span>`);
  if (r.metrics?.retries) pills.push(`<span class="pill warn">${icon("redo")}Rewritten ×${r.metrics.retries}</span>`);
  const lat = r.metrics?.latency_ms;
  if (typeof lat === "number") pills.push(`<span class="pill">${icon("clock")}${fmtMs(lat)}</span>`);
  return pills.join("");
}

function fillAnswer(node, thread, index, animate) {
  const turn = thread.turns[index];
  const r = turn.r;
  node.className = "msg bot";
  node.dataset.thread = thread.id;
  node.dataset.index = index;
  const path = pathFor(r);
  node.innerHTML = `
    <div class="avatar"><i></i></div>
    <div class="bot-body">
      <div class="answer-card">
        <div class="answer-top">${answerPills(r)}</div>
        <div class="answer-text"></div>
        ${r.needs_review ? `<div class="review-banner">${icon("alert")}<span>Not enough reliable evidence was found, so the system abstained instead of guessing. Flagged for review.</span></div>` : ""}
        ${path ? `<div class="mini-path">${path.map((n) => `<span class="${NODES[n].group}">${n}</span>`).join("<b>→</b>")}</div>` : ""}
      </div>
      ${r.sources?.length ? `<div class="sources"></div>` : ""}
      <div class="actions">
        <button class="icon-btn" data-act="copy" title="Copy answer">${icon("copy")}</button>
        <button class="icon-btn" data-act="speak" title="Read aloud">${icon("speak")}</button>
        <button class="icon-btn" data-act="retry" title="Ask again">${icon("redo")}</button>
        <button class="icon-btn${turn.fb === 1 ? " on" : ""}" data-act="up" title="Good answer">${icon("up")}</button>
        <button class="icon-btn${turn.fb === -1 ? " on" : ""}" data-act="down" title="Bad answer">${icon("down")}</button>
        <span class="spacer"></span>
        <button class="inspect-link" data-act="inspect">${icon("scan")}Inspect</button>
        ${path ? `<button class="inspect-link" data-act="trace">${icon("graph")}Trace</button>` : ""}
      </div>
    </div>`;

  const textBox = $(".answer-text", node);
  if (animate) typewriter(textBox, r.answer || ""); else textBox.innerHTML = renderMarkdown(r.answer || "");

  const sources = $(".sources", node);
  if (sources) {
    r.sources.forEach((s, i) => {
      const score = typeof s.score === "number" ? s.score : null;
      const card = el("button", "source-card", `
        <div class="s-head">${icon("file")}<span class="s-name">${escapeHtml(prettyDoc(s.document))}</span><span class="s-page">p.${escapeHtml(String(s.page ?? "?"))}</span></div>
        ${s.snippet ? `<div class="s-snip">${escapeHtml(s.snippet)}</div>` : ""}
        ${score != null ? `<div class="scorebar"><i style="width:${clamp(score, 0, 1) * 100}%"></i></div>` : ""}`);
      card.title = `${s.document} — page ${s.page}${score != null ? ` — similarity ${score.toFixed(3)}` : ""}`;
      card.type = "button";
      card.style.animationDelay = `${i * 60}ms`;
      card.addEventListener("click", () => openSource(s));
      sources.append(card);
    });
  }

  $(".bot-body", node).addEventListener("click", (e) => {
    const btn = e.target.closest("[data-act]");
    if (!btn) { if (!e.target.closest(".source-card")) selectTurn(thread.id, index, true); return; }
    const act = btn.dataset.act;
    if (act === "copy") { navigator.clipboard?.writeText(r.answer || "").then(() => toast("Answer copied", "ok")); }
    if (act === "speak") speak(r.answer);
    if (act === "retry") send(turn.q);
    if (act === "up" || act === "down") {
      const v = act === "up" ? 1 : -1;
      turn.fb = turn.fb === v ? 0 : v;
      saveThreads();
      $$('[data-act="up"],[data-act="down"]', node).forEach((b) => b.classList.toggle("on", (b.dataset.act === "up" ? 1 : -1) === turn.fb));
    }
    if (act === "inspect") selectTurn(thread.id, index, true);
    if (act === "trace") { selectTurn(thread.id, index, false); switchView("pipeline"); replayPath(); }
  });
}

async function typewriter(box, text) {
  const words = text.split(/(\s+)/);
  const frames = Math.min(60, Math.max(12, Math.round(words.length / 3)));
  const per = Math.ceil(words.length / frames);
  for (let i = per; i < words.length; i += per) {
    box.innerHTML = renderMarkdown(words.slice(0, i).join(""));
    const last = box.lastElementChild || box;
    last.insertAdjacentHTML("beforeend", '<span class="cursor"></span>');
    const msgs = $("#messages");
    if (msgs.scrollHeight - msgs.scrollTop - msgs.clientHeight < 160) msgs.scrollTop = msgs.scrollHeight;
    await sleep(22);
  }
  box.innerHTML = renderMarkdown(text);
  $("#messages").scrollTop = $("#messages").scrollHeight;
}

function speak(text) {
  if (!("speechSynthesis" in window)) { toast("Speech is not supported in this browser", "err"); return; }
  if (speechSynthesis.speaking) { speechSynthesis.cancel(); return; }
  const u = new SpeechSynthesisUtterance(plainText(text).slice(0, 2500));
  u.rate = 1.05;
  speechSynthesis.speak(u);
}

function openSource(s) {
  $("#srcTitle").textContent = `${prettyDoc(s.document)} · page ${s.page ?? "?"}`;
  const score = typeof s.score === "number" ? s.score.toFixed(3) : "n/a";
  $("#srcBody").innerHTML = `
    <div class="row" style="margin-bottom:12px"><span class="pill">${icon("file")}${escapeHtml(s.document)}</span><span class="pill">similarity ${score}</span></div>
    <blockquote>${escapeHtml(s.snippet || "No excerpt was returned for this source.")}${s.snippet?.length >= 400 ? "…" : ""}</blockquote>
    <p class="muted" style="font-size:12.5px;margin-top:12px">Excerpt of the best-matching chunk on this page, as it was passed to the model.</p>`;
  $("#sourceModal").hidden = false;
}

function getTurn(sel) {
  const t = state.threads.find((x) => x.id === sel.threadId);
  return t?.turns[sel.index] ? { thread: t, turn: t.turns[sel.index] } : null;
}

function selectTurn(threadId, index, revealInspector) {
  state.selected = { threadId, index };
  $$(".msg.bot").forEach((m) => m.classList.toggle("selected", Number(m.dataset.thread) === threadId && Number(m.dataset.index) === index));
  if (revealInspector) $(".chat-layout").classList.remove("no-insp");
  renderInspector(getTurn(state.selected));
}

// ==========================================================================
// inspector
// ==========================================================================
function confidenceFactors(r) {
  const scores = (r.sources || []).map((s) => s.score).filter((s) => typeof s === "number");
  const relMin = flag("score_rel_min") ?? 0.5;
  return {
    top: scores.length ? clamp(Math.max(...scores), 0, 1) : 0,
    ratio: scores.length ? scores.filter((s) => s >= relMin).length / scores.length : 0,
    grounded: r.grounded,
    w: [flag("w_retrieval") ?? 0.3, flag("w_relevance") ?? 0.2, flag("w_grounded") ?? 0.5],
    relMin,
  };
}

function gauge(score, label) {
  const C = 2 * Math.PI * 44;
  const color = CONF_COLORS[label] || "var(--accent)";
  const off = C * (1 - clamp(score ?? 0, 0, 1));
  return `<div class="gauge"><svg viewBox="0 0 104 104"><circle class="g-track" cx="52" cy="52" r="44" fill="none"/>
    <circle class="g-val" cx="52" cy="52" r="44" fill="none" stroke="${color}" stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C}" data-off="${off}"/></svg>
    <div class="g-label"><div><b style="color:${color}">${score != null ? pct(score) : "—"}</b><span>${escapeHtml(label || "")}</span></div></div></div>`;
}

function factorBar(name, value, color, right) {
  return `<div class="factor"><div class="f-top"><span>${name}</span><span>${right}</span></div><div class="bar"><i style="background:${color}" data-w="${clamp(value, 0, 1) * 100}"></i></div></div>`;
}

function renderInspector(sel) {
  const body = $("#inspBody");
  if (!sel || !sel.turn.r) {
    body.innerHTML = `<div class="insp-empty">${icon("scan")}<p>Ask a question, then see exactly how the answer was produced: route, tools, timings and how confidence was computed.</p></div>`;
    return;
  }
  const { turn } = sel;
  const r = turn.r;
  const m = r.metrics || {};
  const parts = [];

  parts.push(`<div class="insp-sec"><h5>Question</h5><div style="font-weight:600">${escapeHtml(turn.q)}</div></div>`);

  // confidence
  if (typeof r.confidence_score === "number") {
    const f = confidenceFactors(r);
    const g = f.grounded == null ? "skipped" : f.grounded ? "1" : "0";
    parts.push(`<div class="insp-sec"><h5><span class="tagp">P4</span> Measured confidence</h5>
      <div class="gauge-row">${gauge(r.confidence_score, r.confidence)}
        <div class="gauge-sum"><span class="pill ${escapeHtml(r.confidence)}">${escapeHtml(r.confidence)}</span>
          <span>${r.grounded === true ? "Checked against the sources and grounded." : r.grounded === false ? "The LLM judge found unsupported claims." : "Groundedness check skipped on this route."}</span>
          <span class="muted">High ≥ ${flag("conf_high") ?? 0.7} · Medium ≥ ${flag("conf_medium") ?? 0.45} · abstain &lt; ${flag("conf_abstain") ?? 0.3}</span></div></div>
        <div class="factors">
          ${factorBar("Top similarity", f.top, "var(--c-rag)", `${f.top.toFixed(2)} × ${f.w[0]}`)}
          ${factorBar(`Relevant chunks (≥ ${f.relMin})`, f.ratio, "var(--accent)", `${f.ratio.toFixed(2)} × ${f.w[1]}`)}
          ${factorBar("Grounded (LLM judge)", f.grounded ? 1 : 0, f.grounded === false ? "var(--low)" : "var(--high)", f.grounded == null ? "skipped" : `${g} × ${f.w[2]}`)}
        </div>
      <div class="formula">C = ${f.w[0]}·s_top + ${f.w[1]}·r ${f.grounded == null ? "(g skipped, weights renormalised)" : `+ ${f.w[2]}·g`} = ${r.confidence_score.toFixed(3)}</div>
      <div class="muted" style="font-size:11.5px;margin-top:6px">Factors recomputed from the de-duplicated sources; the server value is authoritative.</div>
    </div>`);
  } else {
    const why = r.confidence === "N/A" ? "Direct answers use no document evidence, so verification is skipped."
      : r.confidence === "Unverified" ? "Verification is off or the legacy agent graph is active." : "No evidence was retrieved.";
    parts.push(`<div class="insp-sec"><h5><span class="tagp">P4</span> Confidence</h5><div class="row"><span class="pill ${escapeHtml(r.confidence)}">${escapeHtml(r.confidence)}</span></div><p class="muted" style="font-size:12.5px;margin:8px 0 0">${why}</p></div>`);
  }

  // route
  if (r.route) {
    const rt = ROUTES[r.route] || {};
    parts.push(`<div class="insp-sec"><h5><span class="tagp">P1</span> Routing decision</h5>
      <div class="row" style="margin-bottom:8px"><span class="pill r-${r.route}">${icon("route")}${escapeHtml(rt.label || r.route)}</span><span class="pill">via ${escapeHtml(m.route_method || "?")}</span></div>
      <p class="muted" style="font-size:12.5px;margin:0 0 10px">${escapeHtml(rt.desc || "")}</p>
      <dl class="kv"><dt>Grounded</dt><dd>${r.grounded == null ? "not checked" : r.grounded ? "yes" : "no"}</dd>
      <dt>Query rewrites</dt><dd>${m.retries || 0}</dd><dt>Abstained</dt><dd>${r.abstained ? "yes" : "no"}</dd><dt>Sources</dt><dd>${r.sources?.length || 0}</dd></dl></div>`);
  }

  // tools
  if (Array.isArray(m.tools_selected)) {
    const full = m.schema_tokens_full, selTok = m.schema_tokens_selected;
    const saved = full && selTok != null ? 1 - selTok / full : null;
    parts.push(`<div class="insp-sec"><h5><span class="tagp">P2</span> LO-MCP tool selection</h5>
      ${full ? `<div class="token-compare">
        <div class="tc-row"><span>All tools</span><div class="bar"><i style="background:var(--border-strong)" data-w="100"></i></div><span>${full} tok</span></div>
        <div class="tc-row"><span>Bound</span><div class="bar"><i style="background:var(--c-agent)" data-w="${(selTok / full) * 100}"></i></div><span>${selTok} tok</span></div>
      </div><div class="saving"><b>${pct(saved)}</b> fewer schema tokens in the prompt</div>` : ""}
      <div class="tool-chips">${Object.keys(TOOLS).map((n) => `<span class="tool-chip${m.tools_selected.includes(n) ? " on" : ""}">${n}</span>`).join("")}</div></div>`);
  }

  // timings
  const path = pathFor(r);
  if (path) {
    const seen = new Set();
    const rows = [];
    let offset = 0;
    for (const n of path) {
      if (seen.has(n)) continue;
      seen.add(n);
      const ms = nodeTime(n, m);
      if (ms == null) continue;
      rows.push({ n, ms, offset });
      offset += ms;
    }
    const total = Math.max(m.latency_ms || 0, offset, 1);
    parts.push(`<div class="insp-sec"><h5>Timing waterfall · ${fmtMs(total)}</h5><div class="waterfall">
      ${rows.map((x) => `<div class="wf-row"><span>${x.n}</span><div class="wf-track"><i style="left:${(x.offset / total) * 100}%;width:${(x.ms / total) * 100}%;background:${GROUP_COLORS[NODES[x.n].group]}"></i></div><span>${fmtMs(x.ms)}</span></div>`).join("")}
      </div><button class="btn" style="margin-top:12px;width:100%" id="inspTrace">${icon("graph")}Trace on the pipeline graph</button></div>`);
  }

  parts.push(`<details class="insp-sec"><summary style="cursor:pointer;font-size:12px;color:var(--muted)">Raw metrics</summary><pre style="font-family:var(--mono);font-size:11px;white-space:pre-wrap;margin:10px 0 0">${escapeHtml(JSON.stringify(m, null, 2))}</pre></details>`);

  body.innerHTML = parts.join("");
  requestAnimationFrame(() => requestAnimationFrame(() => {
    $$(".g-val", body).forEach((c) => { c.style.strokeDashoffset = c.dataset.off; });
    $$("[data-w]", body).forEach((b) => { b.style.width = `${b.dataset.w}%`; });
  }));
  $("#inspTrace")?.addEventListener("click", () => { switchView("pipeline"); replayPath(); });
}

// ==========================================================================
// pipeline graph
// ==========================================================================
function clipToBox(cx, cy, tx, ty) {
  const dx = tx - cx, dy = ty - cy;
  if (!dx && !dy) return [cx, cy];
  const s = Math.min(dx ? (NODE_W / 2 + 4) / Math.abs(dx) : Infinity, dy ? (NODE_H / 2 + 4) / Math.abs(dy) : Infinity);
  return [cx + dx * s, cy + dy * s];
}

function buildGraph() {
  const svg = $("#graphSvg");
  const parts = [`<defs>
    <linearGradient id="edgeGrad" gradientUnits="userSpaceOnUse" x1="0" y1="0" x2="1120" y2="0"><stop offset="0" stop-color="#7c5cff"/><stop offset="1" stop-color="#00d4ff"/></linearGradient>
    <marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="11" markerHeight="11" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" style="fill:var(--border-strong)"/></marker>
    <marker id="arrOn" viewBox="0 0 10 10" refX="9" refY="5" markerUnits="userSpaceOnUse" markerWidth="12" markerHeight="12" orient="auto-start-reverse"><path d="M0 0L10 5L0 10z" fill="#00d4ff"/></marker>
  </defs>`];
  for (const [a, b, label, ctrl] of EDGES) {
    const A = NODES[a], B = NODES[b];
    const c = ctrl || [(A.x + B.x) / 2, (A.y + B.y) / 2];
    const [x1, y1] = clipToBox(A.x, A.y, c[0], c[1]);
    const [x2, y2] = clipToBox(B.x, B.y, c[0], c[1]);
    parts.push(`<path class="edge" data-edge="${a}>${b}" d="M${x1} ${y1} Q${c[0]} ${c[1]} ${x2} ${y2}" marker-end="url(#arr)"/>`);
    if (label) {
      const lx = 0.25 * x1 + 0.5 * c[0] + 0.25 * x2, ly = 0.25 * y1 + 0.5 * c[1] + 0.25 * y2;
      parts.push(`<text class="edge-label" x="${lx}" y="${ly - 9}" text-anchor="middle">${label}</text>`);
    }
  }
  for (const [name, n] of Object.entries(NODES)) {
    const color = GROUP_COLORS[n.group];
    parts.push(`<g class="node" data-node="${name}" transform="translate(${n.x - NODE_W / 2} ${n.y - NODE_H / 2})" tabindex="0">
      <rect width="${NODE_W}" height="${NODE_H}" rx="12"/>
      <rect class="stripe" width="5" height="${NODE_H - 16}" x="8" y="8" rx="2.5" style="fill:${color}"/>
      <text x="22" y="22">${name}</text>
      <text class="ntime" x="22" y="40" data-time></text>
    </g>`);
  }
  svg.innerHTML = parts.join("");
  $$(".node", svg).forEach((g) => {
    const open = () => showNodeDetail(g.dataset.node);
    g.addEventListener("click", open);
    g.addEventListener("keydown", (e) => { if (e.key === "Enter") open(); });
  });
}

function tracedTurn() {
  const sel = state.selected ? getTurn(state.selected) : null;
  return sel?.turn.r ? sel : null;
}

function renderPipelineView() {
  if (!$("#graphSvg").childElementCount) buildGraph();
  const select = $("#pathSelect");
  const turns = [];
  state.threads.forEach((t) => t.turns.forEach((x, i) => { if (x.r?.route) turns.push({ t, i, x }); }));
  turns.sort((a, b) => b.x.ts - a.x.ts);
  select.innerHTML = turns.length
    ? turns.slice(0, 40).map(({ t, i, x }) => `<option value="${t.id}:${i}">${escapeHtml(x.q.slice(0, 60))} · ${ROUTES[x.r.route]?.short || x.r.route}</option>`).join("")
    : `<option value="">No answers yet. Ask something in Chat</option>`;
  const cur = tracedTurn();
  if (cur) select.value = `${cur.thread.id}:${cur.thread.turns.indexOf(cur.turn)}`;
  else if (turns.length) { state.selected = { threadId: turns[0].t.id, index: turns[0].i }; }
  applyTrace();
  showNodeDetail($("#graphSvg .node.sel")?.dataset.node || "classify");
}

function applyTrace() {
  const svg = $("#graphSvg");
  const sel = tracedTurn();
  const path = sel ? pathFor(sel.turn.r) : null;
  svg.classList.toggle("traced", !!path);
  const on = new Set(path || []);
  const edgesOn = new Set();
  (path || []).forEach((n, i) => { if (i) edgesOn.add(`${path[i - 1]}>${n}`); });
  $$(".node", svg).forEach((g) => {
    g.classList.toggle("on", on.has(g.dataset.node));
    const ms = sel ? nodeTime(g.dataset.node, sel.turn.r.metrics) : null;
    $("[data-time]", g).textContent = on.has(g.dataset.node) && ms != null ? fmtMs(ms) : NODES[g.dataset.node].tag;
  });
  $$(".edge", svg).forEach((p) => {
    const isOn = edgesOn.has(p.dataset.edge);
    p.classList.toggle("on", isOn);
    p.setAttribute("marker-end", isOn ? "url(#arrOn)" : "url(#arr)");
  });
}

async function replayPath() {
  const sel = tracedTurn();
  const path = sel ? pathFor(sel.turn.r) : null;
  if (!path) { toast("Ask a question first, then replay its path", "info"); return; }
  const svg = $("#graphSvg");
  for (const n of path) {
    const g = $(`.node[data-node="${n}"]`, svg);
    g.classList.add("flash");
    showNodeDetail(n);
    await sleep(520);
    g.classList.remove("flash");
  }
}

function showNodeDetail(name) {
  const n = NODES[name];
  if (!n) return;
  $$("#graphSvg .node").forEach((g) => g.classList.toggle("sel", g.dataset.node === name));
  const sel = tracedTurn();
  const ms = sel ? nodeTime(name, sel.turn.r.metrics) : null;
  const color = GROUP_COLORS[n.group];
  $("#nodeDetail").innerHTML = `
    <span class="nd-tag" style="color:${color};border-color:${color}">${n.tag}</span>
    <h3>${n.title} <code>${name}</code></h3>
    <p>${n.desc}</p>
    <div class="nd-file">graph/adaptive.py · ${name}_node${ms != null ? ` · took ${fmtMs(ms)} on the traced answer` : ""}</div>`;
}

// ==========================================================================
// knowledge base
// ==========================================================================
const INGEST_STEPS = ["Upload", "Parse PDF", "Clean & chunk", "Quality filter", "Embed (Gemini)", "Index (Qdrant)"];

async function loadDocuments() {
  if (!state.documents?.length) $("#docGrid").innerHTML = `<div class="empty-state">Loading documents…</div>`;
  try {
    const { documents } = await api("/documents");
    state.documents = documents;
  } catch (e) {
    state.documents = null;
  }
  renderDocuments();
}

function renderDocuments() {
  const grid = $("#docGrid");
  const docs = state.documents;
  const q = $("#docFilter").value.trim().toLowerCase();
  grid.innerHTML = "";
  if (docs == null) { grid.append(el("div", "empty-state", "Couldn't reach the vector store.")); renderKbStats([]); return; }
  renderKbStats(docs);
  const shown = docs.filter((d) => !q || prettyDoc(d).toLowerCase().includes(q));
  if (!shown.length) { grid.append(el("div", "empty-state", docs.length ? "No matching documents" : "No documents yet. Drop a PDF above to build your knowledge base.")); return; }
  shown.forEach((name, i) => {
    const info = state.uploads[name];
    const pretty = prettyDoc(name);
    const card = el("div", "doc-card", `
      <div class="d-head"><div class="doc-icon">PDF</div><div style="min-width:0"><div class="d-name" title="${escapeHtml(name)}">${escapeHtml(pretty)}</div>
      <div class="d-meta">${info ? `${info.chunks ?? "?"} chunks · ${timeAgo(info.ts)}` : "indexed"}</div></div></div>
      ${info?.quality ? `<div><div class="scorebar"><i style="width:${(info.quality.kept / Math.max(1, info.quality.total)) * 100}%;background:var(--high)"></i></div><div class="d-meta" style="margin-top:4px">${info.quality.kept}/${info.quality.total} chunks passed the quality filter</div></div>` : ""}
      <div class="d-actions">
        <button class="chip" data-q="Summarize the document ${escapeHtml(pretty)}">Summarize</button>
        <button class="chip" data-q="What are the key points of ${escapeHtml(pretty)}?">Key points</button>
        <button class="chip" data-q="Generate 5 interview questions from ${escapeHtml(pretty)}">Quiz me</button>
      </div>`);
    card.style.animationDelay = `${i * 40}ms`;
    $$("[data-q]", card).forEach((b) => b.addEventListener("click", () => { startNewChat(); send(b.dataset.q); }));
    grid.append(card);
  });
}

function renderKbStats(docs) {
  const infos = Object.entries(state.uploads).filter(([k]) => docs.includes(k)).map(([, v]) => v);
  const chunks = infos.reduce((a, b) => a + (b.chunks || 0), 0);
  const total = infos.reduce((a, b) => a + (b.quality?.total || 0), 0);
  const rejected = infos.reduce((a, b) => a + (b.quality?.rejected || 0), 0);
  $("#kbStats").innerHTML = [
    ["Documents", docs.length, "in Qdrant collection Learning_RAG"],
    ["Chunks indexed", infos.length ? chunks : "—", infos.length ? `from ${infos.length} upload(s) in this browser` : "upload here to track"],
    ["Rejected by filter", total ? rejected : "—", total ? `${pct(rejected / total)} of ${total} chunks` : "TOCs, dot leaders, garbage"],
    ["Quality filter", flag("quality_enabled") === false ? "Off" : "On", `min ${flag("quality_min_chars") ?? 60} chars · α ≥ ${flag("quality_min_alpha") ?? 0.55}`],
  ].map(([l, v, s]) => `<div class="kpi"><div class="k-label">${l}</div><div class="k-val">${v}</div><div class="k-sub">${s}</div></div>`).join("");
}

function setIngest(stepIndex, status) {
  $("#ingestSteps").innerHTML = INGEST_STEPS.map((s, i) => {
    const cls = status === "err" && i === stepIndex ? "err" : i < stepIndex || status === "ok" ? "ok" : i === stepIndex ? "run" : "";
    return `<span class="istep ${cls}">${cls === "ok" ? icon("check") : ""}${s}</span>`;
  }).join("");
}

function upload(file) {
  if (!file) return;
  if (!/\.pdf$/i.test(file.name)) { toast("Only PDF files are supported.", "err"); return; }
  const panel = $("#ingest"), bar = $("#ingestBar"), prog = bar.parentElement;
  panel.hidden = false;
  $("#ingestName").textContent = file.name;
  $("#ingestState").textContent = `${(file.size / 1024 / 1024).toFixed(2)} MB`;
  $("#ingestResult").innerHTML = "";
  prog.classList.remove("indet");
  bar.style.width = "0";
  setIngest(0);
  $("#drop").classList.add("busy");
  toast(`Indexing ${file.name}…`, "info");

  const form = new FormData();
  form.append("file", file);
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/upload");
  xhr.upload.onprogress = (e) => { if (e.lengthComputable) bar.style.width = `${(e.loaded / e.total) * 100}%`; };
  xhr.upload.onload = () => {
    setIngest(1);
    prog.classList.add("indet");
    $("#ingestState").textContent = "Processing on the server…";
  };
  xhr.onload = () => {
    prog.classList.remove("indet");
    $("#drop").classList.remove("busy");
    $("#fileInput").value = "";
    let body = null;
    try { body = JSON.parse(xhr.responseText); } catch { /* ignore */ }
    if (xhr.status >= 400) {
      setIngest(1, "err");
      const msg = errorMessage(xhr.status, body);
      $("#ingestState").textContent = msg;
      toast(msg, "err");
      return;
    }
    bar.style.width = "100%";
    setIngest(INGEST_STEPS.length, "ok");
    $("#ingestState").textContent = "Indexed";
    const q = body.quality;
    state.uploads[body.document] = { chunks: body.chunks_indexed, quality: q, ts: Date.now(), size: file.size };
    store.set("sb.uploads", state.uploads);
    $("#ingestResult").innerHTML = [
      ["Chunks indexed", body.chunks_indexed ?? "?"],
      ["Chunks seen", q?.total ?? "—"],
      ["Rejected", q ? q.rejected : "—"],
      ...(q?.reasons ? Object.entries(q.reasons).map(([k, v]) => [`reason: ${k}`, v]) : []),
    ].map(([l, v]) => `<div class="stat"><b>${escapeHtml(String(v))}</b><span>${escapeHtml(l)}</span></div>`).join("");
    toast(`${file.name}: ${body.chunks_indexed ?? "?"} chunks indexed`, "ok");
    loadDocuments();
  };
  xhr.onerror = () => {
    $("#drop").classList.remove("busy");
    setIngest(0, "err");
    toast("Upload failed: network error", "err");
  };
  xhr.send(form);
}

// ==========================================================================
// memory
// ==========================================================================
let memories = [];

async function loadMemory() {
  $("#memUser").textContent = state.userId || "default";
  const list = $("#memList");
  list.innerHTML = `<div class="empty-state">Loading memories…</div>`;
  const uid = encodeURIComponent(state.userId || "default");
  try {
    const res = await api(`/memories?user_id=${uid}`);
    memories = res?.results || [];
  } catch (e) {
    memories = null;
    list.innerHTML = `<div class="empty-state">${escapeHtml(e.message)}</div>`;
  }
  if (memories) renderMemories();
  try {
    const { history } = await api(`/memories/history?user_id=${uid}`);
    $("#memHistory").innerHTML = history.length ? history.map((h) => `<div class="tl-item">
        <div class="old">${escapeHtml(h.old_text || h.memory_id)}</div>
        <div class="new">→ ${escapeHtml(h.new_text || "")}</div>
        <div class="when">${escapeHtml(h.reason || "")} · ${h.deprecated_at ? new Date(h.deprecated_at).toLocaleString() : ""}</div></div>`).join("")
      : `<div class="tl-item muted">No contradictions resolved yet. Tell SecondBrain something that changes, then end the session.</div>`;
  } catch {
    $("#memHistory").innerHTML = `<div class="tl-item muted">Audit trail unavailable.</div>`;
  }
}

function renderMemories() {
  const list = $("#memList");
  const q = $("#memFilter").value.trim().toLowerCase();
  const shown = memories.filter((m) => !q || (m.memory || "").toLowerCase().includes(q));
  $("#memCount").textContent = memories.length;
  list.innerHTML = "";
  if (!shown.length) { list.innerHTML = `<div class="empty-state">${memories.length ? "No matches" : "No memories yet for this user."}</div>`; return; }
  shown.forEach((m, i) => {
    const card = el("div", "mem-card", `<span class="m-dot"></span><div class="m-body"><div class="m-text">${escapeHtml(m.memory)}</div>
      <div class="m-meta">${m.created_at ? `<span>${new Date(m.created_at).toLocaleString()}</span>` : ""}${m.metadata?.source ? `<span class="tag complex">${escapeHtml(m.metadata.source)}</span>` : ""}<code>${escapeHtml(String(m.id).slice(0, 8))}</code></div></div>
      <button class="icon-btn" title="Forget">${icon("trash")}</button>`);
    card.style.animationDelay = `${i * 30}ms`;
    $("button", card).addEventListener("click", async () => {
      if (!confirm("Forget this memory permanently?")) return;
      try { await api(`/memories/${encodeURIComponent(m.id)}`, { method: "DELETE" }); toast("Memory forgotten", "ok"); loadMemory(); }
      catch (e) { toast(e.message, "err"); }
    });
    list.append(card);
  });
}

async function addMemory(text) {
  if (!text.trim()) return;
  try {
    await postJson("/memories", { text, user_id: state.userId || "default" });
    $("#memText").value = "";
    toast("Stored in long-term memory", "ok");
    loadMemory();
  } catch (e) { toast(e.message, "err"); }
}

async function endSession() {
  const t = activeThread();
  if (!t || !t.turns.length) { toast("Start a conversation first", "info"); return; }
  const btn = $("#endSession");
  btn.disabled = true;
  try {
    const uid = encodeURIComponent(state.userId || "");
    const r = await api(`/sessions/${t.id}/end${uid ? `?user_id=${uid}` : ""}`, { method: "POST" });
    const msgs = { scheduled: "AAM reflection started in the background", queued: "AAM reflection queued", done: "Memory updated", skipped: `Nothing to save${r.reason ? ` (${r.reason})` : ""}` };
    toast(msgs[r.status] || `Status: ${r.status}`, r.status === "skipped" ? "info" : "ok");
  } catch (e) { toast(e.message, "err"); }
  finally { btn.disabled = false; }
}

// ==========================================================================
// tool lab
// ==========================================================================
async function runLab(query) {
  query = query.trim();
  if (!query) return;
  $("#labRoute").innerHTML = `<h4>P1 · Router decision</h4><div class="progress indet"><i></i></div>`;
  $("#labTools").innerHTML = `<h4>P2 · Tool relevance (cosine similarity)</h4><div class="progress indet"><i></i></div>`;
  $("#labTokens").innerHTML = `<h4>P2 · Context budget</h4><div class="progress indet"><i></i></div>`;

  postJson("/route", { query }).then(renderLabRoute).catch((e) => {
    $("#labRoute").innerHTML = `<h4>P1 · Router decision</h4><div class="muted">${escapeHtml(e.message)}</div>`;
  });
  postJson("/tools/predict", { query }).then(renderLabTools).catch((e) => {
    $("#labTools").innerHTML = `<h4>P2 · Tool relevance</h4><div class="muted">${escapeHtml(e.message)}</div>`;
    $("#labTokens").innerHTML = `<h4>P2 · Context budget</h4><div class="muted">—</div>`;
  });
}

function renderLabRoute(r) {
  const h = r.heuristic || {};
  const rt = ROUTES[r.label] || {};
  const step = (title, text, cls) => `<div class="rf-step ${cls}"><b>${title}</b>${text}</div>`;
  $("#labRoute").innerHTML = `<h4>P1 · Router decision</h4>
    <div class="route-flow">
      ${step("1 · Heuristics", h.label ? `matched <code>${escapeHtml(h.reason)}</code>` : `unsure (<code>${escapeHtml(h.reason)}</code>)`, r.method === "heuristic" ? "hit" : "")}
      <div class="rf-arrow">→</div>
      ${step("2 · Gemini zero-shot", r.method === "llm" ? "classified" : "not needed", r.method === "llm" ? "hit" : "skip")}
      <div class="rf-arrow">→</div>
      ${step("3 · Fallback", r.method === "fallback" ? "defaulted to complex" : "not needed", r.method === "fallback" ? "hit" : "skip")}
    </div>
    <div class="route-result"><span class="route-big" style="color:${rt.color || "var(--text)"}">${escapeHtml(rt.label || r.label)}</span><span class="pill">${escapeHtml(r.label)}</span></div>
    <p class="muted" style="margin:6px 0 0;font-size:13px">${escapeHtml(rt.desc || "")}</p>`;
}

function renderLabTools(info) {
  const scores = info.tools.map((t) => t.score ?? 0);
  const best = Math.max(...scores);
  const lo = Math.max(0, Math.min(...scores, info.thresholds.min_sim) - 0.05);
  const hi = Math.min(1, best + 0.05);
  const x = (v) => clamp((v - lo) / (hi - lo || 1), 0, 1) * 100;
  const cut = best - info.thresholds.margin;
  $("#labTools").innerHTML = `<h4>P2 · Tool relevance (cosine similarity)</h4>
    <div class="tool-bars">${info.tools.map((t) => `<div class="tb-row ${t.selected ? "on" : ""}">
        <span class="tb-name">${t.selected ? `<span class="sel">${icon("check")}</span>` : ""}${t.name}</span>
        <div class="tb-track"><i data-w="${x(t.score ?? 0)}"></i><span class="tb-mark min" style="left:${x(info.thresholds.min_sim)}%"></span><span class="tb-mark cut" style="left:${x(cut)}%"></span></div>
        <span class="tb-score">${(t.score ?? 0).toFixed(3)}</span>
        <span class="tb-desc">${escapeHtml(t.description)} · ${t.tokens} tokens</span></div>`).join("")}</div>
    <div class="tb-legend"><span><i style="background:var(--low)"></i>min similarity ${info.thresholds.min_sim}</span><span><i style="background:var(--medium)"></i>best − margin (${info.thresholds.margin})</span><span>top-k ${info.thresholds.top_k} · always: ${escapeHtml(flag("lomcp_always_include") || "search_documents")}</span></div>`;
  requestAnimationFrame(() => requestAnimationFrame(() => $$("#labTools [data-w]").forEach((b) => { b.style.width = `${b.dataset.w}%`; })));

  const saved = info.tokens_full ? 1 - info.tokens_selected / info.tokens_full : 0;
  $("#labTokens").innerHTML = `<h4>P2 · Context budget</h4><div class="donut-wrap">${donut([
    { v: info.tokens_selected, c: "var(--c-agent)" }, { v: info.tokens_full - info.tokens_selected, c: "var(--surface-2)" },
  ], pct(saved), "saved")}
    <div class="legend-list"><span><i style="background:var(--c-agent)"></i>Bound to the LLM<b>${info.tokens_selected} tok</b></span>
    <span><i style="background:var(--surface-2);border:1px solid var(--border-strong)"></i>Left out<b>${info.tokens_full - info.tokens_selected} tok</b></span>
    <span class="muted" style="font-size:12px">${info.names.length} of ${info.tools.length} tools exposed</span></div></div>`;
}

// ==========================================================================
// charts (inline SVG)
// ==========================================================================
function donut(segments, center, sub) {
  const total = segments.reduce((a, s) => a + s.v, 0) || 1;
  const R = 50, C = 2 * Math.PI * R;
  let acc = 0;
  const arcs = segments.filter((s) => s.v > 0).map((s) => {
    const len = (s.v / total) * C;
    const a = `<circle cx="65" cy="65" r="${R}" fill="none" stroke="${s.c}" stroke-width="16" stroke-dasharray="${len} ${C - len}" stroke-dashoffset="${-acc}" transform="rotate(-90 65 65)"/>`;
    acc += len;
    return a;
  }).join("");
  return `<svg class="donut" viewBox="0 0 130 130"><circle cx="65" cy="65" r="${R}" fill="none" stroke="var(--surface-2)" stroke-width="16"/>${arcs}
    <text x="65" y="66" text-anchor="middle" font-size="22">${center}</text><text x="65" y="84" text-anchor="middle" font-size="11" style="fill:var(--muted);font-weight:500">${sub}</text></svg>`;
}

function renderAnalytics() {
  const turns = allTurns().sort((a, b) => a.ts - b.ts);
  const rs = turns.map((t) => t.r);
  const n = rs.length;
  const avg = (arr) => (arr.length ? arr.reduce((a, b) => a + b, 0) / arr.length : null);
  const lat = rs.map((r) => r.metrics?.latency_ms).filter((v) => typeof v === "number");
  const conf = rs.map((r) => r.confidence_score).filter((v) => typeof v === "number");
  const grounded = rs.filter((r) => r.grounded != null);
  const tokenRuns = rs.filter((r) => r.metrics?.schema_tokens_full);
  const tokensSaved = tokenRuns.reduce((a, r) => a + (r.metrics.schema_tokens_full - r.metrics.schema_tokens_selected), 0);
  const avgSave = avg(tokenRuns.map((r) => 1 - r.metrics.schema_tokens_selected / r.metrics.schema_tokens_full));
  const fb = turns.filter((t) => t.fb);
  const kpi = (label, val, sub) => `<div class="kpi"><div class="k-label">${label}</div><div class="k-val">${val}</div><div class="k-sub">${sub}</div></div>`;
  $("#kpis").innerHTML = [
    kpi("Questions answered", n, `${state.threads.length} conversation(s)`),
    kpi("Avg latency", lat.length ? fmtMs(avg(lat)) : "—", lat.length ? `p-max ${fmtMs(Math.max(...lat))}` : "end-to-end"),
    kpi("Avg confidence", conf.length ? pct(avg(conf)) : "—", `${conf.length} verified answers`),
    kpi("Grounded rate", grounded.length ? pct(grounded.filter((r) => r.grounded).length / grounded.length) : "—", `${grounded.length} judged by the LLM`),
    kpi("Abstained", n ? pct(rs.filter((r) => r.abstained).length / n) : "—", "said “I don't know” instead of guessing"),
    kpi("Schema tokens saved", tokensSaved || "—", avgSave != null ? `${pct(avgSave)} less per agent call` : "by LO-MCP on agent routes"),
    kpi("User rating", fb.length ? pct(fb.filter((t) => t.fb > 0).length / fb.length) : "—", `${fb.length} rated with 👍/👎`),
  ].join("");

  if (!n) {
    ["#chRoute", "#chConf", "#chLatency", "#chStages"].forEach((id) => { $(id).innerHTML = `<div class="empty-chart">No answers yet. Ask a few questions in Chat.</div>`; });
    return;
  }
  // route mix
  const routeCounts = ["no_search", "simple", "complex"].map((k) => ({ k, v: rs.filter((r) => r.route === k).length }));
  const other = n - routeCounts.reduce((a, b) => a + b.v, 0);
  $("#chRoute").innerHTML = `<div class="donut-wrap">${donut(routeCounts.map((x) => ({ v: x.v, c: ROUTES[x.k].color })).concat([{ v: other, c: "var(--muted)" }]), n, "answers")}
    <div class="legend-list">${routeCounts.map((x) => `<span><i style="background:${ROUTES[x.k].color}"></i>${ROUTES[x.k].label}<b>${x.v}</b></span>`).join("")}${other ? `<span><i style="background:var(--muted)"></i>Legacy<b>${other}</b></span>` : ""}</div></div>`;

  // confidence distribution
  const labels = ["High", "Medium", "Low", "N/A", "Unverified"];
  const cc = labels.map((l) => ({ l, v: rs.filter((r) => r.confidence === l).length }));
  const maxC = Math.max(...cc.map((x) => x.v), 1);
  $("#chConf").innerHTML = `<div class="hbars">${cc.map((x) => `<div class="hb-row"><span>${x.l}</span><div class="bar"><i style="width:${(x.v / maxC) * 100}%;background:${CONF_COLORS[x.l] || "var(--muted)"}"></i></div><span>${x.v}</span></div>`).join("")}</div>`;

  // latency line
  const W = Math.max(320, $("#chLatency").clientWidth || 700), H = 220, P = 40;
  const lv = rs.map((r) => r.metrics?.latency_ms || 0);
  const maxL = Math.max(...lv, 1);
  const px = (i) => P + (n === 1 ? (W - 2 * P) / 2 : (i / (n - 1)) * (W - 2 * P));
  const py = (v) => H - P + 10 - (v / maxL) * (H - 2 * P);
  const line = lv.map((v, i) => `${i ? "L" : "M"}${px(i)} ${py(v)}`).join(" ");
  const grid = [0, 0.5, 1].map((f) => `<line class="grid" x1="${P}" x2="${W - P}" y1="${py(maxL * f)}" y2="${py(maxL * f)}"/><text x="${P - 6}" y="${py(maxL * f) + 4}" text-anchor="end">${fmtMs(maxL * f)}</text>`).join("");
  $("#chLatency").innerHTML = `<svg class="chart-svg" viewBox="0 0 ${W} ${H}">
    <defs><linearGradient id="lgA" x1="0" x2="0" y1="0" y2="1"><stop offset="0" stop-color="#7c5cff"/><stop offset="1" stop-color="#7c5cff" stop-opacity="0"/></linearGradient></defs>
    ${grid}<path class="area" d="${line} L${px(n - 1)} ${py(0)} L${px(0)} ${py(0)}Z" fill="url(#lgA)"/>
    <path d="${line}" fill="none" stroke="#7c5cff" stroke-width="2.5"/>
    ${lv.map((v, i) => `<circle class="pt" cx="${px(i)}" cy="${py(v)}" r="4.5" fill="${ROUTES[rs[i].route]?.color || "var(--muted)"}"><title>${escapeHtml(turns[i].q.slice(0, 60))} — ${fmtMs(v)}</title></circle>`).join("")}
  </svg><div class="legend-list" style="flex-direction:row;gap:16px;font-size:12px">${Object.values(ROUTES).map((r) => `<span><i style="background:${r.color}"></i>${r.label}</span>`).join("")}</div>`;

  // stage averages
  const stage = {};
  rs.forEach((r) => (pathFor(r) || []).forEach((name) => {
    const ms = nodeTime(name, r.metrics);
    if (ms == null) return;
    (stage[name] ??= []).push(ms);
  }));
  const rows = Object.entries(stage).map(([k, v]) => [k, avg(v), v.length]).sort((a, b) => b[1] - a[1]);
  const maxS = Math.max(...rows.map((x) => x[1]), 1);
  $("#chStages").innerHTML = rows.length ? `<div class="hbars">${rows.map(([k, v, c]) => `<div class="hb-row"><span>${k}</span><div class="bar"><i style="width:${(v / maxS) * 100}%;background:${GROUP_COLORS[NODES[k].group]}"></i></div><span title="${c} runs">${fmtMs(v)}</span></div>`).join("")}</div>`
    : `<div class="empty-chart">Stage timings appear with the adaptive graph.</div>`;
}

// ==========================================================================
// system
// ==========================================================================
async function loadSystem() {
  try {
    const sys = await api("/system");
    const flags = {};
    Object.values(sys.groups).flat().forEach((f) => { flags[f.name] = f.value; });
    state.system = { ...sys, flags };
  } catch {
    state.system = null;
  }
  renderPills();
  $$("[data-flag]").forEach((s) => { s.textContent = flag(s.dataset.flag) ?? "?"; });
}

function renderPills() {
  const f = (k) => flag(k);
  const pills = state.system ? [
    ["P1 Router", f("enable_router")], ["P2 LO-MCP", f("enable_lomcp")], ["P3 AAM", f("enable_aam")], ["P4 Verify", f("enable_verify")],
  ] : [];
  $("#featurePills").innerHTML = (state.system ? `<span class="fpill on" title="GRAPH_MODE"><i></i>${escapeHtml(state.system.graph_mode)} graph</span>` : "")
    + pills.map(([l, on]) => `<span class="fpill ${on ? "on" : "off"}" title="${on ? "enabled" : "disabled"}"><i></i>${l}</span>`).join("");
}

function renderSystem() {
  $("#arch").innerHTML = [
    ["Clients", [["Web UI", "this app"], ["REST", "POST /chat · /upload"], ["MCP clients", "Claude Desktop, Cursor"]]],
    ["Interface", [["FastAPI", "uvicorn · Swagger /docs"], ["FastMCP", "tools · resources · prompts"]]],
    ["Orchestration", [["LangGraph", "adaptive state machine"], ["MongoDB", "per-thread checkpointer"]]],
    ["Intelligence", [["Gemini", "chat · routing · judging"], ["Gemini embeddings", "chunks · tools · memory"]]],
    ["Storage", [["Qdrant", "Learning_RAG chunks"], ["Mem0 + Qdrant", "User_Memory"], ["MongoDB", "AAM memory_status"]]],
  ].map(([title, boxes], i, arr) => `<div class="arch-col"><b>${title}</b>${boxes.map(([n, s]) => `<div class="arch-box">${n}<small>${s}</small></div>`).join("")}</div>${i < arr.length - 1 ? '<div class="arch-arrow">→</div>' : ""}`).join("");

  $("#mcpTools").innerHTML = MCP_TOOLS.map(([n, d]) => `<div class="mcp-tool"><code>${n}</code><div>${d}</div></div>`).join("");

  const grid = $("#flagGrid");
  if (!state.system) { grid.innerHTML = `<div class="card muted">Couldn't load the configuration.</div>`; return; }
  grid.innerHTML = Object.entries(state.system.groups).map(([g, flags]) => `<div class="card"><h4>${escapeHtml(g)}</h4>
    ${flags.map((f) => {
      const changed = JSON.stringify(f.value) !== JSON.stringify(f.default);
      const val = f.type === "bool" ? `<span class="toggle ${f.value ? "on" : ""}" title="${f.value ? "on" : "off"}"></span>`
        : `<span class="fl-val${changed ? " changed" : ""}" title="${changed ? `default: ${escapeHtml(String(f.default))}` : "default"}">${escapeHtml(String(f.value === "" ? "—" : f.value))}</span>`;
      return `<div class="flag-row"><span class="fl-name">${escapeHtml(f.name)}<code>${escapeHtml(f.env)}</code></span>${val}</div>`;
    }).join("")}</div>`).join("");
}

// ==========================================================================
// command palette
// ==========================================================================
const COMMANDS = [
  ...Object.entries(VIEW_TITLES).map(([k, v]) => ({ label: `Go to ${v}`, group: "Navigate", icon: "graph", run: () => switchView(k) })),
  { label: "New chat", group: "Chat", icon: "plus", run: startNewChat },
  { label: "Upload a PDF", group: "Knowledge", icon: "upload", run: () => $("#fileInput").click() },
  { label: "End session & remember", group: "Memory", icon: "memory", run: endSession },
  { label: "Export conversation as Markdown", group: "Chat", icon: "download", run: exportChat },
  { label: "Toggle answer inspector", group: "Chat", icon: "scan", run: () => $(".chat-layout").classList.toggle("no-insp") },
  { label: "Replay the last answer's path", group: "Pipeline", icon: "play", run: () => { switchView("pipeline"); replayPath(); } },
  { label: "Toggle light / dark theme", group: "Appearance", icon: "theme", run: toggleTheme },
  { label: "Start the guided presentation", group: "Help", icon: "play", run: startTour },
];
let paletteIndex = 0;

function openPalette() {
  $("#palette").hidden = false;
  $("#paletteInput").value = "";
  paletteIndex = 0;
  renderPalette();
  $("#paletteInput").focus();
}
const closePalette = () => { $("#palette").hidden = true; };

function paletteItems() {
  const q = $("#paletteInput").value.trim();
  const ql = q.toLowerCase();
  const items = COMMANDS.filter((c) => !ql || c.label.toLowerCase().includes(ql) || c.group.toLowerCase().includes(ql));
  if (q) items.unshift({ label: `Ask: “${q}”`, group: "Chat", icon: "send", run: () => send(q) });
  if (q) items.push({ label: `Analyse “${q}” in Tool Lab`, group: "Tool Lab", icon: "lab", run: () => { switchView("lab"); $("#labInput").value = q; runLab(q); } });
  return items;
}

function renderPalette() {
  const items = paletteItems();
  paletteIndex = clamp(paletteIndex, 0, Math.max(0, items.length - 1));
  $("#paletteList").innerHTML = items.map((c, i) => `<li class="${i === paletteIndex ? "active" : ""}" data-i="${i}">${icon(c.icon)}${escapeHtml(c.label)}<span class="p-group">${c.group}</span></li>`).join("");
  $$("#paletteList li").forEach((li) => {
    li.addEventListener("click", () => { closePalette(); items[Number(li.dataset.i)].run(); });
    li.addEventListener("mousemove", () => { if (paletteIndex !== Number(li.dataset.i)) { paletteIndex = Number(li.dataset.i); renderPalette(); } });
  });
}

// ==========================================================================
// guided presentation
// ==========================================================================
const TOUR = [
  { view: "chat", target: "[data-tour=pills]", title: "Four research extensions, live", text: "The header shows which extensions are running right now: P1 adaptive routing, P2 LO-MCP tool selection, P3 adaptive memory and P4 verified confidence. They are read from env flags on every request." },
  { view: "chat", target: "[data-tour=suggestions]", title: "One box, three strategies", text: "Every question is classified first. Small talk is answered directly, single facts take a quick retrieval, and multi-step requests go to a tool-calling agent. Each suggestion triggers a different route." },
  { view: "chat", target: "[data-tour=composer]", title: "Ask anything", text: "Type, dictate with the microphone, or attach a PDF. Conversations are checkpointed per thread in MongoDB, so follow-up questions keep their context." },
  { view: "chat", target: "[data-tour=inspector]", title: "Glass-box answers", text: "The inspector shows how every answer was made: the route and why, which tools were bound, a timing waterfall, and how confidence was computed from similarity, relevance and an LLM groundedness check." },
  { view: "knowledge", target: "[data-tour=dropzone]", title: "Ingestion with a quality gate", text: "PDFs are parsed, chunked and passed through a quality filter that rejects tables of contents and garbage text before Gemini embeds them into Qdrant." },
  { view: "memory", target: "#view-memory .mem-cols", title: "Memory that corrects itself", text: "At the end of a session, AAM extracts durable facts, finds similar memories, and deprecates the ones a new fact contradicts. The audit trail shows every replacement." },
  { view: "pipeline", target: "[data-tour=graph]", title: "The state machine, traced", text: "This is the real LangGraph graph. The highlighted path and timings belong to the selected answer. Press Replay to animate it, or click any node for an explanation." },
  { view: "lab", target: "#labForm", title: "Tool Lab", text: "Probe the router and the LO-MCP predictor in isolation. See which classifier stage decided, the cosine similarity of every tool, and how many prompt tokens were saved." },
  { view: "analytics", target: "[data-tour=kpis]", title: "Measured, not claimed", text: "Latency, confidence, grounded rate, abstentions and token savings are aggregated live from every answer." },
  { view: "system", target: "#flagGrid", title: "Ablation-ready", text: "Every flag and threshold is visible here. Because they are read on each request, the evaluation harness can switch configurations without restarting." },
];
let tourIndex = 0;

function startTour() { tourIndex = 0; $("#tour").hidden = false; showTourStep(); }
function endTour() { $("#tour").hidden = true; switchView("chat"); }

async function showTourStep() {
  const step = TOUR[tourIndex];
  if (state.view !== step.view) { switchView(step.view); await sleep(380); }
  if (step.view === "chat") $(".chat-layout").classList.remove("no-insp");
  const target = $(step.target);
  const spot = $("#tourSpot"), card = $("#tourCard");
  $("#tourStep").textContent = `Step ${tourIndex + 1} of ${TOUR.length}`;
  $("#tourTitle").textContent = step.title;
  $("#tourText").textContent = step.text;
  $("#tourPrev").disabled = tourIndex === 0;
  $("#tourNext").textContent = tourIndex === TOUR.length - 1 ? "Finish" : "Next";
  const rect = target && target.offsetParent !== null ? target.getBoundingClientRect() : null;
  const vw = innerWidth, vh = innerHeight, cw = Math.min(380, vw * 0.9), ch = card.offsetHeight || 220;
  if (!rect || !rect.width) {
    spot.style.cssText = `left:${vw / 2}px;top:${vh / 2}px;width:0;height:0`;
    card.style.left = `${(vw - cw) / 2}px`; card.style.top = `${(vh - ch) / 2}px`;
    return;
  }
  const pad = 8;
  const r = { l: Math.max(4, rect.left - pad), t: Math.max(4, rect.top - pad), w: Math.min(rect.width + pad * 2, vw - 8), h: Math.min(rect.height + pad * 2, vh - 8) };
  spot.style.cssText = `left:${r.l}px;top:${r.t}px;width:${r.w}px;height:${r.h}px`;
  let left, top;
  if (r.l + r.w + cw + 20 < vw) { left = r.l + r.w + 16; top = r.t; }
  else if (r.l - cw - 20 > 0) { left = r.l - cw - 16; top = r.t; }
  else if (r.t + r.h + ch + 20 < vh) { left = r.l; top = r.t + r.h + 16; }
  else if (r.t - ch - 20 > 0) { left = r.l; top = r.t - ch - 16; }
  else { left = (vw - cw) / 2; top = vh - ch - 20; }
  card.style.left = `${clamp(left, 10, vw - cw - 10)}px`;
  card.style.top = `${clamp(top, 10, vh - ch - 10)}px`;
}

// ==========================================================================
// misc
// ==========================================================================
function exportChat() {
  const t = activeThread();
  if (!t || !t.turns.length) { toast("Nothing to export yet", "info"); return; }
  const lines = [`# ${t.title}`, "", `_SecondBrain conversation · thread ${t.id} · ${new Date(t.created).toLocaleString()}_`, ""];
  for (const x of t.turns) {
    lines.push(`## Q: ${x.q}`, "");
    if (x.r) {
      lines.push(x.r.answer, "");
      const meta = [x.r.route && `route: ${x.r.route}`, `confidence: ${x.r.confidence}${typeof x.r.confidence_score === "number" ? ` (${pct(x.r.confidence_score)})` : ""}`,
        typeof x.r.metrics?.latency_ms === "number" && `latency: ${fmtMs(x.r.metrics.latency_ms)}`].filter(Boolean).join(" · ");
      lines.push(`> ${meta}`, "");
      if (x.r.sources?.length) lines.push("Sources:", ...x.r.sources.map((s) => `- ${prettyDoc(s.document)}, p.${s.page}`), "");
    } else if (x.error) lines.push(`_Error: ${x.error}_`, "");
  }
  const blob = new Blob([lines.join("\n")], { type: "text/markdown" });
  const a = el("a");
  a.href = URL.createObjectURL(blob);
  a.download = `secondbrain-${t.id}.md`;
  a.click();
  URL.revokeObjectURL(a.href);
}

function autosize() {
  const i = $("#input");
  i.style.height = "auto";
  i.style.height = `${Math.min(i.scrollHeight, 200)}px`;
}

function toggleTheme() {
  const next = document.documentElement.dataset.theme === "light" ? "dark" : "light";
  document.documentElement.dataset.theme = next;
  store.set("sb.theme", next);
}

async function checkHealth() {
  const dot = $("#health");
  try { await api("/healthz"); dot.className = "status-dot ok"; dot.title = "API online"; }
  catch { dot.className = "status-dot down"; dot.title = "API unreachable"; }
}

function setupMic() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  const btn = $("#micBtn");
  if (!SR) { btn.hidden = true; return; }
  let rec = null;
  btn.addEventListener("click", () => {
    if (rec) { rec.stop(); return; }
    rec = new SR();
    rec.lang = navigator.language || "en-US";
    rec.interimResults = true;
    const base = $("#input").value;
    rec.onresult = (e) => { $("#input").value = base + [...e.results].map((r) => r[0].transcript).join(""); autosize(); };
    rec.onend = () => { rec = null; btn.classList.remove("active"); $("#composerHint").textContent = "Enter to send"; };
    rec.onerror = () => toast("Microphone unavailable", "err");
    rec.start();
    btn.classList.add("active");
    $("#composerHint").textContent = "Listening… click the mic to stop";
  });
}

// ==========================================================================
// wiring
// ==========================================================================
document.documentElement.dataset.theme = store.get("sb.theme", "dark");
$("#userId").value = state.userId;

$$(".rail-btn[data-view]").forEach((b) => b.addEventListener("click", () => switchView(b.dataset.view)));
$("#themeBtn").addEventListener("click", toggleTheme);
$("#railToggle").addEventListener("click", (e) => { e.stopPropagation(); $("#rail").classList.toggle("open"); });
$(".frame").addEventListener("click", () => $("#rail").classList.remove("open"));

$("#composer").addEventListener("submit", (e) => { e.preventDefault(); send($("#input").value); });
$("#input").addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send($("#input").value); }
});
$("#input").addEventListener("input", autosize);
$("#newChat").addEventListener("click", startNewChat);
$("#threadFilter").addEventListener("input", renderThreads);
$("#endSession").addEventListener("click", endSession);
$("#exportChat").addEventListener("click", exportChat);
$("#inspClose").addEventListener("click", () => $(".chat-layout").classList.add("no-insp"));
$$("#suggestions .suggest").forEach((b) => b.addEventListener("click", () => send(b.dataset.q)));
$("#attachBtn").addEventListener("click", () => $("#fileInput").click());

$("#userId").addEventListener("change", () => {
  state.userId = $("#userId").value.trim() || "me";
  $("#userId").value = state.userId;
  store.set("sb.userId", state.userId);
  toast(`Memory now scoped to user “${state.userId}”`, "info");
  if (state.view === "memory") loadMemory();
});

$("#refreshDocs").addEventListener("click", loadDocuments);
$("#docFilter").addEventListener("input", renderDocuments);
$("#fileInput").addEventListener("change", () => upload($("#fileInput").files[0]));
const drop = $("#drop");
["dragenter", "dragover"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.add("over"); }));
["dragleave", "drop"].forEach((t) => drop.addEventListener(t, (e) => { e.preventDefault(); drop.classList.remove("over"); }));
drop.addEventListener("drop", (e) => upload(e.dataTransfer.files[0]));

$("#refreshMem").addEventListener("click", loadMemory);
$("#memFilter").addEventListener("input", () => memories && renderMemories());
$("#memForm").addEventListener("submit", (e) => { e.preventDefault(); addMemory($("#memText").value); });

$("#pathSelect").addEventListener("change", (e) => {
  if (!e.target.value) return;
  const [tid, idx] = e.target.value.split(":").map(Number);
  state.selected = { threadId: tid, index: idx };
  applyTrace();
  showNodeDetail($("#graphSvg .node.sel")?.dataset.node || "classify");
});
$("#replayBtn").addEventListener("click", replayPath);

$("#labForm").addEventListener("submit", (e) => { e.preventDefault(); runLab($("#labInput").value); });
$("#labInput").addEventListener("keydown", (e) => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); runLab($("#labInput").value); } });
$$("#labPresets .chip").forEach((c) => c.addEventListener("click", () => { $("#labInput").value = c.textContent; runLab(c.textContent); }));

$("#clearStats").addEventListener("click", () => {
  if (!confirm("Delete all conversations and analytics stored in this browser?")) return;
  state.threads = []; state.activeId = null; state.selected = null;
  saveThreads(); renderThreads(); renderConversation(); renderInspector(null); renderAnalytics();
  toast("Local history cleared", "ok");
});

$("#paletteBtn").addEventListener("click", openPalette);
$("#paletteInput").addEventListener("input", () => { paletteIndex = 0; renderPalette(); });
$("#paletteInput").addEventListener("keydown", (e) => {
  const items = paletteItems();
  if (e.key === "ArrowDown") { e.preventDefault(); paletteIndex = (paletteIndex + 1) % items.length; renderPalette(); }
  if (e.key === "ArrowUp") { e.preventDefault(); paletteIndex = (paletteIndex - 1 + items.length) % items.length; renderPalette(); }
  if (e.key === "Enter" && items[paletteIndex]) { e.preventDefault(); closePalette(); items[paletteIndex].run(); }
});
$$(".overlay").forEach((o) => o.addEventListener("click", (e) => { if (e.target === o || e.target.closest("[data-close]")) o.hidden = true; }));

$("#tourBtn").addEventListener("click", startTour);
$("#tourNext").addEventListener("click", () => { if (tourIndex >= TOUR.length - 1) endTour(); else { tourIndex += 1; showTourStep(); } });
$("#tourPrev").addEventListener("click", () => { if (tourIndex > 0) { tourIndex -= 1; showTourStep(); } });
$("#tourSkip").addEventListener("click", endTour);
addEventListener("resize", () => { if (!$("#tour").hidden) showTourStep(); });

document.addEventListener("keydown", (e) => {
  if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") { e.preventDefault(); $("#palette").hidden ? openPalette() : closePalette(); }
  if (e.key === "Escape") {
    $$(".overlay").forEach((o) => { o.hidden = true; });
    if (!$("#tour").hidden) endTour();
  }
  if (!$("#tour").hidden && (e.key === "ArrowRight" || e.key === "ArrowLeft")) $(e.key === "ArrowRight" ? "#tourNext" : "#tourPrev").click();
});

// boot
if (innerWidth <= 1080) $(".chat-layout").classList.add("no-insp");
setupMic();
renderThreads();
openThread(state.activeId);
loadSystem();
checkHealth();
setInterval(checkHealth, 30000);
$("#input").focus();
