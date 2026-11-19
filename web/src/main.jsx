import { StrictMode, lazy, Suspense, useState, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import Landing from './Landing.jsx'
import { AuthProvider } from './contexts/AuthContext'
import { capture as captureAttribution } from './lib/attribution'
import { applyConsent } from './lib/consent'

const App = lazy(() => import('./App.jsx'))
const OAuthConsent = lazy(() => import('./components/OAuthConsent'))

function Root() {
  const resolveView = () => {
    const hash = window.location.hash || '';
    if (hash.startsWith('#/auth/')) return 'auth';
    if (hash.startsWith('#/oauth/authorize')) return 'oauth';
    if (hash === '#app' || hash.startsWith('#app?') || hash === '#/app') return 'app';
    // Default to world-class showcase landing if #landing or no hash
    return 'landing';
  };
  const [view, setView] = useState(resolveView);

  useEffect(() => {
    const handleHashChange = () => setView(resolveView());
    window.addEventListener('hashchange', handleHashChange);
    return () => window.removeEventListener('hashchange', handleHashChange);
  }, []);

  const handleLaunchApp = () => {
    window.location.hash = '#app';
    setView('app');
  };

  if (view === 'oauth') return <OAuthConsent />;
  if (view === 'app') return <App onShowLanding={() => { window.location.hash = '#landing'; setView('landing'); }} />;
  return <Landing onLaunchApp={handleLaunchApp} />;
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
