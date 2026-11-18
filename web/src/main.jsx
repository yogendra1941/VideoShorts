import { StrictMode, lazy, Suspense, useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { AuthProvider } from './contexts/AuthContext'
import { capture as captureAttribution } from './lib/attribution'
import { applyConsent } from './lib/consent'

// VideoShorts is a 100% free studio app: the root view is the studio itself,
// no marketing landing, no pricing, no sign-in walls.
const App = lazy(() => import('./App.jsx'))
const OAuthConsent = lazy(() => import('./components/OAuthConsent'))

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
    // Everything else — bare "/", #features, #landing, any old route — lands
    // straight in the studio. No marketing pages remain.
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
    <AuthProvider>
      <Suspense fallback={<div className="min-h-screen bg-paper flex items-center justify-center text-muted text-sm lowercase">loading…</div>}>
        <Root />
      </Suspense>
    </AuthProvider>
  </StrictMode>,
)
