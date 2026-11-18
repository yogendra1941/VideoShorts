import React from 'react';
import { Sparkles, Cpu, Film, Github, ExternalLink } from 'lucide-react';

export default function SiteNav({ className = '' }) {
  return (
    <header className={`sticky top-0 z-50 w-full border-b border-white/10 bg-[#090D16]/80 backdrop-blur-md px-6 py-3.5 transition-all ${className}`}>
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        
        {/* Brand Logo */}
        <div className="flex items-center gap-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-indigo-600 via-indigo-500 to-cyan-400 flex items-center justify-center shadow-lg shadow-indigo-500/25 ring-1 ring-white/20">
            <Film className="w-5 h-5 text-white stroke-[2.2]" />
          </div>
          <div className="flex flex-col">
            <span className="text-lg font-bold tracking-tight text-white flex items-center gap-1.5">
              VideoShorts
              <span className="text-[10px] font-semibold tracking-wider uppercase px-1.5 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                Studio
              </span>
            </span>
          </div>
        </div>

        {/* System & Hardware Status */}
        <div className="hidden md:flex items-center gap-3">
          {/* GPU CUDA Status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-900/90 border border-slate-800 text-xs text-slate-300">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            <Cpu className="w-3.5 h-3.5 text-slate-400" />
            <span className="font-mono text-[11px] text-slate-200">RTX 3050 · CUDA Active</span>
          </div>

          {/* AI Model Status */}
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-indigo-950/40 border border-indigo-800/40 text-xs text-indigo-300">
            <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
            <span className="font-medium text-[11px]">Inception Mercury-3</span>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3">
          <span className="text-xs font-medium text-slate-400 px-3 py-1.5 rounded-lg bg-slate-800/40 border border-slate-700/50">
            100% Free · Unlimited
          </span>
          <a
            href="https://github.com/yogendra1941/VideoShorts"
            target="_blank"
            rel="noopener noreferrer"
            className="flex items-center gap-2 text-xs font-medium text-slate-300 hover:text-white px-3 py-1.5 rounded-lg bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 transition-colors"
          >
            <Github className="w-3.5 h-3.5" />
            <span>GitHub</span>
            <ExternalLink className="w-3 h-3 text-slate-500" />
          </a>
        </div>

      </div>
    </header>
  );
}
