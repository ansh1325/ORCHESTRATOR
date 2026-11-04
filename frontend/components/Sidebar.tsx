"use client";

import {
  Sparkles,
  PhoneCall,
  Binary,
  Compass,
  Wrench,
  FolderGit2,
  MessageSquareText
} from "lucide-react";

export type TabId = "swarm" | "voice" | "rea" | "hermes" | "tools" | "workspaces" | "chat";

interface SidebarProps {
  activeTab: TabId;
  onSelectTab: (tab: TabId) => void;
  agentCount?: number;
}

export function Sidebar({ activeTab, onSelectTab, agentCount }: SidebarProps) {
  const tabs = [
    {
      id: "swarm" as TabId,
      label: "Mission Swarm",
      sublabel: "6-Stage DAG Execution",
      icon: Sparkles,
      badge: agentCount ? `${agentCount} Agents` : undefined,
      color: "text-jarvis-cyan",
      badgeColor: "bg-jarvis-cyan/15 text-jarvis-cyan border-jarvis-cyan/30"
    },
    {
      id: "voice" as TabId,
      label: "Voice Telephony",
      sublabel: "Roleplay & Calling Engine",
      icon: PhoneCall,
      color: "text-emerald-400"
    },
    {
      id: "rea" as TabId,
      label: "REA Decompiler",
      sublabel: "Reverse Engineer Anything",
      icon: Binary,
      color: "text-purple-400"
    },
    {
      id: "hermes" as TabId,
      label: "Hermes Skills",
      sublabel: "44+ Skills & Tiered Memory",
      icon: Compass,
      color: "text-amber-400"
    },
    {
      id: "tools" as TabId,
      label: "Tool Synthesizer",
      sublabel: "Runtime MCP Tool Injection",
      icon: Wrench,
      color: "text-blue-400"
    },
    {
      id: "workspaces" as TabId,
      label: "Workspaces & Leads",
      sublabel: "Deliverables & Fleet Status",
      icon: FolderGit2,
      color: "text-indigo-400"
    },
    {
      id: "chat" as TabId,
      label: "Central Brain CoT",
      sublabel: "Multi-turn Dialogue",
      icon: MessageSquareText,
      color: "text-rose-400"
    }
  ];

  return (
    <aside className="w-64 border-r border-jarvis-border bg-jarvis-surface flex flex-col justify-between select-none">
      <div className="p-4 space-y-1.5">
        <div className="px-3 py-2 text-[11px] font-semibold tracking-wider uppercase text-jarvis-subtle">
          Operating Modules
        </div>

        {tabs.map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;

          return (
            <button
              key={tab.id}
              onClick={() => onSelectTab(tab.id)}
              className={`w-full text-left px-3.5 py-3 rounded-xl flex items-center justify-between transition-all group ${
                isActive
                  ? "bg-jarvis-card border border-jarvis-cyan/40 shadow-sm shadow-jarvis-cyan/10"
                  : "hover:bg-jarvis-card/60 border border-transparent hover:border-jarvis-border"
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`p-2 rounded-lg transition-colors ${
                    isActive ? "bg-white/10 text-white" : "bg-jarvis-bg text-jarvis-muted group-hover:text-white"
                  }`}
                >
                  <Icon className={`w-4 h-4 ${isActive ? tab.color : ""}`} />
                </div>
                <div>
                  <div className={`text-xs font-semibold ${isActive ? "text-white" : "text-jarvis-text group-hover:text-white"}`}>
                    {tab.label}
                  </div>
                  <div className="text-[10px] text-jarvis-subtle truncate max-w-[125px]">
                    {tab.sublabel}
                  </div>
                </div>
              </div>

              {tab.badge && (
                <span className={`text-[10px] font-mono font-bold px-2 py-0.5 rounded-full border ${tab.badgeColor}`}>
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* System Status footer */}
      <div className="p-4 border-t border-jarvis-border bg-jarvis-card/40 m-3 rounded-xl border">
        <div className="flex items-center justify-between text-xs font-medium mb-1.5">
          <span className="text-jarvis-muted flex items-center gap-1.5">
            <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
            Central Brain
          </span>
          <span className="text-emerald-400 font-mono text-[11px]">ACTIVE</span>
        </div>
        <p className="text-[11px] text-jarvis-subtle leading-tight">
          Llama 3.3 70B cognitive multi-agent orchestration online.
        </p>
      </div>
    </aside>
  );
}

