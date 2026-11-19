import React, { useState, useEffect, useMemo } from 'react';
import { Loader2, Download, Film, FolderOpen, Trash2, Folder } from 'lucide-react';
import { apiJson, apiFetch } from '../lib/api';

// Clip Vault: Shows local rendered clips stored in VideoShorts/output
export default function HistoryTab({ onReopenProject }) {
  const [videos, setVideos] = useState(null);
  const [projects, setProjects] = useState({});
  const [reopening, setReopening] = useState(null);
  const [reopenError, setReopenError] = useState('');
  const [error, setError] = useState('');
  const [deleting, setDeleting] = useState(false);

  const fetchVideos = () => {
    apiJson('/api/history')
      .then((d) => setVideos(d.videos || []))
      .catch(() => setError('Could not load your clips vault.'));
    apiJson('/api/projects')
      .then((d) => {
        const map = {};
        for (const p of d.projects || []) map[p.job_id] = p;
        setProjects(map);
      })
      .catch(() => {});
  };

  useEffect(() => {
    fetchVideos();
  }, []);

  const handleClearAll = async () => {
    if (!window.confirm("Are you sure you want to delete all clips from Clip Vault?")) return;
    setDeleting(true);
    try {
      await apiFetch('/api/history', { method: 'DELETE' });
      setVideos([]);
    } catch (e) {
      setError('Failed to clear vault.');
    } finally {
      setDeleting(false);
    }
  };

  const handleDeleteClip = async (filename) => {
    if (!window.confirm(`Delete ${filename}?`)) return;
    try {
      await apiFetch(`/api/history/${filename}`, { method: 'DELETE' });
      setVideos((prev) => prev.filter((v) => v.filename !== filename));
    } catch (e) {
      alert('Failed to delete clip.');
    }
  };

  // Group videos by job, preserving the newest-first order of /api/history.
  const groups = useMemo(() => {
    const byJob = new Map();
    for (const v of videos || []) {
      const key = v.job_id || v.id;
      if (!byJob.has(key)) byJob.set(key, []);
      byJob.get(key).push(v);
    }
    return [...byJob.entries()];
  }, [videos]);

  const handleReopen = async (jobId) => {
    if (!onReopenProject || reopening) return;
    setReopening(jobId);
    setReopenError('');
    try {
      await onReopenProject(jobId);
    } catch (e) {
      setReopenError('Could not reopen this project. Please try again.');
      setReopening(null);
    }
  };

  const fmtDate = (iso) => (iso ? new Date(iso * 1000).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' }) : '');

  if (videos === null && !error) {
    return <div className="flex justify-center py-20"><Loader2 className="animate-spin text-accent" /></div>;
  }

  return (
    <div className="h-full overflow-y-auto p-8 max-w-5xl mx-auto animate-fade">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div>
          <p className="eyebrow mb-1 text-accent font-mono text-xs uppercase">VAULT · OUTPUT STORAGE</p>
          <h1 className="font-display text-2xl font-bold text-ink mb-1">Local Clip Vault</h1>
          <p className="text-muted text-xs font-mono">
            Output folder: <code className="px-1.5 py-0.5 rounded bg-paper3 text-ink">D:\Video Clips\VideoShorts\output</code> (100% Free · No Limits)
          </p>
        </div>

        {videos && videos.length > 0 && (
          <button
            onClick={handleClearAll}
            disabled={deleting}
            className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 text-xs font-medium transition-colors"
          >
            <Trash2 size={14} /> Clear Vault (Delete All)
          </button>
        )}
      </div>

      {error && <p className="text-danger text-sm mb-4">{error}</p>}
      {reopenError && <p className="text-danger text-sm mb-4">{reopenError}</p>}

      {videos && videos.length === 0 && (
        <div className="card p-12 text-center text-muted border border-dashed border-rule">
          <Film size={44} className="mx-auto mb-3 text-muted/60" />
          <h3 className="text-base font-semibold text-ink mb-1">Clip Vault is empty</h3>
          <p className="text-xs text-muted max-w-md mx-auto mb-4">
            All previous test clips have been deleted. When you process a video in Clips Studio, your finished vertical shorts will appear here and in your output directory.
          </p>
        </div>
      )}

      <div className="space-y-8">
        {groups.map(([jobId, vids]) => {
          const project = projects[jobId];
          return (
            <section key={jobId} className="card p-5">
              <div className="flex flex-wrap items-center justify-between gap-3 mb-4 pb-3 border-b border-rule">
                <div>
                  <p className="text-sm text-ink font-semibold truncate" title={project?.title || vids[0]?.filename}>
                    {project?.title || `Batch: ${jobId}`}
                  </p>
                  <p className="text-xs text-muted font-mono mt-0.5">
                    {fmtDate(vids[0]?.created_at)} · {vids.length} clip{vids.length === 1 ? '' : 's'}
                  </p>
                </div>
                {project && onReopenProject && (
                  <button
                    onClick={() => handleReopen(jobId)}
                    disabled={!!reopening}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded bg-paper3 hover:bg-paper2 text-xs font-medium text-ink transition-colors border border-rule"
                  >
                    {reopening === jobId
                      ? <><Loader2 size={13} className="animate-spin" /> reopening…</>
                      : <><FolderOpen size={13} /> Reopen in Studio</>}
                  </button>
                )}
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                {vids.map((v) => (
                  <div key={v.id} className="card overflow-hidden border border-rule/60 bg-paper2 flex flex-col">
                    <div className="aspect-[9/16] bg-black relative">
                      <video src={v.url} controls preload="metadata" className="w-full h-full object-contain" />
                    </div>
                    <div className="p-3 flex-1 flex flex-col justify-between">
                      <p className="text-xs text-ink font-medium truncate mb-2" title={v.filename}>
                        {v.filename}
                      </p>
                      <div className="flex items-center justify-between pt-2 border-t border-rule/40 text-xs">
                        <a 
                          href={v.url} 
                          download={v.filename}
                          className="flex items-center gap-1 text-accent hover:underline font-mono"
                        >
                          <Download size={13} /> Download
                        </a>
                        <button
                          onClick={() => handleDeleteClip(v.filename)}
                          className="flex items-center gap-1 text-rose-400 hover:text-rose-300 font-mono text-[11px]"
                        >
                          <Trash2 size={12} /> Delete
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </section>
          );
        })}
      </div>
    </div>
  );
}
