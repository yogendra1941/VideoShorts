import React from 'react';
import { 
  RotateCcw, 
  Plus, 
  CheckCircle2, 
  Cpu, 
  Github, 
  Zap,
  Flame,
  ShieldCheck
} from 'lucide-react';
import { NAV_ITEMS } from './StudioSidebar';

export default function StudioHeader({ activeTab, onReset, status }) {
  const currentNav = NAV_ITEMS.find((n) => n.id === activeTab) || NAV_ITEMS[0];
  const CurrentIcon = currentNav.icon;

  return (
    <header className="h-16 border-b border-rule bg-paper2/50 backdrop-blur-md flex items-center justify-between px-6 shrink-0 z-10">
      {/* Active Tab Title */}
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-lg bg-paper3 border border-rule flex items-center justify-center text-accent">
          <CurrentIcon size={16} />
        </div>
        <div>
          <h1 className="text-sm font-semibold text-ink leading-tight capitalize">
            {currentNav.label}
          </h1>
          <p className="text-[11px] text-muted font-mono leading-tight">
            VideoShorts AI Clipping Engine
          </p>
        </div>

        {status !== 'idle' && (
          <button
            onClick={onReset}
            className="ml-4 flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rule bg-paper3/60 hover:bg-paper3 text-xs font-medium text-ink transition-colors shadow-sm"
          >
            <Plus size={14} className="text-accent" />
            <span>New Video</span>
          </button>
        )}
      </div>

      {/* Telemetry & Badges */}
      <div className="flex items-center gap-3">
        {/* GPU Status */}
        <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-full border border-emerald-500/20 bg-emerald-500/10 text-emerald-400 font-mono text-xs">
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
          <span>RTX 3050 · CUDA Active</span>
        </div>

        {/* AI Model Badge */}
        <div className="hidden md:flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-cyan-500/20 bg-cyan-500/10 text-cyan-300 font-mono text-xs">
          <Zap size={13} className="text-cyan-400" />
          <span>Inception Mercury-3</span>
        </div>

        {/* 100% Free Pill */}
        <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-accent/25 bg-accent/10 text-accent font-mono text-xs font-medium">
          <ShieldCheck size={14} />
          <span>100% Free · No Limits</span>
        </div>

        {/* GitHub link */}
        <a
          href="https://github.com/yogendra1941/VideoShorts"
          target="_blank"
          rel="noopener noreferrer"
          className="p-2 rounded-lg border border-rule bg-paper3/50 text-muted hover:text-ink hover:bg-paper3 transition-colors"
          title="View GitHub Repository"
        >
          <Github size={16} />
        </a>
      </div>
    </header>
  );
}
