
export enum AppId {
  UI_AUTOMATOR = 'ui-automator',
  DATA_PROFILER = 'data-profiler',
  QUALITY_CHECKER = 'quality-checker',
  RESULTS_GALLERY = 'results-gallery'
}

export interface AppMetadata {
  id: AppId;
  name: string;
  icon: string;
  description: string;
}

export interface ExecutionLog {
  timestamp: string;
  level: 'info' | 'warn' | 'error' | 'success';
  message: string;
}

export interface AutomationResult {
  task: string;
  steps: { action: string; status: 'done' | 'pending' | 'failed' }[];
  summary: string;
  screenshotUrl?: string;
}

export interface DataProfileResult {
  fileName: string;
  stats: {
    rows: number;
    columns: number;
    missingValues: number;
    duplicateRows: number;
  };
  insights: string[];
  anomalies: string[];
}


// ============== Advanced Browser Service Types ==============

export type AgentMode = 'basic' | 'extract' | 'research' | 'compare-products' | 'compare-pages';

export interface TaskStep {
  action: string;
  status: string;
}

export interface AdvancedTaskResult {
  success: boolean;
  task_type: string;
  summary: string;
  data: Record<string, unknown>;
  steps: TaskStep[];
  error?: string | null;
}

export interface ExtractedDataItem {
  [key: string]: string | number | boolean | null;
}

export interface ResearchSource {
  url: string;
  title: string;
  summary: string;
}

export interface ResearchFindings {
  topic: string;
  sources: ResearchSource[];
  key_findings: string[];
  summary: string;
}

export interface ProductComparison {
  products: string[];
  aspects: string[];
  comparison_matrix: Record<string, Record<string, string>>;
  recommendation: string;
}

export interface ParallelTaskInput {
  id: string;
  description: string;
  max_steps?: number;
}
