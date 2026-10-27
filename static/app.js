/**
 * LlamaOrchestrator Frontend State Machine & Telemetry Engine
 * Coordinates Web Speech voice synthesis, EventSource SSE streaming,
 * dynamic DAG visualizer, and stage transitions.
 */

// Global State
const state = {
  sessionId: null,
  voiceEnabled: true,
  currentStage: 0,
  eventSource: null,
  clarificationData: null,
  selectedAnswers: {},
  dagNodes: {}
};

// Initialize on DOM Load
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  setupEventListeners();
  updateStageUI(0);
});

// Setup UI Event Listeners
function setupEventListeners() {
  // Voice Toggle
  const voiceToggleBtn = document.getElementById("voiceToggleBtn");
  const voiceText = document.getElementById("voiceText");
  const voiceIcon = document.getElementById("voiceIcon");

  voiceToggleBtn.addEventListener("click", () => {
    state.voiceEnabled = !state.voiceEnabled;
    voiceText.textContent = state.voiceEnabled ? "Audible Voice: ON" : "Audible Voice: OFF";
    if (state.voiceEnabled) {
      voiceToggleBtn.classList.remove("border-red-800", "text-red-400");
      voiceIcon.setAttribute("data-lucide", "volume-2");
      speakText("Audible voice synthesis enabled.");
    } else {
      voiceToggleBtn.classList.add("border-red-800", "text-red-400");
      voiceIcon.setAttribute("data-lucide", "volume-x");
      if (window.speechSynthesis) window.speechSynthesis.cancel();
    }
    if (window.lucide) lucide.createIcons();
  });

  // Introduce to Judges Button
  document.getElementById("introBtn").addEventListener("click", async () => {
    appendChatMessage("Introduce yourself to the Meta Hackathon judges.", "user");
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: "Introduce yourself to the Meta Hackathon judges." })
      });
      const data = await res.json();
      appendChatMessage(data.text, "assistant");
      if (data.speech_audio) speakText(data.speech_audio);
    } catch (e) {
      appendChatMessage("Connection error with Central Brain.", "assistant");
    }
  });

  // Preset Buttons
  document.getElementById("presetBizBtn").addEventListener("click", () => {
    document.getElementById("visionInput").value = "I know full-stack dev, build me a business and find me clients";
  });

  document.getElementById("presetTechBtn").addEventListener("click", () => {
    document.getElementById("visionInput").value = "Build an authenticated telemetry microservice with JWT & tests";
  });

  // Analyze Vision Button
  document.getElementById("analyzeBtn").addEventListener("click", handleAnalyzeVision);

  // Jarvis Chat Form
  document.getElementById("chatForm").addEventListener("submit", handleChatSubmit);

  // Clarification Modal Buttons
  document.getElementById("closeModalBtn").addEventListener("click", () => {
    document.getElementById("clarificationModal").classList.add("hidden");
  });

  document.getElementById("autoApproveBtn").addEventListener("click", () => {
    launchLifecycle(true);
  });

  document.getElementById("submitCustomClarificationsBtn").addEventListener("click", () => {
    launchLifecycle(false);
  });

  // Clear Logs Button
  document.getElementById("clearLogsBtn").addEventListener("click", () => {
    document.getElementById("terminalLogs").innerHTML = '<div class="text-slate-500">// Terminal logs cleared.</div>';
  });

  // Download ZIP Button
  document.getElementById("downloadZipBtn").addEventListener("click", () => {
    if (state.sessionId) {
      window.location.href = `/api/workspace/${state.sessionId}/download`;
    }
  });
}

// Web Speech Synthesis
function speakText(text) {
  if (!state.voiceEnabled || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  
  const clean = text.replace(/[*_#`]/g, "");
  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.05;
  utterance.pitch = 0.95;
  
  // Attempt to select an authoritative English voice
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("David")));
  if (preferred) utterance.voice = preferred;

  window.speechSynthesis.speak(utterance);
}

// Append Chat Message
function appendChatMessage(text, role) {
  const container = document.getElementById("chatMessages");
  const msgDiv = document.createElement("div");
  msgDiv.className = "flex items-start gap-2.5";

  if (role === "user") {
    msgDiv.innerHTML = `
      <div class="w-6 h-6 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center shrink-0 border border-blue-500/30">
        <i data-lucide="user" class="w-3.5 h-3.5"></i>
      </div>
      <div class="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-200 leading-relaxed max-w-[85%]">
        ${escapeHtml(text)}
      </div>
    `;
  } else {
    msgDiv.innerHTML = `
      <div class="w-6 h-6 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/30">
        <i data-lucide="bot" class="w-3.5 h-3.5"></i>
      </div>
      <div class="p-2.5 rounded-xl bg-slate-900 border border-slate-800 text-slate-300 leading-relaxed max-w-[85%]">
        ${escapeHtml(text)}
      </div>
    `;
  }

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
  if (window.lucide) lucide.createIcons();
}

// Handle Chat Form Submission
async function handleChatSubmit(e) {
  e.preventDefault();
  const input = document.getElementById("chatInput");
  const msg = input.value.trim();
  if (!msg) return;

  input.value = "";
  appendChatMessage(msg, "user");

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, session_id: state.sessionId })
    });
    const data = await res.json();
    appendChatMessage(data.text, "assistant");
    if (data.speech_audio) speakText(data.speech_audio);
  } catch (err) {
    appendChatMessage("Network error contacting Central Brain.", "assistant");
  }
}

// Handle Analyze Vision (Stage 1)
async function handleAnalyzeVision() {
  const visionInput = document.getElementById("visionInput");
  const vision = visionInput.value.trim();
  if (!vision) {
    alert("Please enter a vision or select one of the presets.");
    return;
  }

  const analyzeBtn = document.getElementById("analyzeBtn");
  analyzeBtn.innerHTML = '<span class="inline-block animate-spin mr-2">⚡</span> Analyzing Intent...';
  analyzeBtn.disabled = true;

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vision })
    });
    const analysis = await res.json();
    state.sessionId = analysis.session_id;
    state.clarificationData = analysis;

    document.getElementById("currentSessionTag").textContent = analysis.session_id;
    updateStageUI(1);

    // Open Clarification Modal
    renderClarificationModal(analysis);
  } catch (err) {
    alert("Error performing intent analysis: " + err.message);
  } finally {
    analyzeBtn.innerHTML = '<i data-lucide="wand-2" class="w-4 h-4 mr-2"></i><span>Analyze Vision & Generate Clarifications</span>';
    analyzeBtn.disabled = false;
    if (window.lucide) lucide.createIcons();
  }
}

// Render Clarification Modal
function renderClarificationModal(analysis) {
  const list = document.getElementById("clarificationQuestionsList");
  list.innerHTML = "";
  state.selectedAnswers = { ...analysis.recommended_defaults };

  analysis.clarifications.forEach((q, idx) => {
    const qDiv = document.createElement("div");
    qDiv.className = "p-4 rounded-xl bg-slate-900/90 border border-slate-800 space-y-2";

    let optionsHtml = "";
    q.options.forEach(opt => {
      const isDefault = (opt === q.default_selection);
      optionsHtml += `
        <label class="flex items-center gap-2.5 p-2 rounded-lg hover:bg-slate-800/80 cursor-pointer border border-transparent transition">
          <input type="radio" name="${q.id}" value="${opt}" ${isDefault ? "checked" : ""} class="accent-emerald-500" onchange="state.selectedAnswers['${q.id}'] = this.value">
          <span class="text-xs text-slate-300 font-medium">${opt}</span>
          ${isDefault ? '<span class="ml-auto text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-mono">Recommended</span>' : ""}
        </label>
      `;
    });

    qDiv.innerHTML = `
      <div class="flex items-start gap-2">
        <span class="w-5 h-5 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center font-mono font-bold text-[10px] shrink-0 border border-slate-700">${idx + 1}</span>
        <div>
          <h4 class="text-xs font-semibold text-slate-200">${q.question}</h4>
          <p class="text-[11px] text-slate-400 mt-0.5">${q.why_needed}</p>
        </div>
      </div>
      <div class="space-y-1 pt-1">${optionsHtml}</div>
    `;
    list.appendChild(qDiv);
  });

  document.getElementById("clarificationModal").classList.remove("hidden");
  if (window.lucide) lucide.createIcons();
}

// Launch Autonomous Lifecycle (Stages 2 -> 5)
async function launchLifecycle(autoApprove) {
  document.getElementById("clarificationModal").classList.add("hidden");

  // Connect to SSE telemetry stream
  connectSSE(state.sessionId);

  try {
    const res = await fetch("/api/launch", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        session_id: state.sessionId,
        auto_approve: autoApprove,
        answers: autoApprove ? null : state.selectedAnswers
      })
    });
    const data = await res.json();
    appendLog(`[System] ${data.message}`, "text-emerald-400");
  } catch (err) {
    appendLog(`[Error] Failed to launch execution lifecycle: ${err.message}`, "text-red-400");
  }
}

// Connect to Server-Sent Events (SSE)
function connectSSE(sessionId) {
  if (state.eventSource) {
    state.eventSource.close();
  }

  const sseUrl = `/api/events/${sessionId}`;
  state.eventSource = new EventSource(sseUrl);
  document.getElementById("sseStateText").textContent = "SSE: Connected";

  state.eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleExecutionEvent(data);
    } catch (e) {
      // Ignored heartbeat
    }
  };

  state.eventSource.onerror = () => {
    document.getElementById("sseStateText").textContent = "SSE: Reconnecting...";
  };
}

// Process Real-time Execution Events
function handleExecutionEvent(evt) {
  // Update stage indicator if provided
  if (typeof evt.stage === "number") {
    updateStageUI(evt.stage);
  }

  // Voice speech announcement if present
  if (evt.speech_text && state.voiceEnabled) {
    speakText(evt.speech_text);
  }

  switch (evt.event_type) {
    case "log":
      appendLog(evt.message, "text-slate-300");
      break;

    case "stage_change":
      appendLog(`▶ [STAGE ${evt.stage}] ${evt.message}`, "text-cyan-400 font-bold");
      break;

    case "kb_updated":
      appendLog(`[KnowledgeBase] ${evt.message}`, "text-purple-400 font-semibold");
      renderKnowledgeBase(evt.data.knowledge_base);
      break;

    case "dag_generated":
      appendLog(`[DAG Engine] ${evt.message}`, "text-cyan-400 font-semibold");
      renderDAG(evt.data.dag);
      break;

    case "task_start":
      appendLog(`⚡ [Task Started] ${evt.message}`, "text-yellow-400");
      updateTaskNodeStatus(evt.task_id, "running");
      break;

    case "task_complete":
      appendLog(`✓ [Task Complete] ${evt.message}`, "text-emerald-400 font-semibold");
      updateTaskNodeStatus(evt.task_id, "completed");
      break;

    case "self_correction":
      appendLog(`⚠ [SELF-CORRECTION] ${evt.message}`, "text-amber-400 font-bold");
      updateTaskNodeStatus(evt.task_id, "self_correcting");
      break;

    case "evaluation_passed":
      appendLog(`★ [EVALUATOR CERTIFIED] ${evt.message}`, "text-emerald-400 font-bold");
      renderEvaluatorPassed(evt.data.audit_results);
      break;

    case "done":
      appendLog(`🎉 [MISSION COMPLETE] ${evt.message}`, "text-emerald-300 font-extrabold");
      updateStageUI(5);
      break;

    case "error":
      appendLog(`✖ [ERROR] ${evt.message}`, "text-red-400 font-bold");
      break;
  }
}

// Render Knowledge Base in Drawer
function renderKnowledgeBase(kb) {
  const container = document.getElementById("kbContentContainer");
  const badge = document.getElementById("kbStatusBadge");
  badge.textContent = "Synthesized";
  badge.className = "text-[11px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30 font-mono";

  container.innerHTML = `
    <div class="space-y-2">
      <div><span class="text-purple-400 font-bold">Niche:</span> ${escapeHtml(kb.target_niche)}</div>
      <div><span class="text-purple-400 font-bold">ICP Roles:</span> ${escapeHtml(kb.icp.target_titles.join(", "))}</div>
      <div><span class="text-purple-400 font-bold">Milestone 1:</span> ${escapeHtml(kb.milestone_1)}</div>
      <div><span class="text-purple-400 font-bold">Milestone 2:</span> ${escapeHtml(kb.milestone_2)}</div>
      <div class="pt-1 text-[11px] text-slate-400 border-t border-slate-900">${escapeHtml(kb.synthesis_summary)}</div>
    </div>
  `;
}

// Render DAG Tasks in Visualizer
function renderDAG(dag) {
  const container = document.getElementById("dagContainer");
  const countBadge = document.getElementById("dagNodeCount");
  countBadge.textContent = `${dag.nodes.length} Nodes`;
  container.innerHTML = "";

  dag.nodes.forEach(node => {
    state.dagNodes[node.id] = node;
    const nodeDiv = document.createElement("div");
    nodeDiv.id = `node_${node.id}`;
    nodeDiv.className = "p-3 rounded-xl bg-slate-900/90 border border-slate-800 transition duration-300";

    nodeDiv.innerHTML = `
      <div class="flex items-center justify-between mb-1.5">
        <span class="text-xs font-semibold text-slate-200">${escapeHtml(node.title)}</span>
        <span class="status-badge text-[10px] px-2 py-0.5 rounded font-mono bg-slate-800 text-slate-400 border border-slate-700">Pending</span>
      </div>
      <div class="text-[11px] text-slate-400 mb-2 leading-tight">${escapeHtml(node.description)}</div>
      <div class="flex items-center justify-between text-[10px] text-slate-500 pt-1.5 border-t border-slate-800/80 font-mono">
        <span class="text-cyan-400/90">${escapeHtml(node.agent_type)}</span>
        <span>${node.assigned_tools.join(", ")}</span>
      </div>
    `;
    container.appendChild(nodeDiv);
  });
}

// Update Individual Task Node Status
function updateTaskNodeStatus(taskId, status) {
  const nodeDiv = document.getElementById(`node_${taskId}`);
  if (!nodeDiv) return;

  const badge = nodeDiv.querySelector(".status-badge");
  nodeDiv.classList.remove("border-emerald-500", "border-yellow-500", "border-amber-500", "pulsing-border");

  if (status === "running") {
    nodeDiv.classList.add("border-yellow-500", "pulsing-border");
    badge.textContent = "Executing";
    badge.className = "status-badge text-[10px] px-2 py-0.5 rounded font-mono bg-yellow-500/20 text-yellow-300 border border-yellow-500/40";
  } else if (status === "completed") {
    nodeDiv.classList.add("border-emerald-500");
    badge.textContent = "Completed";
    badge.className = "status-badge text-[10px] px-2 py-0.5 rounded font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/40";
  } else if (status === "self_correcting") {
    nodeDiv.classList.add("border-amber-500", "pulsing-border");
    badge.textContent = "Self-Correcting";
    badge.className = "status-badge text-[10px] px-2 py-0.5 rounded font-mono bg-amber-500/20 text-amber-300 border border-amber-500/40";
  }
}

// Render Evaluator Gatekeeper Passed State
function renderEvaluatorPassed(report) {
  const card = document.getElementById("evaluatorCard");
  const badge = document.getElementById("evaluatorBadge");
  const downloadBtn = document.getElementById("downloadZipBtn");

  card.classList.add("glass-panel-glow", "border-emerald-500/60");
  badge.textContent = "100% Certified Pass";
  badge.className = "px-2.5 py-0.5 rounded-full text-xs font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/50 font-bold";

  document.getElementById("testStatusLabel").innerHTML = '<span class="text-emerald-400 font-bold">100% Passed</span>';
  document.getElementById("leadStatusLabel").innerHTML = '<span class="text-emerald-400 font-bold">RFC-5322 Verified</span>';
  document.getElementById("webhookStatusLabel").innerHTML = '<span class="text-cyan-400 font-bold">Simulated 200 OK</span>';

  downloadBtn.disabled = false;
  downloadBtn.className = "w-full py-2.5 rounded-xl bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-slate-950 font-bold text-xs uppercase tracking-wider flex items-center justify-center gap-2 transition shadow-lg shadow-emerald-500/20 cursor-pointer";
  document.getElementById("downloadBtnText").textContent = "Download Workspace Deliverables (.ZIP)";
}

// Update Top Lifecycle Stage Tracker
function updateStageUI(stageNum) {
  state.currentStage = stageNum;
  document.querySelectorAll(".stage-pill").forEach(el => {
    const s = parseInt(el.getAttribute("data-stage"), 10);
    const circle = el.querySelector("span:first-child");
    const label = el.querySelector("span:last-child");

    if (s <= stageNum) {
      circle.className = "w-5 h-5 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center font-mono font-bold text-[10px] border border-emerald-500/40";
      label.className = "text-emerald-300 font-semibold whitespace-nowrap";
    } else {
      circle.className = "w-5 h-5 rounded-full bg-slate-800 text-slate-400 flex items-center justify-center font-mono font-bold text-[10px] border border-slate-700";
      label.className = "text-slate-500 font-medium whitespace-nowrap";
    }
  });
}

// Append Terminal Log
function appendLog(msg, colorClass = "text-slate-300") {
  const terminal = document.getElementById("terminalLogs");
  const time = new Date().toISOString().substring(11, 19);
  const logDiv = document.createElement("div");
  logDiv.className = `leading-relaxed ${colorClass}`;
  logDiv.innerHTML = `<span class="text-slate-600">[${time}]</span> ${escapeHtml(msg)}`;
  terminal.appendChild(logDiv);
  terminal.scrollTop = terminal.scrollHeight;
}

// Helper: Escape HTML
function escapeHtml(str) {
  if (typeof str !== "string") return "";
  return str
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}
