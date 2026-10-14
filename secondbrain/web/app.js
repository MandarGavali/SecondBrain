"use strict";

// ---------- state ----------
const store = {
  get(key, fallback) {
    try { return localStorage.getItem(key) ?? fallback; } catch { return fallback; }
  },
  set(key, value) {
    try { localStorage.setItem(key, value); } catch { /* private mode: keep in memory only */ }
  },
};

const newThreadId = () => Math.floor(100000 + Math.random() * 900000000);

const state = {
  threadId: Number(store.get("sb.thread", "")) || newThreadId(),
  userId: store.get("sb.user", "me"),
  busy: false,
};

const $ = (id) => document.getElementById(id);
const els = {
  messages: $("messages"), empty: $("empty"), composer: $("composer"), input: $("input"),
  sendBtn: $("sendBtn"), newChat: $("newChat"), fileInput: $("fileInput"), drop: $("drop"),
  uploadStatus: $("uploadStatus"), docList: $("docList"), refreshDocs: $("refreshDocs"),
  userId: $("userId"), threadLabel: $("threadLabel"), endSession: $("endSession"),
  sessionStatus: $("sessionStatus"), health: $("health"), sidebar: $("sidebar"), menuBtn: $("menuBtn"),
};

// ---------- api ----------
async function api(path, options = {}) {
  const res = await fetch(path, options);
  let body = null;
  try { body = await res.json(); } catch { /* non-JSON body */ }
  if (!res.ok) throw new Error(errorMessage(res.status, body));
  return body;
}

function errorMessage(status, body) {
  const detail = body?.detail ?? body?.error?.message;
  if (Array.isArray(detail)) return detail.map((d) => d.msg).join("; ");
  if (detail) return String(detail);
  if (status === 503) return "The language model is temporarily unavailable. Please try again later.";
  return `Request failed (HTTP ${status}).`;
}

// ---------- rendering helpers ----------
const escapeHtml = (s) => s.replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

const inline = (s) => escapeHtml(s)
  .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
  .replace(/`([^`]+)`/g, "<code>$1</code>");

const SECTION = /^\s*\**(Answer|Evidence Summary|Source Pages|Sources)\**\s*:\s*\**\s*(.*)$/i;

/** Tiny, safe markdown: paragraphs, bullet lists, bold, code, and the generator's section labels. */
function renderMarkdown(text) {
  const out = [];
  let para = [];
  let list = null;
  const flushPara = () => { if (para.length) { out.push(`<p>${para.map(inline).join("<br>")}</p>`); para = []; } };
  const flushList = () => { if (list) { out.push(`<ul>${list.map((li) => `<li>${inline(li)}</li>`).join("")}</ul>`); list = null; } };

  for (const raw of text.split("\n")) {
    const line = raw.trimEnd();
    const section = line.match(SECTION);
    const bullet = line.match(/^\s*(?:[-*•]|\d+[.)])\s+(.*)$/);
    if (!line.trim()) { flushPara(); flushList(); }
    else if (section) {
      flushPara(); flushList();
      out.push(`<h4>${escapeHtml(section[1])}</h4>`);
      if (section[2]) para.push(section[2]);
    } else if (bullet) { flushPara(); (list ??= []).push(bullet[1]); }
    else { flushList(); para.push(line); }
  }
  flushPara(); flushList();
  return out.join("");
}

const prettyDoc = (name) => (name || "unknown").replace(/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}_/i, "");

const ROUTE_LABELS = { no_search: "Direct answer", simple: "Quick lookup", complex: "Agent" };

function el(tag, className, html) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (html !== undefined) node.innerHTML = html;
  return node;
}

function scrollToBottom() {
  els.messages.scrollTop = els.messages.scrollHeight;
}

function addUserMessage(text) {
  els.empty.hidden = true;
  const msg = el("div", "msg user");
  const bubble = el("div", "bubble");
  bubble.textContent = text;
  msg.append(bubble);
  els.messages.append(msg);
  scrollToBottom();
}

function addPending() {
  const msg = el("div", "msg bot");
  msg.append(el("div", "bubble", '<span class="typing"><i></i><i></i><i></i></span>'));
  els.messages.append(msg);
  scrollToBottom();
  return msg;
}

function fillBotMessage(msg, r) {
  msg.innerHTML = "";
  msg.append(el("div", "bubble", renderMarkdown(r.answer || "")));

  if (r.needs_review) {
    msg.append(el("div", "review", "Not enough reliable evidence was found — this question was flagged for review."));
  }

  const meta = el("div", "meta");
  if (r.route) meta.append(el("span", "badge route", escapeHtml(ROUTE_LABELS[r.route] || r.route)));
  if (r.confidence) {
    const score = typeof r.confidence_score === "number" ? ` · ${Math.round(r.confidence_score * 100)}%` : "";
    const badge = el("span", `badge ${r.confidence}`, `${escapeHtml(r.confidence)} confidence${score}`);
    badge.title = r.grounded === true ? "Answer checked against the sources"
      : r.grounded === false ? "Answer was not fully supported by the sources"
      : "Confidence from retrieval scores";
    meta.append(badge);
  }
  const latency = r.metrics?.latency_ms;
  if (typeof latency === "number") meta.append(el("span", "", `${(latency / 1000).toFixed(1)} s`));
  msg.append(meta);

  if (r.sources?.length) {
    const sources = el("div", "sources");
    for (const s of r.sources) {
      const score = typeof s.score === "number" ? ` · ${s.score.toFixed(2)}` : "";
      const chip = el("span", "source", `<b>${escapeHtml(prettyDoc(s.document))}</b> p.${escapeHtml(String(s.page ?? "?"))}${score}`);
      chip.title = `${s.document} — page ${s.page}`;
      sources.append(chip);
    }
    msg.append(sources);
  }

  const metrics = r.metrics || {};
  if (Object.keys(metrics).length) {
    const details = el("details", "metrics");
    details.append(el("summary", "", "Details"));
    const dl = el("dl");
    for (const [key, value] of Object.entries(metrics)) {
      dl.append(el("dt", "", escapeHtml(key)));
      dl.append(el("dd", "", escapeHtml(Array.isArray(value) ? value.join(", ") : String(value))));
    }
    details.append(dl);
    msg.append(details);
  }
  scrollToBottom();
}

function fillError(msg, text) {
  msg.className = "msg bot error";
  msg.innerHTML = "";
  msg.append(el("div", "bubble", escapeHtml(text)));
  scrollToBottom();
}

// ---------- chat ----------
async function send(text) {
  const query = text.trim();
  if (!query || state.busy) return;
  state.busy = true;
  els.sendBtn.disabled = true;
  els.input.value = "";
  autosize();
  addUserMessage(query);
  const pending = addPending();
  try {
    const r = await api("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query, thread_id: state.threadId, user_id: state.userId || null }),
    });
    fillBotMessage(pending, r);
  } catch (e) {
    fillError(pending, e.message);
  } finally {
    state.busy = false;
    els.sendBtn.disabled = false;
    els.input.focus();
  }
}

function startNewChat() {
  state.threadId = newThreadId();
  store.set("sb.thread", String(state.threadId));
  els.threadLabel.textContent = state.threadId;
  els.messages.querySelectorAll(".msg").forEach((m) => m.remove());
  els.empty.hidden = false;
  els.sessionStatus.textContent = "";
  els.input.focus();
}

async function endSession() {
  els.endSession.disabled = true;
  els.sessionStatus.className = "upload-status";
  els.sessionStatus.textContent = "Saving to memory…";
  try {
    const user = encodeURIComponent(state.userId || "");
    const r = await api(`/sessions/${state.threadId}/end${user ? `?user_id=${user}` : ""}`, { method: "POST" });
    const messages = {
      scheduled: "Memory update started in the background.",
      queued: "Memory update queued.",
      done: "Memory updated.",
      skipped: `Nothing to save${r.reason ? ` (${r.reason})` : ""}.`,
    };
    els.sessionStatus.textContent = messages[r.status] || `Status: ${r.status}`;
  } catch (e) {
    els.sessionStatus.className = "upload-status error";
    els.sessionStatus.textContent = e.message;
  } finally {
    els.endSession.disabled = false;
  }
}

// ---------- documents ----------
async function loadDocuments() {
  try {
    const { documents } = await api("/documents");
    els.docList.innerHTML = "";
    if (!documents.length) {
      els.docList.append(el("li", "none", "No documents yet"));
      return;
    }
    for (const name of documents) {
      const li = el("li", "", `<span>${escapeHtml(prettyDoc(name))}</span>`);
      li.title = name;
      els.docList.append(li);
    }
  } catch (e) {
    els.docList.innerHTML = "";
    els.docList.append(el("li", "none", "Couldn't load documents"));
  }
}

async function upload(file) {
  if (!file) return;
  if (!/\.pdf$/i.test(file.name)) {
    els.uploadStatus.className = "upload-status error";
    els.uploadStatus.textContent = "Only PDF files are supported.";
    return;
  }
  const form = new FormData();
  form.append("file", file);
  els.drop.classList.add("busy");
  els.uploadStatus.className = "upload-status";
  els.uploadStatus.textContent = `Indexing ${file.name}…`;
  try {
    const r = await api("/upload", { method: "POST", body: form });
    const rejected = r.quality?.rejected ? `, ${r.quality.rejected} low-quality chunks skipped` : "";
    els.uploadStatus.textContent = r.chunks_indexed != null
      ? `${file.name}: ${r.chunks_indexed} chunks indexed${rejected}.`
      : `${file.name} indexed.`;
    loadDocuments();
  } catch (e) {
    els.uploadStatus.className = "upload-status error";
    els.uploadStatus.textContent = e.message;
  } finally {
    els.drop.classList.remove("busy");
    els.fileInput.value = "";
  }
}

// ---------- misc ----------
function autosize() {
  els.input.style.height = "auto";
  els.input.style.height = `${Math.min(els.input.scrollHeight, 180)}px`;
  els.input.style.overflowY = els.input.scrollHeight > 180 ? "auto" : "hidden";
}

async function checkHealth() {
  try {
    await api("/healthz");
    els.health.className = "health ok";
    els.health.title = "API online";
  } catch {
    els.health.className = "health down";
    els.health.title = "API unreachable";
  }
}

// ---------- wiring ----------
els.threadLabel.textContent = state.threadId;
store.set("sb.thread", String(state.threadId));
els.userId.value = state.userId;

els.composer.addEventListener("submit", (e) => { e.preventDefault(); send(els.input.value); });
els.input.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); send(els.input.value); }
});
els.input.addEventListener("input", autosize);
els.newChat.addEventListener("click", startNewChat);
els.endSession.addEventListener("click", endSession);
els.refreshDocs.addEventListener("click", loadDocuments);
els.userId.addEventListener("change", () => {
  state.userId = els.userId.value.trim();
  store.set("sb.user", state.userId);
});
els.fileInput.addEventListener("change", () => upload(els.fileInput.files[0]));
for (const type of ["dragenter", "dragover"]) {
  els.drop.addEventListener(type, (e) => { e.preventDefault(); els.drop.classList.add("over"); });
}
for (const type of ["dragleave", "drop"]) {
  els.drop.addEventListener(type, (e) => { e.preventDefault(); els.drop.classList.remove("over"); });
}
els.drop.addEventListener("drop", (e) => upload(e.dataTransfer.files[0]));
document.querySelectorAll(".suggestions .chip-btn").forEach((b) =>
  b.addEventListener("click", () => send(b.textContent)));
els.menuBtn.addEventListener("click", (e) => { e.stopPropagation(); els.sidebar.classList.toggle("open"); });
document.querySelector(".main").addEventListener("click", () => els.sidebar.classList.remove("open"));

requestAnimationFrame(() => requestAnimationFrame(() => document.body.classList.add("ready")));
checkHealth();
loadDocuments();
els.input.focus();
