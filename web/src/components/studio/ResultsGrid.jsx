import React, { useState } from 'react';
import { 
  Download, 
  Calendar, 
  Loader2, 
  Share2, 
  CheckCircle2, 
  Film,
  Zap,
  SlidersHorizontal
} from 'lucide-react';
import ResultCard from '../ResultCard';
import SocialPublishModal from './SocialPublishModal';

export default function ResultsGrid({
  results,
  rankedClips = [],
  jobId,
  status,
  onEditClip,
  onReframeClip,
  onClipRerendered,
  onDownloadAll,
  downloadingAll = false,
  onScheduleWeek
}) {
  const [socialModalClip, setSocialModalClip] = useState(null);
  const [socialModalIndex, setSocialModalIndex] = useState(0);

  const clips = results?.clips || [];

  return (
    <div className="flex flex-col h-full space-y-4">
      {/* Top Action Bar */}
      <div className="card p-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 shrink-0">
        <div className="flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-accent/15 border border-accent/30 flex items-center justify-center text-accent">
            <Film size={16} />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-ink flex items-center gap-2">
              Generated AI Shorts
              <span className="px-2 py-0.5 rounded-full bg-paper3 font-mono text-[11px] text-accent font-medium">
                {clips.length} {clips.length === 1 ? 'Clip' : 'Clips'}
              </span>
            </h2>
            <p className="text-[11px] text-muted font-mono">
              Ranked by predicted audience retention & engagement
            </p>
          </div>
        </div>

        {clips.length > 0 && (
          <div className="flex items-center gap-2">
            <button
              onClick={onDownloadAll}
              disabled={downloadingAll}
              className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg border border-rule bg-paper3/60 hover:bg-paper3 text-xs font-medium text-ink transition-colors disabled:opacity-50 shadow-sm"
              title="Download all clips in a single ZIP"
            >
              {downloadingAll ? (
                <>
                  <Loader2 size={14} className="animate-spin text-accent" />
                  <span>Archiving ZIP...</span>
                </>
              ) : (
                <>
                  <Download size={14} className="text-accent" />
                  <span>Download All</span>
                </>
              )}
            </button>

            {clips.length > 1 && onScheduleWeek && (
              <button
                onClick={onScheduleWeek}
                className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-accent text-white text-xs font-medium hover:bg-accent/90 transition-all shadow-md shadow-accent/20"
              >
                <Calendar size={14} />
                <span>Schedule Week</span>
              </button>
            )}
          </div>
        )}
      </div>

      {/* Grid of Result Cards */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-1">
        {clips.length === 0 ? (
          <div className="h-64 flex flex-col items-center justify-center text-center p-6 border-2 border-dashed border-rule rounded-2xl">
            <Film size={32} className="text-muted/40 mb-3" />
            <p className="text-sm text-ink font-medium">No clips rendered yet</p>
            <p className="text-xs text-muted max-w-sm mt-1">
              Submit a video or URL on the left to extract viral vertical shorts.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 pb-12 grid-cols-1 md:grid-cols-2 xl:grid-cols-3">
            {rankedClips.map(({ clip, index: i }) => (
              <div key={`${jobId}-${i}`} className="flex flex-col space-y-2">
                <ResultCard
                  clip={clip}
                  index={i}
                  jobId={jobId}
                  onEditClip={onEditClip}
                  onReframeClip={onReframeClip}
                  onModeChanged={status === 'processing' ? null : onClipRerendered}
                />
                
                {/* Custom Quick Action: Social Copy */}
                <button
                  onClick={() => {
                    setSocialModalClip(clip);
                    setSocialModalIndex(i);
                  }}
                  className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg border border-rule bg-paper2 hover:bg-paper3 text-xs text-ink2 hover:text-ink font-medium transition-colors"
                >
                  <Share2 size={13} className="text-accent" />
                  <span>View TikTok / Reels / Shorts Copy</span>
                </button>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Social Publish Modal */}
      <SocialPublishModal
        isOpen={Boolean(socialModalClip)}
        onClose={() => setSocialModalClip(null)}
        clip={socialModalClip}
        index={socialModalIndex}
      />
    </div>
  );
}
