import { useEffect, useState, useCallback } from 'react';
import { TrendingUp, Lightbulb, Activity } from 'lucide-react';
import { getTrendData, type TrendData } from '../api/recommendations';
import { getUserId } from '../hooks/useUserTracking';
import LoadingSpinner from '../components/common/LoadingSpinner';

// Simple line chart component
function LineChart({ data }: { data: Array<{ year: number; count: number }> }) {
  if (!data || data.length === 0) return null;

  const maxCount = Math.max(...data.map((d) => d.count));
  const minYear = Math.min(...data.map((d) => d.year));
  const maxYear = Math.max(...data.map((d) => d.year));

  return (
    <div className="h-32 flex items-end gap-2">
      {data.map((point) => {
        const height = maxCount > 0 ? (point.count / maxCount) * 100 : 0;
        return (
          <div key={point.year} className="flex-1 flex flex-col items-center gap-1">
            <div
              className="w-full bg-blue-200 rounded-t transition-all hover:bg-blue-300"
              style={{ height: `${height}%` }}
              title={`${point.year}: ${point.count}篇`}
            />
            <span className="text-xs text-slate-400">{point.year.toString().slice(-2)}</span>
          </div>
        );
      })}
    </div>
  );
}

// Heatmap cell component
function HeatmapCell({ value, max }: { value: number; max: number }) {
  const intensity = max > 0 ? value / max : 0;
  const opacity = 0.1 + intensity * 0.9;

  return (
    <div
      className="w-8 h-8 rounded transition-all hover:scale-110"
      style={{ backgroundColor: `rgba(59, 130, 246, ${opacity})` }}
      title={`${value}篇`}
    />
  );
}

export default function TrendsPage() {
  const [trendData, setTrendData] = useState<TrendData | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedTopics, setSelectedTopics] = useState<string[]>([]);
  const userId = getUserId();

  const loadTrendData = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getTrendData(userId, selectedTopics.length > 0 ? selectedTopics : undefined, 10);
      setTrendData(data);
    } catch (err) {
      console.error('Failed to load trend data:', err);
    } finally {
      setLoading(false);
    }
  }, [userId, selectedTopics]);

  useEffect(() => {
    loadTrendData();
  }, [loadTrendData]);

  // Extract unique topics from heatmap data
  const allTopics = [...new Set(trendData?.heatmap_data.map((d) => d.topic) || [])];
  const allYears = [...new Set(trendData?.heatmap_data.map((d) => d.year) || [])].sort();

  // Get max count for normalization
  const maxCount = Math.max(...(trendData?.heatmap_data.map((d) => d.count) || [1]));

  if (loading) {
    return (
      <div className="max-w-5xl mx-auto py-12">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center gap-3 mb-2">
          <TrendingUp className="w-6 h-6 text-blue-600" />
          <h1 className="text-2xl font-bold text-slate-900">研究趋势洞察</h1>
        </div>
        <p className="text-slate-500">探索你关注领域的研究热点和演变趋势</p>
      </div>

      {/* AI Summary */}
      {trendData?.ai_summary && (
        <div className="mb-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6 border border-blue-100">
          <div className="flex items-start gap-3">
            <Lightbulb className="w-5 h-5 text-blue-600 mt-0.5" />
            <div>
              <h2 className="font-semibold text-slate-800 mb-1">AI洞察</h2>
              <p className="text-slate-600 text-sm">{trendData.ai_summary}</p>
            </div>
          </div>
        </div>
      )}

      {/* Topic Filter */}
      {allTopics.length > 0 && (
        <div className="mb-6">
          <h3 className="text-sm font-medium text-slate-700 mb-3">关注领域</h3>
          <div className="flex flex-wrap gap-2">
            {allTopics.map((topic) => (
              <button
                key={topic}
                onClick={() => {
                  if (selectedTopics.includes(topic)) {
                    setSelectedTopics(selectedTopics.filter((t) => t !== topic));
                  } else {
                    setSelectedTopics([...selectedTopics, topic]);
                  }
                }}
                className={`px-3 py-1.5 text-sm rounded-full transition-colors ${
                  selectedTopics.includes(topic) || selectedTopics.length === 0
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                }`}
              >
                {topic}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Heatmap */}
      {allTopics.length > 0 && allYears.length > 0 && (
        <div className="mb-6 bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">研究趋势热力图</h2>
          <div className="overflow-x-auto">
            <div className="inline-block">
              {/* Header row */}
              <div className="flex items-center gap-1 mb-1">
                <div className="w-20" /> {/* Empty corner */}
                {allYears.map((year) => (
                  <div key={year} className="w-8 text-center text-xs text-slate-400">
                    {year}
                  </div>
                ))}
              </div>
              {/* Data rows */}
              {allTopics.map((topic) => (
                <div key={topic} className="flex items-center gap-1 mb-1">
                  <div className="w-20 text-sm text-slate-600 truncate pr-2">{topic}</div>
                  {allYears.map((year) => {
                    const cell = trendData?.heatmap_data.find(
                      (d) => d.topic === topic && d.year === year
                    );
                    return (
                      <HeatmapCell
                        key={`${topic}-${year}`}
                        value={cell?.count || 0}
                        max={maxCount}
                      />
                    );
                  })}
                </div>
              ))}
            </div>
          </div>
          <div className="mt-4 flex items-center gap-4 text-xs text-slate-400">
            <span>少</span>
            <div className="flex gap-1">
              {[0.1, 0.3, 0.5, 0.7, 0.9].map((opacity) => (
                <div
                  key={opacity}
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: `rgba(59, 130, 246, ${opacity})` }}
                />
              ))}
            </div>
            <span>多</span>
          </div>
        </div>
      )}

      {/* Keyword Evolution */}
      {trendData?.keyword_evolution && trendData.keyword_evolution.length > 0 && (
        <div className="mb-6 bg-white rounded-xl border border-slate-200 p-6">
          <h2 className="text-lg font-semibold text-slate-800 mb-4">关键词流行度变化</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {trendData.keyword_evolution.slice(0, 4).map((item) => (
              <div key={item.keyword} className="border border-slate-100 rounded-lg p-4">
                <h3 className="text-sm font-medium text-slate-700 mb-3">{item.keyword}</h3>
                <LineChart data={item.data} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Emerging Topics */}
      {trendData?.emerging_topics && trendData.emerging_topics.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-6">
          <div className="flex items-center gap-2 mb-4">
            <Activity className="w-5 h-5 text-green-600" />
            <h2 className="text-lg font-semibold text-slate-800">新兴热点</h2>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {trendData.emerging_topics.map((topic) => (
              <div
                key={topic.topic}
                className="flex items-center justify-between p-4 bg-gradient-to-r from-green-50 to-emerald-50 rounded-lg"
              >
                <div>
                  <h3 className="font-medium text-slate-800">{topic.topic}</h3>
                  <p className="text-sm text-slate-500">{topic.recent_count} 篇近期论文</p>
                </div>
                <div className="flex items-center gap-1 text-green-600">
                  <TrendingUp className="w-4 h-4" />
                  <span className="text-sm font-medium">+{topic.growth_rate}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {(!trendData ||
        (trendData.heatmap_data.length === 0 &&
          trendData.keyword_evolution.length === 0 &&
          trendData.emerging_topics.length === 0)) && (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <TrendingUp className="w-16 h-16 mx-auto text-slate-300 mb-4" />
          <h2 className="text-lg font-semibold text-slate-700 mb-2">暂无趋势数据</h2>
          <p className="text-slate-500">上传并阅读更多论文后，我们将为你生成领域趋势分析</p>
        </div>
      )}
    </div>
  );
}
