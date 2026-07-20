/**
 * Scripted playground replay — no Adaptron / LLM calls.
 * Prefers replay-data.json; falls back to embedded script for file:// opens.
 */

const STEP_MS = 700;

/** Embedded copy of replay-data.json for file:// browsing. */
const EMBEDDED_REPLAY = {
  topic: "adaptron interoperability",
  stages: [
    {
      name: "langchain_researcher",
      kind: "agent",
      framework: "LangChain (mocked)",
      log: "stage='langchain_researcher' in=str out=Message input='adaptron interoperability' output=Message(text='[LC mock research] adaptron interoperability')",
    },
    {
      name: "adapter<Message->str>",
      kind: "adapter",
      framework: "Adaptron (auto-inserted)",
      log: "stage='adapter<Message->str>' in=Message out=str input=Message(text='[LC mock research] adaptron interoperability') output='[LC mock research] adaptron interoperability'",
    },
    {
      name: "crewai_writer",
      kind: "agent",
      framework: "CrewAI (mocked)",
      log: "stage='crewai_writer' in=str out=str input='[LC mock research] adaptron interoperability' output='[CrewAI mock draft] [LC mock research] adaptron interoperability'",
    },
    {
      name: "format_result",
      kind: "agent",
      framework: "plain Python",
      log: "stage='format_result' in=str out=dict input='[CrewAI mock draft] [LC mock research] adaptron interoperability' output={'status': 'ok', 'draft': '[CrewAI mock draft] [LC mock research] adaptron interoperability', 'words': '8'}",
    },
  ],
  result: {
    status: "ok",
    draft:
      "[CrewAI mock draft] [LC mock research] adaptron interoperability",
    words: "8",
  },
};

/** @type {typeof EMBEDDED_REPLAY | null} */
let data = null;
let stepIndex = 0;
let timerId = 0;

const $ = (sel) => document.querySelector(sel);

function buildDiagram(stages) {
  const root = $("#diagram");
  root.replaceChildren();
  stages.forEach((stage, i) => {
    if (i > 0) {
      const arrow = document.createElement("span");
      arrow.className = "arrow";
      arrow.setAttribute("aria-hidden", "true");
      arrow.textContent = "→";
      root.appendChild(arrow);
    }
    const node = document.createElement("div");
    node.className = `stage-node${stage.kind === "adapter" ? " adapter" : ""}`;
    node.dataset.index = String(i);
    node.innerHTML =
      `<span class="label">${escapeHtml(stage.name)}</span>` +
      `<span class="meta">${escapeHtml(stage.framework)}</span>`;
    root.appendChild(node);
  });
}

function escapeHtml(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function setControls({ canPlay, canStep, canReset }) {
  $("#btn-play").disabled = !canPlay;
  $("#btn-step").disabled = !canStep;
  $("#btn-reset").disabled = !canReset;
}

function markNodes() {
  document.querySelectorAll(".stage-node").forEach((node) => {
    const i = Number(node.dataset.index);
    node.classList.remove("active", "done");
    if (i < stepIndex) node.classList.add("done");
    else if (i === stepIndex) node.classList.add("active");
  });
}

function appendLog(stage) {
  const log = $("#log");
  const line = document.createElement("span");
  line.className = `line${stage.kind === "adapter" ? " adapter" : ""}`;
  line.textContent = stage.log;
  log.appendChild(line);
  log.scrollTop = log.scrollHeight;
}

function showResult() {
  const el = $("#result");
  el.classList.add("ready");
  el.textContent = JSON.stringify(data.result, null, 2);
}

function clearUi() {
  $("#log").replaceChildren();
  const el = $("#result");
  el.classList.remove("ready");
  el.textContent = "Replay finishes here — scripted result only.";
  stepIndex = 0;
  markNodes();
}

function advanceOne() {
  if (!data || stepIndex >= data.stages.length) return false;
  markNodes();
  appendLog(data.stages[stepIndex]);
  stepIndex += 1;
  if (stepIndex >= data.stages.length) {
    document.querySelectorAll(".stage-node").forEach((n) => {
      n.classList.remove("active");
      n.classList.add("done");
    });
    showResult();
    setControls({ canPlay: false, canStep: false, canReset: true });
    return false;
  }
  markNodes();
  setControls({ canPlay: true, canStep: true, canReset: true });
  return true;
}

function stopAutoplay() {
  if (timerId) {
    clearInterval(timerId);
    timerId = 0;
  }
}

function play() {
  stopAutoplay();
  setControls({ canPlay: false, canStep: false, canReset: true });
  const tick = () => {
    if (!advanceOne()) stopAutoplay();
  };
  tick();
  if (data && stepIndex < data.stages.length) {
    timerId = window.setInterval(tick, STEP_MS);
  }
}

function reset() {
  stopAutoplay();
  clearUi();
  setControls({ canPlay: true, canStep: true, canReset: false });
}

async function loadData() {
  try {
    const res = await fetch("replay-data.json", { cache: "no-store" });
    if (res.ok) return await res.json();
  } catch {
    /* file:// or offline — use embedded script */
  }
  return EMBEDDED_REPLAY;
}

async function main() {
  data = await loadData();
  $("#topic-value").textContent = data.topic;
  buildDiagram(data.stages);
  clearUi();
  setControls({ canPlay: true, canStep: true, canReset: false });

  $("#btn-play").addEventListener("click", play);
  $("#btn-step").addEventListener("click", () => {
    stopAutoplay();
    advanceOne();
  });
  $("#btn-reset").addEventListener("click", reset);
}

main();
