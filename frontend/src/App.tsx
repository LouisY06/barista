import { useEffect, useMemo, useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import './styles/app.css';
import { LandingPage } from './pages/LandingPage';
import { OrderPage } from './pages/OrderPage';
import { RewardsPage } from './pages/RewardsPage';
import { ProfilePage } from './pages/ProfilePage';
import { HeaderTabs } from './components/HeaderTabs';
import { ThemeToggle } from './components/ThemeToggle';

type Theme = 'light' | 'dark';

const STORAGE_KEY = 'matchabot-theme';

export default function App() {
  const [theme, setTheme] = useState<Theme>(() => {
    if (typeof window === 'undefined') return 'light';
    const stored = window.localStorage.getItem(STORAGE_KEY);
    return stored === 'dark' ? 'dark' : 'light';
  });

  useEffect(() => {
    if (typeof window !== 'undefined') {
      window.localStorage.setItem(STORAGE_KEY, theme);
    }
  }, [theme]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  const themeClass = useMemo(() => (theme === 'dark' ? 'dark' : 'light'), [theme]);

  return (
    <BrowserRouter>
      <div className={`app-shell ${themeClass}`}>
        <header className="app-bar">
          <span className="brand-mark">MATCHABOT</span>
          <div className="header-controls">
            <HeaderTabs />
            <ThemeToggle theme={theme} onToggle={() => setTheme(theme === 'dark' ? 'light' : 'dark')} />
          </div>
        </header>

        <main className="app-main">
          <Routes>
            <Route path="/" element={<LandingPage />} />
            <Route path="/order" element={<OrderPage />} />
            <Route path="/rewards" element={<RewardsPage />} />
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
