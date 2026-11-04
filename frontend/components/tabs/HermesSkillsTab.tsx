"use client";

import React, { useState, useEffect } from "react";
import {
  Brain,
  Search,
  PlusCircle,
  BookOpen,
  User,
  Sparkles,
  Layers,
  CheckCircle,
  FileText,
  Tag,
  ShieldCheck,
  RefreshCw,
} from "lucide-react";
import { listHermesSkills, getHermesMemory, createHermesSkill } from "@/lib/api";

interface HermesSkillsTabProps {
  onNotify: (type: "success" | "error" | "info", message: string) => void;
}

export function HermesSkillsTab({ onNotify }: HermesSkillsTabProps) {
  const [skills, setSkills] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState("");
  const [profile, setProfile] = useState<any | null>(null);

  // New Skill Modal / Inline Form
  const [isSynthesizing, setIsSynthesizing] = useState(false);
  const [newSkillName, setNewSkillName] = useState("");
  const [newSkillDesc, setNewSkillDesc] = useState("");
  const [newSkillInstructions, setNewSkillInstructions] = useState("");
  const [isSubmittingSkill, setIsSubmittingSkill] = useState(false);

  // Active expanded skill
  const [selectedSkill, setSelectedSkill] = useState<any | null>(null);

  const fetchSkillsAndMemory = async () => {
    setLoading(true);
    try {
      const [skillsRes, memoryRes] = await Promise.all([
        listHermesSkills(),
        getHermesMemory().catch(() => ({ profile: null })),
      ]);
      setSkills(skillsRes.skills || []);
      if (memoryRes && memoryRes.profile) {
        setProfile(memoryRes.profile);
      }
    } catch (err: any) {
      onNotify("error", err.message || "Failed to load Hermes skills");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSkillsAndMemory();
  }, []);

  const handleCreateSkill = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSkillName.trim() || !newSkillDesc.trim()) {
      onNotify("error", "Please provide a skill name and description");
      return;
    }

    setIsSubmittingSkill(true);
    try {
      const res = await createHermesSkill(
        newSkillName.trim(),
        newSkillDesc.trim(),
        newSkillInstructions.trim() || `Instructions for ${newSkillName}`
      );
      onNotify("success", `✓ Skill '${res.name}' synthesized and hot-loaded into active memory!`);
      setNewSkillName("");
      setNewSkillDesc("");
      setNewSkillInstructions("");
      setIsSynthesizing(false);
      await fetchSkillsAndMemory();
    } catch (err: any) {
      onNotify("error", err.message || "Failed to synthesize skill");
    } finally {
      setIsSubmittingSkill(false);
    }
  };

  const filteredSkills = skills.filter((s) => {
    const q = searchQuery.toLowerCase();
    const nameMatch = s.name?.toLowerCase().includes(q);
    const descMatch = s.description?.toLowerCase().includes(q);
    const tagMatch = s.tags?.some((t: string) => t.toLowerCase().includes(q));
    return nameMatch || descMatch || tagMatch;
  });

  return (
    <div className="space-y-6">
      {/* Top Banner & Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-cyber-cyan/10 border border-cyber-cyan/30 flex items-center justify-center text-cyber-cyan">
            <Brain className="w-6 h-6" />
          </div>
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider">Agentskills.io Certified</div>
            <div className="text-xl font-bold text-white font-mono">{skills.length || 44} Active Skills</div>
            <div className="text-[11px] text-gray-400 mt-0.5">Hermes Standardized Cognitive Modules</div>
          </div>
        </div>

        <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5 flex items-center space-x-4">
          <div className="w-12 h-12 rounded-xl bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <User className="w-6 h-6" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs text-gray-400 uppercase tracking-wider">Tiered Memory System</div>
            <div className="text-sm font-semibold text-white truncate">
              {profile?.name || "Master Ansh Tiwari"}
            </div>
            <div className="text-[11px] text-gray-400 truncate">
              {profile?.role || "Chief Systems Architect"}
            </div>
          </div>
        </div>

        <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5 flex items-center justify-between">
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider">Skill Synthesis</div>
            <div className="text-sm font-semibold text-white mt-1">Autonomous Hot-Learning</div>
            <div className="text-[11px] text-gray-400 mt-0.5">Generates Markdown &amp; Code</div>
          </div>
          <button
            onClick={() => setIsSynthesizing(!isSynthesizing)}
            className="bg-cyber-cyan text-black px-3.5 py-2 rounded-lg text-xs font-semibold hover:bg-cyber-cyan/90 transition flex items-center space-x-1.5"
          >
            <PlusCircle className="w-4 h-4" />
            <span>{isSynthesizing ? "Cancel" : "New Skill"}</span>
          </button>
        </div>
      </div>

      {/* Synthesis Form Card */}
      {isSynthesizing && (
        <div className="bg-obsidian-card border border-cyber-cyan/40 rounded-xl p-5 animate-fadeIn">
          <div className="flex items-center space-x-2 pb-3 border-b border-obsidian-border/50 mb-4">
            <Sparkles className="w-5 h-5 text-cyber-cyan" />
            <h3 className="font-semibold text-white text-base">Synthesize Permanent Hermes Skill</h3>
          </div>
          <form onSubmit={handleCreateSkill} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="text-xs text-gray-400 block mb-1">Skill Identifier (lowercase_with_underscores)</label>
                <input
                  type="text"
                  value={newSkillName}
                  onChange={(e) => setNewSkillName(e.target.value)}
                  placeholder="e.g. quantum_circuit_optimizer"
                  className="w-full bg-obsidian-bg border border-obsidian-border rounded-lg px-3 py-2 text-xs font-mono text-white focus:border-cyber-cyan focus:outline-none"
                />
              </div>
              <div>
                <label className="text-xs text-gray-400 block mb-1">Brief Description</label>
                <input
                  type="text"
                  value={newSkillDesc}
                  onChange={(e) => setNewSkillDesc(e.target.value)}
                  placeholder="e.g. Synthesizes Qiskit quantum circuit passes and benchmarks fidelity."
                  className="w-full bg-obsidian-bg border border-obsidian-border rounded-lg px-3 py-2 text-xs text-white focus:border-cyber-cyan focus:outline-none"
                />
              </div>
            </div>

            <div>
              <label className="text-xs text-gray-400 block mb-1">Execution System Prompt &amp; Protocol Instructions</label>
              <textarea
                value={newSkillInstructions}
                onChange={(e) => setNewSkillInstructions(e.target.value)}
                placeholder="Step-by-step cognitive guidelines for this skill..."
                rows={4}
                className="w-full bg-obsidian-bg border border-obsidian-border rounded-lg p-3 text-xs font-mono text-white placeholder-gray-500 focus:border-cyber-cyan focus:outline-none"
              />
            </div>

            <div className="flex justify-end space-x-2">
              <button
                type="button"
                onClick={() => setIsSynthesizing(false)}
                className="px-3 py-1.5 rounded-lg text-xs text-gray-400 hover:text-white bg-obsidian-bg border border-obsidian-border"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmittingSkill}
                className="bg-cyber-cyan text-black font-semibold px-4 py-1.5 rounded-lg text-xs hover:bg-cyber-cyan/90 transition disabled:opacity-50 flex items-center space-x-1.5"
              >
                {isSubmittingSkill ? (
                  <>
                    <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                    <span>Compiling Skill...</span>
                  </>
                ) : (
                  <>
                    <Sparkles className="w-3.5 h-3.5" />
                    <span>Compile &amp; Hot-Load Skill</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Search and Filter */}
      <div className="flex items-center justify-between gap-4">
        <div className="flex-1 relative">
          <Search className="w-4 h-4 text-gray-500 absolute left-3 top-2.5" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search Hermes skills by name, capability, or tag..."
            className="w-full bg-obsidian-card border border-obsidian-border rounded-lg pl-9 pr-3 py-2 text-xs text-white placeholder-gray-500 focus:border-cyber-cyan focus:outline-none"
          />
        </div>
        <button
          onClick={fetchSkillsAndMemory}
          className="text-xs text-gray-400 hover:text-white bg-obsidian-card border border-obsidian-border px-3 py-2 rounded-lg flex items-center space-x-1"
        >
          <RefreshCw className={`w-3.5 h-3.5 ${loading ? "animate-spin" : ""}`} />
          <span>Reload</span>
        </button>
      </div>

      {/* Skills Grid */}
      {loading ? (
        <div className="py-20 flex flex-col items-center justify-center text-cyber-cyan space-y-3">
          <RefreshCw className="w-8 h-8 animate-spin" />
          <div className="text-xs font-mono">Loading Hermes 44+ skill matrix...</div>
        </div>
      ) : filteredSkills.length === 0 ? (
        <div className="py-16 text-center text-gray-500">
          <BookOpen className="w-10 h-10 mx-auto mb-2 opacity-30" />
          <p className="text-xs">No skills match '{searchQuery}'.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {filteredSkills.map((skill, index) => (
            <div
              key={index}
              onClick={() => setSelectedSkill(selectedSkill?.name === skill.name ? null : skill)}
              className={`bg-obsidian-card border rounded-xl p-4 cursor-pointer transition flex flex-col justify-between hover:border-cyber-cyan/50 ${
                selectedSkill?.name === skill.name
                  ? "border-cyber-cyan shadow-lg shadow-cyber-cyan/10"
                  : "border-obsidian-border/60"
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <span className="w-2 h-2 rounded-full bg-cyber-cyan shadow-sm shadow-cyber-cyan"></span>
                    <h4 className="text-sm font-bold text-white font-mono tracking-tight">{skill.name}</h4>
                  </div>
                  <span className="text-[10px] bg-cyber-cyan/10 text-cyber-cyan border border-cyber-cyan/20 px-2 py-0.5 rounded font-mono">
                    {skill.source || "hermes"}
                  </span>
                </div>
                <p className="text-xs text-gray-300 line-clamp-3 leading-relaxed mb-3">
                  {skill.description || "Production capability within Hermes cognitive ecosystem."}
                </p>
              </div>

              {skill.tags && Array.isArray(skill.tags) && skill.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 mt-2 pt-2 border-t border-obsidian-border/40">
                  {skill.tags.slice(0, 3).map((tag: string, tidx: number) => (
                    <span
                      key={tidx}
                      className="text-[10px] bg-obsidian-bg text-gray-400 border border-obsidian-border px-1.5 py-0.5 rounded flex items-center space-x-1"
                    >
                      <Tag className="w-2.5 h-2.5 text-gray-500" />
                      <span>{tag}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Selected Skill Details Drawer / Modal */}
      {selectedSkill && (
        <div className="bg-obsidian-card border border-cyber-cyan/50 rounded-xl p-5 shadow-2xl space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-obsidian-border/50">
            <div className="flex items-center space-x-2">
              <FileText className="w-5 h-5 text-cyber-cyan" />
              <h3 className="font-bold text-white text-base font-mono">{selectedSkill.name}</h3>
            </div>
            <button
              onClick={() => setSelectedSkill(null)}
              className="text-xs text-gray-400 hover:text-white px-2 py-1 bg-obsidian-bg rounded border border-obsidian-border"
            >
              Close
            </button>
          </div>

          <div className="text-xs text-gray-300 leading-relaxed">
            <div className="font-semibold text-white mb-1">Standard Description:</div>
            <p className="bg-obsidian-bg p-3 rounded-lg border border-obsidian-border text-gray-300">
              {selectedSkill.description}
            </p>
          </div>

          {selectedSkill.instructions && (
            <div className="text-xs text-gray-300 leading-relaxed">
              <div className="font-semibold text-white mb-1">System Instructions:</div>
              <pre className="bg-obsidian-bg p-3 rounded-lg border border-obsidian-border font-mono text-cyber-cyan overflow-x-auto whitespace-pre-wrap max-h-48">
                {selectedSkill.instructions}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

