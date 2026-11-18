import React from 'react';
import { 
  Film, 
  Type, 
  History, 
  Bot, 
  Sliders, 
  Cpu, 
  Github, 
  CheckCircle2, 
  ExternalLink,
  Flame,
  Layers,
  Image as ImageIcon,
  Radio
} from 'lucide-react';

export const NAV_ITEMS = [
  { id: 'dashboard', label: 'Clips Studio', icon: Film, badge: 'Studio' },
  { id: 'subtitles', label: 'Subtitle Lab', icon: Type, badge: '6 Styles' },
  { id: 'thumbnails', label: 'Thumbnail Studio', icon: ImageIcon, badge: 'Viral' },
  { id: 'autopilot', label: 'Channel Autopilot', icon: Radio, badge: 'Auto' },
  { id: 'history', label: 'Clip Vault', icon: History },
  { id: 'agent', label: 'Autonomous Agent', icon: Bot, badge: 'New' },
  { id: 'settings', label: 'Studio Config', icon: Sliders },
];

export default function StudioSidebar({ activeTab, onSelectTab, status }) {
  return (
    <aside className="w-64 border-r border-rule bg-paper2/80 backdrop-blur-md flex flex-col shrink-0 h-full select-none">
      {/* Brand Header */}
      <div className="h-16 border-b border-rule flex items-center px-5 gap-3">
        <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-accent to-cyan-500 flex items-center justify-center text-white shadow-lg shadow-accent/20">
          <Flame size={20} className="fill-white/20" />
        </div>
        <div>
          <div className="font-display font-bold text-base tracking-wide text-ink flex items-center gap-1.5">
            VideoShorts <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-accent/15 text-accent font-semibold border border-accent/20">2.0</span>
          </div>
          <p className="text-[11px] text-muted font-mono leading-none">Studio Edition</p>
        </div>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto custom-scrollbar">
        <div className="px-3 py-1.5 text-[10px] font-mono tracking-wider text-muted uppercase">
          Workspace
        </div>

        {NAV_ITEMS.map((item) => {
          const Icon = item.icon;
          const isActive = activeTab === item.id;
          
          // Dynamic status badge for dashboard tab
          let displayBadge = item.badge;
          let badgeClass = isActive ? 'bg-accent text-white font-semibold' : 'bg-paper3 text-muted';
          
          if (item.id === 'dashboard' && status && status !== 'idle') {
            if (status === 'processing') {
              displayBadge = 'Processing';
              badgeClass = 'bg-amber-500/20 text-amber-400 font-semibold border border-amber-500/30 animate-pulse';
            } else if (status === 'complete') {
              displayBadge = 'Ready';
              badgeClass = 'bg-emerald-500/20 text-emerald-400 font-semibold border border-emerald-500/30';
            } else if (status === 'error') {
              displayBadge = 'Failed';
              badgeClass = 'bg-rose-500/20 text-rose-400 font-semibold border border-rose-500/30';
            }
          }

          return (
            <button
              key={item.id}
              onClick={() => onSelectTab(item.id)}
              className={`w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm font-medium transition-all group ${
                isActive
                  ? 'bg-accent/10 text-ink border border-accent/30 shadow-sm'
                  : 'text-muted hover:text-ink hover:bg-paper3/60'
              }`}
            >
              <div className="flex items-center gap-3">
                <Icon 
                  size={18} 
                  className={`transition-colors ${
                    isActive ? 'text-accent' : 'text-muted group-hover:text-ink'
                  }`} 
                />
                <span className="capitalize">{item.label}</span>
              </div>
              {displayBadge && (
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded-full ${badgeClass}`}>
                  {displayBadge}
                </span>
              )}
            </button>
          );
        })}
      </nav>

      {/* Hardware Telemetry Card */}
      <div className="p-3 m-3 rounded-xl border border-rule bg-paper3/40 space-y-2.5">
        <div className="flex items-center justify-between text-xs">
          <span className="flex items-center gap-1.5 text-ink font-medium">
            <Cpu size={14} className="text-cyan-400" /> Hardware Engine
          </span>
          <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" title="Engine Live" />
        </div>

        <div className="space-y-1.5 font-mono text-[11px]">
          <div className="flex justify-between text-muted">
            <span>GPU:</span>
            <span className="text-ink font-medium">RTX 3050 CUDA</span>
          </div>
          <div className="flex justify-between text-muted">
            <span>LLM:</span>
            <span className="text-ink font-medium">Inception Mercury-3</span>
          </div>
          <div className="flex justify-between text-muted">
            <span>Transcribe:</span>
            <span className="text-ink font-medium">Whisper + VAD</span>
          </div>
          <div className="flex justify-between text-muted">
            <span>Encoder:</span>
            <span className="text-ink font-medium">h264_nvenc</span>
          </div>
        </div>

        <div className="pt-2 border-t border-rule flex items-center justify-between text-[11px]">
          <span className="text-emerald-400 flex items-center gap-1 font-medium">
            <CheckCircle2 size={12} /> 100% Free
          </span>
          <span className="text-muted">No limits</span>
        </div>
      </div>

      {/* GitHub Repository Link */}
      <div className="p-3 border-t border-rule bg-paper2/50">
        <a
          href="https://github.com/yogendra1941/VideoShorts"
          target="_blank"
          rel="noopener noreferrer"
          className="flex items-center justify-between px-3 py-2 rounded-lg text-xs text-muted hover:text-ink hover:bg-paper3/80 transition-colors"
        >
          <span className="flex items-center gap-2">
            <Github size={14} /> yogendra1941/VideoShorts
          </span>
          <ExternalLink size={12} />
        </a>
      </div>
    </aside>
  );
}
