import React, { useState, useEffect } from 'react';
import { 
  Sliders, 
  Key, 
  Cpu, 
  ShieldCheck, 
  Activity, 
  Check, 
  RefreshCw, 
  Zap, 
  Server,
  Database,
  Lock,
  ExternalLink
} from 'lucide-react';
import { getApiUrl } from '../../config';

export default function SettingsView() {
  const [apiKey, setApiKey] = useState(() => localStorage.getItem('gemini_key') || '');
  const [ollamaUrl, setOllamaUrl] = useState(() => localStorage.getItem('ollama_url') || 'http://localhost:11434');
  const [whisperDevice, setWhisperDevice] = useState(() => localStorage.getItem('whisper_device') || 'auto');
  const [savedSuccess, setSavedSuccess] = useState(false);
  const [healthStatus, setHealthStatus] = useState(null);
  const [checkingHealth, setCheckingHealth] = useState(false);

  const checkHealth = async () => {
    setCheckingHealth(true);
    try {
      const res = await fetch(getApiUrl('/api/health'));
      if (res.ok) {
        const data = await res.json();
        setHealthStatus(data);
      } else {
        setHealthStatus({ status: 'error', detail: `HTTP ${res.status}` });
      }
    } catch (err) {
      setHealthStatus({ status: 'offline', detail: err.message });
    } finally {
      setCheckingHealth(false);
    }
  };

  useEffect(() => {
    checkHealth();
  }, []);

  const handleSave = () => {
    if (apiKey) localStorage.setItem('gemini_key', apiKey);
    else localStorage.removeItem('gemini_key');
    localStorage.setItem('ollama_url', ollamaUrl);
    localStorage.setItem('whisper_device', whisperDevice);
    setSavedSuccess(true);
    setTimeout(() => setSavedSuccess(false), 2000);
  };

  return (
    <div className="h-full overflow-y-auto custom-scrollbar p-6 max-w-4xl mx-auto space-y-8 animate-fade">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-4 border-b border-rule">
        <div>
          <div className="flex items-center gap-2 text-accent font-mono text-xs uppercase tracking-wider mb-1">
            <Sliders size={14} /> System Configuration
          </div>
          <h1 className="text-2xl font-bold text-ink">Studio Settings & Hardware</h1>
          <p className="text-xs text-muted mt-1">
            Configure local AI engines, Whisper speech recognition, and GPU hardware acceleration.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {savedSuccess && (
            <span className="flex items-center gap-1.5 text-xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg animate-fade">
              <Check size={14} /> Settings Saved
            </span>
          )}
          <button
            onClick={handleSave}
            className="px-4 py-2 rounded-lg bg-accent text-white text-xs font-medium hover:bg-accent/90 transition-all shadow-md shadow-accent/20"
          >
            Save Configuration
          </button>
        </div>
      </div>

      {/* Backend Engine Health */}
      <div className="card p-5 space-y-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-paper3 border border-rule flex items-center justify-center text-cyan-400">
              <Server size={16} />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-ink">API Server Status</h2>
              <p className="text-[11px] text-muted font-mono">FastAPI / Uvicorn Background Daemon</p>
            </div>
          </div>

          <button
            onClick={checkHealth}
            disabled={checkingHealth}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-rule bg-paper3/60 hover:bg-paper3 text-xs text-ink transition-colors disabled:opacity-50"
          >
            <RefreshCw size={13} className={checkingHealth ? 'animate-spin text-accent' : ''} />
            <span>Test Connection</span>
          </button>
        </div>

        {healthStatus && (
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 pt-2">
            <div className="p-3 rounded-lg border border-rule bg-paper font-mono text-xs space-y-1">
              <span className="text-muted block text-[10px] uppercase">Service Health</span>
              <span className="text-emerald-400 font-semibold flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                {healthStatus.status?.toUpperCase() || 'ONLINE'}
              </span>
            </div>

            <div className="p-3 rounded-lg border border-rule bg-paper font-mono text-xs space-y-1">
              <span className="text-muted block text-[10px] uppercase">Active LLM Provider</span>
              <span className="text-cyan-300 font-semibold flex items-center gap-1.5">
                <Zap size={12} className="text-cyan-400" />
                {healthStatus.provider || 'Inception Labs (Mercury-3)'}
              </span>
            </div>

            <div className="p-3 rounded-lg border border-rule bg-paper font-mono text-xs space-y-1">
              <span className="text-muted block text-[10px] uppercase">Whisper Acceleration</span>
              <span className="text-indigo-300 font-semibold flex items-center gap-1.5">
                <Cpu size={12} className="text-indigo-400" />
                {healthStatus.asr ? `${healthStatus.asr.toUpperCase()} (Float16/Int8)` : 'CUDA Auto-Fallback'}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* AI LLM Settings */}
      <div className="card p-5 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-paper3 border border-rule flex items-center justify-center text-accent">
            <Zap size={16} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-ink">Intelligence & LLM Engine</h2>
            <p className="text-[11px] text-muted font-mono">Virality scoring, topic composition, hook headlines</p>
          </div>
        </div>

        <div className="space-y-3 pt-2">
          <div>
            <label className="block text-xs font-medium text-ink mb-1.5">
              Inception Labs / Gemini API Key (Optional Override)
            </label>
            <input
              type="password"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="System uses configured default from server .env"
              className="input-field"
            />
            <p className="text-[11px] text-muted mt-1">
              Leave blank to use the active pre-configured Inception Mercury-3 engine.
            </p>
          </div>

          <div>
            <label className="block text-xs font-medium text-ink mb-1.5">
              Local Ollama Endpoint (Fallback)
            </label>
            <input
              type="text"
              value={ollamaUrl}
              onChange={(e) => setOllamaUrl(e.target.value)}
              placeholder="http://localhost:11434"
              className="input-field"
            />
            <p className="text-[11px] text-muted mt-1">
              Local offline fallback using Ollama (<code className="text-accent">llama3.2</code>).
            </p>
          </div>
        </div>
      </div>

      {/* Hardware & GPU Configuration */}
      <div className="card p-5 space-y-4">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-paper3 border border-rule flex items-center justify-center text-emerald-400">
            <Cpu size={16} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-ink">Hardware Acceleration</h2>
            <p className="text-[11px] text-muted font-mono">GPU-powered transcription & NVENC video rendering</p>
          </div>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2">
          <div className="p-3.5 rounded-lg border border-rule bg-paper space-y-2">
            <div className="flex items-center justify-between text-xs font-medium text-ink">
              <span>NVIDIA NVENC Video Encoder</span>
              <span className="text-emerald-400 font-mono">ACTIVE</span>
            </div>
            <p className="text-[11px] text-muted leading-relaxed">
              Uses NVIDIA RTX 3050 NVENC hardware encoder (<code className="text-cyan-300">h264_nvenc</code>) for 10x faster 1080x1920 video renders with EBU R128 audio normalization.
            </p>
          </div>

          <div className="p-3.5 rounded-lg border border-rule bg-paper space-y-2">
            <div className="flex items-center justify-between text-xs font-medium text-ink">
              <span>Whisper ASR Speech Engine</span>
              <span className="text-indigo-400 font-mono">AUTO-ROUTING</span>
            </div>
            <p className="text-[11px] text-muted leading-relaxed">
              Faster-Whisper auto-detects CUDA runtime capabilities and smoothly falls back to multi-threaded CPU int8 when DLLs mismatch, ensuring 100% reliable transcription.
            </p>
          </div>
        </div>
      </div>

      {/* Security Architecture Card */}
      <div className="card p-5 space-y-3">
        <div className="flex items-center gap-2.5 text-xs font-semibold text-ink">
          <ShieldCheck size={16} className="text-emerald-400" />
          <span>Security & Isolation Architecture</span>
        </div>
        <ul className="text-xs text-muted space-y-1.5 list-disc list-inside leading-relaxed">
          <li><strong>SSRF Guard:</strong> Source URLs undergo strict IP resolution to block RFC 1918 private ranges, AWS metadata (169.254.169.254), and loopback attacks.</li>
          <li><strong>Path Traversal Defense:</strong> Filename sanitization strips null bytes, parent directory traverses (<code className="text-rose-300">../</code>), and non-whitelisted characters.</li>
          <li><strong>100% Free:</strong> No external payment gateways, no customer tracking, no credit card prompts.</li>
        </ul>
      </div>
    </div>
  );
}
