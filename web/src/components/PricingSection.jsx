import React from 'react';
import { Check, Zap, Cpu, ShieldCheck, Flame, ArrowRight, Lock } from 'lucide-react';

export default function PricingSection({ onLaunchApp }) {
  return (
    <section id="pricing" className="py-20 border-t border-rule bg-paper2/30">
      <div className="max-w-6xl mx-auto px-6">
        <div className="text-center max-w-2xl mx-auto mb-16">
          <p className="eyebrow mb-2 text-accent uppercase font-mono text-xs">100% FREE · NO SUBSCRIPTIONS</p>
          <h2 className="font-display text-3xl sm:text-4xl text-ink font-bold tracking-tight mb-4">
            Zero Paywalls. No Minutes Cap.
          </h2>
          <p className="text-muted text-sm sm:text-base leading-relaxed">
            Commercial clipping apps charge $20 to $50 every month and cap your video minutes. 
            VideoShorts runs directly on your hardware with unlimited 1080p exports and zero watermarks.
          </p>
        </div>

        {/* Comparison Grid */}
        <div className="grid md:grid-cols-3 gap-6 items-stretch mb-12">
          {/* Opus Clip */}
          <div className="card p-6 border-rule/60 bg-paper/60 flex flex-col justify-between opacity-80 hover:opacity-100 transition-opacity">
            <div>
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm font-semibold text-muted">Opus Clip</span>
                <span className="text-xs px-2 py-0.5 rounded bg-paper3 text-muted font-mono">$29/mo</span>
              </div>
              <ul className="space-y-3 text-xs text-muted">
                <li className="flex items-center gap-2 text-rose-400">✕ 60–150 min monthly ceiling</li>
                <li className="flex items-center gap-2 text-rose-400">✕ Watermarked on free plan</li>
                <li className="flex items-center gap-2 text-rose-400">✕ Slow cloud server render queues</li>
                <li className="flex items-center gap-2 text-rose-400">✕ 720p resolution cap on basic</li>
                <li className="flex items-center gap-2 text-ink2">✓ Face tracking</li>
                <li className="flex items-center gap-2 text-ink2">✓ Auto captions</li>
              </ul>
            </div>
            <div className="pt-6 mt-6 border-t border-rule/50 text-center">
              <span className="text-xs text-muted font-mono">Paid Cloud SaaS</span>
            </div>
          </div>

          {/* VideoShorts 2.0 (Hero Featured) */}
          <div className="card p-7 border-accent bg-gradient-to-b from-accent/15 via-paper2 to-paper ring-1 ring-accent/30 shadow-xl shadow-accent/10 flex flex-col justify-between relative overflow-hidden">
            <div className="absolute top-0 right-0 px-3 py-1 bg-accent text-white font-mono text-[10px] font-bold uppercase rounded-bl-lg tracking-wider">
              YOUR ENGINE
            </div>
            <div>
              <div className="flex justify-between items-center mb-4">
                <div>
                  <span className="text-base font-bold text-ink flex items-center gap-2">
                    VideoShorts 2.0
                  </span>
                  <p className="text-[11px] text-muted font-mono">Local Studio Edition</p>
                </div>
                <div className="text-right">
                  <span className="text-xl font-bold text-accent font-display">$0</span>
                  <span className="text-xs text-muted block font-mono">FREE FOREVER</span>
                </div>
              </div>

              <ul className="space-y-3 text-xs text-ink pt-2 font-medium">
                <li className="flex items-center gap-2 text-emerald-400">
                  <Check size={14} className="shrink-0 stroke-[2.5]" />
                  <span><strong>Unlimited Videos & Minutes</strong> — Zero caps</span>
                </li>
                <li className="flex items-center gap-2 text-emerald-400">
                  <Check size={14} className="shrink-0 stroke-[2.5]" />
                  <span><strong>Zero Watermarks</strong> — 100% Clean Exports</span>
                </li>
                <li className="flex items-center gap-2 text-emerald-400">
                  <Check size={14} className="shrink-0 stroke-[2.5]" />
                  <span><strong>NVIDIA RTX 3050 CUDA</strong> + NVENC Hardware Render</span>
                </li>
                <li className="flex items-center gap-2 text-emerald-400">
                  <Check size={14} className="shrink-0 stroke-[2.5]" />
                  <span><strong>Faster-Whisper ASR</strong> with word timestamps</span>
                </li>
                <li className="flex items-center gap-2 text-emerald-400">
                  <Check size={14} className="shrink-0 stroke-[2.5]" />
                  <span><strong>Inception Mercury-3 AI</strong> Moment Picker</span>
                </li>
                <li className="flex items-center gap-2 text-emerald-400">
                  <Check size={14} className="shrink-0 stroke-[2.5]" />
                  <span><strong>OpenShorts VAD Silence Snapping</strong> (no cut words)</span>
                </li>
                <li className="flex items-center gap-2 text-emerald-400">
                  <Check size={14} className="shrink-0 stroke-[2.5]" />
                  <span><strong>PySceneDetect Face Tracking</strong> (9:16 Portrait Lock)</span>
                </li>
              </ul>
            </div>

            <div className="pt-6 mt-6 border-t border-accent/20">
              <button
                onClick={onLaunchApp}
                className="w-full py-3 rounded-xl bg-accent hover:bg-accent/90 text-white font-medium text-xs flex items-center justify-center gap-2 transition-all shadow-md shadow-accent/25 hover:shadow-lg"
              >
                <span>Launch Clips Studio</span>
                <ArrowRight size={14} />
              </button>
            </div>
          </div>

          {/* Submagic */}
          <div className="card p-6 border-rule/60 bg-paper/60 flex flex-col justify-between opacity-80 hover:opacity-100 transition-opacity">
            <div>
              <div className="flex justify-between items-center mb-4">
                <span className="text-sm font-semibold text-muted">Submagic</span>
                <span className="text-xs px-2 py-0.5 rounded bg-paper3 text-muted font-mono">$20/mo</span>
              </div>
              <ul className="space-y-3 text-xs text-muted">
                <li className="flex items-center gap-2 text-rose-400">✕ 10 videos/mo strict limit</li>
                <li className="flex items-center gap-2 text-rose-400">✕ Watermark branding on free trial</li>
                <li className="flex items-center gap-2 text-rose-400">✕ Subscription billing trap</li>
                <li className="flex items-center gap-2 text-rose-400">✕ Upload queue latency</li>
                <li className="flex items-center gap-2 text-ink2">✓ Animated captions</li>
                <li className="flex items-center gap-2 text-ink2">✓ B-roll overlays</li>
              </ul>
            </div>
            <div className="pt-6 mt-6 border-t border-rule/50 text-center">
              <span className="text-xs text-muted font-mono">Paid Cloud SaaS</span>
            </div>
          </div>
        </div>

        {/* Privacy & Hardware Assurance */}
        <div className="card p-6 border-rule/60 bg-paper3/30 flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400 shrink-0">
              <ShieldCheck size={20} />
            </div>
            <div>
              <h4 className="text-sm font-semibold text-ink">100% Private & Locally Processed</h4>
              <p className="text-xs text-muted">Your videos never touch remote subscription servers. Transcribed and rendered locally on your PC.</p>
            </div>
          </div>
          <button
            onClick={onLaunchApp}
            className="px-4 py-2 rounded-lg bg-paper2 hover:bg-paper text-ink border border-rule text-xs font-medium whitespace-nowrap transition-colors"
          >
            Start Clipping
          </button>
        </div>
      </div>
    </section>
  );
}
