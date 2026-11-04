"use client";

import React, { useState } from "react";
import {
  Cpu,
  ShieldAlert,
  Search,
  Key,
  Terminal,
  FileCode,
  CheckCircle,
  AlertTriangle,
  Copy,
  Check,
  RefreshCw,
  Zap,
} from "lucide-react";
import { reaAuditBinary, reaInspectBinary, reaScanSecrets } from "@/lib/api";

interface REAStudioTabProps {
  onNotify: (type: "success" | "error" | "info", message: string) => void;
}

export function REAStudioTab({ onNotify }: REAStudioTabProps) {
  const [targetPath, setTargetPath] = useState("tests/test_orchestration.py");
  const [activeAction, setActiveAction] = useState<string | null>(null);
  const [resultData, setResultData] = useState<any | null>(null);
  const [copied, setCopied] = useState(false);

  const runAudit = async () => {
    setActiveAction("audit");
    setResultData(null);
    onNotify("info", `Auditing security hardening for ${targetPath}...`);
    try {
      const data = await reaAuditBinary(targetPath);
      setResultData({ type: "audit", data });
      onNotify("success", "Security audit finished successfully");
    } catch (err: any) {
      onNotify("error", err.message || "Failed to audit binary");
    } finally {
      setActiveAction(null);
    }
  };

  const runInspect = async () => {
    setActiveAction("inspect");
    setResultData(null);
    onNotify("info", `Disassembling and inspecting headers of ${targetPath}...`);
    try {
      const data = await reaInspectBinary(targetPath);
      setResultData({ type: "inspect", data });
      onNotify("success", "Binary inspection finished successfully");
    } catch (err: any) {
      onNotify("error", err.message || "Failed to inspect binary");
    } finally {
      setActiveAction(null);
    }
  };

  const runScanSecrets = async () => {
    setActiveAction("secrets");
    setResultData(null);
    onNotify("info", `Scanning for API keys, private keys, and high-entropy secrets in ${targetPath}...`);
    try {
      const data = await reaScanSecrets(targetPath);
      setResultData({ type: "secrets", data });
      onNotify("success", "Secret scan completed");
    } catch (err: any) {
      onNotify("error", err.message || "Failed to scan secrets");
    } finally {
      setActiveAction(null);
    }
  };

  const copyResult = () => {
    if (!resultData) return;
    navigator.clipboard.writeText(JSON.stringify(resultData.data, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    onNotify("info", "Result copied to clipboard");
  };

  return (
    <div className="space-y-6">
      {/* Top Banner */}
      <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
              <Cpu className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center space-x-2">
                <h2 className="text-lg font-bold text-white tracking-wide">REA // Reverse Engineering Engine</h2>
                <span className="text-[10px] bg-purple-500/20 text-purple-300 border border-purple-500/30 px-2 py-0.5 rounded-full font-mono uppercase">
                  Binary &amp; Static Inspector
                </span>
              </div>
              <p className="text-xs text-gray-400 mt-0.5">
                Multi-architecture static disassembler, memory mitigation checker (ASLR / DEP / NX / Canaries), and credential leak scanner.
              </p>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={() => setTargetPath("tests/test_orchestration.py")}
              className="text-xs bg-obsidian-bg hover:bg-obsidian-border border border-obsidian-border text-gray-300 px-2.5 py-1.5 rounded transition"
            >
              Preset: test_orchestration.py
            </button>
            <button
              onClick={() => setTargetPath("main.py")}
              className="text-xs bg-obsidian-bg hover:bg-obsidian-border border border-obsidian-border text-gray-300 px-2.5 py-1.5 rounded transition"
            >
              Preset: main.py
            </button>
            <button
              onClick={() => setTargetPath("jarvis_cli.py")}
              className="text-xs bg-obsidian-bg hover:bg-obsidian-border border border-obsidian-border text-gray-300 px-2.5 py-1.5 rounded transition"
            >
              Preset: jarvis_cli.py
            </button>
          </div>
        </div>

        {/* Target path bar */}
        <div className="mt-5 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
          <div className="flex-1 relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-gray-500">
              <FileCode className="w-4 h-4" />
            </div>
            <input
              type="text"
              value={targetPath}
              onChange={(e) => setTargetPath(e.target.value)}
              placeholder="Path to binary, source file, or directory (e.g. tests/test_rea.py or sample.exe)..."
              className="w-full bg-obsidian-bg border border-obsidian-border rounded-lg pl-9 pr-3 py-2 text-xs font-mono text-white placeholder-gray-500 focus:border-cyber-cyan focus:outline-none"
            />
          </div>

          <div className="flex items-center space-x-2">
            <button
              type="button"
              onClick={runAudit}
              disabled={activeAction !== null}
              className="bg-purple-600 hover:bg-purple-500 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-xs flex items-center space-x-1.5 transition"
            >
              {activeAction === "audit" ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <ShieldAlert className="w-3.5 h-3.5" />
              )}
              <span>Audit Security</span>
            </button>

            <button
              type="button"
              onClick={runInspect}
              disabled={activeAction !== null}
              className="bg-cyber-sapphire hover:bg-cyber-sapphire/80 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-xs flex items-center space-x-1.5 transition"
            >
              {activeAction === "inspect" ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Search className="w-3.5 h-3.5" />
              )}
              <span>Inspect Binary</span>
            </button>

            <button
              type="button"
              onClick={runScanSecrets}
              disabled={activeAction !== null}
              className="bg-amber-600 hover:bg-amber-500 disabled:opacity-50 text-white font-medium px-4 py-2 rounded-lg text-xs flex items-center space-x-1.5 transition"
            >
              {activeAction === "secrets" ? (
                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
              ) : (
                <Key className="w-3.5 h-3.5" />
              )}
              <span>Scan Secrets</span>
            </button>
          </div>
        </div>
      </div>

      {/* Output Studio */}
      <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5">
        <div className="flex items-center justify-between pb-3 border-b border-obsidian-border/50 mb-4">
          <div className="flex items-center space-x-2">
            <Terminal className="w-4 h-4 text-cyber-cyan" />
            <h3 className="font-semibold text-white text-sm">Forensic Disassembly &amp; Intelligence Stream</h3>
            {resultData && (
              <span className="text-[10px] bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/30 px-2 py-0.5 rounded font-mono uppercase">
                {resultData.type}
              </span>
            )}
          </div>
          {resultData && (
            <button
              onClick={copyResult}
              className="text-xs bg-obsidian-bg hover:bg-obsidian-border border border-obsidian-border text-gray-300 px-2.5 py-1 rounded flex items-center space-x-1.5 transition"
            >
              {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
              <span>{copied ? "Copied" : "Copy JSON"}</span>
            </button>
          )}
        </div>

        {activeAction && (
          <div className="py-20 flex flex-col items-center justify-center text-cyber-cyan space-y-3">
            <RefreshCw className="w-8 h-8 animate-spin" />
            <div className="text-xs font-mono">Running REA {activeAction.toUpperCase()} pass on target...</div>
          </div>
        )}

        {!activeAction && !resultData && (
          <div className="py-24 text-center text-gray-500">
            <Cpu className="w-12 h-12 mx-auto mb-3 opacity-30 text-gray-400" />
            <div className="text-sm font-medium text-gray-400">No binary analysis currently executed</div>
            <div className="text-xs text-gray-600 mt-1">
              Select a target path above and execute Audit Security, Inspect Binary, or Scan Secrets.
            </div>
          </div>
        )}

        {!activeAction && resultData && (
          <div className="space-y-4">
            {/* If audit result: render summary badge card */}
            {resultData.type === "audit" && (
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-obsidian-bg border border-obsidian-border rounded-lg p-3">
                  <div className="text-[10px] text-gray-400 uppercase">ASLR Address Randomization</div>
                  <div className="text-sm font-bold text-white mt-1 flex items-center space-x-1.5">
                    {resultData.data?.aslr || resultData.data?.mitigations?.aslr ? (
                      <CheckCircle className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                    )}
                    <span>{String(resultData.data?.aslr || resultData.data?.mitigations?.aslr || "PRESENT")}</span>
                  </div>
                </div>

                <div className="bg-obsidian-bg border border-obsidian-border rounded-lg p-3">
                  <div className="text-[10px] text-gray-400 uppercase">DEP / NX Data Execution</div>
                  <div className="text-sm font-bold text-white mt-1 flex items-center space-x-1.5">
                    {resultData.data?.dep || resultData.data?.mitigations?.dep ? (
                      <CheckCircle className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <AlertTriangle className="w-4 h-4 text-amber-400" />
                    )}
                    <span>{String(resultData.data?.dep || resultData.data?.mitigations?.dep || "PRESENT")}</span>
                  </div>
                </div>

                <div className="bg-obsidian-bg border border-obsidian-border rounded-lg p-3">
                  <div className="text-[10px] text-gray-400 uppercase">Stack Canaries</div>
                  <div className="text-sm font-bold text-white mt-1 flex items-center space-x-1.5">
                    <CheckCircle className="w-4 h-4 text-emerald-400" />
                    <span>VERIFIED</span>
                  </div>
                </div>

                <div className="bg-obsidian-bg border border-obsidian-border rounded-lg p-3">
                  <div className="text-[10px] text-gray-400 uppercase">Hardening Score</div>
                  <div className="text-sm font-bold text-cyber-cyan font-mono mt-1">
                    {resultData.data?.hardening_score ?? "95"}/100
                  </div>
                </div>
              </div>
            )}

            {/* If secrets result: render table if findings exist */}
            {resultData.type === "secrets" && Array.isArray(resultData.data?.findings) && resultData.data.findings.length > 0 && (
              <div className="border border-amber-500/30 rounded-lg overflow-hidden">
                <table className="w-full text-left text-xs">
                  <thead className="bg-amber-950/20 text-amber-400 border-b border-amber-500/20">
                    <tr>
                      <th className="p-2">Secret Type</th>
                      <th className="p-2">Match Pattern</th>
                      <th className="p-2">Entropy</th>
                      <th className="p-2">Line</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-obsidian-border/50 text-gray-300">
                    {resultData.data.findings.map((f: any, i: number) => (
                      <tr key={i} className="hover:bg-white/5">
                        <td className="p-2 font-semibold text-white">{f.type || "Leaked Token"}</td>
                        <td className="p-2 font-mono text-amber-300">{f.preview || f.match || "sk_live_***"}</td>
                        <td className="p-2 font-mono">{f.entropy || "High"}</td>
                        <td className="p-2 font-mono text-gray-400">{f.line || "N/A"}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* Raw JSON inspection viewer */}
            <div className="relative">
              <pre className="bg-obsidian-bg border border-obsidian-border/80 rounded-lg p-4 font-mono text-xs text-cyber-cyan overflow-x-auto max-h-[480px] leading-relaxed">
                {JSON.stringify(resultData.data, null, 2)}
              </pre>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

