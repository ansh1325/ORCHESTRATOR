"use client";

import React, { useState, useRef, useEffect } from "react";
import {
  Send,
  Brain,
  Volume2,
  ChevronDown,
  ChevronUp,
  Sparkles,
  Bot,
  User,
  Copy,
  Check,
  RefreshCw,
} from "lucide-react";
import { sendChat } from "@/lib/api";

interface ChatTabProps {
  onNotify: (type: "success" | "error" | "info", message: string) => void;
}

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  text: string;
  thought?: string;
  strategy?: string;
  speaker?: string;
  timestamp: string;
}

export function ChatTab({ onNotify }: ChatTabProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "initial-msg",
      role: "assistant",
      text: "Greetings, Master Ansh. All cognitive subsystems—REA Reverse Engineering, Hermes 44+ Skills, Autonomous Multi-Agent Swarms, and Voss Telephony—are online and synchronized. What is our objective today?",
      thought: "Initial cognitive bootstrap complete. User profile verified as Chief Systems Architect Ansh Tiwari. Awaiting natural language directive.",
      strategy: "Autonomous Ready",
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [openThoughts, setOpenThoughts] = useState<Record<string, boolean>>({});
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, loading]);

  const toggleThought = (id: string) => {
    setOpenThoughts((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  const handleSpeak = (text: string) => {
    if (typeof window !== "undefined" && "speechSynthesis" in window) {
      window.speechSynthesis.cancel();
      const utter = new SpeechSynthesisUtterance(text);
      utter.rate = 1.05;
      utter.pitch = 0.95;
      window.speechSynthesis.speak(utter);
      onNotify("info", "Playing speech audio...");
    }
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
    onNotify("info", "Message copied to clipboard");
  };

  const handleSend = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || loading) return;

    const query = input.trim();
    setInput("");

    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: "user",
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    setMessages((prev) => [...prev, userMessage]);
    setLoading(true);

    try {
      const res = await sendChat(query);
      const assistantMessage: ChatMessage = {
        id: `asst-${Date.now()}`,
        role: "assistant",
        text: res.text,
        thought: res.thought,
        strategy: res.strategy,
        speaker: res.speaker || "JARVIS",
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };

      setMessages((prev) => [...prev, assistantMessage]);

      // Automatically speak short responses or notifications
      if (res.text && res.text.length < 250) {
        handleSpeak(res.text);
      }
    } catch (err: any) {
      onNotify("error", err.message || "Failed to reach JARVIS Brain");
      const errorMessage: ChatMessage = {
        id: `err-${Date.now()}`,
        role: "assistant",
        text: `⚠️ Communication latency: ${err.message || "Unknown error"}. Local offline fallback active.`,
        timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl flex flex-col h-[750px]">
      {/* Chat Header */}
      <div className="p-4 border-b border-obsidian-border/50 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyber-cyan/10 border border-cyber-cyan/30 flex items-center justify-center text-cyber-cyan">
            <Brain className="w-5 h-5 animate-pulse" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="font-bold text-white text-base">Central Cognitive Brain // CoT Engine</h3>
              <span className="text-[10px] bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 px-2 py-0.5 rounded font-mono">
                ONLINE
              </span>
            </div>
            <p className="text-xs text-gray-400">
              Multi-turn dialogue with deep Chain-of-Thought reasoning, real-time powerup routing, and TTS speech synthesis.
            </p>
          </div>
        </div>

        <button
          onClick={() => {
            setMessages([
              {
                id: `reset-${Date.now()}`,
                role: "assistant",
                text: "Memory context refreshed. Ready for the next directive, Master Ansh.",
                timestamp: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
              },
            ]);
            onNotify("info", "Dialogue session reset");
          }}
          className="text-xs text-gray-400 hover:text-white bg-obsidian-bg border border-obsidian-border px-3 py-1.5 rounded flex items-center space-x-1"
        >
          <RefreshCw className="w-3 h-3" />
          <span>Reset Chat</span>
        </button>
      </div>

      {/* Message Feed */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((m) => {
          const isUser = m.role === "user";
          return (
            <div key={m.id} className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
              <div
                className={`max-w-[85%] rounded-xl p-4 border text-xs leading-relaxed ${
                  isUser
                    ? "bg-cyber-cyan/10 border-cyber-cyan/30 text-white rounded-br-none"
                    : "bg-obsidian-bg/90 border-obsidian-border/80 text-gray-200 rounded-bl-none shadow-lg"
                }`}
              >
                {/* Header inside bubble */}
                <div className="flex items-center justify-between pb-2 mb-2 border-b border-white/5 text-[11px]">
                  <div className="flex items-center space-x-1.5">
                    {isUser ? (
                      <>
                        <User className="w-3.5 h-3.5 text-cyber-cyan" />
                        <span className="font-semibold text-cyber-cyan">Master Ansh Tiwari</span>
                      </>
                    ) : (
                      <>
                        <Bot className="w-3.5 h-3.5 text-purple-400" />
                        <span className="font-semibold text-purple-300">{m.speaker || "JARVIS"}</span>
                        {m.strategy && (
                          <span className="text-[9px] bg-cyber-cyan/10 text-cyber-cyan px-1.5 py-0.2 rounded border border-cyber-cyan/20">
                            {m.strategy}
                          </span>
                        )}
                      </>
                    )}
                  </div>
                  <span className="text-[10px] text-gray-500">{m.timestamp}</span>
                </div>

                {/* Chain of Thought Box */}
                {m.thought && (
                  <div className="mb-3 border border-purple-500/30 rounded-lg overflow-hidden bg-purple-950/10">
                    <button
                      type="button"
                      onClick={() => toggleThought(m.id)}
                      className="w-full px-3 py-1.5 text-left text-[11px] font-mono text-purple-300 hover:bg-purple-900/20 flex items-center justify-between transition"
                    >
                      <div className="flex items-center space-x-1.5">
                        <Sparkles className="w-3 h-3 text-purple-400 animate-spin" />
                        <span>Chain-of-Thought Reasoning</span>
                      </div>
                      {openThoughts[m.id] ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                    </button>
                    {openThoughts[m.id] && (
                      <div className="p-3 border-t border-purple-500/20 font-mono text-[11px] text-gray-300 bg-black/40 whitespace-pre-wrap leading-relaxed">
                        {m.thought}
                      </div>
                    )}
                  </div>
                )}

                {/* Main text content */}
                <div className="whitespace-pre-wrap text-xs font-sans leading-relaxed">{m.text}</div>

                {/* Action footer */}
                {!isUser && (
                  <div className="mt-3 pt-2 border-t border-white/5 flex items-center justify-between text-[11px] text-gray-500">
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleSpeak(m.text)}
                        className="hover:text-cyber-cyan transition flex items-center space-x-1"
                      >
                        <Volume2 className="w-3.5 h-3.5" />
                        <span>Speak</span>
                      </button>
                      <button
                        onClick={() => handleCopy(m.id, m.text)}
                        className="hover:text-cyber-cyan transition flex items-center space-x-1"
                      >
                        {copiedId === m.id ? (
                          <Check className="w-3.5 h-3.5 text-emerald-400" />
                        ) : (
                          <Copy className="w-3.5 h-3.5" />
                        )}
                        <span>{copiedId === m.id ? "Copied" : "Copy"}</span>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {loading && (
          <div className="flex justify-start">
            <div className="bg-obsidian-bg border border-cyber-cyan/30 rounded-xl p-4 text-xs text-cyber-cyan flex items-center space-x-2 animate-pulse">
              <Brain className="w-4 h-4 animate-spin" />
              <span>JARVIS is formulating Chain-of-Thought strategy &amp; evaluating tool routing...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Quick Prompt Suggestions */}
      <div className="px-4 py-2 bg-obsidian-bg/50 border-t border-obsidian-border/40 flex flex-wrap gap-2">
        {[
          "Synthesize a tool to calculate SHA256 hashes",
          "What is the status of our active agent swarms?",
          "Simulate a cold call for Autonomous Drone Delivery Logistics",
          "Audit tests/test_orchestration.py for memory mitigations",
        ].map((chip, idx) => (
          <button
            key={idx}
            type="button"
            onClick={() => setInput(chip)}
            className="text-[11px] bg-obsidian-bg hover:bg-obsidian-border border border-obsidian-border px-2.5 py-1 rounded-full text-gray-300 hover:text-white transition"
          >
            {chip}
          </button>
        ))}
      </div>

      {/* Input Bar */}
      <div className="p-4 border-t border-obsidian-border/50 bg-obsidian-bg/80">
        <form onSubmit={handleSend} className="flex items-center space-x-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type any natural language command or question for JARVIS..."
            className="flex-1 bg-obsidian-card border border-obsidian-border rounded-xl px-4 py-3 text-xs text-white placeholder-gray-500 focus:border-cyber-cyan focus:outline-none"
          />
          <button
            type="submit"
            disabled={loading || !input.trim()}
            className="bg-cyber-cyan hover:bg-cyber-cyan/90 disabled:opacity-50 text-black font-semibold px-5 py-3 rounded-xl text-xs flex items-center space-x-2 transition"
          >
            <span>Transmit</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
}

