import { Link, useLocation } from 'react-router-dom';
import { useUIStore } from '../../store/uiStore';
import { BookOpen, Home, GitCompare, ChevronLeft, ChevronRight } from 'lucide-react';
import { useT } from '../../hooks/useTranslation';

const navItems = [
  { path: '/', labelKey: 'nav.papers', icon: Home },
  { path: '/comparison', labelKey: 'nav.compare', icon: GitCompare },
];

export default function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const location = useLocation();
  const t = useT();

  return (
    <aside
      className={`fixed left-0 top-0 h-full bg-white border-r border-slate-200 transition-all duration-300 z-30 flex flex-col ${
        sidebarOpen ? 'w-64' : 'w-16'
      }`}
    >
      {/* Logo */}
      <div className="flex items-center h-16 px-4 border-b border-slate-200">
        <BookOpen className="w-8 h-8 text-blue-600 flex-shrink-0" />
        {sidebarOpen && (
          <span className="ml-3 text-lg font-bold text-slate-800">ScholarLens</span>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 py-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = location.pathname === item.path;
          return (
            <Link
              key={item.path}
              to={item.path}
              className={`flex items-center px-4 py-3 mx-2 rounded-lg transition-colors ${
                isActive
                  ? 'bg-blue-50 text-blue-700'
                  : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
              }`}
            >
              <Icon className="w-5 h-5 flex-shrink-0" />
              {sidebarOpen && <span className="ml-3 text-sm font-medium">{t(item.labelKey)}</span>}
            </Link>
          );
        })}
      </nav>

      {/* Toggle */}
      <button
        onClick={toggleSidebar}
        className="flex items-center justify-center h-12 border-t border-slate-200 text-slate-400 hover:text-slate-600 transition-colors"
      >
        {sidebarOpen ? <ChevronLeft className="w-5 h-5" /> : <ChevronRight className="w-5 h-5" />}
      </button>
    </aside>
  );
}
