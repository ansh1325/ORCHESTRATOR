/**
 * LlamaOrchestrator Frontend Application Logic
 * Creator: Ansh Tiwari
 * Coordinates:
 * - Central Brain Dialogue & Directives (Chat & Autonomous Lifecycle)
 * - Web Speech Synthesis with Live Soundwave Visualizer
 * - Work History, Search, Folder Filtering & Pinning
 * - Saved Workflows & 24/7 Automation Triggers
 * - Dynamic Synthesized Worker Agents Visualizer
 * - In-Browser Deliverables File Preview & 1-Click Copy
 * - Mission Accomplished Banner with Deliverables ZIP Download
 */

// Global Application State
const state = {
  sessionId: null,
  activeDeliverables: [],
  activeFileContent: "",
  voiceEnabled: true,
  currentStage: 0,
  eventSource: null,
  clarificationData: null,
  selectedAnswers: {},
  dagNodes: {},
  historyItems: [],
  activeFolderFilter: "all",
  searchQuery: "",
  savedWorkflows: []
};

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  setupEventListeners();
  loadWorkHistory();
  loadSavedWorkflows();
  updateStageUI(0);
});

// Event Listeners Setup
function setupEventListeners() {
  // Sidebar Toggle
  const toggleSidebarBtn = document.getElementById("toggleSidebarBtn");
  const sidebar = document.getElementById("sidebar");
  if (toggleSidebarBtn && sidebar) {
    toggleSidebarBtn.addEventListener("click", () => {
      sidebar.classList.toggle("hidden");
    });
  }

  // New Directive / Reset Button
  const newDirectiveBtn = document.getElementById("newDirectiveBtn");
  if (newDirectiveBtn) {
    newDirectiveBtn.addEventListener("click", resetSession);
  }

  // Voice Toggle Button
  const voiceToggleBtn = document.getElementById("voiceToggleBtn");
  const voiceText = document.getElementById("voiceText");
  const voiceIcon = document.getElementById("voiceIcon");
  if (voiceToggleBtn) {
    voiceToggleBtn.addEventListener("click", () => {
      state.voiceEnabled = !state.voiceEnabled;
      if (voiceText) voiceText.textContent = state.voiceEnabled ? "Audible Voice: ON" : "Audible Voice: OFF";
      if (state.voiceEnabled) {
        voiceToggleBtn.classList.remove("border-red-800", "text-red-400");
        if (voiceIcon) voiceIcon.setAttribute("data-lucide", "volume-2");
        speakText("Audible voice synthesis enabled.");
      } else {
        voiceToggleBtn.classList.add("border-red-800", "text-red-400");
        if (voiceIcon) voiceIcon.setAttribute("data-lucide", "volume-x");
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        setVoiceVisualizer(false);
      }
      if (window.lucide) lucide.createIcons();
    });
  }

  // History Search
  const historySearch = document.getElementById("historySearch");
  if (historySearch) {
    historySearch.addEventListener("input", (e) => {
      state.searchQuery = e.target.value.toLowerCase().trim();
      renderHistoryList();
    });
  }

  // Folder Filters
  document.querySelectorAll(".folder-filter").forEach(btn => {
    btn.addEventListener("click", (e) => {
      document.querySelectorAll(".folder-filter").forEach(b => {
        b.classList.remove("active", "bg-emerald-500/20", "text-emerald-400", "border-emerald-500/40");
        b.classList.add("bg-cyber-850", "text-slate-400", "border-cyber-700/60");
      });
      btn.classList.add("active", "bg-emerald-500/20", "text-emerald-400", "border-emerald-500/40");
      btn.classList.remove("bg-cyber-850", "text-slate-400", "border-cyber-700/60");
      state.activeFolderFilter = btn.getAttribute("data-folder");
      renderHistoryList();
    });
  });

  // Add Current Directive to Saved Workflows
  const addWorkflowBtn = document.getElementById("addWorkflowBtn");
  if (addWorkflowBtn) {
    addWorkflowBtn.addEventListener("click", async () => {
      const input = document.getElementById("directiveInput");
      const prompt = input.value.trim() || "Autonomous Multi-Agent Task";
      const name = window.prompt("Name this reusable workflow template:", prompt.slice(0, 30));
      if (!name) return;

      try {
        const res = await fetch("/api/workflows", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            name: name,
            category: "Custom",
            prompt: input.value.trim() || prompt
          })
        });
        const saved = await res.json();
        loadSavedWorkflows();
        appendChatMessage(`Saved workflow "${name}" to your workflow catalog.`, "assistant");
      } catch (err) {
        alert("Could not save workflow: " + err.message);
      }
    });
  }

  // Terminal Drawer Toggle
  const toggleTerminalBtn = document.getElementById("toggleTerminalBtn");
  const terminalDrawer = document.getElementById("terminalDrawer");
  const terminalToggleLabel = document.getElementById("terminalToggleLabel");
  if (toggleTerminalBtn && terminalDrawer) {
    toggleTerminalBtn.addEventListener("click", () => {
      terminalDrawer.classList.toggle("hidden");
      const isHidden = terminalDrawer.classList.contains("hidden");
      if (terminalToggleLabel) {
        terminalToggleLabel.textContent = isHidden ? "Show Telemetry Logs" : "Hide Telemetry Logs";
      }
    });
  }

  // Copy File Preview Button
  const copyFileBtn = document.getElementById("copyFileBtn");
  if (copyFileBtn) {
    copyFileBtn.addEventListener("click", () => {
      if (!state.activeFileContent) return;
      navigator.clipboard.writeText(state.activeFileContent).then(() => {
        const originalHtml = copyFileBtn.innerHTML;
        copyFileBtn.innerHTML = '<i data-lucide="check" class="w-3.5 h-3.5 text-emerald-400"></i><span class="text-emerald-400">Copied!</span>';
        if (window.lucide) lucide.createIcons();
        setTimeout(() => {
          copyFileBtn.innerHTML = originalHtml;
          if (window.lucide) lucide.createIcons();
        }, 2000);
      });
    });
  }

  // Download Completed ZIP Button in Banner
  const downloadCompletedZipBtn = document.getElementById("downloadCompletedZipBtn");
  if (downloadCompletedZipBtn) {
    downloadCompletedZipBtn.addEventListener("click", () => {
      if (state.sessionId) {
        window.location.href = `/api/workspace/${state.sessionId}/download`;
      }
    });
  }

  // Clarification Modal Buttons
  const closeModalBtn = document.getElementById("closeModalBtn");
  if (closeModalBtn) {
    closeModalBtn.addEventListener("click", () => {
      document.getElementById("clarificationModal").classList.add("hidden");
    });
  }

  const autoApproveBtn = document.getElementById("autoApproveBtn");
  if (autoApproveBtn) {
    autoApproveBtn.addEventListener("click", () => {
      launchLifecycle(true);
    });
  }

  const submitCustomClarificationsBtn = document.getElementById("submitCustomClarificationsBtn");
  if (submitCustomClarificationsBtn) {
    submitCustomClarificationsBtn.addEventListener("click", () => {
      launchLifecycle(false);
    });
  }

  // Speech Recognition (Mic Button)
  const micBtn = document.getElementById("micBtn");
  if (micBtn) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = "en-US";

      micBtn.addEventListener("click", () => {
        micBtn.classList.add("text-emerald-400", "animate-pulse");
        recognition.start();
      });

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        const input = document.getElementById("directiveInput");
        if (input) input.value = transcript;
        micBtn.classList.remove("text-emerald-400", "animate-pulse");
        // Automatically submit voice directive
        handleDirectiveSubmit(new Event("submit"));
      };

      recognition.onerror = () => {
        micBtn.classList.remove("text-emerald-400", "animate-pulse");
      };

      recognition.onend = () => {
        micBtn.classList.remove("text-emerald-400", "animate-pulse");
      };
    } else {
      micBtn.title = "Web Speech Recognition not supported in this browser.";
      micBtn.style.opacity = "0.5";
    }
  }

  // Floating Directive Form Submission
  const directiveForm = document.getElementById("directiveForm");
  if (directiveForm) {
    directiveForm.addEventListener("submit", handleDirectiveSubmit);
  }
}

// Reset Current Session & UI
function resetSession() {
  state.sessionId = null;
  state.activeDeliverables = [];
  state.activeFileContent = "";
  state.clarificationData = null;
  state.selectedAnswers = {};
  state.dagNodes = {};

  const input = document.getElementById("directiveInput");
  if (input) {
    input.value = "";
    input.focus();
  }

  const workDoneBanner = document.getElementById("workDoneBanner");
  if (workDoneBanner) workDoneBanner.classList.add("hidden");

  const dagContainer = document.getElementById("dagContainer");
  if (dagContainer) {
    dagContainer.innerHTML = `
      <div class="col-span-full text-center py-6 text-xs text-slate-500">
        Awaiting your directive to compile DAG dependencies and synthesize specialized Llama workers...
      </div>
    `;
  }
  const dagCountBadge = document.getElementById("dagCountBadge");
  if (dagCountBadge) dagCountBadge.textContent = "0 Agents Synthesized";

  const fileContentPre = document.getElementById("fileContentPre");
  if (fileContentPre) fileContentPre.textContent = "Select any deliverable to preview contents.";
  const activeFileName = document.getElementById("activeFileName");
  if (activeFileName) activeFileName.textContent = "No file selected";

  updateStageUI(0);
  appendChatMessage("Ready for your next objective, Ansh.", "assistant");
}

// Speak Text via Web Speech API with Soundwave Feedback
function speakText(text) {
  if (!state.voiceEnabled || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();

  const clean = text.replace(/[*_#`~]/g, "").trim();
  if (!clean) return;

  const utterance = new SpeechSynthesisUtterance(clean);
  utterance.rate = 1.05;
  utterance.pitch = 0.95;

  // Prefer natural English voices
  const voices = window.speechSynthesis.getVoices();
  const preferred = voices.find(v => v.lang.startsWith("en") && (v.name.includes("Natural") || v.name.includes("Google") || v.name.includes("David") || v.name.includes("Daniel")));
  if (preferred) utterance.voice = preferred;

  utterance.onstart = () => {
    setVoiceVisualizer(true);
  };

  utterance.onend = utterance.onerror = () => {
    setVoiceVisualizer(false);
  };

  window.speechSynthesis.speak(utterance);
}

// Toggle Live Soundwave Visualizer
function setVoiceVisualizer(active) {
  const visualizer = document.getElementById("voiceVisualizer");
  if (!visualizer) return;
  if (active) {
    visualizer.classList.remove("hidden");
    visualizer.classList.add("flex");
  } else {
    visualizer.classList.add("hidden");
    visualizer.classList.remove("flex");
  }
}

// Append Chat Message to Jarvis Dialogue
function appendChatMessage(text, role) {
  const container = document.getElementById("chatHistory");
  if (!container) return;

  const msgDiv = document.createElement("div");
  msgDiv.className = "flex items-start gap-2.5";

  if (role === "user") {
    msgDiv.innerHTML = `
      <div class="w-6 h-6 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center shrink-0 border border-blue-500/30">
        <i data-lucide="user" class="w-3.5 h-3.5"></i>
      </div>
      <div class="p-3 rounded-xl bg-cyber-850 border border-cyber-700/60 text-slate-100 leading-relaxed max-w-[85%]">
        ${escapeHtml(text)}
      </div>
    `;
  } else {
    msgDiv.innerHTML = `
      <div class="w-6 h-6 rounded-lg bg-emerald-500/20 text-emerald-400 flex items-center justify-center shrink-0 border border-emerald-500/30">
        <i data-lucide="bot" class="w-3.5 h-3.5"></i>
      </div>
      <div class="p-3 rounded-xl bg-cyber-850 border border-cyber-700/60 text-slate-200 leading-relaxed max-w-[85%]">
        ${escapeHtml(text)}
      </div>
    `;
  }

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
  if (window.lucide) lucide.createIcons();
}

// Append Terminal Log
function appendLog(msg, colorClass = "text-slate-300") {
  const terminal = document.getElementById("terminalLogs");
  if (!terminal) return;
  const time = new Date().toISOString().substring(11, 19);
  const logDiv = document.createElement("div");
  logDiv.className = `leading-relaxed ${colorClass}`;
  logDiv.innerHTML = `<span class="text-slate-600">[${time}]</span> ${escapeHtml(msg)}`;
  terminal.appendChild(logDiv);
  terminal.scrollTop = terminal.scrollHeight;
}

// Handle Bottom Floating Directive Bar Submission
async function handleDirectiveSubmit(e) {
  if (e && e.preventDefault) e.preventDefault();
  const input = document.getElementById("directiveInput");
  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  appendChatMessage(text, "user");

  // Determine if this is a conversational query or an actionable execution task
  const lower = text.toLowerCase();
  const isConversationalGreeting = (lower.split(/\s+/).length <= 4) && 
    (lower.startsWith("hi") || lower.startsWith("hello") || lower === "hey" || lower.includes("how are you") || lower.includes("who are you"));

  if (isConversationalGreeting) {
    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ message: text, session_id: state.sessionId })
      });
      const data = await res.json();
      appendChatMessage(data.text, "assistant");
      if (data.speech_audio) speakText(data.speech_audio);
    } catch (err) {
      appendChatMessage("Connection interrupted. Central Brain standing by.", "assistant");
    }
    return;
  }

  // Actionable Directive -> Run Intent Analysis & Autonomous Lifecycle
  appendChatMessage("Directives received. Analyzing requirements, compiling DAG, and assembling specialized agents...", "assistant");
  speakText("Directives received. Initializing autonomous multi-agent compilation.");

  updateStageUI(1);
  const submitBtn = document.getElementById("submitBtn");
  if (submitBtn) submitBtn.disabled = true;

  try {
    const res = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ vision: text })
    });
    const analysis = await res.json();
    state.sessionId = analysis.session_id;
    state.clarificationData = analysis;

    appendLog(`[Intent Analyzer] Session ${state.sessionId} established. Identified track: ${analysis.detected_track}`, "text-cyan-400");

    // Open Clarification Gate Modal for verification
    renderClarificationModal(analysis);
  } catch (err) {
    appendChatMessage(`Analysis error: ${err.message}`, "assistant");
    appendLog(`[Error] Analysis failure: ${err.message}`, "text-red-400");
  } finally {
    if (submitBtn) submitBtn.disabled = false;
  }
}

// Render Clarification Modal
function renderClarificationModal(analysis) {
  const list = document.getElementById("clarificationQuestionsList");
  if (!list) return;
  list.innerHTML = "";
  state.selectedAnswers = { ...analysis.recommended_defaults };

  analysis.clarifications.forEach((q, idx) => {
    const qDiv = document.createElement("div");
    qDiv.className = "p-4 rounded-xl bg-cyber-950 border border-cyber-700/60 space-y-2";

    let optionsHtml = "";
    q.options.forEach(opt => {
      const isDefault = (opt === q.default_selection);
      optionsHtml += `
        <label class="flex items-center gap-2.5 p-2 rounded-lg hover:bg-cyber-850 cursor-pointer border border-transparent transition">
          <input type="radio" name="${q.id}" value="${escapeHtml(opt)}" ${isDefault ? "checked" : ""} class="accent-emerald-500" onchange="state.selectedAnswers['${q.id}'] = this.value">
          <span class="text-xs text-slate-300 font-medium">${escapeHtml(opt)}</span>
          ${isDefault ? '<span class="ml-auto text-[10px] px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/40 font-mono">Recommended</span>' : ""}
        </label>
      `;
    });

    qDiv.innerHTML = `
      <div class="flex items-start gap-2">
        <span class="w-5 h-5 rounded-full bg-cyber-850 text-slate-400 flex items-center justify-center font-mono font-bold text-[10px] shrink-0 border border-cyber-700">${idx + 1}</span>
        <div>
          <h4 class="text-xs font-semibold text-slate-200">${escapeHtml(q.question)}</h4>
          <p class="text-[11px] text-slate-400 mt-0.5">${escapeHtml(q.why_needed)}</p>
        </div>
      </div>
      <div class="space-y-1 pt-1">${optionsHtml}</div>
    `;
    list.appendChild(qDiv);
  });

  const modal = document.getElementById("clarificationModal");
  if (modal) modal.classList.remove("hidden");
  if (window.lucide) lucide.createIcons();
}

// Launch Autonomous Lifecycle (Stages 2 -> 5)
async function launchLifecycle(autoApprove) {
  const modal = document.getElementById("clarificationModal");
  if (modal) modal.classList.add("hidden");

  // Connect to SSE Telemetry Stream
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

  state.eventSource.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      handleExecutionEvent(data);
    } catch (e) {
      // Keepalive heartbeat
    }
  };

  state.eventSource.onerror = () => {
    // SSE disconnected or complete
  };
}

// Process Real-Time SSE Telemetry Events
function handleExecutionEvent(evt) {
  if (typeof evt.stage === "number") {
    updateStageUI(evt.stage);
  }

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
      appendLog(`[Knowledge Agent] ${evt.message}`, "text-purple-400 font-semibold");
      break;

    case "dag_generated":
      appendLog(`[DAG Engine] ${evt.message}`, "text-cyan-400 font-semibold");
      if (evt.data && evt.data.dag) {
        renderDAG(evt.data.dag);
      }
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
      appendLog(`★ [QUALITY GATEKEEPER] ${evt.message}`, "text-emerald-400 font-bold");
      break;

    case "done":
      appendLog(`🎉 [MISSION ACCOMPLISHED] ${evt.message}`, "text-emerald-300 font-extrabold");
      updateStageUI(5);
      showWorkDoneBanner(evt.data ? evt.data.deliverables : []);
      loadWorkHistory(); // Refresh work history list
      break;

    case "error":
      appendLog(`✖ [ERROR] ${evt.message}`, "text-red-400 font-bold");
      break;
  }
}

// Render DAG Tasks in Dynamic Visualizer
function renderDAG(dag) {
  const container = document.getElementById("dagContainer");
  const countBadge = document.getElementById("dagCountBadge");
  if (!container) return;

  if (countBadge) {
    countBadge.textContent = `${dag.nodes.length} Agents Synthesized`;
  }
  container.innerHTML = "";

  dag.nodes.forEach(node => {
    state.dagNodes[node.id] = node;
    const nodeDiv = document.createElement("div");
    nodeDiv.id = `node_${node.id}`;
    nodeDiv.className = "p-3 rounded-xl bg-cyber-900 border border-cyber-700/60 transition duration-300 space-y-2";

    nodeDiv.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="text-xs font-semibold text-slate-200">${escapeHtml(node.title)}</span>
        <span class="status-badge text-[10px] px-2 py-0.5 rounded font-mono bg-cyber-850 text-slate-400 border border-cyber-700">Pending</span>
      </div>
      <div class="text-[11px] text-slate-400 leading-tight">${escapeHtml(node.description)}</div>
      <div class="flex items-center justify-between text-[10px] text-slate-500 pt-1.5 border-t border-cyber-800 font-mono">
        <span class="text-cyan-400/90">${escapeHtml(node.agent_type)}</span>
        <span>${node.assigned_tools.join(", ")}</span>
      </div>
    `;
    container.appendChild(nodeDiv);
  });
}

// Update Task Node Status Badge
function updateTaskNodeStatus(taskId, status) {
  const nodeDiv = document.getElementById(`node_${taskId}`);
  if (!nodeDiv) return;

  const badge = nodeDiv.querySelector(".status-badge");
  nodeDiv.classList.remove("border-emerald-500", "border-yellow-500", "border-amber-500");

  if (status === "running") {
    nodeDiv.classList.add("border-yellow-500");
    if (badge) {
      badge.textContent = "Executing";
      badge.className = "status-badge text-[10px] px-2 py-0.5 rounded font-mono bg-yellow-500/20 text-yellow-300 border border-yellow-500/40";
    }
  } else if (status === "completed") {
    nodeDiv.classList.add("border-emerald-500");
    if (badge) {
      badge.textContent = "Completed";
      badge.className = "status-badge text-[10px] px-2 py-0.5 rounded font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/40";
    }
  } else if (status === "self_correcting") {
    nodeDiv.classList.add("border-amber-500");
    if (badge) {
      badge.textContent = "Self-Correcting";
      badge.className = "status-badge text-[10px] px-2 py-0.5 rounded font-mono bg-amber-500/20 text-amber-300 border border-amber-500/40";
    }
  }
}

// Show Mission Accomplished Banner with Deliverables
function showWorkDoneBanner(deliverables) {
  const banner = document.getElementById("workDoneBanner");
  const deliverablesList = document.getElementById("completedDeliverablesList");
  if (!banner) return;

  banner.classList.remove("hidden");
  state.activeDeliverables = deliverables || [];

  if (deliverablesList) {
    deliverablesList.innerHTML = "";
    if (state.activeDeliverables.length === 0) {
      // Default common deliverables based on track
      state.activeDeliverables = ["mail_1.md", "mail_2.md", "mail_3.md", "emails.json", "dispatch_summary.md"];
    }

    state.activeDeliverables.forEach(file => {
      const btn = document.createElement("button");
      btn.className = "flex items-center gap-1.5 px-3 py-1 rounded-lg bg-cyber-900 hover:bg-emerald-500/20 text-slate-300 hover:text-emerald-400 border border-cyber-700/60 transition cursor-pointer font-mono text-[11px]";
      btn.innerHTML = `<i data-lucide="file" class="w-3.5 h-3.5"></i><span>${escapeHtml(file)}</span>`;
      btn.addEventListener("click", () => previewWorkspaceFile(file));
      deliverablesList.appendChild(btn);
    });

    if (window.lucide) lucide.createIcons();

    // Auto preview the first file
    if (state.activeDeliverables.length > 0) {
      previewWorkspaceFile(state.activeDeliverables[0]);
    }
  }

  appendChatMessage(`All deliverables are compiled and verified. You can click any file above to preview its contents immediately, or download the full ZIP archive.`, "assistant");
}

// Preview File in In-Browser Viewer Panel
async function previewWorkspaceFile(filePath) {
  if (!state.sessionId) return;
  const fileNameBadge = document.getElementById("activeFileName");
  const pre = document.getElementById("fileContentPre");
  if (fileNameBadge) fileNameBadge.textContent = filePath;

  try {
    const res = await fetch(`/api/workspace/${state.sessionId}/file?path=${encodeURIComponent(filePath)}`);
    const data = await res.json();
    if (data.content) {
      state.activeFileContent = data.content;
      if (pre) pre.textContent = data.content;
    } else {
      if (pre) pre.textContent = "// File exists but is empty or could not be read.";
    }
  } catch (err) {
    if (pre) pre.textContent = `// Error loading file preview: ${err.message}`;
  }
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
      label.className = "text-emerald-300 font-semibold text-[11px] whitespace-nowrap";
    } else {
      circle.className = "w-5 h-5 rounded-full bg-cyber-850 text-slate-400 flex items-center justify-center font-mono font-bold text-[10px] border border-cyber-700";
      label.className = "text-slate-400 font-medium text-[11px] whitespace-nowrap";
    }
  });
}

// Load Work History from Backend
async function loadWorkHistory() {
  try {
    const res = await fetch("/api/history");
    const items = await res.json();
    state.historyItems = items || [];
    renderHistoryList();
  } catch (err) {
    console.error("Failed to fetch work history:", err);
  }
}

// Render Filtered & Searched History List in Sidebar
function renderHistoryList() {
  const container = document.getElementById("historyList");
  if (!container) return;

  let filtered = state.historyItems.filter(item => {
    // Folder filter
    if (state.activeFolderFilter === "pinned") {
      if (!item.is_pinned) return false;
    } else if (state.activeFolderFilter !== "all") {
      if (item.folder !== state.activeFolderFilter) return false;
    }
    // Search query
    if (state.searchQuery) {
      const matchTitle = item.title && item.title.toLowerCase().includes(state.searchQuery);
      const matchPrompt = item.prompt && item.prompt.toLowerCase().includes(state.searchQuery);
      if (!matchTitle && !matchPrompt) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = '<div class="text-center py-6 text-slate-600 text-[11px]">No matching tasks found.</div>';
    return;
  }

  container.innerHTML = "";
  filtered.forEach(item => {
    const itemDiv = document.createElement("div");
    itemDiv.className = `p-2.5 rounded-xl border transition cursor-pointer group flex flex-col gap-1.5 ${
      state.sessionId === item.session_id 
        ? "bg-cyber-850 border-emerald-500/50 shadow-sm" 
        : "bg-cyber-950/70 hover:bg-cyber-850/80 border-cyber-800/80"
    }`;

    itemDiv.innerHTML = `
      <div class="flex items-start justify-between gap-1.5">
        <span class="font-semibold text-slate-200 line-clamp-1 text-xs group-hover:text-emerald-300 transition">${escapeHtml(item.title || item.prompt)}</span>
        <button class="pin-toggle-btn text-slate-500 hover:text-amber-400 transition" title="${item.is_pinned ? "Unpin task" : "Pin task"}">
          <i data-lucide="pin" class="w-3.5 h-3.5 ${item.is_pinned ? "fill-amber-400 text-amber-400" : ""}"></i>
        </button>
      </div>
      <div class="flex items-center justify-between text-[10px] text-slate-500 font-mono">
        <span class="px-1.5 py-0.5 rounded bg-cyber-800 text-slate-400">${escapeHtml(item.folder || "Personal")}</span>
        <span>${escapeHtml(item.created_at ? item.created_at.substring(0, 10) : "")}</span>
      </div>
    `;

    // Click to select task
    itemDiv.addEventListener("click", (e) => {
      if (e.target.closest(".pin-toggle-btn")) return;
      selectHistoryItem(item);
    });

    // Pin button click
    const pinBtn = itemDiv.querySelector(".pin-toggle-btn");
    if (pinBtn) {
      pinBtn.addEventListener("click", async (e) => {
        e.stopPropagation();
        await togglePinTask(item.session_id, !item.is_pinned);
      });
    }

    container.appendChild(itemDiv);
  });

  if (window.lucide) lucide.createIcons();
}

// Select a Past History Task
async function selectHistoryItem(item) {
  state.sessionId = item.session_id;
  renderHistoryList();
  appendChatMessage(`Retrieved workspace for: "${item.title || item.prompt}"`, "assistant");

  // Show Deliverables
  if (item.deliverables && item.deliverables.length > 0) {
    showWorkDoneBanner(item.deliverables);
  }
}

// Toggle Task Pin Status
async function togglePinTask(sessionId, isPinned) {
  try {
    await fetch("/api/history/pin", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ session_id: sessionId, is_pinned: isPinned })
    });
    loadWorkHistory();
  } catch (err) {
    console.error("Could not toggle pin:", err);
  }
}

// Load Saved Reusable Workflows
async function loadSavedWorkflows() {
  const container = document.getElementById("workflowsList");
  if (!container) return;

  try {
    const res = await fetch("/api/workflows");
    const workflows = await res.json();
    state.savedWorkflows = workflows || [];

    if (state.savedWorkflows.length === 0) {
      container.innerHTML = '<div class="text-[11px] text-slate-600">No workflows saved yet.</div>';
      return;
    }

    container.innerHTML = "";
    state.savedWorkflows.forEach(wf => {
      const btn = document.createElement("button");
      btn.className = "w-full text-left p-2 rounded-lg bg-cyber-900 hover:bg-cyber-850 border border-cyber-800/80 hover:border-emerald-500/40 text-slate-300 hover:text-emerald-300 text-xs transition flex items-center justify-between";
      btn.innerHTML = `
        <span class="truncate font-medium">${escapeHtml(wf.name)}</span>
        <i data-lucide="play" class="w-3 h-3 text-slate-500 shrink-0"></i>
      `;

      btn.addEventListener("click", () => {
        const input = document.getElementById("directiveInput");
        if (input) {
          input.value = wf.prompt;
          input.focus();
        }
      });

      container.appendChild(btn);
    });

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Failed to fetch workflows:", err);
  }
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
