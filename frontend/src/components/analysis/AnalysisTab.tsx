import { useState } from 'react';
import { triggerProfiling, getProfile, triggerContributions, getContributions, triggerLimitations, getLimitations, triggerEntityExtraction } from '../../api/analysis';
import { useTaskPolling } from '../../hooks/useTaskPolling';
import LoadingSpinner from '../common/LoadingSpinner';
import ProgressBar from '../common/ProgressBar';
import { useT } from '../../hooks/useTranslation';
import type { PaperProfile, Contribution, Limitation } from '../../api/types';

interface Props {
  paperId: string;
}

export default function AnalysisTab({ paperId }: Props) {
  const [profile, setProfile] = useState<PaperProfile | null>(null);
  const [contributions, setContributions] = useState<Contribution[]>([]);
  const [limitations, setLimitations] = useState<Limitation[]>([]);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskLabel, setTaskLabel] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const t = useT();

  const { task, isComplete, error: taskError } = useTaskPolling(taskId);

  const runAnalysis = async (type: string) => {
    setLoading(true);
    setError(null);
    try {
      let result;
      switch (type) {
        case 'entities':
          result = await triggerEntityExtraction(paperId);
          setTaskLabel(t('analysis.runEntities'));
          break;
        case 'profile':
          result = await triggerProfiling(paperId);
          setTaskLabel(t('analysis.runProfile'));
          break;
        case 'contributions':
          result = await triggerContributions(paperId);
          setTaskLabel(t('analysis.runContributions'));
          break;
        case 'limitations':
          result = await triggerLimitations(paperId);
          setTaskLabel(t('analysis.runLimitations'));
          break;
      }
      if (result) setTaskId(result.task_id);
    } catch (err: any) {
      const msg = err.response?.data?.detail || err.message || t('common.failed');
      setError(msg);
      setLoading(false);
    }
  };

  const loadResults = async () => {
    try {
      const [p, c, l] = await Promise.allSettled([
        getProfile(paperId),
        getContributions(paperId),
        getLimitations(paperId),
      ]);
      if (p.status === 'fulfilled') setProfile(p.value);
      if (c.status === 'fulfilled') setContributions(c.value.contributions);
      if (l.status === 'fulfilled') setLimitations(l.value.limitations);
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

  return (
    <div className="space-y-6">
      {/* Action buttons */}
      <div className="flex flex-wrap gap-3">
        <button onClick={() => runAnalysis('entities')} disabled={loading}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50">
          {t('analysis.runEntities')}
        </button>
        <button onClick={() => runAnalysis('profile')} disabled={loading}
          className="px-4 py-2 bg-purple-600 text-white text-sm rounded-lg hover:bg-purple-700 disabled:opacity-50">
          {t('analysis.runProfile')}
        </button>
        <button onClick={() => runAnalysis('contributions')} disabled={loading}
          className="px-4 py-2 bg-green-600 text-white text-sm rounded-lg hover:bg-green-700 disabled:opacity-50">
          {t('analysis.runContributions')}
        </button>
        <button onClick={() => runAnalysis('limitations')} disabled={loading}
          className="px-4 py-2 bg-amber-600 text-white text-sm rounded-lg hover:bg-amber-700 disabled:opacity-50">
          {t('analysis.runLimitations')}
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
          <ProgressBar progress={task.progress} label={task.current_step || taskLabel} />
        </div>
      )}

      {/* Profile */}
      {profile && (
        <section className="bg-white rounded-lg border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">{t('analysis.profile')}</h3>
          <div className="space-y-3">
            {profile.dimensions.map((dim) => (
              <div key={dim.dimension}>
                <div className="flex justify-between text-sm mb-1">
                  <span className="text-slate-600 capitalize">{t(`analysis.${dim.dimension}`) || dim.dimension.replace(/_/g, ' ')}</span>
                  <span className="font-semibold text-slate-800">{dim.score.toFixed(1)}/10</span>
                </div>
                <div className="w-full bg-slate-100 rounded-full h-2.5">
                  <div
                    className="bg-blue-600 h-2.5 rounded-full transition-all"
                    style={{ width: `${dim.score * 10}%` }}
                  />
                </div>
                <p className="text-xs text-slate-400 mt-1">{dim.reasoning}</p>
              </div>
            ))}
          </div>
          {profile.overall_assessment && (
            <div className="mt-4 pt-4 border-t border-slate-100">
              <p className="text-sm text-slate-600">{profile.overall_assessment}</p>
            </div>
          )}
        </section>
      )}

      {/* Contributions */}
      {contributions.length > 0 && (
        <section className="bg-white rounded-lg border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">{t('analysis.contributions')}</h3>
          <div className="space-y-3">
            {contributions.map((c, i) => (
              <div key={i} className="border-l-3 pl-4" style={{
                borderLeftColor: c.level === 'theoretical' ? '#8b5cf6' : c.level === 'technical' ? '#3b82f6' : '#22c55e',
                borderLeftWidth: '3px',
              }}>
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-medium px-2 py-0.5 rounded-full" style={{
                    backgroundColor: c.level === 'theoretical' ? '#f3e8ff' : c.level === 'technical' ? '#dbeafe' : '#dcfce7',
                    color: c.level === 'theoretical' ? '#7c3aed' : c.level === 'technical' ? '#2563eb' : '#16a34a',
                  }}>
                    {t(`analysis.level.${c.level}`) || c.level}
                  </span>
                  <span className="text-xs text-slate-400">{c.significance}</span>
                </div>
                <p className="text-sm text-slate-600">{c.description}</p>
              </div>
            ))}
          </div>
        </section>
      )}

      {/* Limitations */}
      {limitations.length > 0 && (
        <section className="bg-white rounded-lg border border-slate-200 p-5">
          <h3 className="text-sm font-semibold text-slate-700 mb-4">{t('analysis.limitations')}</h3>
          <div className="space-y-3">
            {limitations.map((l, i) => (
              <div key={i} className="bg-amber-50 rounded-lg p-3">
                <div className="flex items-center gap-2 mb-1">
                  <span className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                    l.severity === 'critical' ? 'bg-red-100 text-red-700' :
                    l.severity === 'major' ? 'bg-amber-100 text-amber-700' :
                    'bg-slate-100 text-slate-600'
                  }`}>
                    {t(`analysis.severity.${l.severity}`) || l.severity}
                  </span>
                  <span className="text-xs text-slate-500">{l.category.replace(/_/g, ' ')}</span>
                </div>
                <p className="text-sm text-slate-600">{l.description}</p>
                {l.suggestion && (
                  <p className="text-xs text-green-700 mt-2">{t('analysis.suggestion')}: {l.suggestion}</p>
                )}
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
