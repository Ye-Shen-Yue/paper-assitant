import { Link, useLocation } from 'react-router-dom';
import { User, TrendingUp, Bell, Rss } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';
import LanguageSwitcher from '../common/LanguageSwitcher';
import { useT } from '../../hooks/useTranslation';

export default function Header() {
  const { theme, setTheme } = useUIStore();
  const t = useT();
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <header className="h-16 bg-white border-b border-slate-200 flex items-center justify-between px-6">
      <div className="flex items-center gap-6">
        <Link to="/" className="hover:opacity-80">
          <h2 className="text-lg font-semibold text-slate-800">{t('app.title')}</h2>
          <p className="text-xs text-slate-500">{t('app.subtitle')}</p>
        </Link>

        {/* Navigation Links */}
        <nav className="hidden md:flex items-center gap-1">
          <Link
            to="/profile"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              isActive('/profile')
                ? 'bg-blue-50 text-blue-600'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <User className="w-4 h-4" />
            研究画像
          </Link>
          <Link
            to="/trends"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              isActive('/trends')
                ? 'bg-blue-50 text-blue-600'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <TrendingUp className="w-4 h-4" />
            趋势洞察
          </Link>
          <Link
            to="/subscriptions"
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-colors ${
              isActive('/subscriptions') || isActive('/arxiv-pushes')
                ? 'bg-blue-50 text-blue-600'
                : 'text-slate-600 hover:bg-slate-50'
            }`}
          >
            <Rss className="w-4 h-4" />
            arXiv订阅
          </Link>
        </nav>
      </div>

      <div className="flex items-center gap-3">
        {/* Theme selector */}
        <select
          value={theme}
          onChange={(e) => setTheme(e.target.value as 'academic' | 'creative' | 'minimal')}
          className="text-sm border border-slate-200 rounded-md px-2 py-1 bg-white text-slate-600 hover:border-slate-300 focus:border-blue-500 focus:ring-1 focus:ring-blue-500 outline-none transition-colors"
        >
          <option value="academic">{t('theme.academic')}</option>
          <option value="creative">{t('theme.creative')}</option>
          <option value="minimal">{t('theme.minimal')}</option>
        </select>

        {/* Language switcher */}
        <LanguageSwitcher variant="header" />
      </div>
    </header>
  );
}
