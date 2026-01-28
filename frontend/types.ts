
export enum AppId {
  UI_AUTOMATOR = 'ui-automator',
  RESULTS_GALLERY = 'results-gallery'
}

export interface AppMetadata {
  id: AppId;
  name: string;
  icon: string;
  description: string;
}

export type LogLevel = 'info' | 'warn' | 'error' | 'success' | 'debug';
export type EventType = 'step_start' | 'step_thinking' | 'step_action' | 'step_result' | 'browser_state' | 'progress' | 'error' | 'done' | 'system';

export interface ExecutionLog {
  timestamp: string;
  level: LogLevel;
  message: string;
  eventType?: EventType;
  step?: number;
  data?: Record<string, unknown>;
}

export interface AutomationResult {
  task: string;
  steps: { action: string; status: 'done' | 'pending' | 'failed' }[];
  summary: string;
  screenshotUrl?: string;
}



// ============== Advanced Browser Service Types ==============

export type AgentMode = 'basic' | 'extract' | 'research' | 'compare-products' | 'compare-pages' | 'a11y-audit';

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
