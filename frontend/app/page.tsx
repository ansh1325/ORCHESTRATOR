"use client";

import { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { Sidebar, TabId } from "@/components/Sidebar";
import { ToastContainer, ToastMessage } from "@/components/Toast";
import { SwarmStudioTab } from "@/components/tabs/SwarmStudioTab";
import { VoiceTelephonyTab } from "@/components/tabs/VoiceTelephonyTab";
import { REAStudioTab } from "@/components/tabs/REAStudioTab";
import { HermesSkillsTab } from "@/components/tabs/HermesSkillsTab";
import { ToolSynthesizerTab } from "@/components/tabs/ToolSynthesizerTab";
import { WorkspacesTab } from "@/components/tabs/WorkspacesTab";
import { ChatTab } from "@/components/tabs/ChatTab";
import { getHealth, getAgentsTelemetry } from "@/lib/api";

export default function Dashboard() {
  const [activeTab, setActiveTab] = useState<TabId>("swarm");
  const [toasts, setToasts] = useState<ToastMessage[]>([]);
  const [voiceMuted, setVoiceMuted] = useState(false);
  const [systemHealth, setSystemHealth] = useState<any>(null);
  const [agentsTelemetry, setAgentsTelemetry] = useState<any>(null);

  const addToast = (type: "success" | "error" | "info", text: string) => {
    const newToast: ToastMessage = {
      id: `${Date.now()}-${Math.random()}`,
      type,
      message: text,
    };
    setToasts((prev) => [...prev, newToast]);
  };

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const fetchTelemetry = async () => {
    try {
      const [h, a] = await Promise.all([
        getHealth().catch(() => null),
        getAgentsTelemetry().catch(() => null),
      ]);
      if (h) setSystemHealth(h);
      if (a) setAgentsTelemetry(a);
    } catch (err) {
      // Background telemetry sync failure is non-blocking
    }
  };

  useEffect(() => {
    fetchTelemetry();
    const interval = setInterval(fetchTelemetry, 15000);
    return () => clearInterval(interval);
  }, []);

  const totalAgentsCount = agentsTelemetry?.total_cumulative_agents || agentsTelemetry?.agents_created || 4;

  return (
    <div className="min-h-screen bg-obsidian-bg text-gray-100 flex flex-col font-sans selection:bg-cyber-cyan selection:text-black">
      {/* Toast Notification Layer */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />

      {/* Global Top Command Header */}
      <Header
        voiceEnabled={!voiceMuted}
        onToggleVoice={() => {
          setVoiceMuted(!voiceMuted);
          addToast("info", voiceMuted ? "Voice speech enabled" : "Voice speech muted");
        }}
      />

      {/* Main Dual-Pane Command Center */}
      <div className="flex-1 flex flex-col md:flex-row overflow-hidden max-w-[1720px] w-full mx-auto px-4 md:px-6 py-6 gap-6">
        {/* Navigation Sidebar */}
        <div className="w-full md:w-64 flex-shrink-0">
          <Sidebar
            activeTab={activeTab}
            onSelectTab={(tab) => {
              setActiveTab(tab);
            }}
            agentCount={totalAgentsCount}
          />
        </div>

        {/* Operating Tab Canvas */}
        <main className="flex-1 min-w-0 overflow-y-auto">
          {activeTab === "swarm" && <SwarmStudioTab onNotify={addToast} />}
          {activeTab === "voice" && <VoiceTelephonyTab onNotify={addToast} />}
          {activeTab === "rea" && <REAStudioTab onNotify={addToast} />}
          {activeTab === "hermes" && <HermesSkillsTab onNotify={addToast} />}
          {activeTab === "tools" && <ToolSynthesizerTab onNotify={addToast} />}
          {activeTab === "workspaces" && <WorkspacesTab onNotify={addToast} />}
          {activeTab === "chat" && <ChatTab onNotify={addToast} />}
        </main>
      </div>

      {/* Footer Status Bar */}
      <footer className="border-t border-obsidian-border/40 bg-obsidian-card/40 px-6 py-2.5 text-[11px] text-gray-500 flex flex-col sm:flex-row items-center justify-between gap-2">
        <div className="flex items-center space-x-3">
          <span className="flex items-center space-x-1">
            <span className={`w-2 h-2 rounded-full ${systemHealth?.status === "online" ? "bg-emerald-400" : "bg-cyan-400"}`}></span>
            <span className="text-gray-300 font-mono">FastAPI Core: {systemHealth?.status ? "Online" : "http://localhost:8000"}</span>
          </span>
          <span>|</span>
          <span className="text-gray-400">Chief Systems Architect: Ansh Tiwari</span>
        </div>
        <div className="flex items-center space-x-3 font-mono text-[10px] text-gray-400">
          <span>Hermes 44+ Skills</span>
          <span>•</span>
          <span>REA Reverse Engineering</span>
          <span>•</span>
          <span>Voss Tactical Empathy</span>
          <span>•</span>
          <span>Agentskills.io Certified</span>
        </div>
      </footer>
    </div>
  );
}
