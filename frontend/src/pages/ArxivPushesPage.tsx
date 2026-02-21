import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Bell,
  Check,
  CheckCircle,
  Clock,
  Download,
  ExternalLink,
  FileText,
  Filter,
  Import,
  RefreshCw,
  Tag,
  Trash2,
  User,
  AlertCircle,
  Inbox,
  ChevronDown,
  ChevronUp
} from 'lucide-react';
import {
  getUserPushes,
  getUnreadCount,
  markPushAsRead,
  importArxivPaper,
  type ArxivPushRecord
} from '../api/arxiv';

export default function ArxivPushesPage() {
  const userId = 'local-user';
  const [pushes, setPushes] = useState<ArxivPushRecord[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [importingId, setImportingId] = useState<string | null>(null);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, [unreadOnly]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [pushesData, countData] = await Promise.all([
        getUserPushes(userId, { unread_only: unreadOnly, limit: 50 }),
        getUnreadCount(userId)
      ]);
      setPushes(pushesData?.pushes || []);
      setUnreadCount(countData?.unread_count || 0);
    } catch (err: any) {
      console.error('加载推送失败:', err);
      setError(err?.response?.data?.detail || err?.message || '加载推送失败，请检查后端服务是否正常运行');
    } finally {
      setLoading(false);
    }
  };

  const handleMarkAsRead = async (pushId: string) => {
    try {
      await markPushAsRead(pushId);
      setPushes(prev =>
        prev.map(p =>
          p.id === pushId ? { ...p, is_read: true } : p
        )
      );
      setUnreadCount(prev => Math.max(0, prev - 1));
    } catch (err) {
      console.error('标记已读失败', err);
    }
  };

  const handleImport = async (push: ArxivPushRecord) => {
    try {
      setImportingId(push.id);
      await importArxivPaper(push.arxiv_paper.id, userId);
      setPushes(prev =>
        prev.map(p =>
          p.id === push.id ? { ...p, is_imported: true } : p
        )
      );
      alert('论文导入成功！');
    } catch (err) {
      setError('导入论文失败');
      console.error(err);
    } finally {
      setImportingId(null);
    }
  };

  const formatTime = (timeStr: string) => {
    const date = new Date(timeStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) return '刚刚';
    if (hours < 24) return `${hours}小时前`;
    if (hours < 168) return `${Math.floor(hours / 24)}天前`;
    return date.toLocaleDateString();
  };

  const getMatchScoreColor = (score: number) => {
    if (score >= 0.8) return 'text-green-600 bg-green-100';
    if (score >= 0.5) return 'text-yellow-600 bg-yellow-100';
    return 'text-slate-600 bg-slate-100';
  };

  return (
    <div className="p-6 max-w-5xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Inbox className="w-6 h-6 text-blue-600" />
            arXiv 论文推送
            {unreadCount > 0 && (
              <span className="px-2 py-0.5 text-sm bg-red-100 text-red-600 rounded-full">
                {unreadCount} 未读
              </span>
            )}
          </h1>
          <p className="text-slate-500 mt-1">
            来自你的arXiv订阅的最新论文推荐
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/subscriptions"
            className="flex items-center gap-1.5 px-4 py-2 text-sm text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50"
          >
            <Bell className="w-4 h-4" />
            管理订阅
          </Link>
          <button
            onClick={() => setUnreadOnly(!unreadOnly)}
            className={`flex items-center gap-1.5 px-4 py-2 text-sm rounded-lg border ${
              unreadOnly
                ? 'bg-blue-50 text-blue-600 border-blue-200'
                : 'bg-white text-slate-600 border-slate-200 hover:bg-slate-50'
            }`}
          >
            <Filter className="w-4 h-4" />
            {unreadOnly ? '显示全部' : '仅未读'}
          </button>
        </div>
      </div>

      {/* Error */}
      {error && (
        <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg">
          <div className="flex items-center gap-2 text-red-600 mb-2">
            <AlertCircle className="w-5 h-5" />
            <span className="font-medium">出错了</span>
          </div>
          <p className="text-red-600 text-sm mb-3">{error}</p>
          <button
            onClick={loadData}
            className="px-3 py-1.5 text-sm text-red-600 bg-red-100 hover:bg-red-200 rounded-lg"
          >
            重试
          </button>
        </div>
      )}

      {/* Pushes List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      ) : pushes.length === 0 ? (
        <div className="text-center py-16 bg-slate-50 rounded-xl border border-slate-200">
          <Inbox className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-700 mb-2">
            {unreadOnly ? '没有未读推送' : '暂无论文推送'}
          </h3>
          <p className="text-slate-500 mb-4">
            {unreadOnly ? '所有推送都已阅读' : '创建订阅以获取arXiv最新论文推送'}
          </p>
          <Link
            to="/subscriptions"
            className="px-4 py-2 text-sm text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100"
          >
            创建订阅
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {pushes.map(push => (
            <div
              key={push.id}
              className={`bg-white border rounded-xl overflow-hidden transition-all ${
                push.is_read ? 'border-slate-200' : 'border-blue-200 shadow-sm'
              }`}
            >
              {/* Header */}
              <div
                className="p-4 cursor-pointer hover:bg-slate-50"
                onClick={() => setExpandedId(expandedId === push.id ? null : push.id)}
              >
                <div className="flex items-start gap-3">
                  {!push.is_read && (
                    <span className="w-2 h-2 bg-blue-500 rounded-full mt-2 flex-shrink-0" />
                  )}
                  <div className="flex-1 min-w-0">
                    <h3 className={`font-semibold text-lg ${
                      push.is_read ? 'text-slate-700' : 'text-slate-900'
                    }`}>
                      {push.arxiv_paper.title}
                    </h3>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-sm text-slate-500">
                      <span className="flex items-center gap-1">
                        <User className="w-3 h-3" />
                        {push.arxiv_paper.authors.slice(0, 3).join(', ')}
                        {push.arxiv_paper.authors.length > 3 && ` +${push.arxiv_paper.authors.length - 3}`}
                      </span>
                      <span className="flex items-center gap-1">
                        <Tag className="w-3 h-3" />
                        {push.arxiv_paper.primary_category}
                      </span>
                      <span className={`px-2 py-0.5 text-xs rounded-full ${getMatchScoreColor(push.match_score)}`}>
                        匹配度: {Math.round(push.match_score * 100)}%
                      </span>
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {formatTime(push.created_at)}
                      </span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        window.open(push.arxiv_paper.arxiv_url, '_blank');
                      }}
                      className="p-2 text-slate-400 hover:text-blue-600 hover:bg-blue-50 rounded-lg"
                      title="在arXiv查看"
                    >
                      <ExternalLink className="w-4 h-4" />
                    </button>
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setExpandedId(expandedId === push.id ? null : push.id);
                      }}
                      className="p-2 text-slate-400 hover:text-slate-600 rounded-lg"
                    >
                      {expandedId === push.id ? (
                        <ChevronUp className="w-4 h-4" />
                      ) : (
                        <ChevronDown className="w-4 h-4" />
                      )}
                    </button>
                  </div>
                </div>
              </div>

              {/* Expanded Content */}
              {expandedId === push.id && (
                <div className="px-4 pb-4 border-t border-slate-100">
                  <div className="pt-4">
                    <h4 className="text-sm font-medium text-slate-700 mb-2">摘要</h4>
                    <p className="text-sm text-slate-600 leading-relaxed bg-slate-50 p-3 rounded-lg">
                      {push.arxiv_paper.summary}
                    </p>

                    <div className="flex flex-wrap gap-2 mt-3">
                      {push.arxiv_paper.categories.map(cat => (
                        <span
                          key={cat}
                          className="px-2 py-1 text-xs bg-slate-100 text-slate-600 rounded"
                        >
                          {cat}
                        </span>
                      ))}
                    </div>

                    <div className="flex items-center gap-3 mt-4">
                      {!push.is_read && (
                        <button
                          onClick={() => handleMarkAsRead(push.id)}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-lg"
                        >
                          <Check className="w-4 h-4" />
                          标记已读
                        </button>
                      )}
                      {push.is_imported ? (
                        <span className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-green-600 bg-green-50 rounded-lg">
                          <CheckCircle className="w-4 h-4" />
                          已导入
                        </span>
                      ) : (
                        <button
                          onClick={() => handleImport(push)}
                          disabled={importingId === push.id}
                          className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg disabled:opacity-50"
                        >
                          {importingId === push.id ? (
                            <RefreshCw className="w-4 h-4 animate-spin" />
                          ) : (
                            <Import className="w-4 h-4" />
                          )}
                          导入到本地
                        </button>
                      )}
                      <a
                        href={push.arxiv_paper.pdf_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg"
                      >
                        <Download className="w-4 h-4" />
                        下载PDF
                      </a>
                      <a
                        href={push.arxiv_paper.arxiv_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1.5 px-3 py-1.5 text-sm text-slate-600 bg-white border border-slate-200 hover:bg-slate-50 rounded-lg"
                      >
                        <ExternalLink className="w-4 h-4" />
                        arXiv页面
                      </a>
                    </div>
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Stats */}
      {!loading && pushes.length > 0 && (
        <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
            <div className="text-2xl font-bold text-blue-700">{pushes.length}</div>
            <div className="text-sm text-blue-600">总推送数</div>
          </div>
          <div className="bg-yellow-50 border border-yellow-100 rounded-xl p-4">
            <div className="text-2xl font-bold text-yellow-700">{unreadCount}</div>
            <div className="text-sm text-yellow-600">未读推送</div>
          </div>
          <div className="bg-green-50 border border-green-100 rounded-xl p-4">
            <div className="text-2xl font-bold text-green-700">
              {pushes.filter(p => p.is_imported).length}
            </div>
            <div className="text-sm text-green-600">已导入论文</div>
          </div>
        </div>
      )}
    </div>
  );
}
