import React, { useState, useEffect, useRef, useMemo } from 'react';
import { 
  Film, 
  Youtube, 
  Instagram, 
  AlertTriangle, 
  CheckCircle2, 
  Loader2, 
  Download
} from 'lucide-react';

import StudioSidebar from './components/studio/StudioSidebar';
import StudioHeader from './components/studio/StudioHeader';
import JobStatusPanel from './components/studio/JobStatusPanel';
import ResultsGrid from './components/studio/ResultsGrid';
import SubtitleLabView from './components/studio/SubtitleLabView';
import SettingsView from './components/studio/SettingsView';
import AiAgentView from './components/studio/AiAgentView';
import MediaInput from './components/MediaInput';
import HistoryTab from './components/HistoryTab';
import ClipEditor from './components/ClipEditor';
import ReframeEditor from './components/ReframeEditor';
import ScheduleWeekModal from './components/ScheduleWeekModal';

import { getApiUrl } from './config';
import { apiFetch } from './lib/api';

const TikTokIcon = ({ size = 16, className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M19.589 6.686a4.793 4.793 0 0 1-3.77-4.245V2h-3.445v13.672a2.896 2.896 0 0 1-5.201 1.743l-.002-.001.002.001a2.895 2.895 0 0 1 3.183-4.51v-3.5a6.329 6.329 0 0 0-5.394 10.692 6.33 6.33 0 0 0 10.857-4.424V8.687a8.182 8.182 0 0 0 4.773 1.526V6.79a4.831 4.831 0 0 1-1.003-.104z" />
  </svg>
);

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [status, setStatus] = useState('idle'); // 'idle' | 'processing' | 'complete' | 'error'
  const [jobId, setJobId] = useState(null);
  const [results, setResults] = useState(null);
  const [logs, setLogs] = useState([]);
  const [logTimes, setLogTimes] = useState([]);
  const [processingMedia, setProcessingMedia] = useState(null);
  const [editingClip, setEditingClip] = useState(null);
  const [reframingClip, setReframingClip] = useState(null);
  const [showScheduleWeek, setShowScheduleWeek] = useState(false);
  const [downloadingAll, setDownloadingAll] = useState(false);
  const [jobError, setJobError] = useState('');

  // Ranked clips calculation (highest predicted score first)
  const rankedClips = useMemo(() => {
    const clips = results?.clips;
    if (!Array.isArray(clips)) return [];
    return clips
      .map((clip, index) => ({ clip, index }))
      .sort((a, b) => {
        const sa = Number.isFinite(a.clip?.predicted_score) ? a.clip.predicted_score : -1;
        const sb = Number.isFinite(b.clip?.predicted_score) ? b.clip.predicted_score : -1;
        return sb - sa || a.index - b.index;
      });
  }, [results]);

  // Handle job status polling
  useEffect(() => {
    if (status !== 'processing' || !jobId) return;

    let isMounted = true;
    const interval = setInterval(async () => {
      try {
        const res = await apiFetch(`/api/status/${jobId}`);
        if (!res.ok) return;
        const data = await res.json();

        if (!isMounted) return;

        if (Array.isArray(data.logs) && data.logs.length > 0) {
          setLogs(data.logs);
          setLogTimes(data.logs.map(() => Date.now() / 1000));
        }

        if (data.status === 'complete' || data.status === 'completed') {
          setStatus('complete');
          setResults({ clips: data.clips || [] });
          clearInterval(interval);
        } else if (data.status === 'error' || data.status === 'failed') {
          setStatus('error');
          setJobError(data.error || 'Job failed during execution.');
          clearInterval(interval);
        }
      } catch (err) {
        console.error('Job polling error:', err);
      }
    }, 2000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [status, jobId]);

  // Reset current workspace to start a new job
  const handleReset = () => {
    setStatus('idle');
    setJobId(null);
    setResults(null);
    setLogs([]);
    setLogTimes([]);
    setProcessingMedia(null);
    setJobError('');
  };

  // Launch clipping job
  const handleProcess = async (data) => {
    setStatus('processing');
    setJobError('');
    setLogs(['Initiating VideoShorts AI pipeline...']);
    setLogTimes([Date.now() / 1000]);
    setResults(null);
    setProcessingMedia(data.type === 'file' ? data : null);

    try {
      let body;
      const headers = {};

      const advanced = {
        clips: data.targetClips ? parseInt(data.targetClips, 10) : 3,
        brand: data.brand || 'default',
        enableHonesty: data.enableHonesty !== false,
        enableDeepClips: data.enableDeepClips !== false,
        layouts: data.layout && data.layout !== 'auto' ? data.layout : null,
      };

      if (data.type === 'url') {
        headers['Content-Type'] = 'application/json';
        body = JSON.stringify({
          url: data.payload,
          ...advanced
        });
      } else {
        const formData = new FormData();
        formData.append('file', data.payload);
        formData.append('clips', String(advanced.clips));
        formData.append('brand', advanced.brand);
        formData.append('enableHonesty', String(advanced.enableHonesty));
        formData.append('enableDeepClips', String(advanced.enableDeepClips));
        if (advanced.layouts) formData.append('layouts', advanced.layouts);
        body = formData;
      }

      const res = await apiFetch('/api/process', {
        method: 'POST',
        headers,
        body
      });

      if (!res.ok) {
        const errText = await res.text();
        throw new Error(errText || 'Failed to initialize processing job');
      }

      const resData = await res.json();
      setJobId(resData.job_id || resData.id);
      setLogs((prev) => [...prev, `Job queued with ID #${resData.job_id || resData.id}`]);

    } catch (err) {
      console.error('Submission error:', err);
      setStatus('error');
      setJobError(err.message || 'Could not start processing.');
      setLogs((prev) => [...prev, `Error: ${err.message}`]);
    }
  };

  // Download all clips as a single ZIP archive
  const handleDownloadAll = async () => {
    if (!jobId) return;
    setDownloadingAll(true);
    try {
      const downloadUrl = getApiUrl(`/api/download-all/${jobId}`);
      const link = document.createElement('a');
      link.href = downloadUrl;
      link.setAttribute('download', `videoshorts_${jobId}.zip`);
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
    } catch (err) {
      console.error('ZIP download error:', err);
    } finally {
      setDownloadingAll(false);
    }
  };

  return (
    <div className="flex h-screen bg-paper text-ink overflow-hidden select-none">
      {/* Sidebar Navigation */}
      <StudioSidebar
        activeTab={activeTab}
        onSelectTab={setActiveTab}
        status={status}
      />

      {/* Main Workspace */}
      <main className="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative">
        {/* Header Telemetry Bar */}
        <StudioHeader
          activeTab={activeTab}
          onReset={handleReset}
          status={status}
        />

        {/* Dynamic Workspace Container */}
        <div className="flex-1 overflow-hidden relative bg-paper">
          {/* TAB: CLIPS STUDIO (DASHBOARD) */}
          {activeTab === 'dashboard' && status === 'idle' && (
            <div className="h-full overflow-y-auto custom-scrollbar flex flex-col items-center justify-center p-6 animate-fade">
              <div className="max-w-xl w-full text-center space-y-6">
                <div className="space-y-3">
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-accent/30 bg-accent/10 text-accent font-mono text-xs uppercase">
                    <Film size={13} /> High-Precision Video Repurposing
                  </div>
                  <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-ink font-display">
                    Transform Long Videos into Viral Shorts
                  </h2>
                  <p className="text-xs sm:text-sm text-muted max-w-md mx-auto leading-relaxed">
                    Paste any YouTube URL or drop your video. Faster-Whisper transcribes, Inception Mercury-3 extracts hooks, and MediaPipe reframes to 9:16 vertical video.
                  </p>
                </div>

                {/* Media Input Component */}
                <MediaInput
                  onProcess={handleProcess}
                  isProcessing={false}
                />

                {/* Platform Badges */}
                <div className="flex items-center justify-center gap-6 text-muted text-xs font-medium">
                  <span className="flex items-center gap-1.5"><Youtube size={15} className="text-rose-400" /> YouTube Shorts</span>
                  <span className="flex items-center gap-1.5"><Instagram size={15} className="text-pink-400" /> Reels</span>
                  <span className="flex items-center gap-1.5"><TikTokIcon size={14} className="text-cyan-400" /> TikTok</span>
                </div>
              </div>
            </div>
          )}

          {/* TAB: CLIPS STUDIO (PROCESSING / COMPLETED SPLIT VIEW) */}
          {activeTab === 'dashboard' && status !== 'idle' && (
            <div className="h-full flex flex-col lg:flex-row gap-4 p-4 overflow-hidden animate-fade">
              {/* Left Column: Telemetry & System Logs */}
              <div className={`${status === 'complete' ? 'w-full lg:w-[32%]' : 'w-full lg:w-[50%]'} h-full transition-all duration-500`}>
                <JobStatusPanel
                  status={status}
                  logs={logs}
                  logTimes={logTimes}
                  processingMedia={processingMedia}
                />
              </div>

              {/* Right Column: Generated Bento Results Grid */}
              <div className={`${status === 'complete' ? 'w-full lg:w-[68%]' : 'w-full lg:w-[50%]'} h-full transition-all duration-500`}>
                <ResultsGrid
                  results={results}
                  rankedClips={rankedClips}
                  jobId={jobId}
                  status={status}
                  onEditClip={(index) => setEditingClip(index)}
                  onReframeClip={(index) => setReframingClip(index)}
                  onClipRerendered={() => {}}
                  onDownloadAll={handleDownloadAll}
                  downloadingAll={downloadingAll}
                  onScheduleWeek={() => setShowScheduleWeek(true)}
                />
              </div>
            </div>
          )}

          {/* TAB: SUBTITLE LAB */}
          {activeTab === 'subtitles' && (
            <SubtitleLabView />
          )}

          {/* TAB: CLIP VAULT (HISTORY) */}
          {activeTab === 'history' && (
            <div className="h-full overflow-y-auto custom-scrollbar p-6 max-w-5xl mx-auto">
              <HistoryTab
                onReopenProject={async (id) => {
                  setJobId(id);
                  setStatus('processing');
                  setActiveTab('dashboard');
                }}
              />
            </div>
          )}

          {/* TAB: AUTONOMOUS AGENT */}
          {activeTab === 'agent' && (
            <AiAgentView />
          )}

          {/* TAB: STUDIO CONFIGURATION */}
          {activeTab === 'settings' && (
            <SettingsView />
          )}
        </div>
      </main>

      {/* MODAL: Word-Level Subtitle Clip Editor */}
      {editingClip !== null && results?.clips?.[editingClip] && (
        <ClipEditor
          jobId={jobId}
          clipIndex={editingClip}
          clipTitle={results.clips[editingClip].video_title_for_youtube_short || ''}
          onClose={() => setEditingClip(null)}
        />
      )}

      {/* MODAL: Smart Reframe Crop Editor */}
      {reframingClip !== null && results?.clips?.[reframingClip] && (
        <ReframeEditor
          jobId={jobId}
          clipIndex={reframingClip}
          onClose={() => setReframingClip(null)}
        />
      )}

      {/* MODAL: Content Calendar / Schedule Week */}
      {showScheduleWeek && results?.clips && (
        <ScheduleWeekModal
          clips={results.clips}
          onClose={() => setShowScheduleWeek(false)}
        />
      )}
    </div>
  );
}
