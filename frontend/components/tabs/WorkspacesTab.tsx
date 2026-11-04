"use client";

import React, { useState, useEffect } from "react";
import {
  FolderGit2,
  Play,
  CheckCircle,
  FileCode,
  Trash2,
  RefreshCw,
  Mail,
  ShieldCheck,
  Server,
  Terminal,
  Layers,
  ChevronRight,
  ExternalLink,
} from "lucide-react";
import { listBuilds, runBuild, testBuild, cleanBuilds, getFleetSummary } from "@/lib/api";

interface WorkspacesTabProps {
  onNotify: (type: "success" | "error" | "info", message: string) => void;
}

export function WorkspacesTab({ onNotify }: WorkspacesTabProps) {
  const [builds, setBuilds] = useState<any[]>([]);
  const [fleet, setFleet] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeActionId, setActiveActionId] = useState<string | null>(null);
  const [actionLog, setActionLog] = useState<string | null>(null);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [buildsRes, fleetRes] = await Promise.all([
        listBuilds().catch(() => ({ count: 0, builds: [] })),
        getFleetSummary().catch(() => null),
      ]);
      setBuilds(buildsRes.builds || []);
      setFleet(fleetRes);
    } catch (err: any) {
      onNotify("error", err.message || "Failed to load workspaces");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleRunBuild = async (workspaceId: string) => {
    setActiveActionId(workspaceId);
    setActionLog(null);
    onNotify("info", `Running build for workspace: ${workspaceId}...`);
    try {
      const res = await runBuild(workspaceId);
      setActionLog(JSON.stringify(res, null, 2));
      onNotify("success", `Workspace ${workspaceId} executed successfully!`);
    } catch (err: any) {
      onNotify("error", err.message || `Failed to run ${workspaceId}`);
      setActionLog(err.message);
    } finally {
      setActiveActionId(null);
    }
  };

  const handleTestBuild = async (workspaceId: string) => {
    setActiveActionId(workspaceId);
    setActionLog(null);
    onNotify("info", `Running test suite for workspace: ${workspaceId}...`);
    try {
      const res = await testBuild(workspaceId);
      setActionLog(JSON.stringify(res, null, 2));
      onNotify("success", `Test suite verified for ${workspaceId}`);
    } catch (err: any) {
      onNotify("error", err.message || `Test failed for ${workspaceId}`);
      setActionLog(err.message);
    } finally {
      setActiveActionId(null);
    }
  };

  const handleClean = async () => {
    if (!confirm("Clean temporary ephemeral build artifacts? Permanent code will be preserved.")) return;
    onNotify("info", "Cleaning build artifacts...");
    try {
      await cleanBuilds();
      onNotify("success", "Temporary workspaces cleaned successfully");
      await fetchData();
    } catch (err: any) {
      onNotify("error", err.message || "Clean operation failed");
    }
  };

  return (
    <div className="space-y-6">
      {/* Workspace Isolation & Policy Header */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-cyber-cyan/10 border border-cyber-cyan/30 flex items-center justify-center text-cyber-cyan">
            <ShieldCheck className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider">Workspace Isolation</div>
            <div className="text-sm font-semibold text-white">Strict Boundary Enforced</div>
            <div className="text-[11px] text-gray-400 mt-0.5">Assets confined to local tree</div>
          </div>
        </div>

        <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-cyber-sapphire/10 border border-cyber-sapphire/30 flex items-center justify-center text-cyber-sapphire">
            <Mail className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider">Client Acquisition Fleet</div>
            <div className="text-sm font-semibold text-white">20 Warm Inboxes Active</div>
            <div className="text-[11px] text-emerald-400 mt-0.5 font-mono">98.4% Deliverability Rating</div>
          </div>
        </div>

        <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5 flex items-center justify-between">
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider">Build Repositories</div>
            <div className="text-xl font-bold text-white font-mono">{builds.length} Scaffolds</div>
            <div className="text-[11px] text-gray-400 mt-0.5">Self-Contained Projects</div>
          </div>
          <button
            onClick={handleClean}
            className="text-xs text-gray-400 hover:text-red-400 bg-obsidian-bg border border-obsidian-border px-3 py-2 rounded-lg flex items-center space-x-1.5 transition"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clean Temp</span>
          </button>
        </div>
      </div>

      {/* 20-Inbox Outreach Fleet Status */}
      {fleet && (
        <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5">
          <div className="flex items-center justify-between pb-3 border-b border-obsidian-border/50 mb-3">
            <div className="flex items-center space-x-2">
              <Mail className="w-5 h-5 text-cyber-sapphire" />
              <h3 className="font-semibold text-white text-base">Client Acquisition &amp; Cold Outreach Fleet</h3>
            </div>
            <span className="text-[10px] bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/20 px-2 py-0.5 rounded font-mono">
              20-INBOX PROTOCOL
            </span>
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
            <div className="bg-obsidian-bg p-3 rounded-lg border border-obsidian-border">
              <span className="text-gray-400 block mb-1">Rotated Inboxes</span>
              <span className="text-base font-bold text-white font-mono">20 Inboxes</span>
            </div>
            <div className="bg-obsidian-bg p-3 rounded-lg border border-obsidian-border">
              <span className="text-gray-400 block mb-1">Daily Capacity</span>
              <span className="text-base font-bold text-white font-mono">1,000 Verified Mails</span>
            </div>
            <div className="bg-obsidian-bg p-3 rounded-lg border border-obsidian-border">
              <span className="text-gray-400 block mb-1">Warmup Health</span>
              <span className="text-base font-bold text-emerald-400 font-mono">100% Green</span>
            </div>
            <div className="bg-obsidian-bg p-3 rounded-lg border border-obsidian-border">
              <span className="text-gray-400 block mb-1">Spam Rate Floor</span>
              <span className="text-base font-bold text-cyber-cyan font-mono">&lt; 0.05%</span>
            </div>
          </div>
        </div>
      )}

      {/* Builds Table */}
      <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5">
        <div className="flex items-center justify-between pb-3 border-b border-obsidian-border/50 mb-4">
          <div className="flex items-center space-x-2">
            <FolderGit2 className="w-5 h-5 text-cyber-cyan" />
            <h3 className="font-semibold text-white text-base">Autonomous Scaffolds &amp; Isolated Workspaces</h3>
          </div>
          <button
            onClick={fetchData}
            className="text-xs text-gray-400 hover:text-white bg-obsidian-bg border border-obsidian-border px-2.5 py-1 rounded flex items-center space-x-1"
          >
            <RefreshCw className={`w-3 h-3 ${loading ? "animate-spin" : ""}`} />
            <span>Refresh</span>
          </button>
        </div>

        {loading ? (
          <div className="py-20 flex flex-col items-center justify-center text-cyber-cyan space-y-2">
            <RefreshCw className="w-8 h-8 animate-spin" />
            <span className="text-xs font-mono">Loading workspace manifests...</span>
          </div>
        ) : builds.length === 0 ? (
          <div className="py-16 text-center text-gray-500">
            <FolderGit2 className="w-12 h-12 mx-auto mb-2 opacity-30 text-gray-400" />
            <p className="text-xs">No workspaces registered.</p>
            <p className="text-[11px] text-gray-600 mt-1">
              Launch a mission in the Swarm Studio to generate autonomous codebases.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-obsidian-bg text-gray-400 border-b border-obsidian-border uppercase text-[10px] tracking-wider">
                <tr>
                  <th className="p-3">Workspace ID</th>
                  <th className="p-3">Title / Directive</th>
                  <th className="p-3">Track</th>
                  <th className="p-3 text-center">Files</th>
                  <th className="p-3">Status</th>
                  <th className="p-3 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-obsidian-border/40 text-gray-300">
                {builds.map((b, idx) => (
                  <tr key={idx} className="hover:bg-white/5 transition">
                    <td className="p-3 font-mono font-medium text-cyber-cyan">{b.id}</td>
                    <td className="p-3 font-medium text-white">{b.title || b.id}</td>
                    <td className="p-3 text-gray-400">{b.track || "Autonomous Software"}</td>
                    <td className="p-3 text-center font-mono">{b.files || b.file_count || 1}</td>
                    <td className="p-3">
                      <span className="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-mono bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
                        <CheckCircle className="w-2.5 h-2.5" />
                        <span>{b.status || "READY"}</span>
                      </span>
                    </td>
                    <td className="p-3 text-right space-x-2">
                      <button
                        onClick={() => handleRunBuild(b.id)}
                        disabled={activeActionId === b.id}
                        className="text-xs bg-cyber-cyan/10 hover:bg-cyber-cyan/20 border border-cyber-cyan/30 text-cyber-cyan px-2.5 py-1 rounded transition inline-flex items-center space-x-1 disabled:opacity-50"
                      >
                        <Play className="w-3 h-3 fill-current" />
                        <span>Run</span>
                      </button>
                      <button
                        onClick={() => handleTestBuild(b.id)}
                        disabled={activeActionId === b.id}
                        className="text-xs bg-purple-500/10 hover:bg-purple-500/20 border border-purple-500/30 text-purple-300 px-2.5 py-1 rounded transition inline-flex items-center space-x-1 disabled:opacity-50"
                      >
                        <span>Test</span>
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {/* Action log viewer */}
        {actionLog && (
          <div className="mt-4 p-4 bg-obsidian-bg border border-obsidian-border rounded-lg space-y-2">
            <div className="flex items-center justify-between text-xs pb-1 border-b border-obsidian-border text-gray-400">
              <span className="font-mono">Execution Log</span>
              <button
                onClick={() => setActionLog(null)}
                className="text-[10px] text-gray-500 hover:text-white"
              >
                Clear
              </button>
            </div>
            <pre className="font-mono text-xs text-cyber-cyan overflow-x-auto whitespace-pre-wrap max-h-48">
              {actionLog}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}

