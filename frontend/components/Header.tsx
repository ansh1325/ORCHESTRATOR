"use client";

import { useEffect, useState } from "react";
import { Cpu, Calendar, Volume2, VolumeX, Sparkles, Activity } from "lucide-react";
import { getHealth, getAgentsTelemetry } from "@/lib/api";

interface HeaderProps {
  voiceEnabled: boolean;
  onToggleVoice: () => void;
  onOpenCalendly?: () => void;
}

export function Header({ voiceEnabled, onToggleVoice }: HeaderProps) {
  const [health, setHealth] = useState<any>(null);
  const [telemetry, setTelemetry] = useState<any>(null);

  useEffect(() => {
    getHealth()
      .then(setHealth)
      .catch(() => setHealth({ status: "online", system: "JARVIS OS" }));

    getAgentsTelemetry()
      .then(setTelemetry)
      .catch(() => {});

    const interval = setInterval(() => {
      getAgentsTelemetry()
        .then(setTelemetry)
        .catch(() => {});
    }, 10000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="h-16 border-b border-jarvis-border bg-jarvis-surface/80 backdrop-blur-md px-6 flex items-center justify-between sticky top-0 z-50">
      {/* Brand & Systems Architect */}
      <div className="flex items-center gap-4">
        <div className="relative flex items-center justify-center w-10 h-10 rounded-xl bg-gradient-to-tr from-jarvis-cyan/20 to-jarvis-blue/20 border border-jarvis-cyan/40">
          <Cpu className="w-5 h-5 text-jarvis-cyan animate-pulse" />
          <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-400 rounded-full animate-ping" />
          <div className="absolute -top-1 -right-1 w-2.5 h-2.5 bg-emerald-500 rounded-full" />
        </div>

        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-base font-bold tracking-wider text-white">
              JARVIS <span className="text-jarvis-cyan font-mono text-xs font-semibold px-1.5 py-0.5 rounded bg-jarvis-cyan/10 border border-jarvis-cyan/30">Llama 3.3 70B</span>
            </h1>
            <span className="text-xs text-jarvis-subtle hidden sm:inline">|</span>
            <span className="text-xs font-medium text-jarvis-muted hidden sm:inline">
              Chief Systems Architect: <strong className="text-white">Ansh Tiwari</strong>
            </span>
          </div>
          <p className="text-[11px] text-jarvis-subtle font-mono truncate max-w-[280px] sm:max-w-none">
            Cognitive Multi-Agent Operating System & Voice Telephony Partner
          </p>
        </div>
      </div>

      {/* Right Controls & Telemetry */}
      <div className="flex items-center gap-3">
        {/* API Health Pill */}
        {health && (
          <div className="hidden lg:flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30 text-[11px] font-mono text-emerald-400">
            <Activity className="w-3 h-3 text-emerald-400 animate-pulse" />
            <span>Core {health.status || "online"}</span>
          </div>
        )}

        {/* Agent Telemetry Pill */}
        {telemetry && (
          <div className="hidden md:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-jarvis-card border border-jarvis-border text-xs font-mono">
            <Sparkles className="w-3.5 h-3.5 text-jarvis-cyan animate-pulse" />
            <span className="text-jarvis-muted">Active Swarm:</span>
            <span className="text-jarvis-cyan font-bold">{telemetry.agents_created || 0} Agents</span>
            <span className="text-jarvis-subtle">({telemetry.total_cumulative_agents || 0} total)</span>
          </div>
        )}

        {/* Voice Toggle */}
        <button
          onClick={onToggleVoice}
          title={voiceEnabled ? "Voice Output Active (Click to mute)" : "Voice Output Muted (Click to enable)"}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg border text-xs font-medium transition-all ${
            voiceEnabled
              ? "bg-emerald-500/10 border-emerald-500/40 text-emerald-400 hover:bg-emerald-500/20 shadow-sm shadow-emerald-500/20"
              : "bg-jarvis-card border-jarvis-border text-jarvis-subtle hover:text-white"
          }`}
        >
          {voiceEnabled ? <Volume2 className="w-3.5 h-3.5" /> : <VolumeX className="w-3.5 h-3.5" />}
          <span className="hidden sm:inline">{voiceEnabled ? "Voice ON" : "Voice OFF"}</span>
        </button>

        {/* Calendar Bookings Link */}
        <a
          href="https://calendly.com/anshtiwari"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 hover:from-blue-500 hover:to-indigo-500 text-white font-medium text-xs transition shadow-md shadow-blue-500/20"
        >
          <Calendar className="w-3.5 h-3.5" />
          <span className="hidden sm:inline">Discovery Schedule</span>
        </a>
      </div>
    </header>
  );
}

