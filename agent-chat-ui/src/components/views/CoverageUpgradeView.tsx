"use client";

import { motion } from "framer-motion";
import { Home, SquarePen, Shield, ArrowRight } from "lucide-react";
import { ChatPanel } from "./shared/ChatPanel";
import { ChatInput, useSubmitMessage } from "./shared/ChatInput";
import { VoiceNav } from "./shared/VoiceNav";

// ---------------------------------------------------------------------------
// Quick upgrade prompts
// ---------------------------------------------------------------------------
const UPGRADE_PROMPTS = [
  { label: "See all options", message: "Show me all available coverage upgrade options for my policy." },
  { label: "Add collision", message: "I'd like to add collision coverage to my policy. What are the options?" },
  { label: "Add comprehensive", message: "What would it cost to add comprehensive coverage?" },
  { label: "Compare tiers", message: "Can you compare the Basic, Standard, and Premium tiers for me?" },
];

// ---------------------------------------------------------------------------
// Background — radial energy burst (IBM Watson–inspired)
// ---------------------------------------------------------------------------
function BurstBackground() {
  return (
    <div className="pointer-events-none absolute inset-0 overflow-hidden">
      <div className="absolute inset-0 bg-[#030303]" />

      {/* Radial glow from top-right */}
      <div className="absolute -top-[20%] -right-[15%] h-[100%] w-[70%] bg-[radial-gradient(ellipse_at_80%_20%,rgba(197,150,26,0.07)_0%,transparent_55%)]" />

      {/* Secondary glow bottom-left */}
      <div className="absolute -bottom-[20%] -left-[10%] h-[50%] w-[40%] bg-[radial-gradient(ellipse,rgba(197,150,26,0.03)_0%,transparent_60%)]" />

      {/* Radial burst SVG — lines radiating from top-right */}
      <svg
        className="absolute inset-0 h-full w-full opacity-[0.03]"
        viewBox="0 0 1200 800"
        fill="none"
        preserveAspectRatio="xMidYMid slice"
      >
        {/* Burst origin at (1050, 100) */}
        <line x1="1050" y1="100" x2="0" y2="150" stroke="#C5961A" strokeWidth="1" />
        <line x1="1050" y1="100" x2="0" y2="300" stroke="#C5961A" strokeWidth="0.5" />
        <line x1="1050" y1="100" x2="0" y2="450" stroke="#C5961A" strokeWidth="1" />
        <line x1="1050" y1="100" x2="0" y2="600" stroke="#C5961A" strokeWidth="0.5" />
        <line x1="1050" y1="100" x2="0" y2="750" stroke="#C5961A" strokeWidth="0.8" />
        <line x1="1050" y1="100" x2="150" y2="800" stroke="#C5961A" strokeWidth="0.5" />
        <line x1="1050" y1="100" x2="350" y2="800" stroke="#C5961A" strokeWidth="1" />
        <line x1="1050" y1="100" x2="550" y2="800" stroke="#C5961A" strokeWidth="0.5" />
        <line x1="1050" y1="100" x2="750" y2="800" stroke="#C5961A" strokeWidth="0.8" />
        <line x1="1050" y1="100" x2="950" y2="800" stroke="#C5961A" strokeWidth="0.4" />
        <line x1="1050" y1="100" x2="1200" y2="500" stroke="#C5961A" strokeWidth="0.5" />
        <line x1="1050" y1="100" x2="1200" y2="300" stroke="#C5961A" strokeWidth="0.3" />

        {/* Concentric arcs around the burst origin */}
        <path d="M850,100 A200,200 0 0,1 1050,300" stroke="#C5961A" strokeWidth="0.4" />
        <path d="M700,100 A350,350 0 0,1 1050,450" stroke="#C5961A" strokeWidth="0.3" />
        <path d="M550,100 A500,500 0 0,1 1050,600" stroke="#C5961A" strokeWidth="0.4" />

        {/* Dots at line tips */}
        <circle cx="0" cy="150" r="2" fill="#C5961A" opacity="0.3" />
        <circle cx="0" cy="450" r="2.5" fill="#C5961A" opacity="0.3" />
        <circle cx="350" cy="800" r="2" fill="#C5961A" opacity="0.2" />
        <circle cx="750" cy="800" r="2" fill="#C5961A" opacity="0.2" />
      </svg>

      {/* Grid */}
      <div className="absolute inset-0 bg-grid-pattern opacity-8" />

      {/* Vignette */}
      <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_80%_20%,transparent_25%,rgba(0,0,0,0.75)_100%)]" />
    </div>
  );
}

// ---------------------------------------------------------------------------
// CoverageUpgradeView — The Showcase
// ---------------------------------------------------------------------------
interface CoverageUpgradeViewProps {
  policyNumber: string;
  policySubmitted: boolean;
  onPolicySubmitted: () => void;
  onHome: () => void;
  onNewThread: () => void;
}

export function CoverageUpgradeView({
  policyNumber,
  policySubmitted,
  onPolicySubmitted,
  onHome,
  onNewThread,
}: CoverageUpgradeViewProps) {
  const submitMessage = useSubmitMessage();

  const handlePromptClick = (message: string) => {
    submitMessage(
      message,
      undefined,
      !policySubmitted ? policyNumber : undefined,
    );
    if (!policySubmitted) onPolicySubmitted();
  };

  return (
    <div className="relative flex h-full flex-col overflow-hidden">
      <BurstBackground />

      {/* ─── Top nav ─── */}
      <div className="relative z-10 flex items-center justify-between px-6 py-4">
        <div className="flex items-center gap-2">
          <button
            onClick={onHome}
            className="flex cursor-pointer items-center gap-2 rounded-lg px-2.5 py-1.5 text-white/20 hover:text-white/50 hover:bg-white/5 transition-all"
          >
            <Home className="h-4 w-4" />
            <span className="text-xs font-medium">Home</span>
          </button>
          <VoiceNav />
        </div>

        <div className="flex items-center gap-1">
          <div className="h-1.5 w-1.5 rounded-full bg-[#C5961A]/40 animate-pulse" />
          <span className="text-[10px] uppercase tracking-[0.2em] text-white/15">
            Coverage Upgrade
          </span>
        </div>

        <button
          onClick={onNewThread}
          className="flex cursor-pointer items-center gap-2 rounded-lg px-2.5 py-1.5 text-white/20 hover:text-white/50 hover:bg-white/5 transition-all"
        >
          <SquarePen className="h-4 w-4" />
        </button>
      </div>

      {/* ─── Main: Reverse editorial split — chat LEFT, upgrade panel RIGHT ─── */}
      <div className="relative z-10 flex flex-1 overflow-hidden">
        {/* LEFT: Chat panel */}
        <motion.div
          initial={{ opacity: 0, x: -30 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
          className="flex flex-1 flex-col"
        >
          <ChatPanel
            className="flex-1"
            footer={
              <div className="w-full px-4 pb-4">
                <ChatInput
                  policyNumber={policyNumber}
                  policySubmitted={policySubmitted}
                  onPolicySubmitted={onPolicySubmitted}
                  placeholder="Ask about coverage options..."
                  showFileUpload={false}
                  showToolCallsToggle={true}
                />
              </div>
            }
          />
        </motion.div>

        {/* Vertical separator */}
        <div className="hidden lg:block w-px bg-gradient-to-b from-transparent via-white/[0.04] to-transparent" />

        {/* RIGHT: Upgrade panel — bold heading + quick prompts (hidden on small) */}
        <motion.div
          initial={{ opacity: 0, x: 50 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.9, ease: [0.22, 1, 0.36, 1] }}
          className="hidden lg:flex w-[38%] xl:w-[35%] flex-col justify-between px-10 xl:px-14 py-8"
        >
          {/* Heading */}
          <div>
            <motion.div
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.1, duration: 0.7, ease: [0.22, 1, 0.36, 1] }}
            >
              <Shield className="h-8 w-8 text-[#C5961A]/20 mb-4" />
            </motion.div>

            <motion.h1
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.15, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
              className="text-[clamp(2.5rem,5vw,5rem)] font-black leading-[0.85] tracking-tighter text-white"
            >
              UPGRADE
            </motion.h1>
            <motion.h2
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.25, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
              className="text-[clamp(2.5rem,5vw,5rem)] font-black leading-[0.85] tracking-tighter text-[#C5961A]/25"
            >
              YOUR
            </motion.h2>
            <motion.h2
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
              className="text-[clamp(2.5rem,5vw,5rem)] font-black leading-[0.85] tracking-tighter text-[#C5961A]/25"
            >
              COVER.
            </motion.h2>

            <motion.div
              initial={{ scaleX: 0 }}
              animate={{ scaleX: 1 }}
              transition={{ delay: 0.5, duration: 0.6 }}
              className="mt-6 h-px w-16 origin-left bg-gradient-to-r from-[#C5961A]/50 to-transparent"
            />

            <motion.p
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 0.6, duration: 0.5 }}
              className="mt-5 max-w-xs text-sm leading-relaxed text-white/20"
            >
              Explore coverage tiers, compare options, and find
              the right plan for your needs.
            </motion.p>
          </div>

          {/* Quick prompts */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.8, duration: 0.5 }}
            className="flex flex-col gap-2"
          >
            <span className="mb-2 text-[9px] font-semibold uppercase tracking-[0.25em] text-white/10">
              Quick Actions
            </span>
            {UPGRADE_PROMPTS.map((p, i) => (
              <motion.button
                key={p.label}
                initial={{ opacity: 0, x: 10 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: 0.9 + i * 0.06, duration: 0.3 }}
                whileHover={{ x: -4 }}
                onClick={() => handlePromptClick(p.message)}
                className="group flex cursor-pointer items-center justify-end gap-2 rounded-full border border-white/[0.05] bg-white/[0.02] px-3.5 py-1.5 transition-all hover:border-[#C5961A]/20 hover:bg-[#C5961A]/5"
              >
                <span className="text-[11px] font-medium text-white/25 transition-colors group-hover:text-[#C5961A]/70">
                  {p.label}
                </span>
                <ArrowRight className="h-3 w-3 text-white/0 transition-all group-hover:text-[#C5961A]/50" />
              </motion.button>
            ))}
          </motion.div>
        </motion.div>
      </div>
    </div>
  );
}
