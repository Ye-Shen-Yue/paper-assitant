import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { getPaper, reparsePaper } from '../api/papers';
import { usePaperStore } from '../store/paperStore';
import { useUIStore } from '../store/uiStore';
import LoadingSpinner from '../components/common/LoadingSpinner';
import OverviewTab from '../components/paper/OverviewTab';
import AnalysisTab from '../components/analysis/AnalysisTab';
import VisualizationTab from '../components/visualization/VisualizationTab';
import ReviewTab from '../components/review/ReviewTab';
import ReadingModeBar from '../components/reading/ReadingModeBar';
import ChatWidget from '../components/chat/ChatWidget';
import SelectionPopover from '../components/chat/SelectionPopover';
import { useT } from '../hooks/useTranslation';
import { useTaskPolling } from '../hooks/useTaskPolling';
import { usePaperTracking } from '../hooks/useUserTracking';
import ProgressBar from '../components/common/ProgressBar';
import type { PaperDetail } from '../api/types';

const TAB_IDS = ['overview', 'analysis', 'visualization', 'review'] as const;
const TAB_KEYS: Record<string, string> = {
  overview: 'tab.overview',
  analysis: 'tab.analysis',
  visualization: 'tab.visualization',
  review: 'tab.review',
};

type TabId = typeof TAB_IDS[number];

export default function PaperPage() {
  const { paperId } = useParams<{ paperId: string }>();
  const { currentPaper, setCurrentPaper } = usePaperStore();
  const { readingMode } = useUIStore();
  const [activeTab, setActiveTab] = useState<TabId>('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reparseTaskId, setReparseTaskId] = useState<string | null>(null);
  const [selectedText, setSelectedText] = useState<string>('');
  const [selectionPosition, setSelectionPosition] = useState<{ x: number; y: number } | null>(null);
  const [showSelectionPopover, setShowSelectionPopover] = useState(false);
  const [chatInputText, setChatInputText] = useState<string>('');
  const t = useT();
  const { track } = usePaperTracking(paperId);

  const { task: reparseTask, isComplete: reparseComplete } = useTaskPolling(reparseTaskId);

  const loadPaper = () => {
    if (!paperId) return;
    setLoading(true);
    setError(null);
    getPaper(paperId)
      .then((paper) => {
        setCurrentPaper(paper);
        setLoading(false);
      })
      .catch(() => {
        setError(t('paper.loadFailed'));
        setLoading(false);
      });
  };

  useEffect(() => {
    loadPaper();
    return () => setCurrentPaper(null);
  }, [paperId, setCurrentPaper]);

  useEffect(() => {
    if (reparseComplete) {
      setReparseTaskId(null);
      loadPaper();
    }
  }, [reparseComplete]);

  const handleReparse = async () => {
    if (!paperId) return;
    try {
      const result = await reparsePaper(paperId);
      setReparseTaskId(result.task_id);
    } catch (err) {
      console.error('Reparse failed:', err);
    }
  };

  // Handle text selection
  const handleTextSelection = useCallback(() => {
    const selection = window.getSelection();
    if (selection && selection.toString().trim().length > 0) {
      const text = selection.toString().trim();
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();
      setSelectedText(text);
      setSelectionPosition({ x: rect.left + rect.width / 2, y: rect.bottom });
      setShowSelectionPopover(true);
    } else {
      setShowSelectionPopover(false);
    }
  }, []);

  useEffect(() => {
    document.addEventListener('mouseup', handleTextSelection);
    return () => document.removeEventListener('mouseup', handleTextSelection);
  }, [handleTextSelection]);

  // Handle reading mode changes
  useEffect(() => {
    switch (readingMode) {
      case 'scan':
        setActiveTab('overview');
        break;
      case 'deep':
        setActiveTab('analysis');
        break;
      case 'critical':
        setActiveTab('review');
        break;
    }
  }, [readingMode]);

  // Track tab changes
  useEffect(() => {
    if (paperId) {
      track('click', { tab: activeTab });
    }
  }, [activeTab, paperId]);

  if (loading) return <LoadingSpinner className="py-24" size="lg" />;
  if (error || !currentPaper) {
    return (
      <div className="text-center py-24 text-red-500">
        {error || t('paper.notFound')}
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Paper header */}
      <div className="mb-6">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h1 className="text-xl font-bold text-slate-900">{currentPaper.title}</h1>
            {currentPaper.authors.length > 0 && (
              <p className="text-sm text-slate-500 mt-1">{currentPaper.authors.join(', ')}</p>
            )}
          </div>
          <div className="flex items-center gap-2">
            <ReadingModeBar />
            <button
              onClick={handleReparse}
              disabled={!!reparseTaskId}
              className="px-3 py-1.5 text-xs bg-slate-100 text-slate-600 rounded-lg hover:bg-slate-200 disabled:opacity-50"
            >
              {reparseTaskId ? t('common.reparsing') : t('common.reparse')}
            </button>
          </div>
        </div>
        <div className="flex items-center gap-4 mt-2 text-xs text-slate-400">
          {currentPaper.venue && <span>{currentPaper.venue}</span>}
          {currentPaper.year && <span>{currentPaper.year}</span>}
          <span>{currentPaper.page_count} {t('home.pages')}</span>
          <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${
            currentPaper.parsing_status === 'completed'
              ? 'bg-green-100 text-green-700'
              : currentPaper.parsing_status === 'failed'
              ? 'bg-red-100 text-red-700'
              : 'bg-yellow-100 text-yellow-700'
          }`}>
            {t(`status.${currentPaper.parsing_status}`)}
          </span>
        </div>
      </div>

      {/* Reparse progress */}
      {reparseTaskId && reparseTask && reparseTask.status !== 'completed' && (
        <div className="mb-6 bg-white rounded-lg border border-slate-200 p-4">
          <ProgressBar progress={reparseTask.progress} label={reparseTask.current_step} />
        </div>
      )}

      {/* Tabs */}
      <div className="border-b border-slate-200 mb-6">
        <div className="flex gap-0">
          {TAB_IDS.map((tabId) => (
            <button
              key={tabId}
              onClick={() => setActiveTab(tabId)}
              className={`px-5 py-3 text-sm font-medium border-b-2 transition-colors ${
                activeTab === tabId
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-700'
              }`}
            >
              {t(TAB_KEYS[tabId])}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div>
        {activeTab === 'overview' && <OverviewTab paper={currentPaper} />}
        {activeTab === 'analysis' && <AnalysisTab paperId={currentPaper.id} />}
        {activeTab === 'visualization' && <VisualizationTab paperId={currentPaper.id} />}
        {activeTab === 'review' && <ReviewTab paperId={currentPaper.id} />}
      </div>

      {/* AI Chat Widget */}
      <ChatWidget
        paperId={currentPaper.id}
        paperTitle={currentPaper.title}
        selectedText={chatInputText}
        onClearSelection={() => setChatInputText('')}
      />

      {/* Selection Popover */}
      {showSelectionPopover && selectionPosition && (
        <SelectionPopover
          position={selectionPosition}
          selectedText={selectedText}
          onAskAI={() => {
            setChatInputText(selectedText);
            setShowSelectionPopover(false);
          }}
          onHighlight={() => {
            // TODO: Implement highlight
            setShowSelectionPopover(false);
          }}
          onAddNote={() => {
            // TODO: Implement note
            setShowSelectionPopover(false);
          }}
          onClose={() => setShowSelectionPopover(false)}
        />
      )}
    </div>
  );
}
