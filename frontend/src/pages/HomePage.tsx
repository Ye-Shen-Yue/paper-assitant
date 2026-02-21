import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Trash2, FileText, Clock, CheckCircle, AlertCircle, Loader, Sparkles, TrendingUp } from 'lucide-react';
import FileUpload from '../components/common/FileUpload';
import ProgressBar from '../components/common/ProgressBar';
import LoadingSpinner from '../components/common/LoadingSpinner';
import RecommendationCarousel from '../components/recommendations/RecommendationCarousel';
import { uploadPaper, listPapers, deletePaper } from '../api/papers';
import { useTaskPolling } from '../hooks/useTaskPolling';
import { usePaperStore } from '../store/paperStore';
import { useT } from '../hooks/useTranslation';
import type { PaperSummary } from '../api/types';

const STATUS_ICONS: Record<string, typeof CheckCircle> = {
  completed: CheckCircle,
  parsing: Loader,
  pending: Clock,
  failed: AlertCircle,
};

const STATUS_COLORS: Record<string, string> = {
  completed: 'text-green-600',
  parsing: 'text-blue-600 animate-spin',
  pending: 'text-yellow-600',
  failed: 'text-red-600',
};

export default function HomePage() {
  const navigate = useNavigate();
  const { papers, setPapers, loading, setLoading, removePaper } = usePaperStore();
  const [uploadTaskId, setUploadTaskId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadStatus, setUploadStatus] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const t = useT();

  const { task: uploadTask, isComplete: uploadComplete, error: taskError } = useTaskPolling(uploadTaskId);

  const loadPapers = useCallback(async () => {
    setLoading(true);
    setUploadError(null);
    try {
      const result = await listPapers(1, 50, search || undefined);
      setPapers(result.items || []);
    } catch (err: any) {
      console.error('Failed to load papers:', err);
      setUploadError(err.message || 'Failed to load papers. Is backend running?');
    } finally {
      setLoading(false);
    }
  }, [search, setPapers, setLoading]);

  useEffect(() => {
    loadPapers();
  }, [loadPapers]);

  useEffect(() => {
    if (uploadComplete) {
      setUploadTaskId(null);
      setUploading(false);
      setUploadStatus(t('home.upload.complete'));
      loadPapers();
      setTimeout(() => setUploadStatus(null), 3000);
    }
  }, [uploadComplete, loadPapers, t]);

  useEffect(() => {
    if (taskError) {
      setUploadError(`${t('home.parseFailed')}: ${taskError}`);
      setUploading(false);
    }
  }, [taskError]);

  const handleUpload = async (file: File) => {
    if (!file || file.size === 0) {
      setUploadError('Please select a valid file');
      return;
    }
    setUploading(true);
    setUploadError(null);
    setUploadStatus(t('home.upload.uploading'));
    try {
      console.log('Uploading file:', file.name, 'Size:', file.size);
      const result = await uploadPaper(file);
      console.log('Upload result:', result);
      setUploadStatus(t('home.upload.parsing'));
      setUploadTaskId(result.task_id);
      loadPapers();
    } catch (err: any) {
      console.error('Upload error:', err);
      const msg = err.response?.data?.detail || err.message || t('home.upload.failed');
      setUploadError(msg);
      setUploadStatus(null);
      setUploading(false);
    }
  };

  const handleDelete = async (e: React.MouseEvent, paperId: string) => {
    e.stopPropagation();
    if (!confirm(t('home.delete.confirm'))) return;
    try {
      await deletePaper(paperId);
      removePaper(paperId);
    } catch (err) {
      console.error('Delete failed:', err);
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900 mb-2">{t('home.title')}</h1>
        <p className="text-slate-500">{t('home.subtitle')}</p>
      </div>

      {/* Upload area */}
      <div className="mb-8">
        <FileUpload onFileSelect={handleUpload} disabled={uploading} />

        {/* Upload status */}
        {uploadStatus && (
          <div className="mt-3 px-4 py-2 bg-blue-50 text-blue-700 text-sm rounded-lg">
            {uploadStatus}
          </div>
        )}

        {/* Upload error */}
        {uploadError && (
          <div className="mt-3 px-4 py-2 bg-red-50 text-red-700 text-sm rounded-lg">
            {uploadError}
          </div>
        )}

        {/* Progress bar */}
        {uploading && uploadTask && (
          <div className="mt-4">
            <ProgressBar
              progress={uploadTask.progress}
              label={uploadTask.current_step}
            />
          </div>
        )}
      </div>

      {/* Recommendations Section */}
      <RecommendationCarousel />

      {/* Search */}
      <div className="mb-6">
        <div className="flex items-center gap-4 mb-4">
          <h2 className="text-lg font-semibold text-slate-800">{t('home.myPapers')}</h2>
          <div className="flex-1">
            <input
              type="text"
              placeholder={t('home.search')}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full px-4 py-2 border border-slate-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>
        </div>
      </div>

      {/* Paper list */}
      {loading ? (
        <LoadingSpinner className="py-12" />
      ) : papers.length === 0 ? (
        <div className="text-center py-16 text-slate-400">
          <FileText className="w-16 h-16 mx-auto mb-4 opacity-50" />
          <p className="text-lg">{t('home.empty')}</p>
          <p className="text-sm mt-1">{t('home.empty.hint')}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {papers.map((paper) => (
            <PaperCard
              key={paper.id}
              paper={paper}
              onClick={() => navigate(`/paper/${paper.id}`)}
              onDelete={(e) => handleDelete(e, paper.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function PaperCard({
  paper,
  onClick,
  onDelete,
}: {
  paper: PaperSummary;
  onClick: () => void;
  onDelete: (e: React.MouseEvent) => void;
}) {
  const StatusIcon = STATUS_ICONS[paper.parsing_status] || Clock;
  const statusColor = STATUS_COLORS[paper.parsing_status] || 'text-slate-400';
  const t = useT();
  const statusKey = `status.${paper.parsing_status}`;

  return (
    <div
      onClick={onClick}
      className="bg-white rounded-lg border border-slate-200 p-4 hover:shadow-md hover:border-blue-200 transition-all cursor-pointer group"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-semibold text-slate-800 truncate">{paper.title}</h3>
          {paper.authors.length > 0 && (
            <p className="text-xs text-slate-500 mt-1 truncate">
              {paper.authors.join(', ')}
            </p>
          )}
          {paper.abstract && (
            <p className="text-xs text-slate-400 mt-2 line-clamp-2">{paper.abstract}</p>
          )}
          <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
            <span className="flex items-center gap-1">
              <StatusIcon className={`w-3.5 h-3.5 ${statusColor}`} />
              {t(statusKey)}
            </span>
            <span>{paper.page_count} {t('home.pages')}</span>
            <span>{paper.language.toUpperCase()}</span>
            <span>{new Date(paper.upload_date).toLocaleDateString()}</span>
          </div>
        </div>
        <button
          onClick={onDelete}
          className="p-2 text-slate-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-opacity"
        >
          <Trash2 className="w-4 h-4" />
        </button>
      </div>
    </div>
  );
}
