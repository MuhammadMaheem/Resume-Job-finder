import { BrowserRouter as Router, Routes, Route, Link, useLocation, Navigate } from 'react-router-dom';
import { useState, useEffect, createContext, useContext } from 'react';
import HomePage from './pages/HomePage';
import ResumeUpload from './pages/ResumeUpload';
import JobDashboard from './pages/JobDashboard';
import ApplicationTracker from './pages/ApplicationTracker';
import ResumeImprovements from './pages/ResumeImprovements';
import CoverLetterGenerator from './pages/CoverLetterGenerator';
import Analytics from './pages/Analytics';
import InterviewPrep from './pages/InterviewPrep';
import ResumeCompare from './pages/ResumeCompare';
import Settings from './pages/Settings';

const ThemeContext = createContext({ dark: false, toggle: () => {} });

function ThemeToggle() {
  const { dark, toggle } = useContext(ThemeContext);
  return (
    <button onClick={toggle} className="p-2 rounded-md text-primary-100 hover:bg-primary-700 transition-colors" title={dark ? 'Switch to Light Mode' : 'Switch to Dark Mode'} aria-label="Toggle theme">
      {dark ? (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 3v1m0 16v1m9-9h-1M4 12H3m15.364 6.364l-.707-.707M6.343 6.343l-.707-.707m12.728 0l-.707.707M6.343 17.657l-.707.707M16 12a4 4 0 11-8 0 4 4 0 018 0z" /></svg>
      ) : (
        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.354 15.354A9 9 0 018.646 3.646 9.003 9.003 0 0012 21a9.003 9.003 0 008.354-5.646z" /></svg>
      )}
    </button>
  );
}

function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => { window.scrollTo(0, 0); }, [pathname]);
  return null;
}

function MobileNav({ open, onClose }: { open: boolean; onClose: () => void }) {
  const location = useLocation();
  const allItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/resume', label: 'Resume' },
    { path: '/jobs', label: 'Find Jobs' },
    { path: '/applications', label: 'Applications' },
    { path: '/improvements', label: 'Improve' },
    { path: '/cover-letters', label: 'Cover Letters' },
    { path: '/interview', label: 'Interview Prep' },
    { path: '/analytics', label: 'Analytics' },
    { path: '/compare', label: 'Compare' },
    { path: '/settings', label: 'Settings' },
  ];

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 md:hidden">
      <div className="fixed inset-0 bg-black/50" onClick={onClose}></div>
      <div className="fixed left-0 top-0 h-full w-64 bg-primary-900 dark:bg-charcoal-900 shadow-xl">
        <div className="flex items-center justify-between p-4 border-b border-primary-700 dark:border-charcoal-700">
          <span className="text-white font-bold">⚡ JobMatcher AI</span>
          <button onClick={onClose} className="text-white p-1" aria-label="Close menu">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
          </button>
        </div>
        <nav className="p-2 space-y-1 overflow-y-auto h-full pb-16">
          {allItems.map(item => (
            <Link key={item.path} to={item.path} onClick={onClose}
              className={`block px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                location.pathname === item.path
                  ? 'bg-primary-800 dark:bg-charcoal-800 text-white'
                  : 'text-primary-100 dark:text-charcoal-300 hover:bg-primary-800/50 dark:hover:bg-charcoal-800/50'
              }`}>
              {item.label}
            </Link>
          ))}
        </nav>
      </div>
    </div>
  );
}

function Navbar() {
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const mainItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/resume', label: 'Resume' },
    { path: '/jobs', label: 'Find Jobs' },
    { path: '/applications', label: 'Applications' },
  ];
  const toolsItems = [
    { path: '/improvements', label: 'Improve' },
    { path: '/cover-letters', label: 'Letters' },
    { path: '/interview', label: 'Interview' },
    { path: '/analytics', label: 'Analytics' },
    { path: '/compare', label: 'Compare' },
    { path: '/settings', label: 'Settings' },
  ];

  return (
    <nav className="bg-primary-800 dark:bg-charcoal-800 text-white shadow-lg border-b border-primary-700 dark:border-charcoal-700">
      <div className="max-w-7xl mx-auto px-4">
        <div className="flex items-center justify-between h-14">
          <div className="flex items-center gap-4">
            <button onClick={() => setMobileOpen(true)} className="md:hidden p-1 text-primary-100 hover:bg-primary-700 rounded" aria-label="Open menu">
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" /></svg>
            </button>
            <Link to="/" className="text-lg font-bold">⚡ JobMatcher AI</Link>
            <div className="hidden md:flex items-center gap-0.5">
              {mainItems.map(item => (
                <Link key={item.path} to={item.path} className={`px-3 py-2 rounded-md text-sm font-medium transition-colors ${location.pathname === item.path ? 'bg-primary-900 dark:bg-charcoal-900' : 'text-primary-100 dark:text-charcoal-300 hover:bg-primary-700 dark:hover:bg-charcoal-700'}`}>
                  {item.label}
                </Link>
              ))}
            </div>
          </div>
          <div className="flex items-center gap-0.5">
            <div className="hidden md:flex items-center gap-0.5">
              {toolsItems.map(item => (
                <Link key={item.path} to={item.path} className={`px-2.5 py-2 rounded-md text-xs transition-colors ${location.pathname === item.path ? 'bg-primary-900 dark:bg-charcoal-900 text-white' : 'text-primary-200 dark:text-charcoal-400 hover:bg-primary-700 dark:hover:bg-charcoal-700'}`}>
                  {item.label}
                </Link>
              ))}
            </div>
            <div className="ml-1 border-l border-primary-600 dark:border-charcoal-600 h-6"></div>
            <ThemeToggle />
          </div>
        </div>
      </div>
      <MobileNav open={mobileOpen} onClose={() => setMobileOpen(false)} />
    </nav>
  );
}

function NotFound() {
  return (
    <div className="max-w-7xl mx-auto px-4 py-20 text-center">
      <div className="text-8xl mb-4">404</div>
      <h1 className="text-2xl font-bold text-gray-900 dark:text-charcoal-50 mb-2">Page Not Found</h1>
      <p className="text-gray-500 dark:text-charcoal-400 mb-6">The page you're looking for doesn't exist</p>
      <Link to="/" className="px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 font-medium">Go to Dashboard</Link>
    </div>
  );
}

export default function App() {
  const [userId, setUserId] = useState<number | null>(null);
  const [userReady, setUserReady] = useState(false);
  const [dark, setDark] = useState(() => {
    const stored = localStorage.getItem('theme');
    if (stored) return stored === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
  });

  useEffect(() => {
    document.documentElement.classList.toggle('dark', dark);
    localStorage.setItem('theme', dark ? 'dark' : 'light');
  }, [dark]);

  useEffect(() => {
    const stored = localStorage.getItem('userId');
    const storedToken = localStorage.getItem('token');
    
    if (stored && storedToken) {
      // We have both userId and token, validate by making an authenticated request
      fetch(`/api/users/${stored}`, {
        headers: { 'Authorization': `Bearer ${storedToken}` }
      })
        .then(res => {
          if (res.ok) {
            setUserId(parseInt(stored));
            setUserReady(true);
          } else {
            // Token invalid, create new user
            console.warn('Stored token invalid, creating new user...');
            localStorage.removeItem('userId');
            localStorage.removeItem('token');
            return fetch('/api/users', { 
              method: 'POST', 
              headers: { 'Content-Type': 'application/json' }, 
              body: JSON.stringify({ name: 'User' }) 
            });
          }
        })
        .then(res => res?.json())
        .then(data => {
          if (data?.access_token) {
            setUserId(data.user.id);
            localStorage.setItem('userId', data.user.id.toString());
            localStorage.setItem('token', data.access_token);
          } else if (data?.id) {
            // Fallback: if no token, just use the id
            setUserId(data.id);
            localStorage.setItem('userId', data.id.toString());
          }
          setUserReady(true);
        })
        .catch((err) => {
          console.error('Failed to initialize user:', err);
          setUserReady(true);
        });
    } else if (stored) {
      // Has userId but no token, create new user
      localStorage.removeItem('userId');
      fetch('/api/users', { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify({ name: 'User' }) 
      })
        .then(res => res.json())
        .then(data => { 
          if (data?.access_token) {
            setUserId(data.user.id);
            localStorage.setItem('userId', data.user.id.toString());
            localStorage.setItem('token', data.access_token);
          } else if (data?.id) {
            setUserId(data.id);
            localStorage.setItem('userId', data.id.toString());
          }
          setUserReady(true); 
        })
        .catch(() => setUserReady(true));
    } else {
      // No stored user, create a new one
      fetch('/api/users', { 
        method: 'POST', 
        headers: { 'Content-Type': 'application/json' }, 
        body: JSON.stringify({ name: 'User' }) 
      })
        .then(res => res.json())
        .then(data => { 
          if (data?.access_token) {
            setUserId(data.user.id);
            localStorage.setItem('userId', data.user.id.toString());
            localStorage.setItem('token', data.access_token);
          } else if (data?.id) {
            setUserId(data.id);
            localStorage.setItem('userId', data.id.toString());
          }
          setUserReady(true); 
        })
        .catch(() => setUserReady(true));
    }
  }, []);


  if (!userReady) return <div className="min-h-screen bg-gray-50 dark:bg-charcoal-950 flex items-center justify-center"><div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div></div>;

  return (
    <ThemeContext.Provider value={{ dark, toggle: () => setDark(!dark) }}>
      <Router>
        <ScrollToTop />
        <div className="min-h-screen bg-gray-50 dark:bg-charcoal-950 text-gray-900 dark:text-charcoal-100 transition-colors">
          <Navbar />
          <Routes>
            <Route path="/" element={<HomePage userId={userId} />} />
            <Route path="/resume" element={<ResumeUpload userId={userId} />} />
            <Route path="/jobs" element={<JobDashboard userId={userId} />} />
            <Route path="/applications" element={<ApplicationTracker userId={userId} />} />
            <Route path="/improvements" element={<ResumeImprovements userId={userId} />} />
            <Route path="/cover-letters" element={<CoverLetterGenerator userId={userId} />} />
            <Route path="/analytics" element={<Analytics userId={userId} />} />
            <Route path="/interview" element={<InterviewPrep userId={userId} />} />
            <Route path="/compare" element={<ResumeCompare userId={userId} />} />
            <Route path="/settings" element={<Settings userId={userId} />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </div>
      </Router>
    </ThemeContext.Provider>
  );
}
