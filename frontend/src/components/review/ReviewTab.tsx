import { useState } from 'react';
import { triggerReview, getReview, getControversy, getReproducibility } from '../../api/review';
import { useTaskPolling } from '../../hooks/useTaskPolling';
import LoadingSpinner from '../common/LoadingSpinner';
import ProgressBar from '../common/ProgressBar';
import { useT } from '../../hooks/useTranslation';
import { useUIStore } from '../../store/uiStore';
import type { ReviewResult, ControversyClaim, ReproducibilityItem } from '../../api/types';

interface Props {
  paperId: string;
}

export default function ReviewTab({ paperId }: Props) {
  const [review, setReview] = useState<ReviewResult | null>(null);
  const [controversy, setControversy] = useState<{ claims: ControversyClaim[]; overall_consistency: number } | null>(null);
  const [reproducibility, setReproducibility] = useState<{ checklist: ReproducibilityItem[]; overall_score: number; summary: string } | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const t = useT();
  const language = useUIStore((s) => s.language);

  const { task, isComplete, error: taskError } = useTaskPolling(taskId);

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await triggerReview(paperId, language);
      setTaskId(result.task_id);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || t('common.failed');
      setError(msg);
      setLoading(false);
    }
  };

  const loadResults = async () => {
    try {
      const [r, c, rp] = await Promise.allSettled([
        getReview(paperId),
        getControversy(paperId),
        getReproducibility(paperId),
      ]);
      if (r.status === 'fulfilled') setReview(r.value);
      if (c.status === 'fulfilled') setControversy(c.value);
      if (rp.status === 'fulfilled') setReproducibility(rp.value);
    } catch {}
    setLoading(false);
    setTaskId(null);
  };

  if (isComplete) {
    loadResults();
  }

  if (taskError) {
    if (!error) setError(taskError);
    if (loading) setLoading(false);
  }

  const recColors: Record<string, string> = {
    accept: 'bg-green-100 text-green-800',
    weak_accept: 'bg-green-50 text-green-700',
    borderline: 'bg-yellow-100 text-yellow-800',
    weak_reject: 'bg-orange-100 text-orange-800',
    reject: 'bg-red-100 text-red-800',
  };

  return (
    <div className="space-y-6">
      {/* Actions */}
      <div className="flex gap-3">
        <button onClick={handleGenerate} disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50">
          {t('review.generate')}
        </button>
        <button onClick={loadResults}
          className="px-4 py-2 bg-slate-600 text-white text-sm rounded-lg hover:bg-slate-700">
          {t('review.refresh')}
        </button>
      </div>

      {/* Error */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Progress */}
      {taskId && task && task.status !== 'completed' && (
        <div className="bg-white rounded-lg border border-slate-200 p-4">
          <ProgressBar progress={task.progress} label={task.current_step} />
        </div>
      )}

      {/* Review */}
      {review && (
        <section className="bg-white rounded-lg border border-slate-200 p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-slate-700">{t('review.autoReview')}</h3>
            <span className={`px-3 py-1 rounded-full text-xs font-medium ${recColors[review.overall_recommendation] || 'bg-slate-100 text-slate-600'}`}>
              {t(`review.rec.${review.overall_recommendation}`)}
            </span>
          </div>

          {/* Summary */}
          <div className="mb-4">
            <h4 className="text-xs font-medium text-slate-500 mb-1">{t('review.summary')}</h4>
            <p className="text-sm text-slate-600">{review.summary}</p>
          </div>

          {/* Strengths */}
          <div className="mb-4">
            <h4 className="text-xs font-medium text-green-600 mb-2">{t('review.strengths')}</h4>
            <ul className="space-y-1">
              {review.strengths.map((s, i) => (
                <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                  <span className="text-green-500 mt-0.5">+</span>
                  {s}
                </li>
              ))}
            </ul>
          </div>

          {/* Weaknesses */}
          <div className="mb-4">
            <h4 className="text-xs font-medium text-red-600 mb-2">{t('review.weaknesses')}</h4>
            <ul className="space-y-1">
              {review.weaknesses.map((w, i) => (
                <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                  <span className="text-red-500 mt-0.5">-</span>
                  {w}
                </li>
              ))}
            </ul>
          </div>

          {/* Questions */}
          {review.questions_to_authors.length > 0 && (
            <div className="mb-4">
              <h4 className="text-xs font-medium text-blue-600 mb-2">{t('review.questions')}</h4>
              <ul className="space-y-1">
                {review.questions_to_authors.map((q, i) => (
                  <li key={i} className="text-sm text-slate-600 flex items-start gap-2">
                    <span className="text-blue-500 mt-0.5">?</span>
                    {q}
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="text-xs text-slate-400 pt-3 border-t border-slate-100">
            {t('review.confidence')}: {review.confidence}/5
          </div>
        </section>
      )}

      {/* Controversy */}
      {controversy && controversy.claims.length > 0 && (
        <section className="bg-white rounded-lg border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">
            {t('review.controversy')}
            <span className="ml-2 text-xs font-normal text-slate-400">
              {t('review.overallConsistency')}: {(controversy.overall_consistency * 100).toFixed(0)}%
            </span>
          </h3>
          <div className="space-y-3">
            {controversy.claims.map((claim, i) => (
              <div key={i} className="border rounded-lg p-3">
                <p className="text-sm font-medium text-slate-700 mb-2">{claim.claim}</p>
                <div className="flex items-center gap-2 mb-2">
                  <div className="flex-1 bg-slate-100 rounded-full h-2">
                    <div
                      className={`h-2 rounded-full ${claim.consistency_score > 0.7 ? 'bg-green-500' : claim.consistency_score > 0.4 ? 'bg-yellow-500' : 'bg-red-500'}`}
                      style={{ width: `${claim.consistency_score * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-500">{(claim.consistency_score * 100).toFixed(0)}%</span>
                </div>
                <p className="text-xs text-slate-500">{claim.assessment}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Reproducibility */}
      {reproducibility && reproducibility.checklist.length > 0 && (
        <section className="bg-white rounded-lg border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">
            {t('review.reproducibility')}
            <span className="ml-2 text-xs font-normal text-slate-400">
              {t('review.score')}: {(reproducibility.overall_score * 100).toFixed(0)}%
            </span>
          </h3>
          <div className="space-y-2">
            {reproducibility.checklist.map((item, i) => {
              const statusIcon = item.status === 'met' ? 'V' : item.status === 'partially_met' ? '~' : 'X';
              const statusColor = item.status === 'met' ? 'text-green-600' : item.status === 'partially_met' ? 'text-yellow-600' : 'text-red-600';
              return (
                <div key={i} className="flex items-start gap-3 text-sm">
                  <span className={`font-mono font-bold ${statusColor}`}>{statusIcon}</span>
                  <div>
                    <span className="text-slate-700">{item.criterion}</span>
                    <p className="text-xs text-slate-400">{item.details}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </section>
      )}
    </div>
  );
}
