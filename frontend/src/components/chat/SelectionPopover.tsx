import { MessageSquare, Highlighter, StickyNote } from 'lucide-react';
import { useT } from '../../hooks/useTranslation';

interface Props {
  position: { x: number; y: number };
  selectedText: string;
  onAskAI: () => void;
  onHighlight: () => void;
  onAddNote: () => void;
  onClose: () => void;
}

export default function SelectionPopover({
  position,
  selectedText,
  onAskAI,
  onHighlight,
  onAddNote,
  onClose,
}: Props) {
  const t = useT();

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-40"
        onClick={onClose}
      />

      {/* Popover */}
      <div
        className="fixed z-50 bg-white rounded-xl shadow-xl border border-slate-200 py-2"
        style={{
          left: Math.min(position.x, window.innerWidth - 200),
          top: Math.min(position.y + 10, window.innerHeight - 100),
        }}
      >
        <div className="px-3 py-2 border-b border-slate-100 max-w-xs">
          <p className="text-xs text-slate-500 line-clamp-2">
            "{selectedText.substring(0, 80)}{selectedText.length > 80 ? '...' : ''}"
          </p>
        </div>

        <div className="p-1">
          <button
            onClick={onAskAI}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-colors"
          >
            <MessageSquare className="w-4 h-4" />
            {t('chat.selectText')}
          </button>

          <button
            onClick={onHighlight}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-amber-50 hover:text-amber-600 rounded-lg transition-colors"
          >
            <Highlighter className="w-4 h-4" />
            Highlight
          </button>

          <button
            onClick={onAddNote}
            className="w-full flex items-center gap-2 px-3 py-2 text-sm text-slate-700 hover:bg-green-50 hover:text-green-600 rounded-lg transition-colors"
          >
            <StickyNote className="w-4 h-4" />
            Add Note
          </button>
        </div>
      </div>
    </>
  );
}
