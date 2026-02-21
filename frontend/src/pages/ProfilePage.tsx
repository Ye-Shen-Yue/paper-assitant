import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, BookOpen, Clock, TrendingUp, RefreshCw, Target, Flame, ChevronRight } from 'lucide-react';
import { getUserProfile, refreshUserProfile, type UserProfile } from '../api/recommendations';
import { getUserId } from '../hooks/useUserTracking';
import LoadingSpinner from '../components/common/LoadingSpinner';

// Simple pie chart component
function TopicDistributionChart({ data }: { data: Record<string, number> }) {
  const entries = Object.entries(data).sort((a, b) => b[1] - a[1]);
  const colors = ['#3b82f6', '#8b5cf6', '#10b981', '#f59e0b', '#ef4444', '#06b6d4'];

  if (entries.length === 0) {
    return <div className="text-sm text-slate-400">暂无数据</div>;
  }

  return (
    <div className="space-y-2">
      {entries.map(([topic, value], index) => (
        <div key={topic} className="flex items-center gap-3">
          <div
            className="w-3 h-3 rounded-full"
            style={{ backgroundColor: colors[index % colors.length] }}
          />
          <div className="flex-1">
            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-700">{topic}</span>
              <span className="text-slate-500">{(value * 100).toFixed(0)}%</span>
            </div>
            <div className="mt-1 h-2 bg-slate-100 rounded-full overflow-hidden">
              <div
                className="h-full rounded-full transition-all"
                style={{
                  width: `${value * 100}%`,
                  backgroundColor: colors[index % colors.length],
                }}
              />
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default function ProfilePage() {
  const navigate = useNavigate();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const userId = getUserId();

  const loadProfile = useCallback(async () => {
    try {
      setLoading(true);
      const data = await getUserProfile(userId);
      setProfile(data);
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadProfile();
  }, [loadProfile]);

  const handleRefresh = async () => {
    try {
      setRefreshing(true);
      await refreshUserProfile(userId);
      await loadProfile();
    } catch (err) {
      console.error('Failed to refresh profile:', err);
    } finally {
      setRefreshing(false);
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto py-12">
        <LoadingSpinner />
      </div>
    );
  }

  const hasData = profile && profile.total_papers_read > 0;

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900 mb-2">个人研究画像</h1>
            <p className="text-slate-500">基于你的阅读历史生成的学术兴趣分析</p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="flex items-center gap-2 px-4 py-2 bg-white border border-slate-200 rounded-lg text-sm text-slate-600 hover:bg-slate-50 disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${refreshing ? 'animate-spin' : ''}`} />
            更新画像
          </button>
        </div>
      </div>

      {!hasData ? (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <User className="w-16 h-16 mx-auto text-slate-300 mb-4" />
          <h2 className="text-lg font-semibold text-slate-700 mb-2">还没有足够的数据</h2>
          <p className="text-slate-500 mb-6">阅读更多论文后，我们将为你生成个性化的研究画像</p>
          <button
            onClick={() => navigate('/')}
            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            去阅读论文
          </button>
        </div>
      ) : (
        <>
          {/* Stats Cards */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex items-center gap-2 text-slate-500 mb-2">
                <BookOpen className="w-4 h-4" />
                <span className="text-xs">累计阅读</span>
              </div>
              <p className="text-2xl font-bold text-slate-800">{profile?.total_papers_read}</p>
              <p className="text-xs text-slate-400">篇论文</p>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex items-center gap-2 text-slate-500 mb-2">
                <Clock className="w-4 h-4" />
                <span className="text-xs">阅读时长</span>
              </div>
              <p className="text-2xl font-bold text-slate-800">
                {((profile?.total_reading_time || 0) / 3600).toFixed(1)}
              </p>
              <p className="text-xs text-slate-400">小时</p>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex items-center gap-2 text-slate-500 mb-2">
                <Flame className="w-4 h-4" />
                <span className="text-xs">连续打卡</span>
              </div>
              <p className="text-2xl font-bold text-orange-600">{profile?.streak_days || 0}</p>
              <p className="text-xs text-slate-400">天</p>
            </div>

            <div className="bg-white rounded-xl border border-slate-200 p-4">
              <div className="flex items-center gap-2 text-slate-500 mb-2">
                <Target className="w-4 h-4" />
                <span className="text-xs">阅读模式</span>
              </div>
              <p className="text-lg font-bold text-slate-800">
                {profile?.reading_pattern === 'researcher' ? '研究型' : '浏览型'}
              </p>
              <p className="text-xs text-slate-400">
                {profile?.reading_pattern === 'researcher' ? '深度阅读为主' : '快速浏览为主'}
              </p>
            </div>
          </div>

          {/* Main Content */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Topic Distribution */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-800 mb-4">研究主题分布</h2>
              {profile?.topic_distribution && Object.keys(profile.topic_distribution).length > 0 ? (
                <TopicDistributionChart data={profile.topic_distribution} />
              ) : (
                <p className="text-sm text-slate-400">阅读更多论文后将显示主题分布</p>
              )}
            </div>

            {/* Method Preferences */}
            <div className="bg-white rounded-xl border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-800 mb-4">关注的方法与技术</h2>
              {profile?.method_preferences && profile.method_preferences.length > 0 ? (
                <div className="flex flex-wrap gap-2">
                  {profile.method_preferences.map((method) => (
                    <span
                      key={method}
                      className="px-3 py-1.5 bg-blue-50 text-blue-700 text-sm rounded-full"
                    >
                      {method}
                    </span>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400">暂无数据</p>
              )}
            </div>
          </div>

          {/* Recent Papers */}
          {profile?.last_read_papers && profile.last_read_papers.length > 0 && (
            <div className="mt-6 bg-white rounded-xl border border-slate-200 p-6">
              <h2 className="text-lg font-semibold text-slate-800 mb-4">最近阅读</h2>
              <div className="space-y-2">
                {profile.last_read_papers.slice(0, 5).map((paperId) => (
                  <div
                    key={paperId}
                    onClick={() => navigate(`/paper/${paperId}`)}
                    className="flex items-center gap-3 p-3 rounded-lg hover:bg-slate-50 cursor-pointer group"
                  >
                    <BookOpen className="w-4 h-4 text-slate-400" />
                    <span className="text-sm text-slate-600 group-hover:text-blue-600 flex-1 truncate">
                      论文 ID: {paperId.slice(0, 8)}...
                    </span>
                    <ChevronRight className="w-4 h-4 text-slate-300" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Trend Insights Link */}
          <div className="mt-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl p-6">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-lg font-semibold text-slate-800 mb-1">探索研究趋势</h2>
                <p className="text-sm text-slate-500">查看你关注领域的研究热点和演变趋势</p>
              </div>
              <button
                onClick={() => navigate('/trends')}
                className="flex items-center gap-2 px-4 py-2 bg-white text-blue-600 rounded-lg hover:bg-blue-50"
              >
                <TrendingUp className="w-4 h-4" />
                查看趋势
              </button>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
