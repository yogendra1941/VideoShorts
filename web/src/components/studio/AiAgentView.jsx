import React from 'react';
import { 
  Bot, 
  Upload, 
  Users, 
  CheckCircle2, 
  ExternalLink, 
  Copy, 
  Check, 
  Terminal, 
  Sparkles,
  Zap,
  ArrowRight,
  FolderSync
} from 'lucide-react';

export default function AiAgentView() {
  const [copied, setCopied] = React.useState(false);

  const command = 'python main.py "YOUR_VIDEO_URL" --clips 3 --brand cyber_neon';

  const handleCopy = () => {
    navigator.clipboard.writeText(command);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="h-full overflow-y-auto custom-scrollbar p-6 max-w-4xl mx-auto space-y-8 animate-fade">
      {/* Header */}
      <div className="space-y-3 pb-4 border-b border-rule">
        <div className="flex items-center gap-2 text-accent font-mono text-xs uppercase tracking-wider">
          <Bot size={14} /> Autonomous CLI & Agent Integration
        </div>
        <h1 className="text-3xl font-bold text-ink">Autonomous Video Clipping Agent</h1>
        <p className="text-sm text-muted max-w-2xl leading-relaxed">
          Automate your vertical content pipeline. Feed raw YouTube URLs, Twitch streams, or local files directly into the VideoShorts CLI, or connect Claude Code and Python workflows.
        </p>
      </div>

      {/* 3 Step Workflow */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card p-5 space-y-3 border-rule hover:border-accent/40 transition-colors">
          <div className="w-10 h-10 rounded-xl bg-accent/15 border border-accent/30 flex items-center justify-center text-accent">
            <Upload size={18} />
          </div>
          <h3 className="font-semibold text-sm text-ink">1. Input Stream / File</h3>
          <p className="text-xs text-muted leading-relaxed">
            Feed any YouTube link or local MP4. The ingestion engine extracts audio and runs scene boundary cuts.
          </p>
        </div>

        <div className="card p-5 space-y-3 border-rule hover:border-cyan-500/40 transition-colors">
          <div className="w-10 h-10 rounded-xl bg-cyan-500/15 border border-cyan-500/30 flex items-center justify-center text-cyan-400">
            <Zap size={18} />
          </div>
          <h3 className="font-semibold text-sm text-ink">2. 4D Virality Engine</h3>
          <p className="text-xs text-muted leading-relaxed">
            Whisper transcribes, Inception Mercury-3 scores 4 virality dimensions, and the honesty gate purges fluff.
          </p>
        </div>

        <div className="card p-5 space-y-3 border-rule hover:border-emerald-500/40 transition-colors">
          <div className="w-10 h-10 rounded-xl bg-emerald-500/15 border border-emerald-500/30 flex items-center justify-center text-emerald-400">
            <CheckCircle2 size={18} />
          </div>
          <h3 className="font-semibold text-sm text-ink">3. Reframed 9:16 Shorts</h3>
          <p className="text-xs text-muted leading-relaxed">
            MediaPipe tracks speakers, FFmpeg NVENC renders 1080x1920 video with dynamic ASS karaoke subtitles.
          </p>
        </div>
      </div>

      {/* Terminal Command Card */}
      <div className="card p-6 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-mono text-muted uppercase">
            <Terminal size={14} className="text-cyan-400" /> CLI Execution Shortcut
          </div>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 text-xs text-accent hover:text-ink transition-colors font-mono"
          >
            {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
            <span>{copied ? 'Copied' : 'Copy Command'}</span>
          </button>
        </div>

        <div className="p-4 rounded-xl bg-paper border border-rule font-mono text-xs text-cyan-300 overflow-x-auto">
          <code>{command}</code>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs text-muted font-mono pt-2">
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-accent" />
            <span>--brand cyber_neon (Style preset)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-accent" />
            <span>--clips 3 (Number of shorts to render)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-accent" />
            <span>--no-honesty (Bypass honesty filter)</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="w-1.5 h-1.5 rounded-full bg-accent" />
            <span>--help (Show all flags)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
