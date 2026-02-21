import { useUIStore } from '../../store/uiStore';

interface Props {
  original: string;
  translated?: string;
  className?: string;
}

export default function BilingualText({ original, translated, className = '' }: Props) {
  const { bilingualMode, language } = useUIStore();

  // If bilingual mode is off, show only the current language
  if (!bilingualMode) {
    const text = language === 'zh' && translated ? translated : original;
    return <span className={className}>{text}</span>;
  }

  // Bilingual mode: show both languages
  return (
    <div className={`space-y-2 ${className}`}>
      <p className="text-slate-900">{original}</p>
      {translated && (
        <p className="text-slate-500 text-sm border-l-2 border-blue-300 pl-3">
          {translated}
        </p>
      )}
    </div>
  );
}
