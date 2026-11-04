"use client";

import { useState, useEffect, useRef } from "react";
import {
  Sparkles,
  Play,
  CheckCircle2,
  FolderDown,
  Terminal,
} from "lucide-react";
import { analyzeMission, launchMission, getSession, getBaseUrl } from "@/lib/api";

interface SwarmStudioTabProps {
  onNotify: (type: "success" | "error" | "info", msg: string) => void;
  onRefreshTelemetry?: () => void;
}

export function SwarmStudioTab({ onNotify, onRefreshTelemetry }: SwarmStudioTabProps) {
  const [vision, setVision] = useState("");
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [analysis, setAnalysis] = useState<any>(null);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [sessionData, setSessionData] = useState<any>(null);
  const [events, setEvents] = useState<any[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const logsEndRef = useRef<HTMLDivElement>(null);

  const samplePrompts = [
    "Build an autonomous drone delivery logistics platform with FastAPI & tests",
    "Scribe and verify 1500 tech lead emails with Proof-of-Need columns",
    "6-DOF robotic humanoid balance and inverse kinematics engine",
    "Quant statistical arbitrage backtest pipeline with Risk Gatekeeper",
  ];

  // Auto-scroll logs
  useEffect(() => {
    logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [events]);

  // Clean up SSE
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  const handleAnalyze = async () => {
    if (!vision.trim()) return;
    setIsAnalyzing(true);
    setAnalysis(null);
    const sid = activeSessionId || `mission_${Date.now()}`;
    setActiveSessionId(sid);
    try {
      const res = await analyzeMission(vision, sid);
      setAnalysis(res);
      onNotify("info", `Mission analyzed. Track: ${res.track_type.toUpperCase()}`);
    } catch (e: any) {
      onNotify("error", `Analysis error: ${e.message}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleLaunch = async () => {
    if (!vision.trim()) return;
    setIsRunning(true);
    setEvents([]);
    const sid = activeSessionId || `mission_${Date.now()}`;
    setActiveSessionId(sid);

    try {
      await launchMission(sid, answers, vision);
      onNotify("success", `Multi-agent swarm launched for session: ${sid}`);

      // Connect SSE
      const base = getBaseUrl();
      const es = new EventSource(`${base}/api/events/${sid}`);
      eventSourceRef.current = es;

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          setEvents((prev) => [...prev, data]);

          if (data.event_type === "done") {
            setIsRunning(false);
            onNotify("success", "Mission accomplished! All deliverables verified & certified.");
            es.close();
            onRefreshTelemetry?.();
            // Fetch session deliverables
            getSession(sid).then(setSessionData).catch(() => {});
          } else if (data.event_type === "error") {
            setIsRunning(false);
            onNotify("error", `Mission error: ${data.message}`);
            es.close();
          }
        } catch {}
      };

      es.onerror = () => {
        // May close cleanly on completion
      };
    } catch (e: any) {
      setIsRunning(false);
      onNotify("error", `Launch error: ${e.message}`);
    }
  };

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Directive Input Card */}
      <div className="glass-card p-6 rounded-2xl border border-jarvis-border space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-jarvis-cyan" />
            <h2 className="text-base font-bold text-white">Central Brain Mission Directive</h2>
          </div>
          <span className="text-xs text-jarvis-subtle font-mono">Unbounded Swarm Scale: 6-10+ Agents</span>
        </div>

        <textarea
          value={vision}
          onChange={(e) => setVision(e.target.value)}
          placeholder="State your software system, data pipeline, or autonomous outreach mission in plain English..."
          rows={3}
          className="w-full p-4 rounded-xl bg-jarvis-bg border border-jarvis-border focus:border-jarvis-cyan focus:outline-none text-sm text-white placeholder-jarvis-subtle transition-all resize-none font-sans"
        />

        {/* Quick Suggestion Chips */}
        <div className="flex flex-wrap items-center gap-2 pt-1">
          <span className="text-[11px] font-medium text-jarvis-subtle">Quick Swarms:</span>
          {samplePrompts.map((p, idx) => (
            <button
              key={idx}
              onClick={() => setVision(p)}
              className="text-[11px] px-2.5 py-1 rounded-lg bg-jarvis-card hover:bg-jarvis-cardHover border border-jarvis-border hover:border-jarvis-cyan/30 text-jarvis-muted hover:text-white transition-all truncate max-w-[260px]"
            >
              {p}
            </button>
          ))}
        </div>

        <div className="flex items-center justify-between pt-2">
          <button
            onClick={handleAnalyze}
            disabled={isAnalyzing || !vision.trim()}
            className="px-4 py-2 rounded-xl bg-jarvis-card hover:bg-jarvis-cardHover border border-jarvis-border text-xs font-semibold text-white transition disabled:opacity-50 flex items-center gap-2"
          >
            {isAnalyzing ? (
              <>
                <span className="w-3.5 h-3.5 border-2 border-jarvis-cyan border-t-transparent rounded-full animate-spin" />
                Analyzing Intent...
              </>
            ) : (
              "1. Cognitive Intent Analysis"
            )}
          </button>

          <button
            onClick={handleLaunch}
            disabled={isRunning || !vision.trim()}
            className="px-6 py-2.5 rounded-xl bg-gradient-to-r from-jarvis-cyan to-jarvis-blue hover:from-cyan-400 hover:to-blue-400 text-slate-950 text-xs font-bold transition shadow-lg shadow-cyan-500/20 disabled:opacity-50 flex items-center gap-2"
          >
            {isRunning ? (
              <>
                <span className="w-4 h-4 border-2 border-slate-950 border-t-transparent rounded-full animate-spin" />
                Executing Swarm...
              </>
            ) : (
              <>
                <Play className="w-4 h-4 fill-current" />
                Deploy Autonomous Swarm
              </>
            )}
          </button>
        </div>
      </div>

      {/* Analysis Preview & Clarifications */}
      {analysis && (
        <div className="glass-card p-6 rounded-2xl border border-jarvis-border/80 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-white flex items-center gap-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-400" />
              Cognitive Decomposition Plan ({analysis.track_type})
            </h3>
            <span className="text-xs px-2.5 py-1 rounded-full bg-emerald-500/10 text-emerald-400 font-mono border border-emerald-500/30">
              Complexity: {analysis.complexity_score}/10
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
            <div className="p-3.5 rounded-xl bg-jarvis-bg/80 border border-jarvis-border space-y-1.5">
              <div className="font-semibold text-jarvis-cyan">100% Autonomous Scope:</div>
              <ul className="list-disc list-inside text-jarvis-muted space-y-1">
                {analysis.autonomous_capabilities?.map((c: string, idx: number) => (
                  <li key={idx} className="truncate">{c}</li>
                ))}
              </ul>
            </div>

            <div className="p-3.5 rounded-xl bg-jarvis-bg/80 border border-jarvis-border space-y-1.5">
              <div className="font-semibold text-amber-400">Human Authorization Boundaries:</div>
              <ul className="list-disc list-inside text-jarvis-muted space-y-1">
                {analysis.human_in_the_loop_boundaries?.map((b: string, idx: number) => (
                  <li key={idx} className="truncate">{b}</li>
                ))}
              </ul>
            </div>
          </div>

          {/* Clarification questions if any */}
          {analysis.clarification_questions?.length > 0 && (
            <div className="p-4 rounded-xl bg-blue-950/20 border border-blue-500/20 space-y-3">
              <div className="text-xs font-semibold text-blue-400">Clarification Parameters:</div>
              {analysis.clarification_questions.map((q: any) => (
                <div key={q.id} className="space-y-1.5">
                  <label className="text-xs text-white">{q.question}</label>
                  <input
                    type="text"
                    placeholder="Your preference or press deploy to let Jarvis decide..."
                    value={answers[q.id] || ""}
                    onChange={(e) => setAnswers({ ...answers, [q.id]: e.target.value })}
                    className="w-full p-2.5 rounded-lg bg-jarvis-bg border border-jarvis-border text-xs text-white focus:outline-none focus:border-blue-400"
                  />
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Live SSE Event Stream & Telemetry */}
      {events.length > 0 && (
        <div className="glass-card p-6 rounded-2xl border border-jarvis-border space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-jarvis-cyan" />
              <h3 className="text-sm font-bold text-white">Live Multi-Agent Swarm Telemetry Stream</h3>
              {isRunning && <span className="w-2 h-2 rounded-full bg-jarvis-cyan animate-ping" />}
            </div>
            <span className="text-xs font-mono text-jarvis-subtle">Session: {activeSessionId}</span>
          </div>

          {/* Terminal Log Box */}
          <div className="h-80 overflow-y-auto p-4 rounded-xl bg-black/80 font-mono text-xs border border-jarvis-border/80 space-y-2">
            {events.map((evt, idx) => {
              const typeColor =
                evt.event_type === "stage_change"
                  ? "text-purple-400 font-bold"
                  : evt.event_type === "task_start"
                  ? "text-amber-400"
                  : evt.event_type === "task_complete"
                  ? "text-emerald-400 font-semibold"
                  : evt.event_type === "done"
                  ? "text-jarvis-cyan font-bold"
                  : "text-jarvis-muted";

              return (
                <div key={idx} className="leading-relaxed flex items-start gap-2">
                  <span className="text-jarvis-subtle select-none">[{evt.stage || 0}/6]</span>
                  <span className={typeColor}>
                    {evt.event_type === "task_complete" && "✓ "}
                    {evt.event_type === "done" && "🎉 "}
                    {evt.message || JSON.stringify(evt.data)}
                  </span>
                </div>
              );
            })}
            <div ref={logsEndRef} />
          </div>

          {/* Deliverables Explorer after completion */}
          {sessionData?.files && (
            <div className="pt-4 border-t border-jarvis-border space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-white flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-400" />
                  Generated Workspace Deliverables ({sessionData.files.length} files)
                </span>
                <a
                  href={`${getBaseUrl()}/api/workspace/${activeSessionId}/download`}
                  className="px-3 py-1.5 rounded-lg bg-jarvis-card hover:bg-jarvis-cardHover border border-jarvis-border text-xs font-medium text-white flex items-center gap-1.5 transition"
                >
                  <FolderDown className="w-3.5 h-3.5" />
                  Download ZIP
                </a>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {sessionData.files.map((f: any, idx: number) => (
                  <div
                    key={idx}
                    className="p-3 rounded-lg bg-jarvis-bg border border-jarvis-border flex items-center justify-between text-xs font-mono"
                  >
                    <span className="text-jarvis-cyan truncate">{f.path}</span>
                    <span className="text-jarvis-subtle">{f.size} B</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

