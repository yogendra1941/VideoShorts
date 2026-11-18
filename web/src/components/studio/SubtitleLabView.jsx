import React, { useState, useEffect } from 'react';
import { 
  Type, 
  Play, 
  Pause, 
  RotateCcw, 
  Check, 
  Palette, 
  Sliders,
  CheckCircle2
} from 'lucide-react';

const PRESETS = [
  {
    id: 'cyber_neon',
    name: 'Cyber Neon',
    description: 'Electric cyan and neon yellow with deep shadow — high-tech, futuristic retention style.',
    font: 'Montserrat ExtraBold',
    primary: '#06B6D4',
    highlight: '#FACC15',
    outline: '#090D16',
    previewBg: 'from-cyan-950/60 to-slate-900',
    tags: ['Gaming', 'Tech', 'Fast-Paced']
  },
  {
    id: 'hormozi_gold',
    name: 'Hormozi Gold',
    description: 'Alex Hormozi style: punchy yellow karaoke word-pop with heavy outline for maximum readability.',
    font: 'Impact / Anton',
    primary: '#FFFFFF',
    highlight: '#FFE600',
    outline: '#000000',
    previewBg: 'from-amber-950/60 to-slate-900',
    tags: ['Business', 'Podcast', 'Viral Hook']
  },
  {
    id: 'podcast_split',
    name: 'Podcast Split',
    description: 'Dual-tone speaker differentiation for interviews, talk shows and dual-host podcasts.',
    font: 'Inter Bold',
    primary: '#E2E8F0',
    highlight: '#6366F1',
    outline: '#020617',
    previewBg: 'from-indigo-950/60 to-slate-900',
    tags: ['Interviews', 'Long-form', 'Dialogue']
  },
  {
    id: 'bold',
    name: 'Bold Impact',
    description: 'Heavy uppercase text centered on screen for impactful motivational and educational shorts.',
    font: 'Impact',
    primary: '#F8FAFC',
    highlight: '#EF4444',
    outline: '#000000',
    previewBg: 'from-rose-950/60 to-slate-900',
    tags: ['Motivational', 'High Energy']
  },
  {
    id: 'minimal',
    name: 'Minimal Clean',
    description: 'Subtle, aesthetic typography with clean translucent pill container for cinematic clips.',
    font: 'System Clean',
    primary: '#FFFFFF',
    highlight: '#A5B4FC',
    outline: 'rgba(0,0,0,0.5)',
    previewBg: 'from-slate-900 to-slate-950',
    tags: ['Cinematic', 'Aesthetic', 'Vlog']
  },
  {
    id: 'default',
    name: 'Default Studio',
    description: 'Balanced modern studio subtitle with smooth word-by-word active highlighting.',
    font: 'Roboto Bold',
    primary: '#FFFFFF',
    highlight: '#38BDF8',
    outline: '#000000',
    previewBg: 'from-sky-950/60 to-slate-900',
    tags: ['Universal', 'Clean']
  }
];

const DEMO_WORDS = [
  "This", "is", "how", "you", "turn", "any", "long", "video", "into", "viral", "shorts", "with", "VideoShorts."
];

export default function SubtitleLabView() {
  const [selectedPreset, setSelectedPreset] = useState(() => {
    try { return localStorage.getItem('vs_default_brand') || 'cyber_neon'; } catch { return 'cyber_neon'; }
  });
  const [activeWordIndex, setActiveWordIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(true);
  const [savedSuccess, setSavedSuccess] = useState(false);

  // Karaoke loop simulation
  useEffect(() => {
    if (!isPlaying) return;
    const interval = setInterval(() => {
      setActiveWordIndex((prev) => (prev + 1) % DEMO_WORDS.length);
    }, 280);
    return () => clearInterval(interval);
  }, [isPlaying]);

  const currentPresetObj = PRESETS.find((p) => p.id === selectedPreset) || PRESETS[0];

  const handleSelectDefault = (presetId) => {
    setSelectedPreset(presetId);
    try {
      localStorage.setItem('vs_default_brand', presetId);
      setSavedSuccess(true);
      setTimeout(() => setSavedSuccess(false), 2000);
    } catch (_) {}
  };

  return (
    <div className="h-full overflow-y-auto custom-scrollbar p-6 max-w-5xl mx-auto space-y-8 animate-fade">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-rule">
        <div>
          <div className="flex items-center gap-2 text-accent font-mono text-xs uppercase tracking-wider mb-1">
            <Type size={14} /> Subtitle Engineering Lab
          </div>
          <h1 className="text-2xl font-bold text-ink">Bespoke Karaoke Style Presets</h1>
          <p className="text-xs text-muted mt-1 max-w-xl">
            Choose from 6 broadcast-grade ASS dynamic subtitle styles. Subtitles are rendered word-by-word with hardware acceleration.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {savedSuccess && (
            <span className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg animate-fade">
              <Check size={14} /> Preset Saved as Default
            </span>
          )}
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="flex items-center gap-2 px-3.5 py-1.5 rounded-lg border border-rule bg-paper3 hover:bg-paper text-xs font-medium text-ink transition-colors"
          >
            {isPlaying ? <Pause size={14} /> : <Play size={14} />}
            <span>{isPlaying ? 'Pause Karaoke' : 'Play Karaoke'}</span>
          </button>
        </div>
      </div>

      {/* Live 9:16 Mobile Simulation Canvas */}
      <div className="card p-6 flex flex-col items-center justify-center space-y-4">
        <span className="text-xs font-mono text-muted uppercase tracking-wider">
          Live 9:16 Video Canvas Preview
        </span>

        <div className="w-[280px] h-[480px] rounded-2xl border-2 border-rule bg-gradient-to-b from-slate-900 to-black relative overflow-hidden shadow-2xl flex flex-col justify-end p-5 select-none">
          {/* Subtle Ambient Video Simulation */}
          <div className={`absolute inset-0 bg-gradient-to-t ${currentPresetObj.previewBg} opacity-40`} />
          <div className="absolute top-4 left-4 flex items-center gap-1.5 bg-black/60 backdrop-blur-md px-2.5 py-1 rounded-full text-[10px] font-mono text-white/80 border border-white/10">
            <span className="w-1.5 h-1.5 rounded-full bg-rose-500 animate-pulse" />
            9:16 VERTICAL
          </div>

          {/* Subtitle Karaoke Display Box */}
          <div className="relative z-10 text-center mb-10 space-y-1">
            <div className="text-base sm:text-lg font-bold leading-snug tracking-wide flex flex-wrap justify-center gap-1.5">
              {DEMO_WORDS.map((word, idx) => {
                const isHighlight = idx === activeWordIndex;
                return (
                  <span
                    key={idx}
                    style={{
                      color: isHighlight ? currentPresetObj.highlight : currentPresetObj.primary,
                      textShadow: isHighlight 
                        ? `0 0 16px ${currentPresetObj.highlight}80, 2px 2px 0px ${currentPresetObj.outline}` 
                        : `2px 2px 0px ${currentPresetObj.outline}`,
                      transform: isHighlight ? 'scale(1.12)' : 'scale(1.0)',
                      transition: 'all 0.15s ease-out'
                    }}
                    className={`inline-block px-0.5 rounded ${
                      isHighlight ? 'font-black' : 'font-bold'
                    }`}
                  >
                    {word}
                  </span>
                );
              })}
            </div>
            <div className="text-[10px] font-mono text-white/50 pt-3">
              Preset: {currentPresetObj.name} ({currentPresetObj.font})
            </div>
          </div>
        </div>
      </div>

      {/* Presets Grid */}
      <div className="space-y-3">
        <h2 className="text-sm font-semibold text-ink uppercase font-mono tracking-wider">
          Available Preset Library
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {PRESETS.map((preset) => {
            const isSelected = selectedPreset === preset.id;
            return (
              <div
                key={preset.id}
                onClick={() => handleSelectDefault(preset.id)}
                className={`card p-4 cursor-pointer transition-all border flex flex-col justify-between space-y-3 group ${
                  isSelected 
                    ? 'border-accent bg-accent/10 shadow-lg shadow-accent/10' 
                    : 'border-rule hover:border-rule2 hover:bg-paper3/40'
                }`}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <h3 className="font-semibold text-sm text-ink group-hover:text-accent transition-colors flex items-center gap-2">
                      {preset.name}
                      {isSelected && (
                        <CheckCircle2 size={15} className="text-accent" />
                      )}
                    </h3>
                    <div className="flex gap-1.5">
                      <span 
                        className="w-3.5 h-3.5 rounded-full border border-black/40" 
                        style={{ backgroundColor: preset.primary }} 
                        title={`Primary: ${preset.primary}`}
                      />
                      <span 
                        className="w-3.5 h-3.5 rounded-full border border-black/40" 
                        style={{ backgroundColor: preset.highlight }} 
                        title={`Highlight: ${preset.highlight}`}
                      />
                    </div>
                  </div>

                  <p className="text-xs text-muted leading-relaxed">
                    {preset.description}
                  </p>
                </div>

                <div className="pt-2 border-t border-rule flex items-center justify-between">
                  <div className="flex gap-1">
                    {preset.tags.map((t, i) => (
                      <span key={i} className="text-[10px] font-mono px-2 py-0.5 rounded bg-paper3 text-muted">
                        {t}
                      </span>
                    ))}
                  </div>
                  <span className={`text-[11px] font-mono font-medium ${
                    isSelected ? 'text-accent' : 'text-muted group-hover:text-ink'
                  }`}>
                    {isSelected ? 'Active Preset' : 'Set Active'}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
