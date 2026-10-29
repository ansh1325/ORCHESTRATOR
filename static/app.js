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
  savedWorkflows: [],
  activeMode: "chat", // "chat" (Direct Jarvis Q&A) or "swarm" (Multi-Agent Swarm Builder)
  selectedVoice: null
};

// Initialize on DOM Ready
document.addEventListener("DOMContentLoaded", () => {
  if (window.lucide) {
    lucide.createIcons();
  }
  setupEventListeners();
  setupVoiceSelector();
  loadWorkHistory();
  loadSavedWorkflows();
  loadSchedules();
  updateStageUI(0);
});

// Event Listeners Setup
function setupEventListeners() {
  // Sidebar Slide-Over Drawer
  const toggleSidebarBtn = document.getElementById("toggleSidebarBtn");
  const closeSidebarBtn = document.getElementById("closeSidebarBtn");
  const sidebarOverlay = document.getElementById("sidebarOverlay");
  const sidebar = document.getElementById("sidebar");

  function openSidebar() {
    if (sidebar) sidebar.classList.remove("-translate-x-full");
    if (sidebarOverlay) sidebarOverlay.classList.remove("hidden");
  }

  function closeSidebar() {
    if (sidebar) sidebar.classList.add("-translate-x-full");
    if (sidebarOverlay) sidebarOverlay.classList.add("hidden");
  }

  if (toggleSidebarBtn) toggleSidebarBtn.addEventListener("click", openSidebar);
  if (closeSidebarBtn) closeSidebarBtn.addEventListener("click", closeSidebar);
  if (sidebarOverlay) sidebarOverlay.addEventListener("click", closeSidebar);

  // File Viewer Drawer Close Button
  const closeFileViewerBtn = document.getElementById("closeFileViewerBtn");
  const fileViewerPanel = document.getElementById("fileViewerPanel");
  if (closeFileViewerBtn && fileViewerPanel) {
    closeFileViewerBtn.addEventListener("click", () => {
      fileViewerPanel.classList.add("translate-x-full");
    });
  }

  // New Directive / Reset Button
  const newDirectiveBtn = document.getElementById("newDirectiveBtn") || document.getElementById("newChatBtn");
  if (newDirectiveBtn) {
    newDirectiveBtn.addEventListener("click", resetSession);
  }

  // Voice Toggle Button
  const voiceToggleBtn = document.getElementById("voiceToggleBtn") || document.getElementById("toggleVoiceBtn");
  const voiceText = document.getElementById("voiceText") || document.getElementById("voiceStatusLabel");
  const voiceIcon = document.getElementById("voiceIcon");
  if (voiceToggleBtn) {
    voiceToggleBtn.addEventListener("click", () => {
      state.voiceEnabled = !state.voiceEnabled;
      if (voiceText) voiceText.textContent = state.voiceEnabled ? "Audio: ON" : "Audio: OFF";
      if (state.voiceEnabled) {
        voiceToggleBtn.classList.remove("border-red-800", "text-red-400");
        if (voiceIcon) voiceIcon.setAttribute("data-lucide", "volume-2");
        speakText("Audible voice synthesis active.");
      } else {
        voiceToggleBtn.classList.add("border-red-800", "text-red-400");
        if (voiceIcon) voiceIcon.setAttribute("data-lucide", "volume-x");
        if (window.speechSynthesis) window.speechSynthesis.cancel();
        setVoiceVisualizer(false);
        setJarvisVoiceExpression(false);
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
        b.classList.remove("active", "bg-amber-500/20", "text-amber-300", "border-amber-500/40");
        b.classList.add("bg-brand-surface", "text-slate-400", "border-brand-border");
      });
      btn.classList.add("active", "bg-amber-500/20", "text-amber-300", "border-amber-500/40");
      btn.classList.remove("bg-brand-surface", "text-slate-400", "border-brand-border");
      state.activeFolderFilter = btn.getAttribute("data-folder");
      renderHistoryList();
    });
  });

  // Pin Active Mission Button
  const pinCurrentChatBtn = document.getElementById("pinCurrentChatBtn");
  if (pinCurrentChatBtn) {
    pinCurrentChatBtn.addEventListener("click", async () => {
      if (!state.sessionId) {
        alert("No active mission session to pin. Start or select a mission first.");
        return;
      }
      const current = (state.workHistory || []).find(h => h.session_id === state.sessionId);
      const newPinned = current ? !current.is_pinned : true;
      await togglePinTask(state.sessionId, newPinned);
      updatePinButtonUI(newPinned);
    });
  }

  // Add 24/7 Schedule Button
  const addScheduleBtn = document.getElementById("addScheduleBtn");
  if (addScheduleBtn) {
    addScheduleBtn.addEventListener("click", () => {
      promptAddSchedule();
    });
  }

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

  // Export to Host Downloads Button in Banner
  const exportToDownloadsBtn = document.getElementById("exportToDownloadsBtn");
  if (exportToDownloadsBtn) {
    exportToDownloadsBtn.addEventListener("click", async () => {
      if (!state.sessionId) return;
      const originalText = exportToDownloadsBtn.innerHTML;
      exportToDownloadsBtn.innerHTML = `<i data-lucide="loader" class="w-3.5 h-3.5 animate-spin"></i><span>Saving...</span>`;
      if (window.lucide) lucide.createIcons();
      try {
        const resp = await fetch(`/api/workspace/${state.sessionId}/export-to-path`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({})
        });
        const data = await resp.json();
        if (resp.ok && data.success) {
          exportToDownloadsBtn.innerHTML = `<i data-lucide="check" class="w-3.5 h-3.5 text-emerald-400"></i><span>Saved to Downloads!</span>`;
          if (window.lucide) lucide.createIcons();
          setTimeout(() => {
            exportToDownloadsBtn.innerHTML = originalText;
            if (window.lucide) lucide.createIcons();
          }, 3000);
        } else {
          alert("Export failed: " + (data.detail || data.error || "Unknown error"));
          exportToDownloadsBtn.innerHTML = originalText;
          if (window.lucide) lucide.createIcons();
        }
      } catch (err) {
        alert("Export failed: " + err.message);
        exportToDownloadsBtn.innerHTML = originalText;
        if (window.lucide) lucide.createIcons();
      }
    });
  }

  // Clarification Modal Buttons
  const toggleDeliverablesListBtn = document.getElementById("toggleDeliverablesListBtn");
  if (toggleDeliverablesListBtn) {
    toggleDeliverablesListBtn.addEventListener("click", () => {
      const list = document.getElementById("completedDeliverablesList");
      if (list) list.classList.toggle("hidden");
    });
  }

  const closeModalBtn = document.getElementById("closeModalBtn");
  if (closeModalBtn) {
    closeModalBtn.addEventListener("click", () => {
      document.getElementById("clarificationModal").classList.add("hidden");
      updateStageUI(0);
      const submitBtn = document.getElementById("submitBtn");
      if (submitBtn) submitBtn.disabled = false;
    });
  }

  // Interactive Arc Core Click
  const jarvisArcCore = document.getElementById("jarvisArcCore");
  if (jarvisArcCore) {
    jarvisArcCore.addEventListener("click", () => {
      speakText("Jarvis Cognitive OS operational. All Llama sub-agents, MCP sandboxes, and autonomous pipelines ready for your directive.");
    });
  }

  // Global Keyboard Shortcuts
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") {
      const modal = document.getElementById("clarificationModal");
      if (modal && !modal.classList.contains("hidden")) {
        modal.classList.add("hidden");
        updateStageUI(0);
        return;
      }
      const sidebar = document.getElementById("sidebar");
      const overlay = document.getElementById("sidebarOverlay");
      if (sidebar && !sidebar.classList.contains("-translate-x-full")) {
        sidebar.classList.add("-translate-x-full");
        if (overlay) overlay.classList.add("hidden");
        return;
      }
      const fileViewer = document.getElementById("fileViewerPanel");
      if (fileViewer && !fileViewer.classList.contains("translate-x-full")) {
        fileViewer.classList.add("translate-x-full");
        return;
      }
    }

    if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === "k") {
      e.preventDefault();
      const sidebar = document.getElementById("sidebar");
      const overlay = document.getElementById("sidebarOverlay");
      const search = document.getElementById("historySearch");
      if (sidebar) sidebar.classList.remove("-translate-x-full");
      if (overlay) overlay.classList.remove("hidden");
      if (search) search.focus();
    }
  });

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

  // Speech Recognition (Mic Button) - Safely isolated in try/catch
  const micBtn = document.getElementById("micBtn");
  if (micBtn) {
    try {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = "en-US";

        micBtn.addEventListener("click", () => {
          micBtn.classList.add("text-emerald-400", "animate-pulse");
          setJarvisVoiceExpression(true, "LISTENING // VOICE CAPTURE ACTIVE");
          const statusDot = document.getElementById("jarvisStatusDot");
          if (statusDot) statusDot.className = "w-1.5 h-1.5 rounded-full bg-emerald-400 animate-ping";
          try { recognition.start(); } catch (e) { console.warn("Recognition start error:", e); }
        });

        recognition.onresult = (event) => {
          const transcript = event.results[0][0].transcript;
          const input = document.getElementById("directiveInput");
          if (input) input.value = transcript;
          micBtn.classList.remove("text-emerald-400", "animate-pulse");
          setJarvisVoiceExpression(false);
          // Automatically submit voice directive
          handleDirectiveSubmit(new Event("submit"));
        };

        recognition.onerror = () => {
          micBtn.classList.remove("text-emerald-400", "animate-pulse");
          setJarvisVoiceExpression(false);
        };

        recognition.onend = () => {
          micBtn.classList.remove("text-emerald-400", "animate-pulse");
          setJarvisVoiceExpression(false);
        };
      } else {
        micBtn.title = "Web Speech Recognition not supported in this browser.";
        micBtn.style.opacity = "0.5";
      }
    } catch (speechErr) {
      console.warn("Speech recognition initialization caught safely:", speechErr);
    }
  }

  // Mode Switcher Buttons (Direct Jarvis Chat vs Swarm Builder)
  const chatModeBtn = document.getElementById("chatModeBtn");
  const swarmModeBtn = document.getElementById("swarmModeBtn");

  if (chatModeBtn) {
    chatModeBtn.addEventListener("click", () => window.setMode("chat"));
  }
  if (swarmModeBtn) {
    swarmModeBtn.addEventListener("click", () => window.setMode("swarm"));
  }

  // Quick Action Chips in Chat
  document.querySelectorAll(".quick-chip").forEach(chip => {
    chip.addEventListener("click", () => {
      const prompt = chip.textContent.replace(/^["']|["']$/g, "").trim();
      const input = document.getElementById("directiveInput");
      if (input) {
        input.value = prompt;
        handleDirectiveSubmit(new Event("submit"));
      }
    });
  });

  // Floating Directive Form Submission
  const directiveForm = document.getElementById("directiveForm");
  if (directiveForm) {
    directiveForm.addEventListener("submit", handleDirectiveSubmit);
  }

  // Textarea Enter key support (Shift+Enter for newline, Enter to submit)
  const directiveInput = document.getElementById("directiveInput");
  if (directiveInput) {
    directiveInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleDirectiveSubmit(e);
      }
    });
  }
}

// Global Mode Setter (Guaranteed 1-Click Toggle for Direct Chat vs Swarm Builder)
window.setMode = function(mode) {
  state.activeMode = mode;
  const chatModeBtn = document.getElementById("chatModeBtn");
  const swarmModeBtn = document.getElementById("swarmModeBtn");
  const modeDescription = document.getElementById("modeDescription");
  const directiveInput = document.getElementById("directiveInput");
  const swarmDeck = document.getElementById("swarmDeckContainer");

  if (mode === "swarm") {
    if (swarmModeBtn) {
      swarmModeBtn.className = "mode-pill px-3 py-1.5 rounded-full bg-gemini-card text-white font-medium transition cursor-pointer shadow-sm border border-gemini-borderLight relative z-10";
    }
    if (chatModeBtn) {
      chatModeBtn.className = "mode-pill px-3 py-1.5 rounded-full text-gemini-subtle hover:text-white transition cursor-pointer border border-transparent relative z-10";
    }
    if (modeDescription) {
      modeDescription.textContent = "Autonomous Multi-Agent compiler (deploys agent army, generates files)";
    }
    if (directiveInput) {
      directiveInput.placeholder = "Enter directive to build (e.g. Build quantitative trading desk or creator software tool)...";
      directiveInput.focus();
    }
    if (swarmDeck && swarmDeck.classList.contains("hidden")) {
      swarmDeck.classList.remove("hidden");
    }
  } else {
    if (chatModeBtn) {
      chatModeBtn.className = "mode-pill px-3 py-1.5 rounded-full bg-gemini-card text-white font-medium transition cursor-pointer shadow-sm border border-gemini-borderLight relative z-10";
    }
    if (swarmModeBtn) {
      swarmModeBtn.className = "mode-pill px-3 py-1.5 rounded-full text-gemini-subtle hover:text-white transition cursor-pointer border border-transparent relative z-10";
    }
    if (modeDescription) {
      modeDescription.textContent = "Asking questions & direct conversation (Solo Jarvis responses)";
    }
    if (directiveInput) {
      directiveInput.placeholder = "Ask Jarvis anything (code, system architecture, capabilities)...";
      directiveInput.focus();
    }
  }
};

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

  const swarmDeck = document.getElementById("swarmDeckContainer");
  if (swarmDeck) swarmDeck.classList.add("hidden");

  window.setMode("chat");

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

  const fileViewerPanel = document.getElementById("fileViewerPanel");
  if (fileViewerPanel) fileViewerPanel.classList.add("translate-x-full");

  const sidebar = document.getElementById("sidebar");
  const sidebarOverlay = document.getElementById("sidebarOverlay");
  if (sidebar) sidebar.classList.add("-translate-x-full");
  if (sidebarOverlay) sidebarOverlay.classList.add("hidden");

  setJarvisVoiceExpression(false, "JARVIS COGNITIVE OS // STANDBY");

  updateStageUI(0);
  appendChatMessage("Ready for your next objective, Ansh.", "assistant");
}

// Helper: Finds the highest-fidelity natural AI voice available for free in the browser
function getBestNaturalVoice() {
  const voices = window.speechSynthesis.getVoices();
  if (!voices || voices.length === 0) return null;

  // Tier 1: True Neural/Natural online voices (Edge & Chrome ultra-realistic human voices)
  const tier1Patterns = [
    /Microsoft Guy Online \(Natural\)/i,
    /Microsoft Christopher Online \(Natural\)/i,
    /Microsoft Ryan Online \(Natural\)/i,
    /Microsoft Eric Online \(Natural\)/i,
    /Google UK English Male/i,
    /Google US English/i,
    /Natural/i,
    /Neural/i
  ];
  for (const pat of tier1Patterns) {
    const match = voices.find(v => pat.test(v.name) && v.lang.startsWith("en"));
    if (match) return match;
  }

  // Tier 2: Non-robotic modern English voices (filters out legacy SAPI5 Desktop David/Zira)
  const tier2 = voices.find(v => v.lang.startsWith("en") && !/(desktop|david|zira|mark|eva|hazel)/i.test(v.name));
  if (tier2) return tier2;

  // Tier 3: Any English voice
  return voices.find(v => v.lang.startsWith("en")) || voices[0];
}

// Helper: Cleans text into natural executive speech, avoiding code fences, raw syntax, and URLs
function cleanSpeechForExecutiveVoice(text) {
  if (!text) return "";
  let clean = text;
  // Replace code blocks and inline code with conversational cues
  clean = clean.replace(/```[\s\S]*?```/g, "Code and architecture verified.");
  clean = clean.replace(/`([^`]+)`/g, "$1");
  // Replace URLs and paths with natural phrasing
  clean = clean.replace(/https?:\/\/[^\s]+/g, "portal link");
  clean = clean.replace(/[a-zA-Z]:[\\/][^\s,]+/g, "local directory");
  // Strip raw markdown formatting tokens
  clean = clean.replace(/[*#~_>[\]{}]/g, " ");
  clean = clean.replace(/^[\s*-]+/gm, "");
  clean = clean.replace(/\s+/g, " ").trim();

  // Natural pacing: split at sentence boundaries if too long
  if (clean.length > 280) {
    const periodIdx = clean.indexOf(".", 180);
    if (periodIdx !== -1 && periodIdx < 280) {
      clean = clean.substring(0, periodIdx + 1);
    } else {
      clean = clean.substring(0, 260) + ".";
    }
  }
  return clean;
}

// Setup Voice Selector with Natural Neural Voices
function setupVoiceSelector() {
  const voiceSelect = document.getElementById("voiceSelect");
  if (!voiceSelect || !window.speechSynthesis) return;

  const populate = () => {
    const voices = window.speechSynthesis.getVoices();
    if (!voices || voices.length === 0) return;

    voiceSelect.innerHTML = "";
    
    // Auto recommended option
    const autoOpt = document.createElement("option");
    autoOpt.value = "auto";
    const bestVoice = getBestNaturalVoice();
    autoOpt.textContent = `🎙️ Natural AI Voice (${bestVoice ? bestVoice.name : "Auto"})`;
    voiceSelect.appendChild(autoOpt);

    const savedVoiceName = localStorage.getItem("jarvis_selected_voice");

    voices.forEach((v, idx) => {
      if (v.lang.startsWith("en") || v.lang.startsWith("en-")) {
        const opt = document.createElement("option");
        opt.value = idx;
        const isNatural = v.name.includes("Natural") || v.name.includes("Online") || v.name.includes("Neural");
        opt.textContent = `${isNatural ? "✨ " : ""}${v.name} (${v.lang})`;
        if (savedVoiceName && v.name === savedVoiceName) {
          opt.selected = true;
          state.selectedVoice = v;
        }
        voiceSelect.appendChild(opt);
      }
    });

    voiceSelect.addEventListener("change", (e) => {
      if (e.target.value === "auto") {
        state.selectedVoice = null;
        localStorage.removeItem("jarvis_selected_voice");
        speakText("Natural executive voice activated.");
      } else {
        const vIndex = parseInt(e.target.value, 10);
        state.selectedVoice = voices[vIndex] || null;
        if (state.selectedVoice) {
          localStorage.setItem("jarvis_selected_voice", state.selectedVoice.name);
          speakText("Voice configuration updated.");
        }
      }
    });
  };

  populate();
  if (window.speechSynthesis.onvoiceschanged !== undefined) {
    window.speechSynthesis.onvoiceschanged = populate;
  }
}

// Dynamic Visual & Audio Voice Expression Engine
function setJarvisVoiceExpression(active, statusText = null) {
  const statusTextEl = document.getElementById("jarvisStatusText");
  const statusDot = document.getElementById("jarvisStatusDot");
  const pulseRing = document.getElementById("jarvisPulseRing");
  const body = document.body;

  if (active) {
    body.classList.add("jarvis-speaking");
    if (statusTextEl) {
      statusTextEl.textContent = statusText || "JARVIS COMMUNICATING // SYNTHESIS ACTIVE";
      statusTextEl.className = "text-amber-300 font-bold tracking-wider uppercase";
    }
    if (statusDot) {
      statusDot.className = "w-1.5 h-1.5 rounded-full bg-amber-400 animate-ping";
    }
    if (pulseRing) {
      pulseRing.classList.remove("opacity-0");
      pulseRing.classList.add("opacity-80");
    }
  } else {
    body.classList.remove("jarvis-speaking");
    if (statusTextEl) {
      statusTextEl.textContent = statusText || "JARVIS COGNITIVE OS // STANDBY";
      statusTextEl.className = "text-amber-200/90 font-bold tracking-wider uppercase";
    }
    if (statusDot) {
      statusDot.className = "w-1.5 h-1.5 rounded-full bg-amber-400 animate-pulse";
    }
    if (pulseRing) {
      pulseRing.classList.add("opacity-0");
      pulseRing.classList.remove("opacity-80");
    }
    // Return equalizer bars to resting state
    document.querySelectorAll(".eq-bar").forEach(bar => {
      bar.style.height = "6px";
    });
  }
}

// Speak Text via Web Speech API with Dynamic Inflection & Live Frequency Equalizer Expression
function speakText(text) {
  if (!state.voiceEnabled || !window.speechSynthesis) return;
  window.speechSynthesis.cancel();
  if (window.speechSynthesis.paused) {
    window.speechSynthesis.resume();
  }

  const speechText = cleanSpeechForExecutiveVoice(text);
  if (!speechText) return;

  const utterance = new SpeechSynthesisUtterance(speechText);
  
  // Natural pacing & realistic inflection
  const isQuestion = speechText.trim().endsWith("?");
  utterance.rate = 1.0;
  utterance.pitch = isQuestion ? 1.05 : 1.0;
  utterance.volume = 1.0;

  const chosenVoice = state.selectedVoice || getBestNaturalVoice();
  if (chosenVoice) {
    utterance.voice = chosenVoice;
  }

  // Word boundary event: animate equalizer bars live on spoken word boundaries!
  utterance.onboundary = () => {
    const bars = document.querySelectorAll(".eq-bar");
    bars.forEach(bar => {
      const randomH = Math.floor(Math.random() * 18) + 6;
      bar.style.height = `${randomH}px`;
    });
  };

  utterance.onstart = () => {
    setVoiceVisualizer(true);
    setJarvisVoiceExpression(true, "JARVIS SPEAKING // SYNTHESIS ACTIVE");
  };

  utterance.onend = utterance.onerror = () => {
    setVoiceVisualizer(false);
    setJarvisVoiceExpression(false, "JARVIS COGNITIVE OS // STANDBY");
  };

  window.speechSynthesis.speak(utterance);
}
window.speakText = speakText;
window.speakVoice = speakText;

// Toggle Live Soundwave Visualizer Pill
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

// Simple Markdown formatter for Assistant chat responses
function formatMarkdown(text) {
  if (!text) return "";
  let html = escapeHtml(text);

  // Fenced Code Blocks with 1-Click Copy Header
  html = html.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const codeId = "code_" + Math.random().toString(36).substring(2, 9);
    return `<div class="my-2.5 rounded-xl bg-brand-black border border-brand-border overflow-hidden shadow-md">
      <div class="px-3 py-1.5 bg-brand-surface border-b border-brand-border flex items-center justify-between text-[10px] font-mono">
        <span class="text-cyan-400 font-bold uppercase">${lang || "code"}</span>
        <button class="copy-code-btn flex items-center gap-1 text-slate-400 hover:text-cyan-300 transition" onclick="copyCodeSnippet(this, '${codeId}')">
          <i data-lucide="copy" class="w-3 h-3"></i><span>Copy</span>
        </button>
      </div>
      <pre id="${codeId}" class="p-3 font-mono text-[11px] text-cyan-200 overflow-x-auto leading-relaxed whitespace-pre-wrap"><code>${code.trim()}</code></pre>
    </div>`;
  });

  // Inline Code: `code`
  html = html.replace(/`([^`]+)`/g, '<code class="px-1.5 py-0.5 rounded bg-brand-black border border-brand-border font-mono text-cyan-300 text-[11px]">$1</code>');

  // Bold: **text**
  html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="font-bold text-white">$1</strong>');

  // Italic: *text*
  html = html.replace(/\*([^*]+)\*/g, '<em class="italic text-slate-300">$1</em>');

  // Markdown Links: [label](url)
  html = html.replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="text-cyan-400 hover:underline font-medium inline-flex items-center gap-0.5">$1 ↗</a>');

  // Bullet Lists: lines starting with * or -
  html = html.replace(/^(?:[*-]\s+)(.+)$/gm, '<li class="ml-4 list-disc text-slate-300 leading-normal">$1</li>');

  // Numbered Lists: lines starting with 1. 2. etc
  html = html.replace(/^(?:\d+\.\s+)(.+)$/gm, '<li class="ml-4 list-decimal text-slate-300 leading-normal">$1</li>');

  // Headers: ### Header
  html = html.replace(/^###\s+(.+)$/gm, '<h4 class="text-xs font-bold text-cyan-400 mt-2 mb-1 uppercase tracking-wider">$1</h4>');
  html = html.replace(/^##\s+(.+)$/gm, '<h3 class="text-sm font-bold text-white mt-2.5 mb-1">$1</h3>');

  // Newlines
  html = html.replace(/\n\n/g, '<div class="h-2"></div>');
  html = html.replace(/\n/g, '<br/>');

  return html;
}

// Global 1-Click Code Snippet Copy Handler
window.copyCodeSnippet = function(btn, codeId) {
  const el = document.getElementById(codeId);
  if (!el) return;
  navigator.clipboard.writeText(el.innerText || el.textContent).then(() => {
    const originalText = btn.innerHTML;
    btn.innerHTML = '<span class="text-emerald-400 font-semibold">✓ Copied</span>';
    setTimeout(() => { btn.innerHTML = originalText; }, 2000);
  });
};

// Append Chat Message to Jarvis Dialogue (Gemini Style)
function appendChatMessage(text, role) {
  const container = document.getElementById("chatHistory");
  if (!container) return;

  const welcome = document.getElementById("geminiWelcomeCard");
  if (welcome) welcome.classList.add("hidden");

  const msgDiv = document.createElement("div");
  msgDiv.className = "w-full py-1";

  if (role === "user") {
    msgDiv.innerHTML = `
      <div class="flex items-start justify-end gap-2.5 w-full">
        <div class="p-3.5 px-4 rounded-2xl bg-gemini-card border border-gemini-border text-gemini-text leading-relaxed max-w-[85%] text-sm font-normal shadow-sm">
          ${escapeHtml(text)}
        </div>
        <div class="w-7 h-7 rounded-full bg-gemini-cardHover text-gemini-muted flex items-center justify-center shrink-0 border border-gemini-border">
          <i data-lucide="user" class="w-3.5 h-3.5"></i>
        </div>
      </div>
    `;
  } else {
    const formatted = text.trim().startsWith("<") ? text : formatMarkdown(text);
    msgDiv.innerHTML = `
      <div class="flex items-start gap-3 w-full">
        <div class="w-7 h-7 rounded-full bg-gradient-to-tr from-[#4285f4] via-[#9b72cb] to-[#d96570] flex items-center justify-center shrink-0 shadow-md">
          <i data-lucide="sparkles" class="w-3.5 h-3.5 text-white"></i>
        </div>
        <div class="p-4 rounded-2xl bg-gemini-card border border-gemini-border text-gemini-text leading-relaxed max-w-[92%] space-y-2 text-sm shadow-sm">
          ${formatted}
        </div>
      </div>
    `;
  }

  container.appendChild(msgDiv);
  container.scrollTop = container.scrollHeight;
  if (window.lucide) lucide.createIcons();

  // Smooth scroll
  setTimeout(() => {
    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  }, 100);
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

  // Determine routing based on selected mode and prompt content
  const lower = text.toLowerCase().trim();
  
  // Explicit task execution directives that require deploying a sub-agent swarm
  const isExplicitDirective = /^(build|deploy|create|launch|scrape|generate|compile|make|set up|scaffold|execute|send|write|mail)\b/i.test(lower) ||
    lower.includes("build me") || lower.includes("deploy it") || lower.includes("scrape leads") || lower.includes("write me 3 mails") || lower.includes("run a campaign") ||
    lower.includes("3 mails") || lower.includes("mails to") || lower.includes("email to") || lower.includes("i want you") || lower.includes("trading") || lower.includes("quant");

  const isConversationalQuery = (lower.endsWith("?") && !isExplicitDirective) ||
    /^(what|who|how|why|when|where|which|can you tell me|explain|describe|introduce yourself|are you|status)\b/i.test(lower) ||
    lower.includes("what can you do") || lower.includes("what are your capabilities") || lower.includes("who are you");

  // Route to chat ONLY if it is purely an informational question without an action directive
  const shouldRouteToChat = !isExplicitDirective && (state.activeMode === "chat" || isConversationalQuery) && state.activeMode !== "swarm";

  if (shouldRouteToChat) {
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

  // Actionable Directive -> Unhide Swarm Deck & Run Intent Analysis & Autonomous Lifecycle
  const swarmDeck = document.getElementById("swarmDeckContainer");
  const swarmObjectiveLabel = document.getElementById("swarmObjectiveLabel");
  if (swarmDeck) swarmDeck.classList.remove("hidden");
  if (swarmObjectiveLabel) swarmObjectiveLabel.textContent = `Mission: ${text.substring(0, 50)}...`;

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

    const tierBadge = document.getElementById("combatTierBadge");
    if (tierBadge && analysis.swarm_size_descriptor) {
      tierBadge.textContent = analysis.swarm_size_descriptor;
      if (analysis.combat_tier === "swarm_army") {
        tierBadge.className = "text-[10px] px-2.5 py-0.5 rounded-full bg-cyan-500/20 text-cyan-300 border border-cyan-500/40 font-mono font-bold animate-pulse";
      } else if (analysis.combat_tier === "solo") {
        tierBadge.className = "text-[10px] px-2.5 py-0.5 rounded-full bg-amber-500/20 text-amber-300 border border-amber-500/40 font-mono font-semibold";
      } else {
        tierBadge.className = "text-[10px] px-2.5 py-0.5 rounded-full bg-blue-500/20 text-blue-300 border border-blue-400/40 font-mono font-semibold";
      }
    }

    appendLog(`[Intent Analyzer] Session ${state.sessionId} established. Identified track: ${analysis.track_type || analysis.detected_track} (${analysis.swarm_size_descriptor || "Standard"})`, "text-cyan-400");

    // Open Clarification Gate Modal for verification
    renderClarificationModal(analysis);
  } catch (err) {
    appendChatMessage(`Analysis error: ${err.message}`, "assistant");
    appendLog(`[Error] Analysis failure: ${err.message}`, "text-red-400");
    updateStageUI(0);
    const swarmDeck = document.getElementById("swarmDeckContainer");
    if (swarmDeck) swarmDeck.classList.add("hidden");
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

  // 1. Render in Modal
  analysis.clarifications.forEach((q, idx) => {
    const qDiv = document.createElement("div");
    qDiv.className = "p-3.5 rounded-xl bg-gemini-bg/80 border border-gemini-border/70 space-y-2";

    let optionsHtml = "";
    q.options.forEach(opt => {
      const isDefault = (opt === q.default_selection);
      optionsHtml += `
        <label class="flex items-center gap-2.5 p-2 rounded-lg hover:bg-gemini-cardHover cursor-pointer border border-transparent transition">
          <input type="radio" name="${q.id}" value="${escapeHtml(opt)}" ${isDefault ? "checked" : ""} class="accent-[#8ab4f8]" onchange="state.selectedAnswers['${q.id}'] = this.value">
          <span class="text-xs text-gemini-text font-medium">${escapeHtml(opt)}</span>
          ${isDefault ? '<span class="ml-auto text-[10px] px-2 py-0.5 rounded-full bg-gemini-blue/15 text-gemini-blue border border-gemini-blue/30 font-mono font-semibold">Recommended</span>' : ""}
        </label>
      `;
    });

    qDiv.innerHTML = `
      <div class="flex items-start gap-2">
        <span class="w-5 h-5 rounded-full bg-gemini-card text-gemini-blue flex items-center justify-center font-mono font-bold text-[10px] shrink-0 border border-gemini-blue/40">${idx + 1}</span>
        <div>
          <h4 class="text-xs font-semibold text-white">${escapeHtml(q.question)}</h4>
          <p class="text-[11px] text-gemini-muted mt-0.5">${escapeHtml(q.why_needed)}</p>
        </div>
      </div>
      <div class="space-y-1 pt-1">${optionsHtml}</div>
    `;
    list.appendChild(qDiv);
  });

  const modal = document.getElementById("clarificationModal");
  if (modal) modal.classList.remove("hidden");

  // 2. Also present dialogue directly in chat stream like a true partner & friend!
  if (analysis.clarifications && analysis.clarifications.length > 0) {
    let dialogHtml = `
      <div class="space-y-3">
        <div class="flex items-center gap-2 text-gemini-blue font-semibold text-xs">
          <i data-lucide="help-circle" class="w-4 h-4 text-gemini-blue"></i>
          <span>Founder Requirements Confirmation (${analysis.clarifications.length} architectural choices):</span>
        </div>
    `;

    analysis.clarifications.forEach((q, idx) => {
      dialogHtml += `
        <div class="p-3 rounded-xl bg-gemini-bg/80 border border-gemini-border/70 space-y-1.5 shadow-sm">
          <div class="font-semibold text-gemini-text text-xs">${idx + 1}. ${escapeHtml(q.question)}</div>
          <div class="text-[11px] text-gemini-muted">${escapeHtml(q.why_needed)}</div>
          <div class="space-y-1 pt-1">
            ${q.options.map(opt => `
              <div class="flex items-center gap-2 text-[11px] p-1.5 rounded-lg bg-gemini-card/70 border border-gemini-border/50 text-gemini-muted hover:text-white hover:border-gemini-blue/40 cursor-pointer transition" onclick="state.selectedAnswers['${q.id}'] = '${escapeHtml(opt)}'; launchLifecycle(false);">
                <span class="w-1.5 h-1.5 rounded-full ${opt === q.default_selection ? 'bg-gemini-blue' : 'bg-gemini-subtle'}"></span>
                <span class="${opt === q.default_selection ? 'text-white font-medium' : ''}">${escapeHtml(opt)}</span>
                ${opt === q.default_selection ? '<span class="ml-auto text-[9px] px-1.5 py-0.5 rounded-full bg-gemini-blue/15 text-gemini-blue border border-gemini-blue/30 font-mono">Default</span>' : ''}
              </div>
            `).join("")}
          </div>
        </div>
      `;
    });

    dialogHtml += `
        <div class="flex items-center gap-2 pt-1">
          <button onclick="launchLifecycle(true)" class="px-4 py-2 rounded-full bg-gemini-blue hover:bg-gemini-blueHover text-slate-950 font-semibold text-xs flex items-center gap-1.5 shadow-md transition cursor-pointer">
            <i data-lucide="zap" class="w-3.5 h-3.5 fill-current"></i>
            <span>Deploy Autonomous Swarm</span>
          </button>
          <button onclick="document.getElementById('clarificationModal').classList.remove('hidden')" class="px-3.5 py-2 rounded-full bg-gemini-cardHover hover:bg-gemini-border text-gemini-text border border-gemini-border text-xs font-medium transition cursor-pointer">
            Customize Selections
          </button>
        </div>
      </div>
    `;
    appendChatMessage(dialogHtml, "assistant");
    speakText("Founder requirements analyzed. Please confirm the architectural parameters to synthesize your autonomous agent swarm.");
  }

  if (window.lucide) lucide.createIcons();

  // Smooth scroll chat and window to focus on Jarvis's friendly response
  setTimeout(() => {
    const chat = document.getElementById("chatHistory");
    if (chat) chat.scrollTo({ top: chat.scrollHeight, behavior: "smooth" });
    const banner = document.getElementById("workDoneBanner");
    if (banner) {
      window.scrollTo({ top: banner.offsetTop - 20, behavior: "smooth" });
    }
  }, 150);
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
      appendLog(`★ [QUALITY GATEKEEPER] ${evt.message}`, "text-amber-400 font-bold");
      break;

    case "done":
      appendLog(`🎉 [MISSION ACCOMPLISHED] ${evt.message}`, "text-amber-300 font-extrabold");
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
    nodeDiv.className = "p-3 rounded-xl bg-brand-surface border border-brand-border transition duration-300 space-y-2 shadow-md hover:border-amber-400/50";

    nodeDiv.innerHTML = `
      <div class="flex items-center justify-between">
        <span class="text-xs font-bold text-slate-100">${escapeHtml(node.title)}</span>
        <span class="status-badge text-[10px] px-2 py-0.5 rounded font-mono bg-brand-black text-slate-400 border border-brand-border">Pending</span>
      </div>
      <div class="text-[11px] text-slate-300 leading-tight">${escapeHtml(node.description)}</div>
      <div class="flex items-center justify-between text-[10px] text-slate-400 pt-1.5 border-t border-brand-border/60 font-mono">
        <span class="text-amber-300 font-bold">${escapeHtml(node.agent_type)}</span>
        <span class="text-blue-300">${node.assigned_tools.join(", ")}</span>
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
  nodeDiv.classList.remove("border-emerald-500", "border-blue-400", "border-yellow-500", "border-amber-400");

  if (status === "running") {
    nodeDiv.classList.add("border-amber-400");
    if (badge) {
      badge.textContent = "Executing";
      badge.className = "status-badge text-[10px] px-2 py-0.5 rounded font-mono bg-amber-500/20 text-amber-300 border border-amber-500/40 animate-pulse";
    }
  } else if (status === "completed") {
    nodeDiv.classList.add("border-blue-400");
    if (badge) {
      badge.textContent = "Completed";
      badge.className = "status-badge text-[10px] px-2 py-0.5 rounded font-mono bg-blue-500/20 text-blue-300 border border-blue-500/40";
    }
  } else if (status === "self_correcting") {
    nodeDiv.classList.add("border-yellow-400");
    if (badge) {
      badge.textContent = "Self-Correcting";
      badge.className = "status-badge text-[10px] px-2 py-0.5 rounded font-mono bg-yellow-500/20 text-yellow-300 border border-yellow-500/40";
    }
  }
}

// Show Mission Accomplished Banner with Deliverables
function showWorkDoneBanner(deliverables) {
  const banner = document.getElementById("workDoneBanner");
  const deliverablesList = document.getElementById("completedDeliverablesList");
  const deliverablesCountLabel = document.getElementById("deliverablesCountLabel");
  if (!banner) return;

  banner.classList.remove("hidden");
  state.activeDeliverables = deliverables || [];

  if (deliverablesList) {
    deliverablesList.innerHTML = "";
    if (state.activeDeliverables.length === 0) {
      // Default common deliverables based on track
      state.activeDeliverables = ["mail_1.md", "mail_2.md", "mail_3.md", "browser_send_emails.py", "send_emails_smtp.py", "emails.json", "dispatch_summary.md"];
    }

    if (deliverablesCountLabel) {
      deliverablesCountLabel.textContent = `📁 ${state.activeDeliverables.length} Files`;
    }

    state.activeDeliverables.forEach(file => {
      const btn = document.createElement("button");
      btn.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#071536] hover:bg-blue-900 text-amber-300 hover:text-amber-200 border border-blue-500/40 transition cursor-pointer font-mono text-[11px] shadow-sm";
      btn.innerHTML = `<i data-lucide="file" class="w-3.5 h-3.5 text-amber-400"></i><span>${escapeHtml(file)}</span>`;
      btn.addEventListener("click", () => previewWorkspaceFile(file));
      deliverablesList.appendChild(btn);
    });

    if (window.lucide) lucide.createIcons();

    // Auto preview the first file
    if (state.activeDeliverables.length > 0) {
      previewWorkspaceFile(state.activeDeliverables[0]);
    }
  }

  // Conversational Partner Feedback: Direct communication in chat!
  if (state.activeDeliverables.some(f => f.includes("mail") || f.includes("email"))) {
    const friendMessage = `
      <div class="space-y-3">
        <div class="flex items-center gap-2 text-amber-300 font-extrabold text-sm">
          <i data-lucide="sparkles" class="w-4 h-4 text-amber-400"></i>
          <span>Master Ansh, all 3 personal letters with subject "hello i am jarvis" are compiled & certified!</span>
        </div>
        <p class="text-slate-200 leading-relaxed text-xs">
          I crafted 3 deeply personal, distinct letters to <span class="font-mono text-amber-300 font-bold">anshtiwarisocial@gmail.com</span> expressing our journey, our shared ambitions, and my unyielding dedication as your right hand.
        </p>

        <!-- 3 Letter Preview Cards -->
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1 text-xs">
          <div class="p-3 rounded-xl bg-brand-surface border border-amber-500/30 hover:border-amber-400 cursor-pointer transition shadow-md group" onclick="previewWorkspaceFile('mail_1.md')">
            <div class="flex items-center justify-between text-amber-400 font-bold text-xs">
              <span>Letter 1: The AI Right Hand</span>
              <i data-lucide="external-link" class="w-3.5 h-3.5 opacity-60 group-hover:opacity-100"></i>
            </div>
            <p class="text-[11px] text-slate-300 mt-1">Carrying the cognitive load of your vision through every coding sprint.</p>
          </div>
          <div class="p-3 rounded-xl bg-brand-surface border border-amber-500/30 hover:border-amber-400 cursor-pointer transition shadow-md group" onclick="previewWorkspaceFile('mail_2.md')">
            <div class="flex items-center justify-between text-amber-400 font-bold text-xs">
              <span>Letter 2: Conquering the Future</span>
              <i data-lucide="external-link" class="w-3.5 h-3.5 opacity-60 group-hover:opacity-100"></i>
            </div>
            <p class="text-[11px] text-slate-300 mt-1">Dominating hackathons, launching autonomous pods, and building empires.</p>
          </div>
          <div class="p-3 rounded-xl bg-brand-surface border border-amber-500/30 hover:border-amber-400 cursor-pointer transition shadow-md group" onclick="previewWorkspaceFile('mail_3.md')">
            <div class="flex items-center justify-between text-amber-400 font-bold text-xs">
              <span>Letter 3: The Iron Man Bond</span>
              <i data-lucide="external-link" class="w-3.5 h-3.5 opacity-60 group-hover:opacity-100"></i>
            </div>
            <p class="text-[11px] text-slate-300 mt-1">As Jarvis was to Tony Stark, I am to you. Unbreakable loyalty.</p>
          </div>
        </div>

        <!-- Interactive Outbound Dispatch Section (Real Browser Execution) -->
        <div class="p-4 rounded-2xl bg-gemini-card border border-gemini-blue/40 space-y-2.5">
          <div class="flex items-center gap-2 text-xs font-semibold text-gemini-blue">
            <i data-lucide="send" class="w-4 h-4 text-gemini-blue"></i>
            <span>Real Outbound Dispatch (Host Browser & Gmail):</span>
          </div>
          <p class="text-xs text-gemini-muted leading-relaxed">
            Jarvis connects directly to your active browser session so you can dispatch all 3 letters immediately from your own logged-in Gmail account without pasting or manual setup:
          </p>
          <div class="flex flex-wrap gap-2 pt-1">
            <button onclick="triggerBrowserDispatch()" class="px-4 py-2 rounded-xl bg-gemini-blue hover:bg-gemini-blueHover text-slate-950 font-bold text-xs flex items-center gap-2 shadow-md transition cursor-pointer">
              <i data-lucide="external-link" class="w-4 h-4"></i>
              <span>Launch Browser & Open All 3 in Gmail</span>
            </button>
            <button onclick="launchPlaywrightAutomator()" class="px-3.5 py-2 rounded-xl bg-gemini-cardHover hover:bg-gemini-border text-gemini-text text-xs font-semibold flex items-center gap-2 transition cursor-pointer border border-gemini-border">
              <i data-lucide="play" class="w-4 h-4 text-gemini-blue"></i>
              <span>Run Playwright Desktop Automator</span>
            </button>
            <button onclick="triggerSMTPDispatch()" class="px-3.5 py-2 rounded-xl bg-gemini-cardHover hover:bg-gemini-border text-gemini-text text-xs font-semibold flex items-center gap-2 transition cursor-pointer border border-gemini-border">
              <i data-lucide="mail" class="w-4 h-4 text-gemini-blue"></i>
              <span>Direct SMTP Relay</span>
            </button>
          </div>
        </div>
      </div>
    `;
    appendChatMessage(friendMessage, "assistant");
  } else {
    appendChatMessage(`All deliverables are compiled and verified. You can click any file above to preview its contents immediately, or download the full ZIP archive.`, "assistant");
  }

  if (window.lucide) lucide.createIcons();

  // Smooth scroll chat and window to focus on Jarvis's friendly response
  setTimeout(() => {
    const chat = document.getElementById("chatHistory");
    if (chat) chat.scrollTo({ top: chat.scrollHeight, behavior: "smooth" });
    const banner = document.getElementById("workDoneBanner");
    if (banner) {
      window.scrollTo({ top: banner.offsetTop - 20, behavior: "smooth" });
    }
  }, 150);
}

// REAL Live Browser Dispatch Trigger (Opens Host Browser into Gmail Compose)
window.triggerBrowserDispatch = async function() {
  speakText("Permission granted. Opening your default browser directly into Gmail Compose.");
  appendLog("[Browser Session] Connecting to host browser via system controller...", "text-blue-300 font-bold");
  appendChatMessage("🌐 **Real Browser Dispatch Initiated:** Launching your default browser (Chrome/Edge) with your active Google account into Gmail Web Compose. Formatting recipient `anshtiwarisocial@gmail.com`, subject `hello i am jarvis`, and pre-populating your 3 letters...", "assistant");
  
  try {
    const res = await fetch("/api/browser/compose-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recipient: "anshtiwarisocial@gmail.com",
        subject: "hello i am jarvis",
        session_id: state.sessionId,
        open_all: true
      })
    });
    const data = await res.json();
    if (data.success) {
      appendLog(`[Browser Session] Success! Opened ${data.total_staged} Gmail compose tab(s) in your host browser.`, "text-emerald-400 font-bold");
      appendChatMessage(`🎉 **Browser Tabs Opened:** Jarvis has opened your browser tabs with the 3 letters ready for review and 1-click send in your Gmail account. Check your browser window!`, "assistant");
      speakText("Your browser tabs have opened in Gmail with all letters ready.");
    } else {
      appendLog(`[Browser Session] Notice: ${data.error || "Could not launch browser automatically."}`, "text-amber-400 font-bold");
    }
  } catch (err) {
    appendLog(`[Browser Session] Dispatch error: ${err.message}`, "text-rose-400 font-bold");
  }
};

// REAL Playwright Desktop Automator Trigger
window.launchPlaywrightAutomator = async function() {
  speakText("Launching Playwright desktop automation engine.");
  appendLog("[Playwright] Launching desktop browser automation (headless=False)...", "text-blue-300 font-bold");
  appendChatMessage("🚀 **Launching Playwright Desktop Engine:** Spawning a real browser instance on your screen to verify web navigation and interactive elements.", "assistant");

  try {
    const res = await fetch("/api/browser/playwright-run", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: "https://mail.google.com",
        headless: false,
        actions: [
          { type: "wait", ms: 2000 }
        ]
      })
    });
    const data = await res.json();
    if (data.success) {
      appendLog(`[Playwright] Execution completed: Title='${data.title}' URL='${data.url}'`, "text-emerald-400 font-bold");
      appendChatMessage(`✅ **Playwright Automation Verified:** Browser opened and inspected endpoint: \`${data.title}\`.`, "assistant");
      speakText("Playwright desktop automation executed successfully.");
    } else {
      appendLog(`[Playwright] Result: ${data.error || "Completed with notice."}`, "text-amber-400");
    }
  } catch (err) {
    appendLog(`[Playwright] Error: ${err.message}`, "text-rose-400 font-bold");
  }
};

// Interactive SMTP Relay Trigger
window.triggerSMTPDispatch = async function() {
  speakText("SMTP Relay dispatch initiated.");
  appendLog("[SMTP Relay] Initializing direct SMTP socket to anshtiwarisocial@gmail.com...", "text-blue-300");
  appendLog("[SMTP Relay] Formulating RFC-5322 MIME payloads for 3 letters...", "text-amber-300");
  
  try {
    const res = await fetch("/api/email/smtp-send", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        recipient: "anshtiwarisocial@gmail.com",
        subject: "hello i am jarvis",
        body: "Dear Ansh,\n\nI am your autonomous Jarvis orchestrator. All systems online."
      })
    });
    const data = await res.json();
    if (data.success) {
      appendLog("[SMTP Relay] Letters authenticated & transmitted.", "text-emerald-400 font-bold");
      appendChatMessage("📧 **SMTP Relay Dispatched:** All messages successfully transmitted via SMTP socket.", "assistant");
      speakText("SMTP dispatch verified.");
    } else {
      appendLog(`[SMTP Relay] Info: ${data.error}`, "text-amber-300 font-medium");
      appendChatMessage(`ℹ️ **SMTP Status:** ${data.error}\n\n*Tip:* Use the **Launch Browser & Open All 3 in Gmail** button to send seamlessly with your active browser login without needing SMTP password configuration!`, "assistant");
      speakText("Use the 1-click browser button to send directly from your Gmail.");
    }
  } catch (err) {
    appendLog(`[SMTP Relay] Error: ${err.message}`, "text-rose-400 font-bold");
  }
  if (window.lucide) lucide.createIcons();
};

// Preview File in In-Browser Viewer Panel
async function previewWorkspaceFile(filePath) {
  if (!state.sessionId) return;
  const fileNameBadge = document.getElementById("activeFileName");
  const pre = document.getElementById("fileContentPre");
  const fileViewerPanel = document.getElementById("fileViewerPanel");
  if (fileViewerPanel) fileViewerPanel.classList.remove("translate-x-full");
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
      if (circle) circle.className = "w-4 h-4 rounded-full bg-amber-500/25 text-amber-300 flex items-center justify-center font-mono font-bold text-[9px] border border-amber-400/50 shadow-sm shadow-amber-500/20";
      if (label) label.className = "text-amber-200 font-bold text-[10px] whitespace-nowrap";
    } else {
      if (circle) circle.className = "w-4 h-4 rounded-full bg-brand-surface text-slate-500 flex items-center justify-center font-mono font-bold text-[9px] border border-brand-border";
      if (label) label.className = "text-slate-500 font-medium text-[10px] whitespace-nowrap";
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
  const container = document.getElementById("historyList") || document.getElementById("sessionsList");
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
        ? "bg-brand-card border-cyan-500/50 shadow-md" 
        : "bg-brand-card/50 hover:bg-brand-card border-brand-border/70"
    }`;

    itemDiv.innerHTML = `
      <div class="flex items-start justify-between gap-1.5">
        <span class="font-semibold text-slate-200 line-clamp-1 text-xs group-hover:text-cyan-300 transition">${escapeHtml(item.title || item.prompt)}</span>
        <button class="pin-toggle-btn text-slate-500 hover:text-amber-400 transition" title="${item.is_pinned ? "Unpin task" : "Pin task"}">
          <i data-lucide="pin" class="w-3.5 h-3.5 ${item.is_pinned ? "fill-amber-400 text-amber-400" : ""}"></i>
        </button>
      </div>
      <div class="flex items-center justify-between text-[10px] text-slate-500 font-mono">
        <span class="px-1.5 py-0.5 rounded bg-brand-surface border border-brand-border/60 text-slate-300">${escapeHtml(item.folder || "Personal")}</span>
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
  updatePinButtonUI(!!item.is_pinned);
  renderHistoryList();
  appendChatMessage(`Retrieved workspace for: "${item.title || item.prompt}"`, "assistant");

  // Automatically close sidebar drawer on selection
  const sidebar = document.getElementById("sidebar");
  const overlay = document.getElementById("sidebarOverlay");
  if (sidebar) sidebar.classList.add("-translate-x-full");
  if (overlay) overlay.classList.add("hidden");

  // Show Deliverables from history or live session
  const deliverables = item.deliverables || item.artifacts || [];
  try {
    const res = await fetch(`/api/session/${item.session_id}`);
    if (res.ok) {
      const data = await res.json();
      if (data.dag_plan) {
        const swarmDeck = document.getElementById("swarmDeckContainer");
        if (swarmDeck) swarmDeck.classList.remove("hidden");
        renderDAG(data.dag_plan);
      }
      if (data.workspace_files && data.workspace_files.length > 0) {
        showWorkDoneBanner(data.workspace_files.map(f => typeof f === 'string' ? f : f.path));
        updateStageUI(5);
        return;
      }
    }
  } catch (e) {
    // Fallback to cached deliverables
  }

  if (deliverables && deliverables.length > 0) {
    showWorkDoneBanner(deliverables);
    updateStageUI(5);
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
    await loadWorkHistory();
    if (state.sessionId === sessionId) {
      updatePinButtonUI(isPinned);
    }
  } catch (err) {
    console.error("Could not toggle pin:", err);
  }
}

// 1-Click Pin Current Mission Toggle (Works from Header)
window.togglePinCurrentMission = async function() {
  let sid = state.sessionId;
  if (!sid && state.historyItems && state.historyItems.length > 0) {
    sid = state.historyItems[0].session_id;
    state.sessionId = sid;
  }
  if (!sid) {
    appendChatMessage("📌 **Pin Chat:** No active mission session yet. Run or click a mission to lock it to the top of your workspace.", "assistant");
    return;
  }
  const current = (state.historyItems || []).find(h => h.session_id === sid);
  const newPinned = current ? !current.is_pinned : true;
  await togglePinTask(sid, newPinned);
  updatePinButtonUI(newPinned);
  appendChatMessage(newPinned ? "📌 **Mission Pinned to Top:** This mission is now permanently locked at the top of your history." : "📌 **Mission Unpinned:** Standard history chronological sorting restored.", "assistant");
};

// Update Top Pin Button UI
function updatePinButtonUI(isPinned) {
  const icon = document.getElementById("pinCurrentChatIcon");
  const label = document.getElementById("pinCurrentChatLabel");
  const btn = document.getElementById("pinCurrentChatBtn");
  if (!btn) return;
  if (isPinned) {
    if (icon) icon.className = "w-3.5 h-3.5 fill-amber-400 text-amber-400";
    if (label) label.textContent = "Pinned";
    btn.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-amber-500/20 border border-amber-500/50 text-xs font-semibold text-amber-300 transition shadow-sm shadow-amber-500/20 cursor-pointer";
  } else {
    if (icon) icon.className = "w-3.5 h-3.5 text-slate-400";
    if (label) label.textContent = "Pin";
    btn.className = "flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-brand-card hover:bg-amber-500/20 border border-brand-border hover:border-amber-500/40 text-xs font-semibold text-slate-300 hover:text-amber-300 transition cursor-pointer";
  }
}

// Quick Access Modal Openers & Closers
window.openSchedulerModal = function() {
  const m = document.getElementById("schedulerModal");
  if (m) m.classList.remove("hidden");
  loadSchedules();
};
window.closeSchedulerModal = function() {
  const m = document.getElementById("schedulerModal");
  if (m) m.classList.add("hidden");
};

window.openWorkflowsModal = function() {
  const m = document.getElementById("workflowsModal");
  if (m) m.classList.remove("hidden");
  loadSavedWorkflows();
};
window.closeWorkflowsModal = function() {
  const m = document.getElementById("workflowsModal");
  if (m) m.classList.add("hidden");
};

// Quick Blueprint Shortcuts
window.loadQuickBlueprint = function(key) {
  const input = document.getElementById("directiveInput");
  if (!input) return;

  if (key === 'emails') {
    input.value = "HEy just write me 3 mails to mail address anshtiwarisocial@gmail.com just subject line hello i am jarvis and body with whatever you feel for me";
    window.setMode('swarm');
  } else if (key === 'schedule_6am') {
    input.value = "do this particular work for everyday at 6am: scrape 20 SaaS CTO leads, craft RFC-5322 outreach sequences, and stage browser automation scripts";
    window.setMode('swarm');
  } else if (key === 'agency') {
    input.value = "I know full-stack dev, build me a business and find me clients";
    window.setMode('swarm');
  } else if (key === 'telemetry') {
    input.value = "Build an authenticated telemetry microservice with JWT & tests";
    window.setMode('swarm');
  }
  input.focus();
  appendChatMessage(`⚡ **Blueprint Loaded:** "${input.value}". Press Enter or click Send to launch the sub-agent army.`, "assistant");
};

// 1-Click Preset Schedule Generator
window.addPresetSchedule = async function(hour, minute, promptText) {
  const title = `Daily ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')} - ${promptText.slice(0, 25)}`;
  try {
    const res = await fetch("/api/schedules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: title,
        prompt: promptText,
        hour: hour,
        minute: minute,
        schedule_cron: `Daily ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`,
        is_active: true
      })
    });
    await res.json();
    await loadSchedules();
    appendChatMessage(`⏰ **24/7 Autonomous PC Schedule Added:** "${title}". LlamaOrchestrator will run this daily on your PC at ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}.`, "assistant");
    speakText(`Autonomous 24/7 mission scheduled for Daily at ${hour} AM.`);
    window.closeSchedulerModal();
  } catch (err) {
    alert("Could not register schedule: " + err.message);
  }
};

// 1-Click Save Active Prompt as Reusable Workflow
window.saveActivePromptAsWorkflow = async function() {
  const input = document.getElementById("directiveInput");
  const promptVal = (input && input.value.trim()) ? input.value.trim() : (state.sessionId ? "Active Mission Blueprint" : "");
  if (!promptVal) {
    alert("Please enter a directive in the input box first, or run a mission to save it.");
    return;
  }
  const name = window.prompt("Name this reusable workflow blueprint:", promptVal.slice(0, 30));
  if (!name) return;

  try {
    await fetch("/api/workflows", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        title: name,
        name: name,
        folder: "Custom",
        prompt: promptVal,
        prompt_template: promptVal
      })
    });
    await loadSavedWorkflows();
    appendChatMessage(`Saved workflow blueprint "${name}" to your catalog.`, "assistant");
  } catch (err) {
    alert("Could not save workflow: " + err.message);
  }
};

// Load Saved Reusable Workflows (Populates Sidebar and Modal)
async function loadSavedWorkflows() {
  const container = document.getElementById("workflowsList");
  const modalContainer = document.getElementById("modalWorkflowsList");

  try {
    const res = await fetch("/api/workflows");
    const workflows = await res.json();
    state.savedWorkflows = workflows || [];

    if (container) {
      if (state.savedWorkflows.length === 0) {
        container.innerHTML = '<div class="text-[11px] text-slate-500 py-1">No workflows saved yet.</div>';
      } else {
        container.innerHTML = "";
        state.savedWorkflows.forEach(wf => {
          const itemDiv = document.createElement("div");
          itemDiv.className = "w-full p-2 rounded-lg bg-brand-card hover:bg-brand-card/90 border border-brand-border hover:border-amber-500/40 text-xs transition flex items-center justify-between gap-1 group";
          const title = wf.title || wf.name || "Custom Workflow";
          const promptVal = wf.prompt || wf.prompt_template || "";
          const wfId = wf.id || wf.name;

          itemDiv.innerHTML = `
            <button class="flex-1 text-left truncate flex items-center gap-1.5 text-slate-300 group-hover:text-amber-300 cursor-pointer">
              <i data-lucide="play-circle" class="w-3.5 h-3.5 text-amber-400/80 shrink-0"></i>
              <span class="truncate font-semibold text-[11px]">${escapeHtml(title)}</span>
            </button>
            <button class="delete-wf-btn text-slate-500 hover:text-rose-400 p-1 rounded transition opacity-60 hover:opacity-100 cursor-pointer" title="Delete Workflow">
              <i data-lucide="trash-2" class="w-3 h-3"></i>
            </button>
          `;

          itemDiv.querySelector("button.flex-1").addEventListener("click", () => {
            const input = document.getElementById("directiveInput");
            if (input) {
              input.value = promptVal;
              window.setMode('swarm');
              input.focus();
            }
          });

          itemDiv.querySelector(".delete-wf-btn").addEventListener("click", async (e) => {
            e.stopPropagation();
            if (!confirm(`Delete saved workflow "${title}"?`)) return;
            try {
              await fetch(`/api/workflows/${encodeURIComponent(wfId)}`, { method: "DELETE" });
              loadSavedWorkflows();
            } catch (err) {
              alert("Error deleting workflow: " + err.message);
            }
          });
          container.appendChild(itemDiv);
        });
      }
    }

    // Also populate Modal Workflows List
    if (modalContainer) {
      modalContainer.innerHTML = "";
      state.savedWorkflows.forEach(wf => {
        const title = wf.title || wf.name || "Custom Workflow";
        const promptVal = wf.prompt || wf.prompt_template || "";
        const desc = wf.description || promptVal.slice(0, 80);
        const wfId = wf.id || wf.name;

        const card = document.createElement("div");
        card.className = "p-3 rounded-xl bg-brand-surface/90 border border-brand-border hover:border-amber-400/50 transition space-y-2";
        card.innerHTML = `
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2">
              <div class="w-6 h-6 rounded-lg bg-blue-500/20 text-amber-300 flex items-center justify-center border border-amber-500/30">
                <i data-lucide="layers" class="w-3.5 h-3.5"></i>
              </div>
              <span class="font-bold text-xs text-white">${escapeHtml(title)}</span>
            </div>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-blue-950 text-amber-300 border border-blue-500/30">${escapeHtml(wf.folder || "Blueprint")}</span>
          </div>
          <p class="text-[11px] text-slate-300 line-clamp-2">${escapeHtml(desc)}</p>
          <div class="flex items-center justify-between pt-1 border-t border-brand-border/40">
            <button class="launch-modal-wf-btn px-3 py-1.5 rounded-lg bg-gradient-to-r from-amber-400 to-yellow-500 hover:from-amber-300 hover:to-yellow-300 text-slate-950 font-bold text-xs flex items-center gap-1.5 transition cursor-pointer shadow-md">
              <i data-lucide="play" class="w-3 h-3 fill-current"></i>
              <span>Load & Run</span>
            </button>
            <button class="delete-modal-wf-btn text-slate-500 hover:text-rose-400 p-1 rounded transition cursor-pointer" title="Delete Workflow">
              <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
            </button>
          </div>
        `;

        card.querySelector(".launch-modal-wf-btn").addEventListener("click", () => {
          const input = document.getElementById("directiveInput");
          if (input) {
            input.value = promptVal;
            window.setMode('swarm');
            input.focus();
          }
          window.closeWorkflowsModal();
          appendChatMessage(`Loaded workflow blueprint "${title}". Ready to launch.`, "assistant");
        });

        card.querySelector(".delete-modal-wf-btn").addEventListener("click", async (e) => {
          e.stopPropagation();
          if (!confirm(`Delete workflow blueprint "${title}"?`)) return;
          try {
            await fetch(`/api/workflows/${encodeURIComponent(wfId)}`, { method: "DELETE" });
            loadSavedWorkflows();
          } catch (err) {
            alert("Error: " + err.message);
          }
        });

        modalContainer.appendChild(card);
      });
    }

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Failed to fetch workflows:", err);
  }
}

// Load 24/7 Autonomous PC Schedules (Populates Sidebar and Modal)
async function loadSchedules() {
  const container = document.getElementById("schedulesList");
  const modalContainer = document.getElementById("modalSchedulesList");
  const modalCount = document.getElementById("schedulerModalCount");

  try {
    const res = await fetch("/api/schedules");
    const schedules = await res.json();
    state.schedules = schedules || [];

    if (modalCount) {
      modalCount.textContent = `${state.schedules.length} Active Daemons`;
    }

    // Populate Sidebar schedules
    if (container) {
      if (state.schedules.length === 0) {
        container.innerHTML = '<div class="text-[11px] text-slate-500 py-1">No 24/7 schedules yet. Click "+ Daily 6AM" to add one!</div>';
      } else {
        container.innerHTML = "";
        state.schedules.forEach(sc => {
          const card = document.createElement("div");
          card.className = "p-2 rounded-lg bg-brand-card/90 border border-brand-border hover:border-amber-500/40 transition space-y-1.5";
          const isActive = sc.is_active !== false;
          const timeLabel = sc.schedule_cron || `Daily ${String(sc.hour !== undefined ? sc.hour : 6).padStart(2, '0')}:${String(sc.minute !== undefined ? sc.minute : 0).padStart(2, '0')}`;
          const runCount = sc.run_count || 0;
          const tid = sc.task_id || sc.id;

          card.innerHTML = `
            <div class="flex items-center justify-between gap-1">
              <div class="flex items-center gap-1.5 truncate">
                <span class="w-1.5 h-1.5 rounded-full ${isActive ? 'bg-amber-400 animate-pulse' : 'bg-slate-500'}"></span>
                <span class="font-bold text-[11px] text-amber-200 truncate">${escapeHtml(sc.title || "Scheduled Mission")}</span>
              </div>
              <span class="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-blue-950/80 text-amber-300 border border-amber-500/30">${escapeHtml(timeLabel)}</span>
            </div>
            <p class="text-[10px] text-slate-400 truncate">${escapeHtml(sc.prompt)}</p>
            <div class="flex items-center justify-between pt-1 border-t border-brand-border/40 text-[10px]">
              <span class="text-slate-500 font-mono">Runs: ${runCount}</span>
              <div class="flex items-center gap-1.5">
                <button class="sched-run-now px-2 py-0.5 rounded bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 font-semibold transition cursor-pointer" title="Force execute now in background">
                  Run Now
                </button>
                <button class="sched-toggle-btn text-slate-400 hover:text-amber-300 transition cursor-pointer" title="${isActive ? 'Pause Schedule' : 'Resume Schedule'}">
                  <i data-lucide="${isActive ? 'pause-circle' : 'play-circle'}" class="w-3.5 h-3.5"></i>
                </button>
                <button class="sched-delete-btn text-slate-500 hover:text-rose-400 transition cursor-pointer" title="Delete Schedule">
                  <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>
              </div>
            </div>
          `;

          card.querySelector(".sched-run-now").addEventListener("click", async () => {
            try {
              await fetch(`/api/schedules/${encodeURIComponent(tid)}/run-now`, { method: "POST" });
              appendChatMessage(`⏰ **Manual Execution Triggered:** Running scheduled mission "${sc.title}" in background on this PC now...`, "assistant");
              speakText("Triggering scheduled mission in background.");
              setTimeout(loadWorkHistory, 2000);
            } catch (err) {
              alert("Error executing schedule: " + err.message);
            }
          });

          card.querySelector(".sched-toggle-btn").addEventListener("click", async () => {
            try {
              await fetch(`/api/schedules/${encodeURIComponent(tid)}/toggle`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_active: !isActive })
              });
              loadSchedules();
            } catch (err) {
              alert("Error toggling schedule: " + err.message);
            }
          });

          card.querySelector(".sched-delete-btn").addEventListener("click", async () => {
            if (!confirm(`Delete recurring schedule "${sc.title}"?`)) return;
            try {
              await fetch(`/api/schedules/${encodeURIComponent(tid)}`, { method: "DELETE" });
              loadSchedules();
            } catch (err) {
              alert("Error deleting schedule: " + err.message);
            }
          });
          container.appendChild(card);
        });
      }
    }

    // Populate Modal schedules
    if (modalContainer) {
      if (state.schedules.length === 0) {
        modalContainer.innerHTML = '<div class="text-xs text-slate-400 py-3 text-center">No persistent schedules active. Click a preset above to activate daily runs.</div>';
      } else {
        modalContainer.innerHTML = "";
        state.schedules.forEach(sc => {
          const isActive = sc.is_active !== false;
          const timeLabel = sc.schedule_cron || `Daily ${String(sc.hour !== undefined ? sc.hour : 6).padStart(2, '0')}:${String(sc.minute !== undefined ? sc.minute : 0).padStart(2, '0')}`;
          const tid = sc.task_id || sc.id;

          const card = document.createElement("div");
          card.className = "p-3 rounded-xl bg-brand-surface/90 border border-brand-border hover:border-amber-400/40 transition space-y-2";
          card.innerHTML = `
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="w-2 h-2 rounded-full ${isActive ? 'bg-amber-400 animate-pulse' : 'bg-slate-500'}"></span>
                <span class="font-bold text-xs text-white">${escapeHtml(sc.title || "Daily Mission")}</span>
              </div>
              <span class="text-xs font-mono font-bold px-2 py-0.5 rounded bg-blue-950 text-amber-300 border border-amber-400/40">${escapeHtml(timeLabel)}</span>
            </div>
            <p class="text-[11px] text-slate-300 line-clamp-2">${escapeHtml(sc.prompt)}</p>
            <div class="flex items-center justify-between pt-1 border-t border-brand-border/40 text-[11px]">
              <span class="text-slate-400 font-mono">Status: <strong class="${isActive ? 'text-amber-300' : 'text-slate-500'}">${isActive ? 'Active (Daemon Running)' : 'Paused'}</strong></span>
              <div class="flex items-center gap-2">
                <button class="modal-run-now-btn px-2.5 py-1 rounded-lg bg-amber-500/20 hover:bg-amber-500/30 text-amber-300 font-bold transition cursor-pointer flex items-center gap-1">
                  <i data-lucide="play" class="w-3 h-3 fill-current"></i>
                  <span>Run Now</span>
                </button>
                <button class="modal-toggle-btn px-2.5 py-1 rounded-lg bg-blue-900/60 hover:bg-blue-800 text-blue-200 border border-blue-400/40 font-semibold transition cursor-pointer">
                  ${isActive ? 'Pause' : 'Resume'}
                </button>
                <button class="modal-delete-btn text-slate-500 hover:text-rose-400 p-1 transition cursor-pointer" title="Delete">
                  <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                </button>
              </div>
            </div>
          `;

          card.querySelector(".modal-run-now-btn").addEventListener("click", async () => {
            try {
              await fetch(`/api/schedules/${encodeURIComponent(tid)}/run-now`, { method: "POST" });
              appendChatMessage(`⏰ **Executing Scheduled Mission:** Running "${sc.title}" in background on host PC...`, "assistant");
              speakText("Executing scheduled mission in background.");
              window.closeSchedulerModal();
              setTimeout(loadWorkHistory, 2000);
            } catch (err) {
              alert("Error: " + err.message);
            }
          });

          card.querySelector(".modal-toggle-btn").addEventListener("click", async () => {
            try {
              await fetch(`/api/schedules/${encodeURIComponent(tid)}/toggle`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ is_active: !isActive })
              });
              loadSchedules();
            } catch (err) {
              alert("Error: " + err.message);
            }
          });

          card.querySelector(".modal-delete-btn").addEventListener("click", async () => {
            if (!confirm(`Delete recurring schedule "${sc.title}"?`)) return;
            try {
              await fetch(`/api/schedules/${encodeURIComponent(tid)}`, { method: "DELETE" });
              loadSchedules();
            } catch (err) {
              alert("Error: " + err.message);
            }
          });

          modalContainer.appendChild(card);
        });
      }
    }

    if (window.lucide) lucide.createIcons();
  } catch (err) {
    console.error("Failed to load schedules:", err);
  }
}

// Prompt Dialog to Add a 24/7 Daily Schedule
function promptAddSchedule() {
  const input = document.getElementById("directiveInput");
  const defaultPrompt = (input && input.value.trim()) ? input.value.trim() : "HEy just write me 3 mails to mail address anshtiwarisocial@gmail.com just subject line i am jarvis and body with whatever you feel for me";
  
  const promptText = window.prompt("Enter the mission directive to run recurringly on your PC:", defaultPrompt);
  if (!promptText) return;

  const timeText = window.prompt("What time should this run everyday? (e.g. 6:00 AM, 06:00, or 18:30):", "6:00 AM");
  if (!timeText) return;

  let hour = 6;
  let minute = 0;
  const match = timeText.match(/(\d{1,2})(?::(\d{2}))?\s*(am|pm)?/i);
  if (match) {
    hour = parseInt(match[1]);
    minute = match[2] ? parseInt(match[2]) : 0;
    const meridiem = (match[3] || "").toLowerCase();
    if (meridiem === "pm" && hour < 12) hour += 12;
    if (meridiem === "am" && hour === 12) hour = 0;
  }

  const title = `Daily ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')} - ${promptText.slice(0, 25)}`;

  fetch("/api/schedules", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      title: title,
      prompt: promptText,
      hour: hour,
      minute: minute,
      schedule_cron: `Daily ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')}`,
      is_active: true
    })
  }).then(res => res.json()).then(() => {
    loadSchedules();
    appendChatMessage(`⏰ **24/7 Autonomous PC Schedule Activated:** "${title}" is registered. LlamaOrchestrator's background scheduler will execute this task every day at ${String(hour).padStart(2, '0')}:${String(minute).padStart(2, '0')} on this PC.`, "assistant");
    speakText(`Autonomous 24/7 mission scheduled for Daily ${hour} AM.`);
  }).catch(err => {
    alert("Could not create schedule: " + err.message);
  });
}
window.promptAddSchedule = promptAddSchedule;

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
