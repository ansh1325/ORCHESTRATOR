"use client";

import React, { useState, useEffect } from "react";
import {
  Wrench,
  Sparkles,
  Play,
  CheckCircle2,
  AlertCircle,
  FileCode,
  RefreshCw,
  Terminal,
  Layers,
  Cpu,
  Clock,
} from "lucide-react";
import { listTools, synthesizeTool } from "@/lib/api";

interface ToolSynthesizerTabProps {
  onNotify: (type: "success" | "error" | "info", message: string) => void;
}

export function ToolSynthesizerTab({ onNotify }: ToolSynthesizerTabProps) {
  const [toolName, setToolName] = useState("ping_latency");
  const [toolGoal, setToolGoal] = useState("measure round trip ping in milliseconds");
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [toolsList, setToolsList] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [lastResult, setLastResult] = useState<any | null>(null);

  const fetchTools = async () => {
    setLoading(true);
    try {
      const res = await listTools();
      setToolsList(res.tools || []);
    } catch (err: any) {
      onNotify("error", err.message || "Failed to list dynamic tools");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTools();
  }, []);

  const handleSynthesize = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!toolName.trim() || !toolGoal.trim()) {
      onNotify("error", "Please provide both tool name and goal");
      return;
    }

    setIsSynthesizing(true);
    setLastResult(null);
    onNotify("info", `Synthesizing, compiling, and hot-reloading tool: ${toolName}...`);

    try {
      const res = await synthesizeTool(toolName.trim(), toolGoal.trim());
      setLastResult(res);
      onNotify("success", `✓ Tool '${toolName}' compiled, verified, and hot-loaded into active agent swarm!`);
      await fetchTools();
    } catch (err: any) {
      onNotify("error", err.message || "Tool synthesis failed");
    } finally {
      setIsSynthesizing(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-xl bg-cyber-cyan/10 border border-cyber-cyan/30 flex items-center justify-center text-cyber-cyan">
              <Wrench className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white tracking-wide">Runtime Tool Synthesizer</h2>
                <span className="text-[10px] bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/30 px-2 py-0.5 rounded-full font-mono">
                  Autonomous JIT Compiler
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                Generates Python tools on-the-fly, validates them in an AST verification sandbox, sanitizes unicode characters, and hot-reloads into active swarms.
              </p>
            </div>
          </div>

          {/* Quick presets */}
          <div className="flex flex-wrap gap-2">
            {[
              { name: "ping_latency", goal: "measure round trip ping in milliseconds" },
              { name: "json_diff_auditor", goal: "deep diff two JSON payloads and output modified keys" },
              { name: "jwt_decoder", goal: "decode JWT header and payload without external key" },
            ].map((preset, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setToolName(preset.name);
                  setToolGoal(preset.goal);
                }}
                className="text-xs bg-obsidian-bg hover:bg-obsidian-border border border-obsidian-border text-gray-300 px-2.5 py-1.5 rounded transition"
              >
                + {preset.name}
              </button>
            ))}
          </div>
        </div>

        {/* Input Form */}
        <form onSubmit={handleSynthesize} className="mt-5 space-y-3">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
            <div>
              <label className="text-xs text-gray-400 block mb-1">Tool Function Name</label>
              <input
                type="text"
                value={toolName}
                onChange={(e) => setToolName(e.target.value)}
                placeholder="e.g. ping_latency"
                className="w-full bg-obsidian-bg border border-obsidian-border rounded-lg px-3 py-2 text-xs font-mono text-white focus:border-cyber-cyan focus:outline-none"
              />
            </div>
            <div className="md:col-span-2">
              <label className="text-xs text-gray-400 block mb-1">Tool Specification / Natural Language Objective</label>
              <input
                type="text"
                value={toolGoal}
                onChange={(e) => setToolGoal(e.target.value)}
                placeholder="e.g. measure round trip ICMP or TCP ping to a host in milliseconds"
                className="w-full bg-obsidian-bg border border-obsidian-border rounded-lg px-3 py-2 text-xs text-white focus:border-cyber-cyan focus:outline-none"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isSynthesizing}
              className="bg-cyber-cyan hover:bg-cyber-cyan/90 disabled:opacity-50 text-black font-semibold px-5 py-2 rounded-lg text-xs flex items-center space-x-2 transition"
            >
              {isSynthesizing ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Synthesizing &amp; Hot-Reloading Tool...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Synthesize &amp; Compile Tool</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* Synthesis Output if present */}
      {lastResult && (
        <div className="bg-obsidian-card border border-emerald-500/40 rounded-xl p-4 animate-fadeIn">
          <div className="flex items-center justify-between pb-2 border-b border-obsidian-border/50 mb-3">
            <div className="flex items-center space-x-2 text-emerald-400">
              <CheckCircle2 className="w-5 h-5" />
              <span className="font-semibold text-sm">Tool Synthesized &amp; Loaded Successfully</span>
            </div>
            <span className="text-[10px] bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded font-mono">
              HOT-RELOADED
            </span>
          </div>
          <div className="text-xs text-gray-300 font-mono bg-obsidian-bg p-3 rounded border border-obsidian-border space-y-1">
            <div><strong>Tool Name:</strong> {lastResult.tool_name || toolName}</div>
            <div><strong>Target File:</strong> {lastResult.file || `dynamic_tools/${toolName}.py`}</div>
            <div><strong>Verification:</strong> Passed AST syntax &amp; unit execution sandbox</div>
          </div>
        </div>
      )}

      {/* Dynamic Tools Table */}
      <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5">
        <div className="flex items-center justify-between pb-3 border-b border-obsidian-border/50 mb-4">
          <div className="flex items-center space-x-2">
            <Cpu className="w-4 h-4 text-cyber-cyan" />
            <h3 className="font-semibold text-white text-sm">Active Hot-Reloaded Dynamic Tools</h3>
            <span className="text-xs text-gray-500 font-mono">({toolsList.length})</span>
          </div>
          <button
            onClick={fetchTools}
            className="text-xs text-gray-400 hover:text-white bg-obsidian-bg border border-obsidian-border px-2.5 py-1 rounded flex items-center space-x-1"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>

        {loading ? (
          <div className="py-16 text-center text-cyber-cyan flex flex-col items-center justify-center space-y-2">
            <RefreshCw className="w-6 h-6 animate-spin" />
            <span className="text-xs font-mono">Scanning dynamic tools repository...</span>
          </div>
        ) : toolsList.length === 0 ? (
          <div className="py-16 text-center text-gray-500">
            <Wrench className="w-10 h-10 mx-auto mb-2 opacity-30 text-gray-400" />
            <p className="text-xs">No dynamic tools synthesized yet.</p>
            <p className="text-[11px] text-gray-600 mt-1">
              Use the form above to synthesize a new tool like 'ping_latency'.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-obsidian-bg text-gray-400 border-b border-obsidian-border/60 uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3">Tool Name</th>
                  <th className="p-3">Objective &amp; Description</th>
                  <th className="p-3">Module Path</th>
                  <th className="p-3">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-obsidian-border/40 text-gray-300">
                {toolsList.map((tool, idx) => (
                  <tr key={idx} className="hover:bg-white/5 transition">
                    <td className="p-3 font-mono font-semibold text-cyber-cyan flex items-center space-x-2">
                      <FileCode className="w-3.5 h-3.5 text-gray-500" />
                      <span>{tool.name}</span>
                    </td>
                    <td className="p-3 text-gray-300">{tool.description || "Synthesized dynamic tool"}</td>
                    <td className="p-3 font-mono text-[11px] text-gray-400">{tool.file || `tools/${tool.name}.py`}</td>
                    <td className="p-3">
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        <CheckCircle2 className="w-2.5 h-2.5" />
                        <span>READY</span>
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

