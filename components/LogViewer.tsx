
import React, { useEffect, useRef, useState, useMemo } from 'react';
import { ExecutionLog, EventType, LogLevel } from '../types';

interface LogViewerProps {
  logs: ExecutionLog[];
  maxSteps?: number;
  currentStep?: number;
}

interface StepGroup {
  stepNumber: number;
  logs: ExecutionLog[];
  isExpanded: boolean;
}

const EVENT_CONFIG: Record<EventType, { icon: string; color: string; bgColor: string; label: string }> = {
  step_start: { icon: 'fa-flag', color: 'text-purple-400', bgColor: 'bg-purple-500/10', label: 'STEP' },
  step_thinking: { icon: 'fa-brain', color: 'text-cyan-400', bgColor: 'bg-cyan-500/10', label: 'GOAL' },
  step_action: { icon: 'fa-bolt', color: 'text-amber-400', bgColor: 'bg-amber-500/10', label: 'ACTION' },
  step_result: { icon: 'fa-check-circle', color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', label: 'RESULT' },
  browser_state: { icon: 'fa-globe', color: 'text-blue-400', bgColor: 'bg-blue-500/10', label: 'BROWSER' },
  progress: { icon: 'fa-spinner', color: 'text-slate-400', bgColor: 'bg-slate-500/10', label: 'INFO' },
  error: { icon: 'fa-exclamation-triangle', color: 'text-rose-400', bgColor: 'bg-rose-500/10', label: 'ERROR' },
  done: { icon: 'fa-trophy', color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', label: 'DONE' },
  system: { icon: 'fa-cog', color: 'text-slate-500', bgColor: 'bg-slate-500/10', label: 'SYS' },
};

const LEVEL_CONFIG: Record<LogLevel, { color: string; textColor: string }> = {
  info: { color: 'text-blue-400', textColor: 'text-slate-300' },
  success: { color: 'text-emerald-400', textColor: 'text-emerald-300' },
  warn: { color: 'text-amber-400', textColor: 'text-amber-200' },
  error: { color: 'text-rose-400', textColor: 'text-rose-300' },
  debug: { color: 'text-slate-500', textColor: 'text-slate-400' },
};

const LogViewer: React.FC<LogViewerProps> = ({ logs, maxSteps = 30, currentStep = 0 }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isAutoScroll, setIsAutoScroll] = useState(true);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  const [viewMode, setViewMode] = useState<'stream' | 'grouped'>('stream');

  // Group logs by step
  const groupedLogs = useMemo((): Map<number, ExecutionLog[]> => {
    const groups = new Map<number, ExecutionLog[]>();
    let currentStepNum = 0;

    logs.forEach(log => {
      if (log.eventType === 'step_start' && log.step !== undefined) {
        currentStepNum = log.step;
      }
      const stepKey = log.step ?? currentStepNum;
      if (!groups.has(stepKey)) {
        groups.set(stepKey, []);
      }
      groups.get(stepKey)!.push(log);
    });

    return groups;
  }, [logs]);

  // Auto-scroll when new logs arrive (if enabled)
  useEffect(() => {
    if (isAutoScroll && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isAutoScroll]);

  // Handle scroll to detect user interaction
  const handleScroll = () => {
    if (scrollRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
      const isAtBottom = scrollHeight - scrollTop - clientHeight < 50;
      setIsAutoScroll(isAtBottom);
    }
  };

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

  const getEventConfig = (log: ExecutionLog) => {
    if (log.eventType && EVENT_CONFIG[log.eventType]) {
      return EVENT_CONFIG[log.eventType];
    }
    // Fallback based on level
    return {
      icon: 'fa-circle',
      color: LEVEL_CONFIG[log.level]?.color || 'text-slate-400',
      bgColor: 'bg-slate-500/10',
      label: log.level.toUpperCase()
    };
  };

  const renderLogEntry = (log: ExecutionLog, index: number) => {
    const config = getEventConfig(log);
    const levelConfig = LEVEL_CONFIG[log.level] || LEVEL_CONFIG.info;

    return (
      <div
        key={index}
        className={`flex gap-3 py-1.5 px-2 rounded-md transition-colors hover:bg-slate-800/50 ${config.bgColor}`}
      >
        {/* Timestamp */}
        <span className="text-slate-600 shrink-0 text-[10px] font-mono w-16">
          {log.timestamp}
        </span>

        {/* Event Type Badge */}
        <span className={`shrink-0 flex items-center gap-1.5 w-20`}>
          <i className={`fas ${config.icon} ${config.color} text-[10px]`}></i>
          <span className={`${config.color} text-[10px] font-bold uppercase tracking-wider`}>
            {config.label}
          </span>
        </span>

        {/* Message */}
        <span className={`${levelConfig.textColor} break-all flex-1`}>
          {log.message}
        </span>

        {/* Step indicator */}
        {log.step !== undefined && (
          <span className="text-slate-600 text-[10px] font-mono shrink-0">
            #{log.step}
          </span>
        )}
      </div>
    );
  };

  const renderGroupedView = () => {
    const stepNumbers = [...groupedLogs.keys()].sort((a, b) => a - b);

    return (
      <div className="space-y-2">
        {stepNumbers.map(stepNum => {
          const stepLogs = groupedLogs.get(stepNum) || [];
          const isExpanded = expandedSteps.has(stepNum);
          const hasError = stepLogs.some(l => l.level === 'error');
          const firstThinking = stepLogs.find(l => l.eventType === 'step_thinking');

          return (
            <div key={stepNum} className="border border-slate-800 rounded-lg overflow-hidden">
              {/* Step Header */}
              <button
                onClick={() => toggleStep(stepNum)}
                className={`w-full flex items-center gap-3 px-3 py-2 text-left transition-colors
                  ${hasError ? 'bg-rose-500/10 hover:bg-rose-500/20' : 'bg-slate-800/50 hover:bg-slate-800'}
                `}
              >
                <i className={`fas ${isExpanded ? 'fa-chevron-down' : 'fa-chevron-right'} text-slate-500 text-xs w-3`}></i>
                <span className="text-purple-400 font-mono text-xs font-bold">Step {stepNum}</span>
                {firstThinking && (
                  <span className="text-slate-400 text-xs truncate flex-1">
                    {firstThinking.message}
                  </span>
                )}
                <span className={`text-[10px] px-2 py-0.5 rounded ${hasError ? 'bg-rose-500/20 text-rose-400' : 'bg-slate-700 text-slate-400'}`}>
                  {stepLogs.length} events
                </span>
              </button>

              {/* Step Content */}
              {isExpanded && (
                <div className="px-3 py-2 border-t border-slate-800 space-y-1">
                  {stepLogs.map((log, idx) => renderLogEntry(log, idx))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    );
  };

  const progressPercent = maxSteps > 0 ? Math.min((currentStep / maxSteps) * 100, 100) : 0;

  return (
    <div className="bg-slate-950 rounded-xl border border-slate-800 overflow-hidden flex flex-col shadow-xl">
      {/* Header */}
      <div className="bg-slate-900 px-4 py-2.5 border-b border-slate-800 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <span className="text-xs font-mono text-slate-400 uppercase tracking-widest">
            Execution Terminal
          </span>
          {currentStep > 0 && (
            <span className="text-[10px] font-mono text-slate-500 bg-slate-800 px-2 py-0.5 rounded">
              Step {currentStep}/{maxSteps}
            </span>
          )}
        </div>

        <div className="flex items-center gap-3">
          {/* View Mode Toggle */}
          <div className="flex bg-slate-800 rounded-md p-0.5">
            <button
              onClick={() => setViewMode('stream')}
              className={`px-2 py-1 text-[10px] rounded transition-colors ${
                viewMode === 'stream' ? 'bg-slate-700 text-slate-200' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              Stream
            </button>
            <button
              onClick={() => setViewMode('grouped')}
              className={`px-2 py-1 text-[10px] rounded transition-colors ${
                viewMode === 'grouped' ? 'bg-slate-700 text-slate-200' : 'text-slate-500 hover:text-slate-300'
              }`}
            >
              Grouped
            </button>
          </div>

          {/* Auto-scroll indicator */}
          <button
            onClick={() => setIsAutoScroll(!isAutoScroll)}
            className={`text-[10px] px-2 py-1 rounded transition-colors ${
              isAutoScroll ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-slate-500'
            }`}
            title={isAutoScroll ? 'Auto-scroll ON' : 'Auto-scroll OFF'}
          >
            <i className={`fas fa-arrow-down mr-1`}></i>
            Auto
          </button>

          {/* Window dots */}
          <div className="flex gap-1.5 ml-2">
            <div className="w-2.5 h-2.5 rounded-full bg-rose-500/30"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-amber-500/30"></div>
            <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/30"></div>
          </div>
        </div>
      </div>

      {/* Progress Bar */}
      {currentStep > 0 && (
        <div className="h-1 bg-slate-800">
          <div
            className="h-full bg-gradient-to-r from-blue-500 to-purple-500 transition-all duration-300"
            style={{ width: `${progressPercent}%` }}
          />
        </div>
      )}

      {/* Log Content */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 p-3 font-mono text-xs overflow-y-auto min-h-[250px] max-h-[400px] scrollbar-thin scrollbar-thumb-slate-700 scrollbar-track-slate-900"
      >
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-600">
            <i className="fas fa-terminal text-2xl mb-2 opacity-50"></i>
            <span className="animate-pulse">Waiting for execution...</span>
          </div>
        ) : viewMode === 'stream' ? (
          <div className="space-y-0.5">
            {logs.map((log, i) => renderLogEntry(log, i))}
          </div>
        ) : (
          renderGroupedView()
        )}
      </div>

      {/* Footer Stats */}
      {logs.length > 0 && (
        <div className="bg-slate-900/50 px-4 py-2 border-t border-slate-800 flex items-center justify-between text-[10px] text-slate-500">
          <div className="flex items-center gap-4">
            <span><i className="fas fa-list mr-1"></i>{logs.length} events</span>
            <span><i className="fas fa-layer-group mr-1"></i>{groupedLogs.size} steps</span>
          </div>
          <div className="flex items-center gap-3">
            {logs.filter(l => l.level === 'error').length > 0 && (
              <span className="text-rose-400">
                <i className="fas fa-exclamation-circle mr-1"></i>
                {logs.filter(l => l.level === 'error').length} errors
              </span>
            )}
            {logs.filter(l => l.level === 'success').length > 0 && (
              <span className="text-emerald-400">
                <i className="fas fa-check-circle mr-1"></i>
                {logs.filter(l => l.level === 'success').length} success
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LogViewer;
