import React, { useState, useEffect, useRef } from 'react';
import { 
  Activity, 
  Terminal, 
  ChevronDown, 
  Loader2, 
  CheckCircle2, 
  AlertCircle,
  Film,
  TrendingUp,
  Scissors,
  Crosshair,
  Subtitles,
  Cpu
} from 'lucide-react';
import ProcessingAnimation from '../ProcessingAnimation';

const PIPELINE_STAGES = [
  { id: 'ingest', label: 'Ingest & Audio', icon: Film },
  { id: 'whisper', label: 'Faster-Whisper ASR', icon: Activity },
  { id: 'scoring', label: 'Virality Scoring', icon: TrendingUp },
  { id: 'honesty', label: 'Honesty Gate', icon: Scissors },
  { id: 'reframe', label: 'Face Tracking', icon: Crosshair },
  { id: 'render', label: 'NVENC Render', icon: Subtitles },
];

export default function JobStatusPanel({
  status,
  logs = [],
  logTimes = [],
  processingMedia,
  jobError = '',
  onRetry = null,
}) {
  const [logsVisible, setLogsVisible] = useState(true);
  const logContainerRef = useRef(null);

  // Auto-scroll logs terminal
  useEffect(() => {
    if (logContainerRef.current) {
      logContainerRef.current.scrollTop = logContainerRef.current.scrollHeight;
    }
  }, [logs]);

  // Determine active stage from log text
  const currentStageIndex = (() => {
    if (status === 'complete') return 6;
    const allText = logs.join(' ').toLowerCase();
    if (allText.includes('rendering') || allText.includes('nvenc') || allText.includes('subtitle')) return 5;
    if (allText.includes('reframe') || allText.includes('mediapipe') || allText.includes('tracking')) return 4;
    if (allText.includes('honesty') || allText.includes('deep clips') || allText.includes('thread')) return 3;
    if (allText.includes('virality') || allText.includes('scoring') || allText.includes('critic') || allText.includes('hook')) return 2;
    if (allText.includes('transcrib') || allText.includes('whisper')) return 1;
    return 0;
  })();

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Live Pipeline Tracker */}
      <div className="card p-4 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-sm font-semibold text-ink">
            <Activity 
              size={16} 
              className={`text-accent ${status === 'processing' ? 'animate-pulse' : ''}`} 
            />
            <span>Pipeline Telemetry</span>
          </div>
          <span className={`px-2 py-0.5 rounded text-[11px] font-mono font-semibold uppercase ${
            status === 'processing'
              ? 'bg-amber-500/15 text-amber-400 border border-amber-500/30'
              : status === 'complete'
              ? 'bg-emerald-500/15 text-emerald-400 border border-emerald-500/30'
              : 'bg-rose-500/15 text-rose-400 border border-rose-500/30'
          }`}>
            {status}
          </span>
        </div>

        {/* Stage Pills */}
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-1">
          {PIPELINE_STAGES.map((stage, idx) => {
            const Icon = stage.icon;
            const isDone = currentStageIndex > idx;
            const isCurrent = currentStageIndex === idx && status === 'processing';
            return (
              <div
                key={stage.id}
                className={`p-2 rounded-lg border flex items-center gap-2 text-xs transition-all ${
                  isDone
                    ? 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                    : isCurrent
                    ? 'border-accent bg-accent/15 text-accent shadow-sm shadow-accent/10'
                    : 'border-rule bg-paper3/30 text-muted'
                }`}
              >
                {isDone ? (
                  <CheckCircle2 size={14} className="text-emerald-400 shrink-0" />
                ) : isCurrent ? (
                  <Loader2 size={14} className="animate-spin text-accent shrink-0" />
                ) : (
                  <Icon size={14} className="shrink-0 text-muted" />
                )}
                <span className="truncate font-medium">{stage.label}</span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Error Banner */}
      {(status === 'error' || jobError) && (
        <div className="card p-4 border border-rose-500/40 bg-rose-500/10 space-y-2.5 animate-fade">
          <div className="flex items-center gap-2 text-rose-400 font-semibold text-xs">
            <AlertCircle size={16} className="shrink-0" />
            <span>Pipeline Execution Failed</span>
          </div>
          <p className="text-xs text-rose-200 font-mono leading-relaxed break-words">
            {jobError || 'An error occurred during video clipping. Check terminal logs below.'}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="px-3 py-1.5 rounded-lg bg-rose-500/20 hover:bg-rose-500/30 text-rose-300 text-xs font-medium transition-colors"
            >
              Start New Run
            </button>
          )}
        </div>
      )}

      {/* Video Preview Waveform Animation */}
      {processingMedia && (
        <div className="card p-3 overflow-hidden">
          <ProcessingAnimation
            media={processingMedia}
            isComplete={status === 'complete'}
            syncedTime={syncedTime}
            isSyncedPlaying={isSyncedPlaying}
            syncTrigger={syncTrigger}
          />
        </div>
      )}

      {/* Real-time System Terminal */}
      <div className={`card overflow-hidden flex flex-col flex-1 min-h-[220px] transition-all`}>
        <button
          type="button"
          onClick={() => setLogsVisible(!logsVisible)}
          className="w-full px-4 py-2.5 border-b border-rule flex items-center justify-between bg-paper2/90 shrink-0 text-left"
        >
          <div className="flex items-center gap-2 font-mono text-xs text-ink font-medium">
            <Terminal size={14} className="text-cyan-400" />
            <span>Execution Terminal</span>
            {logs.length > 0 && (
              <span className="text-[10px] px-1.5 py-0.2 rounded bg-paper3 text-muted">
                {logs.length} events
              </span>
            )}
          </div>
          <ChevronDown 
            size={16} 
            className={`text-muted transition-transform duration-200 ${logsVisible ? '' : 'rotate-180'}`} 
          />
        </button>

        {logsVisible && (
          <div 
            ref={logContainerRef}
            className="flex-1 p-3.5 overflow-y-auto font-mono text-xs space-y-1.5 custom-scrollbar bg-paper/90 text-slate-300 leading-relaxed"
          >
            {logs.map((log, i) => {
              const isError = log.toLowerCase().includes('error') || log.toLowerCase().includes('failed');
              const isSuccess = log.toLowerCase().includes('complete') || log.toLowerCase().includes('rendered') || log.toLowerCase().includes('ready');
              const timeStr = logTimes[i] ? new Date(logTimes[i] * 1000).toLocaleTimeString() : '';

              return (
                <div key={i} className="flex items-start gap-2 text-[11px]">
                  {timeStr && (
                    <span className="text-muted/60 shrink-0 select-none tabular-nums font-mono">
                      {timeStr}
                    </span>
                  )}
                  <span className={`break-all ${
                    isError 
                      ? 'text-rose-400 font-semibold' 
                      : isSuccess 
                      ? 'text-emerald-400 font-medium' 
                      : 'text-slate-300'
                  }`}>
                    {log}
                  </span>
                </div>
              );
            })}

            {status === 'processing' && (
              <div className="flex items-center gap-2 text-accent text-xs pt-1">
                <span className="animate-pulse">▶</span>
                <span className="animate-pulse text-muted">Awaiting pipeline thread response...</span>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
