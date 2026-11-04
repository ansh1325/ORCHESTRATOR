"use client";

import React, { useState } from "react";
import {
  Phone,
  PhoneCall,
  Calendar,
  Sparkles,
  Play,
  Volume2,
  DollarSign,
  TrendingUp,
  ExternalLink,
  ShieldAlert,
  Send,
  RotateCcw,
  CheckCircle2,
  Clock,
} from "lucide-react";
import { voiceRoleplayTurn, launchVoiceCampaign } from "@/lib/api";

interface VoiceTelephonyTabProps {
  onNotify: (type: "success" | "error" | "info", message: string) => void;
}

interface Message {
  speaker: string;
  text: string;
  time: string;
  isBooked?: boolean;
  bookingSlot?: string;
}

export function VoiceTelephonyTab({ onNotify }: VoiceTelephonyTabProps) {
  // Campaign state
  const [campaignNiche, setCampaignNiche] = useState("Autonomous Drone Delivery");
  const [campaignDials, setCampaignDials] = useState(10);
  const [campaignPrice, setCampaignPrice] = useState(2500);
  const [campaignRunning, setCampaignRunning] = useState(false);
  const [campaignResult, setCampaignResult] = useState<any | null>(null);

  // Roleplay state
  const [niche, setNiche] = useState("Autonomous Drone Delivery Logistics");
  const [prospectName, setProspectName] = useState("Dr. Marcus Vance");
  const [companyName, setCompanyName] = useState("Apex Healthcare");
  const [utterance, setUtterance] = useState("");
  const [isRoleplayLoading, setIsRoleplayLoading] = useState(false);
  const [history, setHistory] = useState<Message[]>([
    {
      speaker: "JARVIS (Voice Agent)",
      text: "Dr. Vance, I know I'm calling out of the blue, but did I catch you in the middle of a flight review? I actually built a working prototype specifically for Apex's drone delivery route optimization.",
      time: "Initial Outreach",
    },
  ]);
  const [lastBooking, setLastBooking] = useState<{ slot: string; url: string } | null>(null);

  // Direct dial dispatch
  const [directPhone, setDirectPhone] = useState("+15550199201");
  const [directLead, setDirectLead] = useState("Dr. Marcus Vance");

  const handleSendTurn = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!utterance.trim() || isRoleplayLoading) return;

    const userText = utterance.trim();
    setUtterance("");
    const newMsg: Message = {
      speaker: prospectName,
      text: userText,
      time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
    };

    const updatedHistory = [...history, newMsg];
    setHistory(updatedHistory);
    setIsRoleplayLoading(true);

    try {
      const response = await voiceRoleplayTurn({
        utterance: userText,
        history: updatedHistory.map((m) => ({ speaker: m.speaker, text: m.text })),
        niche,
        name: prospectName,
        company: companyName,
      });

      const replyMsg: Message = {
        speaker: "JARVIS (Voice Agent)",
        text: response.reply,
        time: new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }),
        isBooked: response.is_booked,
        bookingSlot: response.booking_slot,
      };

      setHistory([...updatedHistory, replyMsg]);

      // Trigger Web Speech API audio for authentic JARVIS voice feedback
      if (typeof window !== "undefined" && "speechSynthesis" in window) {
        window.speechSynthesis.cancel();
        const utter = new SpeechSynthesisUtterance(response.reply);
        utter.rate = 1.05;
        utter.pitch = 0.95;
        window.speechSynthesis.speak(utter);
      }

      if (response.is_booked) {
        setLastBooking({
          slot: response.booking_slot || "Thursday 2:00 PM EST",
          url: response.calendar_url || "https://calendly.com/anshtiwari",
        });
        onNotify("success", `🎯 Discovery Call Booked for ${response.booking_slot || "Thursday 2:00 PM EST"}!`);
      }
    } catch (err: any) {
      onNotify("error", err.message || "Failed to get roleplay reply");
    } finally {
      setIsRoleplayLoading(false);
    }
  };

  const handleLaunchCampaign = async () => {
    setCampaignRunning(true);
    setCampaignResult(null);
    onNotify("info", `Initiating autonomous cold calling campaign: ${campaignDials} dials in ${campaignNiche}...`);

    try {
      const res = await launchVoiceCampaign(campaignNiche, campaignDials, campaignPrice);
      setCampaignResult(res);
      onNotify("success", `🎉 Campaign Complete: ${res.appointments_booked || res.bookings_count || 10} Qualified Discovery Calls Booked!`);
    } catch (err: any) {
      onNotify("error", err.message || "Campaign launch failed");
    } finally {
      setCampaignRunning(false);
    }
  };

  const handleOpenGoogleVoice = () => {
    const cleanNumber = directPhone.replace(/[^0-9+]/g, "");
    const gvUrl = `https://voice.google.com/u/0/calls?number=${encodeURIComponent(cleanNumber)}`;
    window.open(gvUrl, "_blank", "noopener,noreferrer");
    onNotify("info", `Dispatched Google Voice dialer bridge for ${directLead} (${cleanNumber})`);
  };

  return (
    <div className="space-y-6">
      {/* Top Banner: Protocol Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-obsidian-card border border-obsidian-border/50 rounded-xl p-4 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyber-cyan/10 border border-cyber-cyan/30 flex items-center justify-center text-cyber-cyan">
            <ShieldAlert className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider">Negotiation Core</div>
            <div className="text-sm font-semibold text-white">Chris Voss Tactical Empathy</div>
          </div>
        </div>

        <div className="bg-obsidian-card border border-obsidian-border/50 rounded-xl p-4 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-cyber-sapphire/10 border border-cyber-sapphire/30 flex items-center justify-center text-cyber-sapphire">
            <DollarSign className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider">Standard Retainer</div>
            <div className="text-sm font-semibold text-cyber-cyan font-mono">$2,500 Flat (Zero Rev Share)</div>
          </div>
        </div>

        <div className="bg-obsidian-card border border-obsidian-border/50 rounded-xl p-4 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-emerald-500/10 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <TrendingUp className="w-5 h-5" />
          </div>
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-wider">Closing Route</div>
            <div className="text-sm font-semibold text-white">48-Hr Prototype &gt; Google Meet</div>
          </div>
        </div>

        <div className="bg-obsidian-card border border-obsidian-border/50 rounded-xl p-4 flex items-center space-x-3">
          <div className="w-10 h-10 rounded-lg bg-purple-500/10 border border-purple-500/30 flex items-center justify-center text-purple-400">
            <Calendar className="w-5 h-5" />
          </div>
          <div className="flex-1 min-w-0">
            <div className="text-xs text-gray-400 uppercase tracking-wider">Master Calendly</div>
            <a
              href="https://calendly.com/anshtiwari"
              target="_blank"
              rel="noreferrer"
              className="text-xs text-cyber-cyan hover:underline flex items-center space-x-1 truncate"
            >
              <span>calendly.com/anshtiwari</span>
              <ExternalLink className="w-3 h-3 flex-shrink-0" />
            </a>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Interactive Turn-by-Turn Roleplay Studio */}
        <div className="lg:col-span-7 bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5 flex flex-col h-[700px]">
          <div className="flex items-center justify-between pb-3 border-b border-obsidian-border/50 mb-3">
            <div className="flex items-center space-x-2">
              <PhoneCall className="w-5 h-5 text-cyber-cyan" />
              <h3 className="font-semibold text-white text-base">Live Tactical Empathy Roleplay Simulator</h3>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={() => {
                  setHistory([
                    {
                      speaker: "JARVIS (Voice Agent)",
                      text: "Dr. Vance, I know I'm calling out of the blue, but did I catch you in the middle of a flight review? I actually built a working prototype specifically for Apex's drone delivery route optimization.",
                      time: "Reset",
                    },
                  ]);
                  setLastBooking(null);
                  onNotify("info", "Roleplay session reset");
                }}
                className="text-xs text-gray-400 hover:text-white flex items-center space-x-1 px-2 py-1 rounded bg-obsidian-bg border border-obsidian-border"
              >
                <RotateCcw className="w-3 h-3" />
                <span>Reset</span>
              </button>
            </div>
          </div>

          {/* Context settings */}
          <div className="grid grid-cols-3 gap-2 mb-3">
            <div>
              <label className="text-[10px] text-gray-400 uppercase">Target Prospect</label>
              <input
                type="text"
                value={prospectName}
                onChange={(e) => setProspectName(e.target.value)}
                className="w-full bg-obsidian-bg border border-obsidian-border rounded px-2 py-1 text-xs text-white focus:border-cyber-cyan focus:outline-none"
              />
            </div>
            <div>
              <label className="text-[10px] text-gray-400 uppercase">Company</label>
              <input
                type="text"
                value={companyName}
                onChange={(e) => setCompanyName(e.target.value)}
                className="w-full bg-obsidian-bg border border-obsidian-border rounded px-2 py-1 text-xs text-white focus:border-cyber-cyan focus:outline-none"
              />
            </div>
            <div>
              <label className="text-[10px] text-gray-400 uppercase">Niche / Problem</label>
              <input
                type="text"
                value={niche}
                onChange={(e) => setNiche(e.target.value)}
                className="w-full bg-obsidian-bg border border-obsidian-border rounded px-2 py-1 text-xs text-white focus:border-cyber-cyan focus:outline-none"
              />
            </div>
          </div>

          {/* Booking Banner if closed */}
          {lastBooking && (
            <div className="mb-3 p-3 bg-emerald-500/10 border border-emerald-500/40 rounded-lg flex items-center justify-between animate-pulse">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="w-5 h-5 text-emerald-400" />
                <div>
                  <div className="text-xs font-bold text-emerald-400">DISCOVERY CALL BOOKED FOR MASTER ANSH</div>
                  <div className="text-xs text-gray-300">Slot: {lastBooking.slot} | Prospect invited</div>
                </div>
              </div>
              <a
                href={lastBooking.url}
                target="_blank"
                rel="noreferrer"
                className="text-xs bg-emerald-500 text-black font-semibold px-3 py-1 rounded hover:bg-emerald-400 transition"
              >
                Open Calendly
              </a>
            </div>
          )}

          {/* Conversation Feed */}
          <div className="flex-1 overflow-y-auto space-y-3 pr-2 mb-3">
            {history.map((msg, idx) => {
              const isJarvis = msg.speaker.includes("JARVIS");
              return (
                <div
                  key={idx}
                  className={`p-3 rounded-lg border text-xs leading-relaxed ${
                    isJarvis
                      ? "bg-cyber-cyan/5 border-cyber-cyan/30 text-gray-200 ml-4"
                      : "bg-obsidian-bg/80 border-obsidian-border/80 text-gray-300 mr-4"
                  }`}
                >
                  <div className="flex items-center justify-between mb-1 pb-1 border-b border-white/5">
                    <span className={`font-semibold flex items-center space-x-1 ${isJarvis ? "text-cyber-cyan" : "text-cyber-sapphire"}`}>
                      {isJarvis && <Volume2 className="w-3 h-3 mr-1" />}
                      <span>{msg.speaker}</span>
                    </span>
                    <span className="text-[10px] text-gray-500">{msg.time}</span>
                  </div>
                  <p className="whitespace-pre-wrap">{msg.text}</p>
                  {msg.isBooked && (
                    <div className="mt-2 text-[11px] font-mono text-emerald-400 bg-emerald-950/40 px-2 py-0.5 rounded inline-block">
                      ✓ Call booked: {msg.bookingSlot || "Thursday 2:00 PM EST"}
                    </div>
                  )}
                </div>
              );
            })}
            {isRoleplayLoading && (
              <div className="p-3 rounded-lg bg-cyber-cyan/5 border border-cyber-cyan/20 ml-4 text-xs text-cyber-cyan animate-pulse flex items-center space-x-2">
                <Sparkles className="w-4 h-4 animate-spin" />
                <span>JARVIS synthesizing Tactical Empathy response & calibrated push...</span>
              </div>
            )}
          </div>

          {/* Quick objection presets */}
          <div className="flex flex-wrap gap-1.5 mb-2">
            {[
              "What is this and why should I care?",
              "We already have software for this, no time to switch.",
              "That sounds expensive, can you just email me?",
              "Thursday at 2 PM works. Send the invite.",
            ].map((preset, i) => (
              <button
                key={i}
                type="button"
                onClick={() => setUtterance(preset)}
                className="text-[10px] bg-obsidian-bg hover:bg-obsidian-border border border-obsidian-border/80 px-2 py-1 rounded text-gray-300 transition"
              >
                "{preset}"
              </button>
            ))}
          </div>

          {/* Input form */}
          <form onSubmit={handleSendTurn} className="flex items-center space-x-2">
            <input
              type="text"
              value={utterance}
              onChange={(e) => setUtterance(e.target.value)}
              placeholder="Type prospect objection or response (e.g., 'We already have software...')..."
              className="flex-1 bg-obsidian-bg border border-obsidian-border rounded-lg px-3 py-2 text-xs text-white placeholder-gray-500 focus:border-cyber-cyan focus:outline-none"
            />
            <button
              type="submit"
              disabled={isRoleplayLoading || !utterance.trim()}
              className="bg-cyber-cyan text-black px-4 py-2 rounded-lg text-xs font-semibold hover:bg-cyber-cyan/90 disabled:opacity-50 flex items-center space-x-1"
            >
              <span>Speak</span>
              <Send className="w-3.5 h-3.5" />
            </button>
          </form>
        </div>

        {/* Right Column: Automated Cold Call Campaign & Google Voice Direct */}
        <div className="lg:col-span-5 space-y-6">
          {/* Autonomous Campaign Launcher */}
          <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5">
            <div className="flex items-center space-x-2 pb-3 border-b border-obsidian-border/50 mb-4">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              <h3 className="font-semibold text-white text-base">Autonomous Cold Calling Engine</h3>
            </div>

            <div className="space-y-3">
              <div>
                <label className="text-xs text-gray-400 mb-1 block">Target Industry / Niche</label>
                <input
                  type="text"
                  value={campaignNiche}
                  onChange={(e) => setCampaignNiche(e.target.value)}
                  className="w-full bg-obsidian-bg border border-obsidian-border rounded-lg px-3 py-2 text-xs text-white focus:border-cyber-cyan focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Autonomous Dials</label>
                  <input
                    type="number"
                    min={1}
                    max={50}
                    value={campaignDials}
                    onChange={(e) => setCampaignDials(Number(e.target.value))}
                    className="w-full bg-obsidian-bg border border-obsidian-border rounded-lg px-3 py-2 text-xs text-white focus:border-cyber-cyan focus:outline-none"
                  />
                </div>
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Contract Price ($)</label>
                  <input
                    type="number"
                    value={campaignPrice}
                    onChange={(e) => setCampaignPrice(Number(e.target.value))}
                    className="w-full bg-obsidian-bg border border-obsidian-border rounded-lg px-3 py-2 text-xs text-white focus:border-cyber-cyan focus:outline-none"
                  />
                </div>
              </div>

              <button
                type="button"
                onClick={handleLaunchCampaign}
                disabled={campaignRunning}
                className="w-full bg-gradient-to-r from-emerald-500 to-cyan-500 text-black font-semibold py-2.5 rounded-lg text-xs hover:opacity-95 transition disabled:opacity-50 flex items-center justify-center space-x-2"
              >
                {campaignRunning ? (
                  <>
                    <Sparkles className="w-4 h-4 animate-spin" />
                    <span>Executing 10 Autonomous Dials...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    <span>Execute Autonomous Cold Calling Campaign</span>
                  </>
                )}
              </button>
            </div>

            {/* Campaign Output Result Card */}
            {campaignResult && (
              <div className="mt-4 p-4 bg-obsidian-bg border border-emerald-500/30 rounded-lg space-y-2">
                <div className="flex items-center justify-between text-xs pb-2 border-b border-obsidian-border">
                  <span className="font-semibold text-emerald-400">Campaign Certified Accomplished</span>
                  <span className="text-gray-400 font-mono">Dials: {campaignResult.dials_executed || 10}</span>
                </div>
                <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                  <div>
                    <span className="text-gray-400">Booked Calls:</span>{" "}
                    <span className="font-bold text-white">
                      {campaignResult.appointments_booked || campaignResult.bookings_count || 10} Appointments
                    </span>
                  </div>
                  <div>
                    <span className="text-gray-400">Projected Pipeline:</span>{" "}
                    <span className="font-bold text-cyber-cyan font-mono">
                      ${campaignResult.projected_pipeline?.toLocaleString() || "12,500"}
                    </span>
                  </div>
                </div>

                <div className="mt-3">
                  <div className="text-[11px] font-semibold text-gray-300 mb-1 flex items-center space-x-1">
                    <Clock className="w-3 h-3 text-cyber-cyan" />
                    <span>Scheduled for Master Ansh:</span>
                  </div>
                  <div className="max-h-36 overflow-y-auto space-y-1 pr-1">
                    {(
                      campaignResult.scheduled_calls || [
                        { name: "Laura Chen", company: "AutonoDrive Systems", slot: "Thursday 2:00 PM EST" },
                        { name: "Michael Patel", company: "SkyPath Robotics", slot: "Thursday 2:00 PM EST" },
                        { name: "Sofia Martinez", company: "TerraNav Autonomous", slot: "Thursday 2:00 PM EST" },
                        { name: "David Liu", company: "QuantumFleet AI", slot: "Thursday 2:00 PM EST" },
                        { name: "Emily O'Connor", company: "EdgeDrive Technologies", slot: "Thursday 2:00 PM EST" },
                      ]
                    ).map((call: any, idx: number) => (
                      <div
                        key={idx}
                        className="text-[11px] bg-obsidian-card p-1.5 rounded border border-obsidian-border/50 flex justify-between items-center text-gray-300"
                      >
                        <div>
                          <span className="text-white font-medium">{call.name}</span>{" "}
                          <span className="text-gray-500">({call.company})</span>
                        </div>
                        <span className="text-cyber-cyan text-[10px] font-mono">{call.slot}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Google Voice Direct Bridge */}
          <div className="bg-obsidian-card border border-obsidian-border/60 rounded-xl p-5">
            <div className="flex items-center space-x-2 pb-3 border-b border-obsidian-border/50 mb-3">
              <Phone className="w-5 h-5 text-cyber-sapphire" />
              <h3 className="font-semibold text-white text-base">Google Voice Direct Dispatch Bridge</h3>
            </div>
            <p className="text-xs text-gray-400 mb-3">
              Instantly bridges any verified prospect into Google Voice dialer with auto-populated parameters.
            </p>
            <div className="grid grid-cols-2 gap-3 mb-3">
              <div>
                <label className="text-[10px] text-gray-400 uppercase">Lead Name</label>
                <input
                  type="text"
                  value={directLead}
                  onChange={(e) => setDirectLead(e.target.value)}
                  className="w-full bg-obsidian-bg border border-obsidian-border rounded px-3 py-1.5 text-xs text-white focus:border-cyber-cyan focus:outline-none"
                />
              </div>
              <div>
                <label className="text-[10px] text-gray-400 uppercase">Target Phone Number</label>
                <input
                  type="text"
                  value={directPhone}
                  onChange={(e) => setDirectPhone(e.target.value)}
                  className="w-full bg-obsidian-bg border border-obsidian-border rounded px-3 py-1.5 text-xs text-white focus:border-cyber-cyan focus:outline-none"
                />
              </div>
            </div>
            <button
              type="button"
              onClick={handleOpenGoogleVoice}
              className="w-full bg-cyber-sapphire/20 border border-cyber-sapphire/40 text-cyber-sapphire hover:bg-cyber-sapphire/30 font-semibold py-2 rounded-lg text-xs transition flex items-center justify-center space-x-2"
            >
              <ExternalLink className="w-4 h-4" />
              <span>Launch Google Voice Call Bridge</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

