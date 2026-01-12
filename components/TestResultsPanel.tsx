
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

  // Show empty state if no data
  if (logs.length === 0 && !isRunning && !result) {
    return (
      <div className="h-full flex items-center justify-center bg-acme-gray-50/50">
        <div className="text-center max-w-xs">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-acme-gray-100 flex items-center justify-center">
            <i className="fas fa-chart-pie text-2xl text-acme-gray-300"></i>
          </div>
          <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">No Results Yet</h3>
          <p className="text-xs text-acme-gray-600">Run a task to see execution results and analytics</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-acme-gray-50/30 overflow-hidden">
      {/* Dashboard Stats - Corporate Widget Style */}
      <div className="p-4 border-b border-acme-gray-100 flex-shrink-0 overflow-x-auto">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 min-w-0">
          {/* Steps Widget */}
          <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-semibold text-acme-gray-600 uppercase tracking-wider">Steps</span>
              <div className="w-6 h-6 rounded-lg bg-acme-navy/10 flex items-center justify-center">
                <i className="fas fa-layer-group text-[10px] text-acme-navy"></i>
              </div>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-acme-gray-800">{stats.totalSteps}</span>
              <span className="text-xs text-acme-gray-500">total</span>
            </div>
          </div>

          {/* Passed Widget */}
          <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-semibold text-acme-gray-600 uppercase tracking-wider">Passed</span>
              <div className="w-6 h-6 rounded-lg bg-emerald-50 flex items-center justify-center">
                <i className="fas fa-check text-[10px] text-emerald-600"></i>
              </div>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-emerald-600">{stats.passedSteps}</span>
              <span className="text-xs text-acme-gray-500">steps</span>
            </div>
          </div>

          {/* Failed Widget */}
          <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-semibold text-acme-gray-600 uppercase tracking-wider">Failed</span>
              <div className="w-6 h-6 rounded-lg bg-acme-red/10 flex items-center justify-center">
                <i className="fas fa-times text-[10px] text-acme-red"></i>
              </div>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="text-2xl font-bold text-acme-red">{stats.failedSteps}</span>
              <span className="text-xs text-acme-gray-500">errors</span>
            </div>
          </div>

          {/* Success Rate Widget */}
          <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-[10px] font-semibold text-acme-gray-600 uppercase tracking-wider">Success</span>
              {isRunning && (
                <i className="fas fa-spinner fa-spin text-[10px] text-acme-navy"></i>
              )}
            </div>
            <div className="flex items-baseline gap-1">
              <span className={`text-2xl font-bold ${
                stats.passRate >= 80 ? 'text-emerald-600' :
                stats.passRate >= 50 ? 'text-amber-600' : 'text-acme-red'
              }`}>{stats.passRate.toFixed(0)}</span>
              <span className="text-xs text-acme-gray-500">%</span>
            </div>
            {/* Mini progress bar */}
            <div className="mt-2 h-1.5 bg-acme-gray-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-500 ${
                  stats.passRate >= 80 ? 'bg-emerald-500' :
                  stats.passRate >= 50 ? 'bg-amber-500' : 'bg-acme-red'
                }`}
                style={{ width: `${stats.passRate}%` }}
              />
            </div>
          </div>
        </div>
      </div>

      {/* Status Banner */}
      {(isRunning || result) && (
        <div className={`px-4 py-3 flex items-center gap-3 border-b flex-shrink-0 ${
          isRunning
            ? 'bg-acme-navy/5 border-acme-navy/10'
            : result?.success
              ? 'bg-emerald-50 border-emerald-100'
              : 'bg-acme-red/5 border-acme-red/10'
        }`}>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            isRunning
              ? 'bg-acme-navy/10'
              : result?.success
                ? 'bg-emerald-100'
                : 'bg-acme-red/10'
          }`}>
            <i className={`fas ${
              isRunning
                ? 'fa-spinner fa-spin text-acme-navy'
                : result?.success
                  ? 'fa-check text-emerald-600'
                  : 'fa-exclamation-triangle text-acme-red'
            } text-sm`}></i>
          </div>
          <div className="flex-1 min-w-0">
            <p className={`text-sm font-medium ${
              isRunning
                ? 'text-acme-navy'
                : result?.success
                  ? 'text-emerald-800'
                  : 'text-acme-red'
            }`}>
              {isRunning ? `Running step ${currentStep} of ${maxSteps}...` : result?.summary}
            </p>
            {result?.data?.output_directory && (
              <p className="text-xs text-acme-gray-600 mt-0.5 truncate">
                <i className="fas fa-folder-open mr-1"></i>
                {String(result.data.output_directory)}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Step Breakdown - Card List */}
      <div className="flex-1 overflow-y-auto p-4">
        <div className="space-y-2">
          {stepSummaries.length > 0 ? (
            stepSummaries.map((step) => (
              <div
                key={step.stepNumber}
                className={`bg-white rounded-xl border overflow-hidden transition-all hover:shadow-sm ${
                  step.hasError ? 'border-acme-red/30' : 'border-acme-gray-200'
                }`}
              >
                <button
                  onClick={() => toggleStep(step.stepNumber)}
                  className="w-full px-4 py-3 flex items-center gap-3 text-left"
                >
                  {/* Status Icon */}
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${
                    step.hasError ? 'bg-acme-red/10' : 'bg-emerald-50'
                  }`}>
                    {step.hasError
                      ? <i className="fas fa-times text-acme-red text-xs"></i>
                      : <i className="fas fa-check text-emerald-600 text-xs"></i>
                    }
                  </div>

                  {/* Step Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-0.5">
                      <span className="text-[10px] font-bold text-acme-navy bg-acme-navy/10 px-2 py-0.5 rounded-full">
                        STEP {step.stepNumber}
                      </span>
                      <span className="text-[10px] text-acme-gray-500">
                        {step.actions.length} action{step.actions.length !== 1 ? 's' : ''}
                      </span>
                    </div>
                    <p className="text-sm text-acme-gray-700 truncate font-medium">
                      {step.goal || 'Processing...'}
                    </p>
                  </div>

                  {/* Chevron */}
                  <i className={`fas fa-chevron-right text-acme-gray-400 text-xs transition-transform ${
                    expandedSteps.has(step.stepNumber) ? 'rotate-90' : ''
                  }`}></i>
                </button>

                {/* Expanded Content */}
                {expandedSteps.has(step.stepNumber) && (
                  <div className="px-4 pb-4 pt-2 border-t border-acme-gray-100 ml-11 overflow-hidden">
                    {step.actions.length > 0 && (
                      <div className="space-y-2">
                        {step.actions.map((action, idx) => (
                          <div key={idx} className="flex items-start gap-2 text-xs min-w-0">
                            <div className="w-5 h-5 rounded-md bg-amber-50 flex items-center justify-center flex-shrink-0 mt-0.5">
                              <i className="fas fa-bolt text-amber-600 text-[8px]"></i>
                            </div>
                            <span className="text-acme-gray-700 leading-relaxed break-words min-w-0">{action}</span>
                          </div>
                        ))}
                      </div>
                    )}
                    {step.hasError && step.errorMessage && (
                      <div className="mt-3 p-3 bg-acme-red/5 border border-acme-red/20 rounded-lg overflow-hidden">
                        <div className="flex items-start gap-2 min-w-0">
                          <i className="fas fa-exclamation-triangle text-acme-red text-xs mt-0.5 flex-shrink-0"></i>
                          <span className="text-xs text-acme-red break-words min-w-0">{step.errorMessage}</span>
                        </div>
                      </div>
                    )}
                  </div>
                )}
              </div>
            ))
          ) : (
            <div className="text-center py-12">
              <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-acme-gray-100 flex items-center justify-center">
                <i className="fas fa-list-ul text-acme-gray-300 text-lg"></i>
              </div>
              <p className="text-sm text-acme-gray-600">No steps recorded yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Footer Stats */}
      <div className="px-4 py-2 bg-white border-t border-acme-gray-200 flex items-center justify-between text-xs text-acme-gray-600 flex-shrink-0">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5">
            <i className="fas fa-bolt text-amber-500"></i>
            <span className="font-medium">{stats.totalActions}</span> actions
          </span>
          <span className="flex items-center gap-1.5">
            <i className="fas fa-layer-group text-acme-navy"></i>
            <span className="font-medium">{stats.totalSteps}</span> steps
          </span>
        </div>
        <span className="text-acme-gray-500 text-[10px]">
          Updated {new Date().toLocaleTimeString()}
        </span>
      </div>
    </div>
  );
};

export default TestResultsPanel;
