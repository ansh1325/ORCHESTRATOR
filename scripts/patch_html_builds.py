path = 'D:/LlamaOrchestrator/static/index.html'
with open(path, 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Add nav button
nav_target = """    <!-- Quick Access Navigation -->
    <div class="px-3 pt-3 space-y-1">
      <button type="button" onclick="openSchedulerModal()\""""

nav_replacement = """    <!-- Quick Access Navigation -->
    <div class="px-3 pt-3 space-y-1">
      <button type="button" onclick="openBuildsModal()" class="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs text-gemini-muted hover:text-white hover:bg-gemini-cardHover transition cursor-pointer">
        <i data-lucide="cpu" class="w-4 h-4 text-emerald-400"></i>
        <span>Builds & Workspaces</span>
      </button>
      <button type="button" onclick="openSchedulerModal()\""""

# 2. Add modal before closing script tag
modal_code = """  <!-- ============================================================ -->
  <!-- BUILDS & WORKSPACES OPERATING HUB MODAL                      -->
  <!-- ============================================================ -->
  <div id="buildsModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/75 backdrop-blur-sm p-4 hidden">
    <div class="bg-gemini-card border border-gemini-border rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in fade-in duration-200">
      <div class="px-6 py-4 border-b border-gemini-border/80 flex items-center justify-between">
        <div class="flex items-center gap-3">
          <div class="w-9 h-9 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
            <i data-lucide="cpu" class="w-5 h-5 text-emerald-400"></i>
          </div>
          <div>
            <h3 class="font-bold text-base text-white">JARVIS Builds & Workspaces Hub</h3>
            <p class="text-xs text-gemini-subtle font-mono">Inspect, execute, test, and manage all autonomous builds on your machine</p>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <span id="buildsCountBadge" class="text-[11px] px-2.5 py-1 rounded-full bg-gemini-sidebar border border-gemini-border font-mono text-emerald-400">--</span>
          <button type="button" onclick="cleanGhostWorkspacesUI()" class="px-3 py-1.5 rounded-xl bg-gemini-sidebar hover:bg-gemini-cardHover border border-gemini-border text-xs text-gemini-text font-semibold transition cursor-pointer flex items-center gap-1.5" title="Safely prune empty ghost folders">
            <i data-lucide="sparkles" class="w-3.5 h-3.5 text-amber-400"></i> Clean Ghosts
          </button>
          <button type="button" onclick="openBuildFolderUI('workspaces')" class="px-3 py-1.5 rounded-xl bg-gemini-sidebar hover:bg-gemini-cardHover border border-gemini-border text-xs text-gemini-text font-semibold transition cursor-pointer flex items-center gap-1.5" title="Open root workspaces folder">
            <i data-lucide="folder" class="w-3.5 h-3.5 text-gemini-blue"></i> Open Workspaces
          </button>
          <button type="button" onclick="closeBuildsModal()" class="p-2 rounded-lg text-gemini-muted hover:text-white hover:bg-gemini-cardHover transition cursor-pointer">
            <i data-lucide="x" class="w-5 h-5"></i>
          </button>
        </div>
      </div>

      <!-- Live Execution Console Box -->
      <div id="buildRunOutputConsole" class="px-6 pt-4 pb-2 hidden">
        <div class="p-3 bg-black/90 border border-emerald-500/30 rounded-xl space-y-2 font-mono text-xs">
          <div class="flex items-center justify-between text-emerald-400 border-b border-white/10 pb-1">
            <span class="flex items-center gap-2"><i data-lucide="terminal" class="w-4 h-4"></i> Live Build Console Output</span>
            <button onclick="document.getElementById('buildRunOutputConsole').classList.add('hidden')" class="text-gemini-subtle hover:text-white text-[11px] cursor-pointer">Close Console</button>
          </div>
          <pre id="buildRunOutputContent" class="text-emerald-300 whitespace-pre-wrap max-h-48 overflow-y-auto custom-scrollbar select-text leading-relaxed font-mono"></pre>
        </div>
      </div>

      <!-- Scrollable Container of Builds -->
      <div class="p-6 overflow-y-auto custom-scrollbar flex-1 space-y-3" id="buildsContainer">
        <!-- Rendered by JS -->
      </div>
    </div>
  </div>

"""

modal_target = """  <div id="sidebarOverlay" class="fixed inset-0 bg-black/60 z-20 hidden md:hidden"></div>"""

text_norm = text.replace('\r\n', '\n')
nav_target_norm = nav_target.replace('\r\n', '\n')
nav_rep_norm = nav_replacement.replace('\r\n', '\n')
modal_target_norm = modal_target.replace('\r\n', '\n')
modal_rep_norm = (modal_code + modal_target).replace('\r\n', '\n')

if nav_target_norm in text_norm and modal_target_norm in text_norm:
    new_text = text_norm.replace(nav_target_norm, nav_rep_norm, 1)
    new_text = new_text.replace(modal_target_norm, modal_rep_norm, 1)
    if '\r\n' in text:
        new_text = new_text.replace('\n', '\r\n')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("index.html patched with builds UI successfully!")
else:
    print("nav_target or modal_target not found in index.html!")

