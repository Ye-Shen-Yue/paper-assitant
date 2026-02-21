const translations: Record<string, Record<string, string>> = {
  // Layout
  'app.title': { en: 'ScholarLens', zh: 'ScholarLens' },
  'app.subtitle': { en: 'Paper Intelligence Platform', zh: '论文智能分析平台' },

  // Sidebar
  'nav.papers': { en: 'Papers', zh: '论文' },
  'nav.compare': { en: 'Compare', zh: '对比' },

  // HomePage
  'home.title': { en: 'Paper Library', zh: '论文库' },
  'home.subtitle': { en: 'Upload and analyze academic papers', zh: '上传并分析学术论文' },
  'home.upload.drop': { en: 'Drop PDF here or click to upload', zh: '拖拽 PDF 到此处或点击上传' },
  'home.upload.hint': { en: 'Supports academic papers in PDF format', zh: '支持 PDF 格式的学术论文' },
  'home.upload.uploading': { en: 'Uploading...', zh: '上传中...' },
  'home.upload.parsing': { en: 'Uploaded! Parsing in progress...', zh: '已上传！正在解析中...' },
  'home.upload.complete': { en: 'Upload and parsing complete!', zh: '上传和解析完成！' },
  'home.upload.failed': { en: 'Upload failed', zh: '上传失败' },
  'home.search': { en: 'Search papers...', zh: '搜索论文...' },
  'home.empty': { en: 'No papers yet', zh: '暂无论文' },
  'home.empty.hint': { en: 'Upload a PDF to get started', zh: '上传 PDF 开始使用' },
  'home.delete.confirm': { en: 'Delete this paper and all analysis data?', zh: '删除此论文及所有分析数据？' },
  'home.pages': { en: 'pages', zh: '页' },
  'home.parseFailed': { en: 'Parsing failed', zh: '解析失败' },

  // Status
  'status.completed': { en: 'Completed', zh: '已完成' },
  'status.parsing': { en: 'Parsing', zh: '解析中' },
  'status.pending': { en: 'Pending', zh: '等待中' },
  'status.failed': { en: 'Failed', zh: '失败' },

  // Tabs
  'tab.overview': { en: 'Overview', zh: '概览' },
  'tab.analysis': { en: 'Analysis', zh: '深度分析' },
  'tab.visualization': { en: 'Visualization', zh: '可视化' },
  'tab.review': { en: 'Review', zh: '智能审稿' },

  // PaperPage
  'paper.notFound': { en: 'Paper not found', zh: '论文未找到' },
  'paper.loadFailed': { en: 'Failed to load paper', zh: '加载论文失败' },

  // Overview tab
  'overview.abstract': { en: 'Abstract', zh: '摘要' },
  'overview.keywords': { en: 'Keywords', zh: '关键词' },
  'overview.sections': { en: 'Sections', zh: '章节' },
  'overview.entities': { en: 'Entities', zh: '实体' },
  'overview.references': { en: 'References', zh: '参考文献' },
  'overview.tables': { en: 'Tables', zh: '表格' },

  // Section type labels
  'section.title': { en: 'Title', zh: '标题' },
  'section.abstract': { en: 'Abstract', zh: '摘要' },
  'section.introduction': { en: 'Introduction', zh: '引言' },
  'section.related_work': { en: 'Related Work', zh: '相关工作' },
  'section.methods': { en: 'Methods', zh: '方法' },
  'section.experiments': { en: 'Experiments', zh: '实验' },
  'section.results': { en: 'Results', zh: '结果' },
  'section.discussion': { en: 'Discussion', zh: '讨论' },
  'section.conclusion': { en: 'Conclusion', zh: '结论' },
  'section.references': { en: 'References', zh: '参考文献' },
  'section.acknowledgments': { en: 'Acknowledgments', zh: '致谢' },
  'section.appendix': { en: 'Appendix', zh: '附录' },
  'section.other': { en: 'Other', zh: '其他' },

  // Entity type labels
  'entity.research_problem': { en: 'Research Problem', zh: '研究问题' },
  'entity.method': { en: 'Method', zh: '方法' },
  'entity.dataset': { en: 'Dataset', zh: '数据集' },
  'entity.metric': { en: 'Metric', zh: '评估指标' },
  'entity.innovation': { en: 'Innovation', zh: '创新点' },
  'entity.baseline': { en: 'Baseline', zh: '基线方法' },
  'entity.tool': { en: 'Tool', zh: '工具' },
  'entity.theory': { en: 'Theory', zh: '理论' },

  // Analysis tab
  'analysis.profile': { en: 'Paper Profile', zh: '论文画像' },
  'analysis.contributions': { en: 'Contributions', zh: '贡献点' },
  'analysis.limitations': { en: 'Limitations', zh: '局限性' },
  'analysis.runProfile': { en: 'Generate Profile', zh: '生成画像' },
  'analysis.runEntities': { en: 'Extract Entities', zh: '提取实体' },
  'analysis.runContributions': { en: 'Extract Contributions', zh: '提取贡献' },
  'analysis.runLimitations': { en: 'Identify Limitations', zh: '识别局限' },
  'analysis.noProfile': { en: 'No profile generated yet. Click "Generate Profile" to start.', zh: '尚未生成画像。点击"生成画像"开始。' },
  'analysis.noContributions': { en: 'No contributions extracted yet.', zh: '尚未提取贡献点。' },
  'analysis.noLimitations': { en: 'No limitations identified yet.', zh: '尚未识别局限性。' },
  'analysis.overall': { en: 'Overall Assessment', zh: '总体评估' },
  'analysis.innovation': { en: 'Innovation', zh: '创新性' },
  'analysis.methodology': { en: 'Methodology', zh: '方法复杂度' },
  'analysis.experiments': { en: 'Experiments', zh: '实验充分性' },
  'analysis.reproducibility': { en: 'Reproducibility', zh: '可复现性' },
  'analysis.impact': { en: 'Impact', zh: '影响力预测' },
  'analysis.suggestion': { en: 'Suggestion', zh: '建议' },
  'analysis.level.theoretical': { en: 'Theoretical', zh: '理论层面' },
  'analysis.level.technical': { en: 'Technical', zh: '技术层面' },
  'analysis.level.application': { en: 'Application', zh: '应用层面' },
  'analysis.severity.critical': { en: 'Critical', zh: '严重' },
  'analysis.severity.major': { en: 'Major', zh: '主要' },
  'analysis.severity.minor': { en: 'Minor', zh: '次要' },

  // Visualization tab
  'viz.knowledgeGraph': { en: 'Knowledge Graph', zh: '知识图谱' },
  'viz.flowchart': { en: 'Method Flowchart', zh: '方法流程图' },
  'viz.radar': { en: 'Radar Chart', zh: '雷达图' },
  'viz.noGraph': { en: 'No entities found. Extract entities in the Analysis tab first.', zh: '未找到实体。请先在"深度分析"标签页中提取实体。' },
  'viz.noFlowchart': { en: 'No flowchart data available.', zh: '无流程图数据。' },
  'viz.noRadar': { en: 'No radar data. Generate profile first.', zh: '无雷达图数据。请先生成画像。' },
  'viz.loadFailed': { en: 'Failed to load visualization', zh: '加载可视化失败' },

  // Relation type labels (for knowledge graph edges)
  'relation.uses': { en: 'uses', zh: '使用' },
  'relation.evaluates_on': { en: 'evaluates on', zh: '评估于' },
  'relation.improves': { en: 'improves', zh: '改进' },
  'relation.comparative': { en: 'compared with', zh: '对比' },
  'relation.part_of': { en: 'part of', zh: '属于' },
  'relation.causal': { en: 'leads to', zh: '导致' },
  'relation.co_occurrence': { en: 'related to', zh: '相关' },

  // Review tab
  'review.autoReview': { en: 'Auto Review', zh: '自动审稿' },
  'review.generate': { en: 'Generate Review', zh: '生成审稿意见' },
  'review.refresh': { en: 'Refresh Results', zh: '刷新结果' },
  'review.summary': { en: 'Summary', zh: '摘要评价' },
  'review.strengths': { en: 'Strengths', zh: '优点' },
  'review.weaknesses': { en: 'Weaknesses', zh: '不足' },
  'review.questions': { en: 'Questions to Authors', zh: '给作者的问题' },
  'review.recommendation': { en: 'Recommendation', zh: '推荐意见' },
  'review.confidence': { en: 'Confidence', zh: '置信度' },
  'review.controversy': { en: 'Controversy Analysis', zh: '争议性分析' },
  'review.reproducibility': { en: 'Reproducibility Checklist', zh: '可复现性检查' },
  'review.noReview': { en: 'No review generated yet. Click "Generate Review" to start.', zh: '尚未生成审稿意见。点击"生成审稿意见"开始。' },
  'review.overallConsistency': { en: 'Overall consistency', zh: '总体一致性' },
  'review.score': { en: 'Score', zh: '得分' },
  'review.rec.accept': { en: 'Accept', zh: '接受' },
  'review.rec.weak_accept': { en: 'Weak Accept', zh: '弱接受' },
  'review.rec.borderline': { en: 'Borderline', zh: '边界' },
  'review.rec.weak_reject': { en: 'Weak Reject', zh: '弱拒绝' },
  'review.rec.reject': { en: 'Reject', zh: '拒绝' },

  // Common
  'common.loading': { en: 'Loading...', zh: '加载中...' },
  'common.error': { en: 'Error', zh: '错误' },
  'common.retry': { en: 'Retry', zh: '重试' },
  'common.reparse': { en: 'Re-parse', zh: '重新解析' },
  'common.reparsing': { en: 'Re-parsing...', zh: '重新解析中...' },
  'common.apiKeyMissing': { en: 'Qwen API key not configured. Please set QWEN_API_KEY in backend/.env', zh: 'Qwen API 密钥未配置。请在 backend/.env 中设置 QWEN_API_KEY' },

  // Theme
  'theme.academic': { en: 'Academic', zh: '学术' },
  'theme.creative': { en: 'Creative', zh: '创意' },
  'theme.minimal': { en: 'Minimal', zh: '简约' },

  // Dimension labels (for radar chart and profile)
  'dim.innovation': { en: 'Innovation', zh: '创新性' },
  'dim.methodology': { en: 'Methodology', zh: '方法论' },
  'dim.experiments': { en: 'Experiments', zh: '实验' },
  'dim.reproducibility': { en: 'Reproducibility', zh: '可复现性' },
  'dim.impact': { en: 'Impact', zh: '影响力' },

  // Comparison page
  'compare.title': { en: 'Compare Papers', zh: '论文对比' },
  'compare.subtitle': { en: 'Select 2-5 papers to compare', zh: '选择 2-5 篇论文进行对比' },
  'compare.comparing': { en: 'Comparing...', zh: '对比中...' },
  'compare.button': { en: 'Compare', zh: '对比' },
  'compare.papers': { en: 'Papers', zh: '篇论文' },
  'compare.table': { en: 'Comparison Table', zh: '对比表格' },
  'compare.aspect': { en: 'Aspect', zh: '维度' },
  'compare.analysis': { en: 'Comparison Analysis', zh: '对比分析' },
  'common.failed': { en: 'Failed', zh: '失败' },

  // Language switcher
  'lang.switch': { en: 'Switch Language', zh: '切换语言' },
  'lang.en': { en: 'English', zh: 'English' },
  'lang.zh': { en: '中文', zh: '中文' },
  'lang.bilingual': { en: 'Bilingual Mode', zh: '双语模式' },
  'lang.auto': { en: 'Auto Detect', zh: '自动检测' },

  // Reading modes
  'reading.mode': { en: 'Reading Mode', zh: '阅读模式' },
  'reading.mode.scan': { en: 'Scan Mode', zh: '速览模式' },
  'reading.mode.scan.desc': { en: 'Quick overview for paper screening', zh: '快速浏览，筛选论文' },
  'reading.mode.deep': { en: 'Deep Mode', zh: '精读模式' },
  'reading.mode.deep.desc': { en: 'In-depth method understanding', zh: '深入理解论文方法' },
  'reading.mode.critical': { en: 'Critical Mode', zh: '批判模式' },
  'reading.mode.critical.desc': { en: 'Review and quality assessment', zh: '审稿评估视角' },

  // AI Chat
  'chat.title': { en: 'AI Assistant', zh: 'AI助手' },
  'chat.placeholder': { en: 'Ask about this paper...', zh: '询问关于这篇论文的问题...' },
  'chat.send': { en: 'Send', zh: '发送' },
  'chat.loading': { en: 'AI is thinking...', zh: 'AI思考中...' },
  'chat.summarize': { en: 'Summarize', zh: '总结' },
  'chat.translate': { en: 'Translate', zh: '翻译' },
  'chat.explain': { en: 'Explain', zh: '解释' },
  'chat.criticize': { en: 'Critique', zh: '批判分析' },
  'chat.selectText': { en: 'Ask about selection', zh: '询问选中内容' },
  'chat.quickActions': { en: 'Quick Actions', zh: '快捷操作' },
  'chat.close': { en: 'Close', zh: '关闭' },
  'chat.new': { en: 'New Chat', zh: '新对话' },

  // Paper translation
  'translate.title': { en: 'Translate Paper', zh: '翻译论文' },
  'translate.abstract': { en: 'Translate Abstract', zh: '翻译摘要' },
  'translate.section': { en: 'Translate Section', zh: '翻译章节' },
  'translate.toEn': { en: 'Translate to English', zh: '翻译成英文' },
  'translate.toZh': { en: 'Translate to Chinese', zh: '翻译成中文' },
  'translate.original': { en: 'Original', zh: '原文' },
  'translate.translated': { en: 'Translated', zh: '译文' },

  // Quick insights
  'insight.oneSentence': { en: 'One-sentence Summary', zh: '一句话总结' },
  'insight.keyInnovation': { en: 'Key Innovation', zh: '核心创新' },
  'insight.coreMethod': { en: 'Core Method', zh: '核心方法' },
  'insight.suitableFor': { en: 'Suitable For', zh: '适合人群' },
};

export type Language = 'en' | 'zh';

export function t(key: string, lang: Language): string {
  const entry = translations[key];
  if (!entry) return key;
  return entry[lang] || entry['en'] || key;
}
