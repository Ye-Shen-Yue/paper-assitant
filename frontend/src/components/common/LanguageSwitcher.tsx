import { useState, useRef, useEffect } from 'react';
import { Globe, Check, Languages } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';
import { useT } from '../../hooks/useTranslation';

interface Props {
  variant?: 'header' | 'floating';
}

export default function LanguageSwitcher({ variant = 'header' }: Props) {
  const { language, setLanguage, bilingualMode, setBilingualMode } = useUIStore();
  const [isOpen, setIsOpen] = useState(false);
  const t = useT();
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const languages = [
    { code: 'en', label: t('lang.en'), flag: '🇺🇸' },
    { code: 'zh', label: t('lang.zh'), flag: '🇨🇳' },
  ] as const;

  if (variant === 'floating') {
    return (
      <div ref={ref} className="relative">
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="flex items-center gap-2 px-3 py-2 bg-white/90 backdrop-blur-sm border border-slate-200 rounded-full shadow-sm hover:shadow-md transition-all"
        >
          <Languages className="w-4 h-4 text-blue-600" />
          <span className="text-sm font-medium text-slate-700">
            {language === 'en' ? 'EN' : '中文'}
          </span>
          {bilingualMode && (
            <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded-full">
              双语
            </span>
          )}
        </button>

        {isOpen && (
          <div className="absolute bottom-full right-0 mb-2 w-48 bg-white rounded-xl shadow-lg border border-slate-200 py-2 z-50">
            <div className="px-3 py-2 text-xs font-medium text-slate-400 uppercase tracking-wider">
              {t('lang.switch')}
            </div>
            {languages.map((lang) => (
              <button
                key={lang.code}
                onClick={() => {
                  setLanguage(lang.code as 'en' | 'zh');
                  setIsOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-slate-50 transition-colors ${
                  language === lang.code ? 'bg-blue-50 text-blue-700' : 'text-slate-700'
                }`}
              >
                <span className="text-lg">{lang.flag}</span>
                <span className="flex-1">{lang.label}</span>
                {language === lang.code && <Check className="w-4 h-4" />}
              </button>
            ))}
            <div className="border-t border-slate-100 my-2" />
            <button
              onClick={() => {
                setBilingualMode(!bilingualMode);
                setIsOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-slate-50 transition-colors ${
                bilingualMode ? 'bg-blue-50 text-blue-700' : 'text-slate-700'
              }`}
            >
              <Languages className="w-4 h-4" />
              <span className="flex-1">{t('lang.bilingual')}</span>
              {bilingualMode && <Check className="w-4 h-4" />}
            </button>
          </div>
        )}
      </div>
    );
  }

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-900 px-3 py-1.5 rounded-lg hover:bg-slate-100 transition-colors"
      >
        <Globe className="w-4 h-4" />
        <span>{language === 'en' ? 'English' : '中文'}</span>
        {bilingualMode && (
          <span className="text-xs bg-blue-100 text-blue-700 px-1.5 py-0.5 rounded">
            双语
          </span>
        )}
      </button>

      {isOpen && (
        <div className="absolute top-full right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-slate-200 py-2 z-50">
          <div className="px-3 py-2 text-xs font-medium text-slate-400 uppercase tracking-wider">
            {t('lang.switch')}
          </div>
          {languages.map((lang) => (
            <button
              key={lang.code}
              onClick={() => {
                setLanguage(lang.code as 'en' | 'zh');
                setIsOpen(false);
              }}
              className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-slate-50 transition-colors ${
                language === lang.code ? 'bg-blue-50 text-blue-700' : 'text-slate-700'
              }`}
            >
              <span className="text-lg">{lang.flag}</span>
              <span className="flex-1">{lang.label}</span>
              {language === lang.code && <Check className="w-4 h-4" />}
            </button>
          ))}
          <div className="border-t border-slate-100 my-2" />
          <button
            onClick={() => {
              setBilingualMode(!bilingualMode);
              setIsOpen(false);
            }}
            className={`w-full flex items-center gap-3 px-3 py-2 text-left hover:bg-slate-50 transition-colors ${
              bilingualMode ? 'bg-blue-50 text-blue-700' : 'text-slate-700'
            }`}
          >
            <Languages className="w-4 h-4" />
            <span className="flex-1">{t('lang.bilingual')}</span>
            {bilingualMode && <Check className="w-4 h-4" />}
          </button>
        </div>
      )}
    </div>
  );
}
