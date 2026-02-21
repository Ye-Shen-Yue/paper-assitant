// ===== Paper Types =====
export interface PaperSummary {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  upload_date: string;
  parsing_status: string;
  language: string;
  page_count: number;
}

export interface PaperSection {
  id: string;
  section_type: string;
  heading: string;
  content: string;
  page_start: number;
  page_end: number;
  order: number;
}

export interface PaperEntity {
  id: string;
  text: string;
  entity_type: string;
  section_id: string | null;
  start_char: number;
  end_char: number;
  confidence: number;
}

export interface Reference {
  id: string;
  raw_text: string;
  title: string | null;
  authors: string[];
  year: number | null;
  venue: string | null;
  doi: string | null;
  order: number;
}

export interface ExtractedTable {
  id: string;
  caption: string;
  headers: string[];
  rows: string[][];
  page: number;
}

export interface PaperDetail extends PaperSummary {
  sections: PaperSection[];
  entities: PaperEntity[];
  references: Reference[];
  tables: ExtractedTable[];
  doi: string | null;
  venue: string | null;
  year: number | null;
  keywords: string[];
  pdf_path: string;
  file_size: number;
}

// ===== Analysis Types =====
export interface DimensionScore {
  dimension: string;
  score: number;
  reasoning: string;
  evidence: string[];
}

export interface PaperProfile {
  paper_id: string;
  dimensions: DimensionScore[];
  overall_assessment: string;
  generated_at: string | null;
}

export interface Contribution {
  level: string;
  description: string;
  evidence: string[];
  significance: string;
}

export interface Limitation {
  category: string;
  description: string;
  severity: string;
  suggestion: string;
}

export interface Relationship {
  source_entity_id: string;
  target_entity_id: string;
  source_text: string;
  target_text: string;
  relation_type: string;
  description: string;
  confidence: number;
}

// ===== Review Types =====
export interface ReviewResult {
  paper_id: string;
  summary: string;
  strengths: string[];
  weaknesses: string[];
  questions_to_authors: string[];
  overall_recommendation: string;
  confidence: number;
  generated_at: string | null;
}

export interface ControversyClaim {
  claim: string;
  evidence_for: string[];
  evidence_against: string[];
  consistency_score: number;
  assessment: string;
}

export interface ReproducibilityItem {
  criterion: string;
  status: string;
  details: string;
}

// ===== Visualization Types =====
export interface GraphNode {
  id: string;
  label: string;
  node_type: string;
  size: number;
  metadata: Record<string, unknown>;
}

export interface GraphEdge {
  source: string;
  target: string;
  relation: string;
  label?: string;
  weight: number;
}

export interface GraphData {
  nodes: GraphNode[];
  edges: GraphEdge[];
}

export interface FlowchartData {
  mermaid_code: string;
  steps: Record<string, unknown>[];
}

export interface TimelineEntry {
  year: number;
  event: string;
  category: string;
  related_paper: string | null;
}

export interface TimelineData {
  entries: TimelineEntry[];
  current_paper_position: Record<string, unknown>;
}

export interface RadarData {
  dimensions: string[];
  scores: number[];
  max_score: number;
  paper_title: string;
}

// ===== Common Types =====
export interface TaskResponse {
  task_id: string;
  status: string;
  message: string;
}

export interface TaskStatus {
  task_id: string;
  paper_id: string;
  task_type: string;
  status: string;
  progress: number;
  current_step: string;
  created_at: string;
  updated_at: string;
  error_message: string | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  total_pages: number;
}
