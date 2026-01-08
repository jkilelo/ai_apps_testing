
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
