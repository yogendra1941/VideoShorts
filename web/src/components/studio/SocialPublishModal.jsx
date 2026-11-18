import React, { useState } from 'react';
import { 
  X, 
  Copy, 
  Check, 
  Share2, 
  Youtube, 
  Instagram, 
  Flame,
  Hash,
  MessageSquare
} from 'lucide-react';

const TikTokIcon = ({ size = 16, className = "" }) => (
  <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor" className={className}>
    <path d="M19.589 6.686a4.793 4.793 0 0 1-3.77-4.245V2h-3.445v13.672a2.896 2.896 0 0 1-5.201 1.743l-.002-.001.002.001a2.895 2.895 0 0 1 3.183-4.51v-3.5a6.329 6.329 0 0 0-5.394 10.692 6.33 6.33 0 0 0 10.857-4.424V8.687a8.182 8.182 0 0 0 4.773 1.526V6.79a4.831 4.831 0 0 1-1.003-.104z" />
  </svg>
);

export default function SocialPublishModal({ isOpen, onClose, clip, index }) {
  const [platform, setPlatform] = useState('tiktok');
  const [copied, setCopied] = useState(false);

  if (!isOpen || !clip) return null;

  const social = clip.social || {};
  const currentData = social[platform] || {
    title: clip.title || `Viral Short #${index + 1}`,
    caption: clip.text ? clip.text.slice(0, 180) + '...' : 'Watch until the end! 🔥',
    hashtags: ['#shorts', '#viral', '#fyp', '#trending'],
    character_count: 120
  };

  const copyText = `${currentData.title ? currentData.title + '\n\n' : ''}${currentData.caption || ''}\n\n${(currentData.hashtags || []).join(' ')}`;

  const handleCopy = () => {
    navigator.clipboard.writeText(copyText);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/75 backdrop-blur-sm animate-fade">
      <div className="w-full max-w-xl card border border-rule bg-paper2/95 shadow-2xl rounded-2xl overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-6 py-4 border-b border-rule flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-accent/15 border border-accent/30 flex items-center justify-center text-accent">
              <Share2 size={16} />
            </div>
            <div>
              <h2 className="text-sm font-semibold text-ink">Viral Social Copy</h2>
              <p className="text-[11px] text-muted font-mono">Clip #{index + 1} · Multi-Platform Formats</p>
            </div>
          </div>
          <button 
            onClick={onClose}
            className="p-1.5 rounded-lg text-muted hover:text-ink hover:bg-paper3 transition-colors"
          >
            <X size={18} />
          </button>
        </div>

        {/* Platform Tabs */}
        <div className="flex border-b border-rule bg-paper3/40 p-1 gap-1">
          {[
            { id: 'tiktok', label: 'TikTok', icon: TikTokIcon },
            { id: 'instagram', label: 'Instagram Reels', icon: Instagram },
            { id: 'youtube', label: 'YouTube Shorts', icon: Youtube },
          ].map((tab) => {
            const Icon = tab.icon;
            const active = platform === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setPlatform(tab.id)}
                className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
                  active 
                    ? 'bg-paper text-ink shadow-sm border border-rule' 
                    : 'text-muted hover:text-ink hover:bg-paper/50'
                }`}
              >
                <Icon size={14} className={active ? 'text-accent' : ''} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </div>

        {/* Content Body */}
        <div className="p-6 space-y-4">
          {/* Headline Title */}
          {currentData.title && (
            <div className="space-y-1.5">
              <label className="text-[11px] font-mono uppercase tracking-wider text-muted flex items-center gap-1.5">
                <Flame size={12} className="text-accent" /> Recommended Hook Title
              </label>
              <div className="p-3 rounded-lg bg-paper border border-rule text-sm font-medium text-ink">
                {currentData.title}
              </div>
            </div>
          )}

          {/* Caption */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-mono uppercase tracking-wider text-muted flex items-center gap-1.5">
              <MessageSquare size={12} className="text-cyan-400" /> Platform Caption
            </label>
            <div className="p-3.5 rounded-lg bg-paper border border-rule text-xs text-ink2 leading-relaxed whitespace-pre-wrap font-sans">
              {currentData.caption}
            </div>
          </div>

          {/* Hashtags */}
          <div className="space-y-1.5">
            <label className="text-[11px] font-mono uppercase tracking-wider text-muted flex items-center gap-1.5">
              <Hash size={12} className="text-emerald-400" /> Optimized Tags
            </label>
            <div className="flex flex-wrap gap-1.5">
              {(currentData.hashtags || []).map((tag, idx) => (
                <span 
                  key={idx}
                  className="px-2.5 py-1 rounded-md bg-paper border border-rule text-xs font-mono text-cyan-300"
                >
                  {tag}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="px-6 py-4 border-t border-rule bg-paper3/20 flex items-center justify-between">
          <span className="text-xs text-muted font-mono">
            Ready to paste into {platform}
          </span>
          <button
            onClick={handleCopy}
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-accent text-white text-xs font-medium hover:bg-accent/90 transition-all shadow-md shadow-accent/20"
          >
            {copied ? (
              <>
                <Check size={14} className="text-emerald-300" />
                <span>Copied to Clipboard!</span>
              </>
            ) : (
              <>
                <Copy size={14} />
                <span>Copy Full Caption & Tags</span>
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
