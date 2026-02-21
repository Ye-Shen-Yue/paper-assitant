export const API_BASE_URL = '/api/v1';

export const ENTITY_TYPE_COLORS: Record<string, string> = {
  research_problem: '#ef4444',
  method: '#3b82f6',
  dataset: '#22c55e',
  metric: '#f59e0b',
  innovation: '#8b5cf6',
  baseline: '#6b7280',
  tool: '#06b6d4',
  theory: '#ec4899',
};

// i18n keys for entity type labels
export const ENTITY_TYPE_KEYS: Record<string, string> = {
  research_problem: 'entity.research_problem',
  method: 'entity.method',
  dataset: 'entity.dataset',
  metric: 'entity.metric',
  innovation: 'entity.innovation',
  baseline: 'entity.baseline',
  tool: 'entity.tool',
  theory: 'entity.theory',
};

// i18n keys for section type labels
export const SECTION_TYPE_KEYS: Record<string, string> = {
  title: 'section.title',
  abstract: 'section.abstract',
  introduction: 'section.introduction',
  related_work: 'section.related_work',
  methods: 'section.methods',
  experiments: 'section.experiments',
  results: 'section.results',
  discussion: 'section.discussion',
  conclusion: 'section.conclusion',
  references: 'section.references',
  acknowledgments: 'section.acknowledgments',
  appendix: 'section.appendix',
  other: 'section.other',
};

// Fallback English labels
export const ENTITY_TYPE_LABELS: Record<string, string> = {
  research_problem: 'Research Problem',
  method: 'Method',
  dataset: 'Dataset',
  metric: 'Metric',
  innovation: 'Innovation',
  baseline: 'Baseline',
  tool: 'Tool',
  theory: 'Theory',
};

export const SECTION_TYPE_LABELS: Record<string, string> = {
  title: 'Title',
  abstract: 'Abstract',
  introduction: 'Introduction',
  related_work: 'Related Work',
  methods: 'Methods',
  experiments: 'Experiments',
  results: 'Results',
  discussion: 'Discussion',
  conclusion: 'Conclusion',
  references: 'References',
  other: 'Other',
};
