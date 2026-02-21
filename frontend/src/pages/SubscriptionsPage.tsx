import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  Plus,
  Search,
  Trash2,
  Edit3,
  RefreshCw,
  ExternalLink,
  Bell,
  CheckCircle,
  AlertCircle,
  Clock,
  Tag,
  Users,
  FolderOpen
} from 'lucide-react';
import {
  listSubscriptions,
  createSubscription,
  updateSubscription,
  deleteSubscription,
  triggerCrawl,
  getCategories,
  type ArxivSubscription,
  type ArxivCategory
} from '../api/arxiv';

interface SubscriptionFormData {
  name: string;
  keywords: string;
  categories: string[];
  authors: string;
  max_results: number;
}

export default function SubscriptionsPage() {
  const userId = 'local-user';
  const [subscriptions, setSubscriptions] = useState<ArxivSubscription[]>([]);
  const [categories, setCategories] = useState<ArxivCategory[]>([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [crawlingId, setCrawlingId] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState<SubscriptionFormData>({
    name: '',
    keywords: '',
    categories: [],
    authors: '',
    max_results: 50
  });

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [subsData, catsData] = await Promise.all([
        listSubscriptions(userId),
        getCategories()
      ]);
      setSubscriptions(subsData || []);
      setCategories(catsData || []);
    } catch (err: any) {
      console.error('加载数据失败:', err);
      setError(err?.response?.data?.detail || err?.message || '加载数据失败，请检查后端服务是否正常运行');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const data = {
        user_id: userId,
        name: formData.name,
        keywords: formData.keywords.split(',').map(k => k.trim()).filter(Boolean),
        categories: formData.categories,
        authors: formData.authors.split(',').map(a => a.trim()).filter(Boolean),
        max_results: formData.max_results
      };

      if (editingId) {
        await updateSubscription(editingId, data);
      } else {
        await createSubscription(data);
      }

      setShowForm(false);
      setEditingId(null);
      setFormData({ name: '', keywords: '', categories: [], authors: '', max_results: 50 });
      await loadData();
    } catch (err) {
      setError('保存订阅失败');
      console.error(err);
    }
  };

  const handleEdit = (sub: ArxivSubscription) => {
    setFormData({
      name: sub.name,
      keywords: sub.keywords.join(', '),
      categories: sub.categories,
      authors: sub.authors.join(', '),
      max_results: sub.max_results
    });
    setEditingId(sub.id);
    setShowForm(true);
  };

  const handleDelete = async (id: string) => {
    if (!confirm('确定要删除这个订阅吗？')) return;
    try {
      await deleteSubscription(id);
      await loadData();
    } catch (err) {
      setError('删除订阅失败');
      console.error(err);
    }
  };

  const handleCrawl = async (id: string) => {
    try {
      setCrawlingId(id);
      setError(null);
      await triggerCrawl(id);
      alert('爬取任务已启动，请稍后查看推送');
    } catch (err: any) {
      console.error('启动爬取失败:', err);
      const errorMsg = err?.response?.data?.detail || err?.message || '启动爬取失败';
      setError(`启动爬取失败: ${errorMsg}`);
    } finally {
      setCrawlingId(null);
    }
  };

  const toggleCategory = (code: string) => {
    setFormData(prev => ({
      ...prev,
      categories: prev.categories.includes(code)
        ? prev.categories.filter(c => c !== code)
        : [...prev.categories, code]
    }));
  };

  const getCategoryName = (code: string) => {
    const cat = categories.find(c => c.code === code);
    return cat ? cat.name : code;
  };

  const formatTime = (timeStr?: string) => {
    if (!timeStr) return '从未更新';
    const date = new Date(timeStr);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) return '刚刚';
    if (hours < 24) return `${hours}小时前`;
    return `${Math.floor(hours / 24)}天前`;
  };

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Bell className="w-6 h-6 text-blue-600" />
            arXiv 订阅管理
          </h1>
          <p className="text-slate-500 mt-1">
            订阅感兴趣的领域，自动获取arXiv最新论文推送
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            to="/arxiv-pushes"
            className="flex items-center gap-1.5 px-4 py-2 text-sm text-slate-600 bg-white border border-slate-200 rounded-lg hover:bg-slate-50"
          >
            <ExternalLink className="w-4 h-4" />
            查看推送
          </Link>
          <button
            onClick={() => {
              setEditingId(null);
              setFormData({ name: '', keywords: '', categories: [], authors: '', max_results: 50 });
              setShowForm(true);
            }}
            className="flex items-center gap-1.5 px-4 py-2 text-sm text-white bg-blue-600 rounded-lg hover:bg-blue-700"
          >
            <Plus className="w-4 h-4" />
            新建订阅
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

      {/* Subscription Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-xl shadow-xl w-full max-w-lg max-h-[90vh] overflow-auto">
            <div className="p-6 border-b border-slate-200">
              <h2 className="text-lg font-semibold text-slate-800">
                {editingId ? '编辑订阅' : '新建订阅'}
              </h2>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  订阅名称
                </label>
                <input
                  type="text"
                  value={formData.name}
                  onChange={e => setFormData({ ...formData, name: e.target.value })}
                  placeholder="如：NLP最新论文"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  required
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  关键词（用逗号分隔）
                </label>
                <input
                  type="text"
                  value={formData.keywords}
                  onChange={e => setFormData({ ...formData, keywords: e.target.value })}
                  placeholder="如：transformer, attention, LLM"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  arXiv分类
                </label>
                <div className="max-h-40 overflow-y-auto border border-slate-200 rounded-lg p-2 space-y-1">
                  {categories.map(cat => (
                    <label key={cat.code} className="flex items-center gap-2 p-1 hover:bg-slate-50 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={formData.categories.includes(cat.code)}
                        onChange={() => toggleCategory(cat.code)}
                        className="rounded border-slate-300 text-blue-600"
                      />
                      <span className="text-sm text-slate-600">
                        {cat.code} - {cat.name}
                      </span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  关注作者（用逗号分隔，可选）
                </label>
                <input
                  type="text"
                  value={formData.authors}
                  onChange={e => setFormData({ ...formData, authors: e.target.value })}
                  placeholder="如：Yoshua Bengio, Yann LeCun"
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">
                  最大结果数
                </label>
                <input
                  type="number"
                  min={1}
                  max={200}
                  value={formData.max_results}
                  onChange={e => {
                    const value = parseInt(e.target.value);
                    setFormData({ ...formData, max_results: isNaN(value) ? 50 : value })
                  }}
                  className="w-full px-3 py-2 border border-slate-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
              </div>

              <div className="flex justify-end gap-3 pt-4">
                <button
                  type="button"
                  onClick={() => setShowForm(false)}
                  className="px-4 py-2 text-sm text-slate-600 hover:bg-slate-100 rounded-lg"
                >
                  取消
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 text-sm text-white bg-blue-600 hover:bg-blue-700 rounded-lg"
                >
                  {editingId ? '保存' : '创建'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Subscriptions List */}
      {loading ? (
        <div className="flex items-center justify-center h-64">
          <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
        </div>
      ) : subscriptions.length === 0 ? (
        <div className="text-center py-16 bg-slate-50 rounded-xl border border-slate-200">
          <Bell className="w-12 h-12 text-slate-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-slate-700 mb-2">暂无订阅</h3>
          <p className="text-slate-500 mb-4">创建订阅以自动获取arXiv最新论文推送</p>
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 text-sm text-blue-600 bg-blue-50 rounded-lg hover:bg-blue-100"
          >
            创建第一个订阅
          </button>
        </div>
      ) : (
        <div className="grid gap-4">
          {subscriptions.map(sub => (
            <div
              key={sub.id}
              className="bg-white border border-slate-200 rounded-xl p-5 hover:shadow-md transition-shadow"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-slate-800">{sub.name}</h3>
                    <span className={`px-2 py-0.5 text-xs rounded-full ${
                      sub.is_active
                        ? 'bg-green-100 text-green-700'
                        : 'bg-slate-100 text-slate-500'
                    }`}>
                      {sub.is_active ? '活跃' : '已暂停'}
                    </span>
                  </div>

                  <div className="flex flex-wrap gap-4 text-sm text-slate-600 mb-3">
                    {sub.keywords.length > 0 && (
                      <div className="flex items-center gap-1">
                        <Tag className="w-4 h-4 text-blue-500" />
                        <span>关键词: {sub.keywords.join(', ')}</span>
                      </div>
                    )}
                    {sub.categories.length > 0 && (
                      <div className="flex items-center gap-1">
                        <FolderOpen className="w-4 h-4 text-purple-500" />
                        <span>分类: {sub.categories.map(getCategoryName).join(', ')}</span>
                      </div>
                    )}
                    {sub.authors.length > 0 && (
                      <div className="flex items-center gap-1">
                        <Users className="w-4 h-4 text-orange-500" />
                        <span>作者: {sub.authors.join(', ')}</span>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-4 text-xs text-slate-400">
                    <span className="flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      上次更新: {formatTime(sub.last_crawled)}
                    </span>
                    <span>最大结果: {sub.max_results}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2 ml-4">
                  <button
                    onClick={() => handleCrawl(sub.id)}
                    disabled={crawlingId === sub.id}
                    className="p-2 text-slate-500 hover:text-blue-600 hover:bg-blue-50 rounded-lg disabled:opacity-50"
                    title="立即爬取"
                  >
                    <RefreshCw className={`w-4 h-4 ${crawlingId === sub.id ? 'animate-spin' : ''}`} />
                  </button>
                  <button
                    onClick={() => handleEdit(sub)}
                    className="p-2 text-slate-500 hover:text-green-600 hover:bg-green-50 rounded-lg"
                    title="编辑"
                  >
                    <Edit3 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(sub.id)}
                    className="p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 rounded-lg"
                    title="删除"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Info Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-8">
        <div className="bg-blue-50 border border-blue-100 rounded-xl p-4">
          <div className="flex items-center gap-2 text-blue-700 mb-2">
            <Search className="w-5 h-5" />
            <h4 className="font-medium">智能匹配</h4>
          </div>
          <p className="text-sm text-blue-600">
            系统根据关键词、分类和作者三重维度计算论文匹配度，只推送最相关的论文
          </p>
        </div>
        <div className="bg-green-50 border border-green-100 rounded-xl p-4">
          <div className="flex items-center gap-2 text-green-700 mb-2">
            <CheckCircle className="w-5 h-5" />
            <h4 className="font-medium">真实可靠</h4>
          </div>
          <p className="text-sm text-green-600">
            直接对接arXiv官方API，确保所有论文来源真实可信
          </p>
        </div>
        <div className="bg-purple-50 border border-purple-100 rounded-xl p-4">
          <div className="flex items-center gap-2 text-purple-700 mb-2">
            <Clock className="w-5 h-5" />
            <h4 className="font-medium">定时更新</h4>
          </div>
          <p className="text-sm text-purple-600">
            每6小时自动检查arXiv更新，确保你不会错过任何重要论文
          </p>
        </div>
      </div>
    </div>
  );
}
