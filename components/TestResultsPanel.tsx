
import React, { useState, useMemo } from 'react';
import { ExecutionLog } from '../types';

interface TestResultsPanelProps {
  logs: ExecutionLog[];
  result: {
    success: boolean;
    summary: string;
    data?: Record<string, unknown>;
  } | null;
  isRunning: boolean;
  currentStep: number;
  maxSteps: number;
}

interface StepSummary {
  stepNumber: number;
  goal: string;
  actions: string[];
  hasError: boolean;
  errorMessage?: string;
}

const TestResultsPanel: React.FC<TestResultsPanelProps> = ({
  logs,
  result,
  isRunning,
  currentStep,
  maxSteps,
}) => {
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());

  // Process logs into step summaries
  const stepSummaries = useMemo((): StepSummary[] => {
    const summaries: Map<number, StepSummary> = new Map();

    logs.forEach(log => {
      const stepNum = log.step ?? 0;

      if (!summaries.has(stepNum)) {
        summaries.set(stepNum, {
          stepNumber: stepNum,
          goal: '',
          actions: [],
          hasError: false,
        });
      }

      const summary = summaries.get(stepNum)!;

      if (log.eventType === 'step_thinking' && !summary.goal) {
        summary.goal = log.message;
      }
      if (log.eventType === 'step_action') {
        summary.actions.push(log.message);
      }
      if (log.level === 'error') {
        summary.hasError = true;
        summary.errorMessage = log.message;
      }
    });

    return Array.from(summaries.values()).sort((a, b) => a.stepNumber - b.stepNumber);
  }, [logs]);

  // Calculate statistics
  const stats = useMemo(() => {
    const totalSteps = stepSummaries.length;
    const failedSteps = stepSummaries.filter(s => s.hasError).length;
    const passedSteps = totalSteps - failedSteps;
    const totalActions = stepSummaries.reduce((acc, s) => acc + s.actions.length, 0);
    const passRate = totalSteps > 0 ? (passedSteps / totalSteps) * 100 : 0;

    return { totalSteps, passedSteps, failedSteps, totalActions, passRate };
  }, [stepSummaries]);

  const toggleStep = (stepNum: number) => {
    setExpandedSteps(prev => {
      const newSet = new Set(prev);
      if (newSet.has(stepNum)) {
        newSet.delete(stepNum);
      } else {
        newSet.add(stepNum);
      }
      return newSet;
    });
  };

  // Don't show panel if no logs and not running
  if (logs.length === 0 && !isRunning && !result) {
    return null;
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-50 to-slate-100 px-6 py-4 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <i className="fas fa-chart-bar text-blue-500"></i>
            Test Results
          </h3>
          {isRunning && (
            <span className="flex items-center gap-2 text-sm text-amber-600 bg-amber-50 px-3 py-1 rounded-full">
              <i className="fas fa-spinner fa-spin"></i>
              Running...
            </span>
          )}
          {result && !isRunning && (
            <span className={`flex items-center gap-2 text-sm px-3 py-1 rounded-full ${
              result.success
                ? 'text-emerald-600 bg-emerald-50'
                : 'text-rose-600 bg-rose-50'
            }`}>
              <i className={`fas ${result.success ? 'fa-check-circle' : 'fa-times-circle'}`}></i>
              {result.success ? 'Completed' : 'Failed'}
            </span>
          )}
        </div>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 p-6 bg-slate-50/50">
        {/* Total Steps */}
        <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
              <i className="fas fa-layer-group text-blue-600"></i>
            </div>
            <div>
              <div className="text-2xl font-bold text-slate-800">{stats.totalSteps}</div>
              <div className="text-xs text-slate-500 uppercase tracking-wide">Steps</div>
            </div>
          </div>
        </div>

        {/* Passed */}
        <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
              <i className="fas fa-check text-emerald-600"></i>
            </div>
            <div>
              <div className="text-2xl font-bold text-emerald-600">{stats.passedSteps}</div>
              <div className="text-xs text-slate-500 uppercase tracking-wide">Passed</div>
            </div>
          </div>
        </div>

        {/* Failed */}
        <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-lg bg-rose-100 flex items-center justify-center">
              <i className="fas fa-times text-rose-600"></i>
            </div>
            <div>
              <div className="text-2xl font-bold text-rose-600">{stats.failedSteps}</div>
              <div className="text-xs text-slate-500 uppercase tracking-wide">Failed</div>
            </div>
          </div>
        </div>

        {/* Pass Rate */}
        <div className="bg-white rounded-lg p-4 border border-slate-200 shadow-sm">
          <div className="flex items-center gap-3">
            <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
              stats.passRate >= 80 ? 'bg-emerald-100' : stats.passRate >= 50 ? 'bg-amber-100' : 'bg-rose-100'
            }`}>
              <i className={`fas fa-percentage ${
                stats.passRate >= 80 ? 'text-emerald-600' : stats.passRate >= 50 ? 'text-amber-600' : 'text-rose-600'
              }`}></i>
            </div>
            <div>
              <div className={`text-2xl font-bold ${
                stats.passRate >= 80 ? 'text-emerald-600' : stats.passRate >= 50 ? 'text-amber-600' : 'text-rose-600'
              }`}>
                {stats.passRate.toFixed(0)}%
              </div>
              <div className="text-xs text-slate-500 uppercase tracking-wide">Pass Rate</div>
            </div>
          </div>
        </div>
      </div>

      {/* Progress Bar (when running) */}
      {isRunning && (
        <div className="px-6 py-3 bg-white border-t border-slate-100">
          <div className="flex items-center justify-between text-xs text-slate-500 mb-2">
            <span>Progress</span>
            <span>{currentStep} / {maxSteps} steps</span>
          </div>
          <div className="h-2 bg-slate-100 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
              style={{ width: `${(currentStep / maxSteps) * 100}%` }}
            />
          </div>
        </div>
      )}

      {/* Result Summary */}
      {result && (
        <div className={`px-6 py-4 border-t ${
          result.success ? 'bg-emerald-50 border-emerald-100' : 'bg-rose-50 border-rose-100'
        }`}>
          <p className={`text-sm ${result.success ? 'text-emerald-800' : 'text-rose-800'}`}>
            {result.summary}
          </p>
        </div>
      )}

      {/* Step Breakdown */}
      {stepSummaries.length > 0 && (
        <div className="border-t border-slate-200">
          <div className="px-6 py-3 bg-slate-50 border-b border-slate-200">
            <h4 className="text-sm font-semibold text-slate-700 flex items-center gap-2">
              <i className="fas fa-list-ol text-slate-400"></i>
              Step Breakdown
            </h4>
          </div>
          <div className="divide-y divide-slate-100 max-h-80 overflow-y-auto">
            {stepSummaries.map((step) => (
              <div key={step.stepNumber} className="group">
                <button
                  onClick={() => toggleStep(step.stepNumber)}
                  className={`w-full px-6 py-3 flex items-center gap-3 text-left hover:bg-slate-50 transition-colors ${
                    step.hasError ? 'bg-rose-50/50' : ''
                  }`}
                >
                  {/* Step indicator */}
                  <div className={`w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold ${
                    step.hasError
                      ? 'bg-rose-100 text-rose-600'
                      : 'bg-emerald-100 text-emerald-600'
                  }`}>
                    {step.hasError ? <i className="fas fa-times"></i> : <i className="fas fa-check"></i>}
                  </div>

                  {/* Step info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-xs font-mono text-slate-400">Step {step.stepNumber}</span>
                      <span className="text-xs text-slate-300">|</span>
                      <span className="text-xs text-slate-500">{step.actions.length} action(s)</span>
                    </div>
                    <div className="text-sm text-slate-700 truncate">
                      {step.goal || 'Processing...'}
                    </div>
                  </div>

                  {/* Expand icon */}
                  <i className={`fas fa-chevron-right text-slate-300 text-xs transition-transform ${
                    expandedSteps.has(step.stepNumber) ? 'rotate-90' : ''
                  }`}></i>
                </button>

                {/* Expanded content */}
                {expandedSteps.has(step.stepNumber) && (
                  <div className="px-6 py-3 bg-slate-50 border-t border-slate-100">
                    {step.actions.length > 0 && (
                      <div className="space-y-1.5">
                        {step.actions.map((action, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-xs">
                            <i className="fas fa-bolt text-amber-400 mt-0.5"></i>
                            <span className="text-slate-600">{action}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {step.hasError && step.errorMessage && (
                      <div className="mt-2 p-2 bg-rose-100 rounded text-xs text-rose-700">
                        <i className="fas fa-exclamation-triangle mr-1"></i>
                        {step.errorMessage}
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Actions Count Footer */}
      <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 flex items-center justify-between text-xs text-slate-500">
        <span>
          <i className="fas fa-bolt mr-1"></i>
          {stats.totalActions} total actions
        </span>
        {result?.data?.output_directory && (
          <span className="text-blue-600">
            <i className="fas fa-folder mr-1"></i>
            {String(result.data.output_directory)}
          </span>
        )}
      </div>
    </div>
  );
};

export default TestResultsPanel;
