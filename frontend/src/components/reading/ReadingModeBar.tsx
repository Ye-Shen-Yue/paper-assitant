import { ScanLine, BookOpen, AlertTriangle } from 'lucide-react';
import { useUIStore } from '../../store/uiStore';
import { useT } from '../../hooks/useTranslation';

type ReadingMode = 'scan' | 'deep' | 'critical';

interface ModeConfig {
  id: ReadingMode;
  icon: React.ReactNode;
  label: string;
  description: string;
  color: string;
  bgColor: string;
}

export default function ReadingModeBar() {
  const { readingMode, setReadingMode } = useUIStore();
  const t = useT();

  const modes: ModeConfig[] = [
    {
      id: 'scan',
      icon: <ScanLine className="w-4 h-4" />,
      label: t('reading.mode.scan'),
      description: t('reading.mode.scan.desc'),
      color: 'text-emerald-600',
      bgColor: 'bg-emerald-50',
    },
    {
      id: 'deep',
      icon: <BookOpen className="w-4 h-4" />,
      label: t('reading.mode.deep'),
      description: t('reading.mode.deep.desc'),
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
    },
    {
      id: 'critical',
      icon: <AlertTriangle className="w-4 h-4" />,
      label: t('reading.mode.critical'),
      description: t('reading.mode.critical.desc'),
      color: 'text-amber-600',
      bgColor: 'bg-amber-50',
    },
  ];

  return (
    <div className="flex items-center gap-2 p-2 bg-white/80 backdrop-blur-sm border border-slate-200 rounded-xl shadow-sm">
      <span className="text-xs font-medium text-slate-400 px-2">
        {t('reading.mode')}
      </span>
      {modes.map((mode) => (
        <button
          key={mode.id}
          onClick={() => setReadingMode(mode.id)}
          className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-sm transition-all ${
            readingMode === mode.id
              ? `${mode.bgColor} ${mode.color} font-medium`
              : 'text-slate-600 hover:bg-slate-100'
          }`}
          title={mode.description}
        >
          {mode.icon}
          <span>{mode.label}</span>
        </button>
      ))}
    </div>
  );
}
