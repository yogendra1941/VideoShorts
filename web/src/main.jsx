import React, { StrictMode, Component, lazy, Suspense, useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from './contexts/AuthContext'
import { capture as captureAttribution } from './lib/attribution'
import { applyConsent } from './lib/consent'

const OAuthConsent = lazy(() => import('./components/OAuthConsent'))

class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error("VideoShorts Studio Runtime Error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-[#0b0d12] text-slate-200 flex flex-col items-center justify-center p-6 select-none font-sans">
          <div className="max-w-lg w-full bg-[#131722] border border-red-500/30 rounded-2xl p-6 shadow-2xl space-y-4 text-center">
            <div className="w-12 h-12 mx-auto rounded-full bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-400 text-xl font-bold">
              !
            </div>
            <h2 className="text-xl font-bold text-white font-display">Studio Rendering Error</h2>
            <p className="text-xs text-slate-400">
              An unexpected error occurred while rendering the workspace:
            </p>
            <div className="p-3 rounded-lg bg-black/60 border border-white/10 font-mono text-left text-xs text-rose-300 overflow-x-auto max-h-40">
              {this.state.error?.message || String(this.state.error)}
            </div>
            <div className="pt-2 flex items-center justify-center gap-3">
              <button
                onClick={() => {
                  window.location.hash = '#app';
                  window.location.reload();
                }}
                className="px-4 py-2 rounded-lg bg-accent text-white font-semibold text-xs hover:bg-accent/90 transition-colors shadow-lg shadow-accent/20"
              >
                Reload Studio
              </button>
              <button
                onClick={() => {
                  localStorage.clear();
                  window.location.hash = '#app';
                  window.location.reload();
                }}
                className="px-4 py-2 rounded-lg bg-slate-800 border border-slate-700 text-slate-300 text-xs hover:bg-slate-700 transition-colors"
              >
                Clear Cache & Reload
              </button>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

function DeletedView() {
  return (
    <div className="min-h-screen bg-paper text-ink2 flex items-center justify-center p-6">
      <div className="max-w-md text-center space-y-4">
        <h1 className="font-display lowercase text-2xl sm:text-3xl text-ink">All local data cleared</h1>
        <p className="text-sm text-muted">
          VideoShorts runs fully on your machine. Nothing was uploaded, sold, or
          shared — you can start fresh any time.
        </p>
        <a href="#app" className="btn-ghost px-4 py-2 inline-flex">Back to studio</a>
      </div>
    </div>
  );
}

function Root() {
  const resolveView = () => {
    const hash = window.location.hash || '';
    if (hash.startsWith('#/auth/')) return 'auth';       // AuthContext consumes then redirects
    if (hash.startsWith('#/oauth/authorize')) return 'oauth';
    if (hash.startsWith('#/deleted')) return 'deleted';
    if (hash === '#app' || hash.startsWith('#app?') || hash === '#/app') return 'app';
    // Direct clean studio entrypoint: always loads the studio app directly
    return 'app';
  };
  const [view, setView] = useState(resolveView);

  useEffect(() => {
    const handleHashChange = () => setView(resolveView());
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  if (view === 'oauth') return <OAuthConsent />;
  if (view === 'deleted') return <DeletedView />;
  if (view === 'auth') {
    return <div className="min-h-screen flex items-center justify-center bg-background text-zinc-400">Signing you in…</div>;
  }
  return <App />;
}

// Before React mounts: AuthContext rewrites the URL on auth redirects.
captureAttribution();
applyConsent();

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <ErrorBoundary>
      <AuthProvider>
        <Suspense fallback={<div className="min-h-screen bg-[#0b0d12] flex items-center justify-center text-slate-400 text-sm">Loading VideoShorts Studio…</div>}>
          <Root />
        </Suspense>
      </AuthProvider>
    </ErrorBoundary>
  </StrictMode>,
)
