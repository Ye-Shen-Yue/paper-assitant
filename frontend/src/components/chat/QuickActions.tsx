import { FileText, Languages, HelpCircle, AlertCircle } from 'lucide-react';
import { useT } from '../../hooks/useTranslation';

interface Props {
  onAction: (action: string) => void;
}

export default function QuickActions({ onAction }: Props) {
  const t = useT();

  const actions = [
    { id: 'summarize', icon: <FileText className="w-3.5 h-3.5" />, label: t('chat.summarize') },
    { id: 'translate', icon: <Languages className="w-3.5 h-3.5" />, label: t('chat.translate') },
    { id: 'explain', icon: <HelpCircle className="w-3.5 h-3.5" />, label: t('chat.explain') },
    { id: 'criticize', icon: <AlertCircle className="w-3.5 h-3.5" />, label: t('chat.criticize') },
  ];

  return (
    <div className="px-3 py-2 bg-slate-50 border-b border-slate-100">
      <p className="text-xs text-slate-400 mb-2">{t('chat.quickActions')}</p>
      <div className="flex flex-wrap gap-2">
        {actions.map((action) => (
          <button
            key={action.id}
            onClick={() => onAction(action.id)}
            className="flex items-center gap-1.5 px-2.5 py-1.5 bg-white border border-slate-200 rounded-lg text-xs text-slate-600 hover:border-blue-300 hover:text-blue-600 hover:bg-blue-50 transition-colors"
          >
            {action.icon}
            {action.label}
          </button>
        ))}
      </div>
    </div>
  );
}
