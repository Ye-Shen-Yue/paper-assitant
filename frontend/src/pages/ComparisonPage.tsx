import { useState, useEffect } from 'react';
import { listPapers } from '../api/papers';
import { comparePapers } from '../api/review';
import LoadingSpinner from '../components/common/LoadingSpinner';
import { useT } from '../hooks/useTranslation';
import type { PaperSummary } from '../api/types';

export default function ComparisonPage() {
  const [papers, setPapers] = useState<PaperSummary[]>([]);
  const [selected, setSelected] = useState<string[]>([]);
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [loadingPapers, setLoadingPapers] = useState(true);
  const t = useT();

  useEffect(() => {
    listPapers(1, 50)
      .then((res) => setPapers(res.items))
      .finally(() => setLoadingPapers(false));
  }, []);

  const toggleSelect = (id: string) => {
    setSelected((prev) =>
      prev.includes(id) ? prev.filter((p) => p !== id) : prev.length < 5 ? [...prev, id] : prev
    );
  };

  const handleCompare = async () => {
    if (selected.length < 2) return;
    setLoading(true);
    try {
      const res = await comparePapers(selected);
      setResult(res);
    } catch (err) {
      console.error('Comparison failed:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-5xl mx-auto">
      <h1 className="text-2xl font-bold text-slate-900 mb-2">{t('compare.title')}</h1>
      <p className="text-slate-500 mb-6">{t('compare.subtitle')}</p>

      {/* Paper selection */}
      {loadingPapers ? (
        <LoadingSpinner className="py-12" />
      ) : (
        <div className="space-y-2 mb-6">
          {papers.filter((p) => p.parsing_status === 'completed').map((paper) => (
            <div
              key={paper.id}
              onClick={() => toggleSelect(paper.id)}
              className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                selected.includes(paper.id)
                  ? 'border-blue-500 bg-blue-50'
                  : 'border-slate-200 bg-white hover:bg-slate-50'
              }`}
            >
              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={selected.includes(paper.id)}
                  onChange={() => toggleSelect(paper.id)}
                  className="rounded"
                />
                <div>
                  <p className="text-sm font-medium text-slate-700">{paper.title}</p>
                  <p className="text-xs text-slate-400">{paper.authors.join(', ')}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      <button
        onClick={handleCompare}
        disabled={selected.length < 2 || loading}
        className="px-6 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50 mb-8"
      >
        {loading ? t('compare.comparing') : `${t('compare.button')} ${selected.length} ${t('compare.papers')}`}
      </button>

      {/* Results */}
      {result && (
        <div className="space-y-6">
          {/* Comparison table */}
          {result.comparison_table && result.comparison_table.length > 0 && (
            <section className="bg-white rounded-lg border border-slate-200 p-5 overflow-x-auto">
              <h3 className="text-sm font-semibold text-slate-700 mb-4">{t('compare.table')}</h3>
              <table className="min-w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-2 px-3 text-slate-600 font-medium">{t('compare.aspect')}</th>
                    {result.papers?.map((p: any) => (
                      <th key={p.id} className="text-left py-2 px-3 text-slate-600 font-medium">
                        {p.title?.slice(0, 40)}...
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {result.comparison_table.map((row: any, i: number) => (
                    <tr key={i} className="border-b border-slate-100">
                      <td className="py-2 px-3 font-medium text-slate-700">{row.aspect}</td>
                      {result.papers?.map((p: any) => (
                        <td key={p.id} className="py-2 px-3 text-slate-500">
                          {row.papers?.[p.title] || '-'}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {/* Narrative */}
          {result.narrative && (
            <section className="bg-white rounded-lg border border-slate-200 p-5">
              <h3 className="text-sm font-semibold text-slate-700 mb-3">{t('compare.analysis')}</h3>
              <p className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">{result.narrative}</p>
            </section>
          )}
        </div>
      )}
    </div>
  );
}
