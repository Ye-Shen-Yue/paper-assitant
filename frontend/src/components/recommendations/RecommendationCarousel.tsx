import { useEffect, useState, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ChevronLeft, ChevronRight, TrendingUp, Star } from 'lucide-react';
import { getRecommendations, getUserProfile, type RecommendationItem, type UserProfile } from '../../api/recommendations';
import { getUserId } from '../../hooks/useUserTracking';
import LoadingSpinner from '../common/LoadingSpinner';

export default function RecommendationCarousel() {
  const navigate = useNavigate();
  const [recommendations, setRecommendations] = useState<RecommendationItem[]>([]);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [currentIndex, setCurrentIndex] = useState(0);
  const userId = getUserId();

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [recsData, profileData] = await Promise.all([
        getRecommendations(userId, 6, 'mixed'),
        getUserProfile(userId),
      ]);
      setRecommendations(recsData.recommendations);
      setProfile(profileData);
    } catch (err) {
      console.error('Failed to load recommendations:', err);
    } finally {
      setLoading(false);
    }
  }, [userId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const nextSlide = () => {
    setCurrentIndex((prev) => (prev + 1) % Math.max(recommendations.length - 2, 1));
  };

  const prevSlide = () => {
    setCurrentIndex((prev) => (prev - 1 + Math.max(recommendations.length - 2, 1)) % Math.max(recommendations.length - 2, 1));
  };

  if (loading) {
    return (
      <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl">
        <LoadingSpinner size="sm" />
      </div>
    );
  }

  if (recommendations.length === 0) {
    return (
      <div className="mb-8 p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-xl">
        <div className="flex items-center gap-2 mb-3">
          <Sparkles className="w-5 h-5 text-blue-600" />
          <h2 className="text-lg font-semibold text-slate-800">为你推荐</h2>
        </div>
        <p className="text-sm text-slate-500">
          阅读更多论文后，我们将为你生成个性化推荐
        </p>
      </div>
    );
  }

  const visibleRecs = recommendations.slice(currentIndex, currentIndex + 3);
  const topTopics = profile?.topic_distribution
    ? Object.entries(profile.topic_distribution)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 2)
        .map(([t]) => t)
    : [];

  return (
    <div className="mb-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-blue-600" />
            <h2 className="text-lg font-semibold text-slate-800">
              为你推荐
              {topTopics.length > 0 && (
                <span className="text-sm font-normal text-slate-500 ml-2">
                  基于你的{topTopics.join('、')}兴趣
                </span>
              )}
            </h2>
          </div>
          {profile && profile.streak_days > 0 && (
            <div className="flex items-center gap-1 px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-full">
              <TrendingUp className="w-3 h-3" />
              连续{profile.streak_days}天
            </div>
          )}
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={prevSlide}
            disabled={currentIndex === 0}
            className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronLeft className="w-5 h-5" />
          </button>
          <button
            onClick={nextSlide}
            disabled={currentIndex >= recommendations.length - 3}
            className="p-1.5 rounded-lg hover:bg-slate-100 disabled:opacity-30 disabled:cursor-not-allowed"
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {visibleRecs.map((rec) => (
          <div
            key={rec.paper.id}
            onClick={() => navigate(`/paper/${rec.paper.id}`)}
            className="group bg-white rounded-xl border border-slate-200 p-4 hover:shadow-lg hover:border-blue-300 transition-all cursor-pointer"
          >
            {/* Reason badge */}
            <div className="flex items-center gap-1.5 mb-3">
              {rec.reason === 'content_based' ? (
                <Star className="w-3.5 h-3.5 text-amber-500" />
              ) : (
                <TrendingUp className="w-3.5 h-3.5 text-blue-500" />
              )}
              <span className="text-xs text-slate-500">{rec.reason_text}</span>
              <span className="ml-auto text-xs text-slate-400">
                相关度 {(rec.score * 100).toFixed(0)}%
              </span>
            </div>

            {/* Paper info */}
            <h3 className="text-sm font-semibold text-slate-800 line-clamp-2 mb-2 group-hover:text-blue-600 transition-colors">
              {rec.paper.title}
            </h3>

            {rec.paper.authors.length > 0 && (
              <p className="text-xs text-slate-500 truncate mb-2">
                {rec.paper.authors.slice(0, 3).join(', ')}
                {rec.paper.authors.length > 3 && ' et al.'}
              </p>
            )}

            {rec.paper.abstract && (
              <p className="text-xs text-slate-400 line-clamp-2">
                {rec.paper.abstract}
              </p>
            )}

            {/* Footer */}
            <div className="flex items-center gap-3 mt-3 pt-3 border-t border-slate-100 text-xs text-slate-400">
              <span>{rec.paper.page_count} 页</span>
              <span>{rec.paper.language.toUpperCase()}</span>
              <span>{new Date(rec.paper.upload_date).toLocaleDateString()}</span>
            </div>
          </div>
        ))}
      </div>

      {/* View profile link */}
      <div className="flex items-center justify-between mt-4 px-1">
        <p className="text-xs text-slate-400">
          已读 {profile?.total_papers_read || 0} 篇论文 · 累计 {(profile?.total_reading_time || 0 / 3600).toFixed(1)} 小时
        </p>
        <button
          onClick={() => navigate('/profile')}
          className="text-sm text-blue-600 hover:text-blue-700 font-medium"
        >
          查看研究画像 →
        </button>
      </div>
    </div>
  );
}
