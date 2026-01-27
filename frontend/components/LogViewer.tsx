
import React, { useEffect, useRef, useState, useMemo } from 'react';
import { ExecutionLog, EventType, LogLevel } from '../types';

interface LogViewerProps {
  logs: ExecutionLog[];
  maxSteps?: number;
  currentStep?: number;
  onClear?: () => void;
  isInitializing?: boolean;
  isRunning?: boolean;
}

const EVENT_CONFIG: Record<EventType, { icon: string; color: string; bgColor: string; label: string }> = {
  step_start: { icon: 'fa-flag', color: 'text-sky-400', bgColor: 'bg-sky-500/10', label: 'STEP' },
  step_thinking: { icon: 'fa-brain', color: 'text-violet-400', bgColor: 'bg-violet-500/10', label: 'GOAL' },
  step_action: { icon: 'fa-bolt', color: 'text-amber-400', bgColor: 'bg-amber-500/10', label: 'ACTION' },
  step_result: { icon: 'fa-check-circle', color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', label: 'RESULT' },
  browser_state: { icon: 'fa-globe', color: 'text-sky-400', bgColor: 'bg-sky-500/10', label: 'BROWSER' },
  progress: { icon: 'fa-spinner', color: 'text-acme-gray-400', bgColor: 'bg-acme-gray-500/10', label: 'INFO' },
  error: { icon: 'fa-exclamation-triangle', color: 'text-acme-red', bgColor: 'bg-acme-red/10', label: 'ERROR' },
  done: { icon: 'fa-trophy', color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', label: 'DONE' },
  system: { icon: 'fa-cog', color: 'text-acme-gray-500', bgColor: 'bg-acme-gray-500/10', label: 'SYS' },
};

const LEVEL_CONFIG: Record<LogLevel, { color: string; textColor: string; badge: string }> = {
  info: { color: 'text-sky-400', textColor: 'text-acme-gray-300', badge: 'bg-sky-500/20 text-sky-400' },
  success: { color: 'text-emerald-400', textColor: 'text-emerald-300', badge: 'bg-emerald-500/20 text-emerald-400' },
  warn: { color: 'text-amber-400', textColor: 'text-amber-200', badge: 'bg-amber-500/20 text-amber-400' },
  error: { color: 'text-acme-red', textColor: 'text-red-300', badge: 'bg-acme-red/20 text-acme-red' },
  debug: { color: 'text-acme-gray-500', textColor: 'text-acme-gray-400', badge: 'bg-acme-gray-500/20 text-acme-gray-400' },
};

const LogViewer: React.FC<LogViewerProps> = ({ logs, maxSteps = 30, currentStep = 0, onClear, isInitializing = false, isRunning = false }) => {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [isAutoScroll, setIsAutoScroll] = useState(true);
  const [expandedSteps, setExpandedSteps] = useState<Set<number>>(new Set());
  const [viewMode, setViewMode] = useState<'stream' | 'grouped'>('stream');
  const [copiedIndex, setCopiedIndex] = useState<number | null>(null);
  const [showFilters, setShowFilters] = useState(false);
  const [levelFilters, setLevelFilters] = useState<Set<LogLevel>>(new Set(['info', 'success', 'warn', 'error', 'debug']));
  const [searchText, setSearchText] = useState('');

  // Filter logs based on level and search text
  const filteredLogs = useMemo(() => {
    return logs.filter(log => {
      if (!levelFilters.has(log.level)) return false;
      if (searchText && !log.message.toLowerCase().includes(searchText.toLowerCase())) return false;
      return true;
    });
  }, [logs, levelFilters, searchText]);

  // Toggle a level filter
  const toggleLevelFilter = (level: LogLevel) => {
    setLevelFilters(prev => {
      const newSet = new Set(prev);
      if (newSet.has(level)) {
        newSet.delete(level);
      } else {
        newSet.add(level);
      }
      return newSet;
    });
  };

  // Copy log entry to clipboard
  const copyLogEntry = async (log: ExecutionLog, index: number) => {
    const text = `[${log.timestamp}] [${log.eventType || log.level}] ${log.message}`;
    await navigator.clipboard.writeText(text);
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 1500);
  };

  // Group logs by step
  const groupedLogs = useMemo((): Map<number, ExecutionLog[]> => {
    const groups = new Map<number, ExecutionLog[]>();
    let currentStepNum = 0;

    filteredLogs.forEach(log => {
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
  }, [filteredLogs]);

  // Auto-scroll when new logs arrive
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
    return {
      icon: 'fa-circle',
      color: LEVEL_CONFIG[log.level]?.color || 'text-acme-gray-400',
      bgColor: 'bg-acme-gray-500/10',
      label: log.level.toUpperCase()
    };
  };

  const renderLogEntry = (log: ExecutionLog, index: number) => {
    const config = getEventConfig(log);
    const levelConfig = LEVEL_CONFIG[log.level] || LEVEL_CONFIG.info;

    return (
      <div
        key={index}
        className="group flex items-start gap-3 py-2 px-3 border-b border-acme-navy-dark/50 hover:bg-acme-navy-dark/30 transition-colors animate-logEntryIn"
      >
        {/* Timestamp */}
        <span className="text-acme-gray-400 shrink-0 text-[11px] font-mono pt-0.5">
          {log.timestamp}
        </span>

        {/* Event Type Badge */}
        <div className={`shrink-0 flex items-center gap-1.5 px-2 py-0.5 rounded-full ${config.bgColor}`}>
          <i className={`fas ${config.icon} ${config.color} text-[10px]`}></i>
          <span className={`${config.color} text-[11px] font-bold uppercase tracking-wider`}>
            {config.label}
          </span>
        </div>

        {/* Message */}
        <span className={`${levelConfig.textColor} text-xs break-all flex-1 leading-relaxed`}>
          {log.message}
        </span>

        {/* Actions */}
        <div className="shrink-0 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
          <button
            onClick={() => copyLogEntry(log, index)}
            className={`text-xs w-6 h-6 rounded flex items-center justify-center transition-all ${
              copiedIndex === index
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'bg-acme-navy-dark text-acme-gray-400 hover:text-white hover:bg-acme-navy-light'
            }`}
            title="Copy log entry"
          >
            <i className={`fas ${copiedIndex === index ? 'fa-check' : 'fa-copy'}`}></i>
          </button>
        </div>

        {/* Step indicator */}
        {log.step !== undefined && (
          <span className="text-acme-gray-300 text-[11px] font-mono shrink-0 bg-acme-navy-dark px-1.5 py-0.5 rounded">
            #{log.step}
          </span>
        )}
      </div>
    );
  };

  const renderGroupedView = () => {
    const stepNumbers = [...groupedLogs.keys()].sort((a, b) => a - b);

    return (
      <div className="space-y-3 p-3">
        {stepNumbers.map(stepNum => {
          const stepLogs = groupedLogs.get(stepNum) || [];
          const isExpanded = expandedSteps.has(stepNum);
          const hasError = stepLogs.some(l => l.level === 'error');
          const firstThinking = stepLogs.find(l => l.eventType === 'step_thinking');
          const actionCount = stepLogs.filter(l => l.eventType === 'step_action').length;

          return (
            <div
              key={stepNum}
              className={`rounded-xl overflow-hidden border ${
                hasError ? 'border-acme-red/30 bg-acme-red/5' : 'border-acme-navy-light/50 bg-acme-navy-dark/30'
              }`}
            >
              {/* Step Header */}
              <button
                onClick={() => toggleStep(stepNum)}
                className="w-full flex items-center gap-3 px-4 py-3 text-left hover:bg-acme-navy-dark/50 transition-colors"
              >
                {/* Step Number Badge */}
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                  hasError ? 'bg-acme-red/20' : 'bg-acme-navy-light'
                }`}>
                  <span className={`text-xs font-bold ${hasError ? 'text-acme-red' : 'text-white'}`}>
                    {stepNum}
                  </span>
                </div>

                {/* Step Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-0.5">
                    <span className="text-[11px] font-bold text-sky-400 uppercase tracking-wider">
                      Step {stepNum}
                    </span>
                    <span className="text-[11px] text-acme-gray-400">
                      · {actionCount} action{actionCount !== 1 ? 's' : ''}
                    </span>
                  </div>
                  {firstThinking && (
                    <p className="text-sm text-acme-gray-300 truncate">
                      {firstThinking.message}
                    </p>
                  )}
                </div>

                {/* Stats */}
                <div className="flex items-center gap-2">
                  {hasError && (
                    <span className="px-2 py-1 rounded-full bg-acme-red/20 text-acme-red text-xs font-medium">
                      <i className="fas fa-exclamation-triangle mr-1"></i>
                      Error
                    </span>
                  )}
                  <span className="px-2 py-1 rounded-full bg-acme-navy-light text-acme-gray-300 text-xs">
                    {stepLogs.length} events
                  </span>
                </div>

                {/* Chevron */}
                <i className={`fas fa-chevron-right text-acme-gray-400 text-xs transition-transform ${
                  isExpanded ? 'rotate-90' : ''
                }`}></i>
              </button>

              {/* Step Content */}
              {isExpanded && (
                <div className="border-t border-acme-navy-light/30">
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
  const errorCount = filteredLogs.filter(l => l.level === 'error').length;
  const successCount = filteredLogs.filter(l => l.level === 'success').length;

  return (
    <div className="h-full flex flex-col bg-acme-navy rounded-xl overflow-hidden">
      {/* Terminal-style Header */}
      <div className="px-4 py-3 bg-acme-navy-dark flex items-center justify-between flex-shrink-0">
        <div className="flex items-center gap-3">
          {/* Traffic Light Buttons */}
          <div className="flex gap-1.5">
            <div className="w-3 h-3 rounded-full bg-red-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-amber-500/80"></div>
            <div className="w-3 h-3 rounded-full bg-emerald-500/80"></div>
          </div>

          {/* Title */}
          <div className="flex items-center gap-2 pl-3 border-l border-acme-navy-light/30">
            <i className="fas fa-terminal text-acme-gray-400 text-xs"></i>
            <span className="text-xs font-semibold text-acme-gray-200">Execution Log</span>
          </div>

          {/* Step Progress */}
          {currentStep > 0 && (
            <div className="flex items-center gap-2 ml-3 pl-3 border-l border-acme-navy-light/30">
              <span className="text-xs font-mono text-acme-gray-300">
                Step <span className="text-sky-400 font-bold">{currentStep}</span>
                <span className="text-acme-gray-400"> / {maxSteps}</span>
              </span>
              <div className="w-20 h-1.5 bg-acme-navy rounded-full overflow-hidden">
                <div
                  className="h-full bg-sky-400 transition-all duration-300"
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>
          )}
        </div>

        {/* Toolbar Actions */}
        <div className="flex items-center gap-1">
          {/* View Mode Toggle */}
          <div className="flex bg-acme-navy rounded-lg p-0.5 mr-2">
            <button
              onClick={() => setViewMode('stream')}
              className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
                viewMode === 'stream'
                  ? 'bg-acme-navy-light text-white shadow-sm'
                  : 'text-acme-gray-300 hover:text-white'
              }`}
            >
              <i className="fas fa-stream mr-1"></i>
              Stream
            </button>
            <button
              onClick={() => setViewMode('grouped')}
              className={`px-2.5 py-1 text-xs rounded-md font-medium transition-all ${
                viewMode === 'grouped'
                  ? 'bg-acme-navy-light text-white shadow-sm'
                  : 'text-acme-gray-300 hover:text-white'
              }`}
            >
              <i className="fas fa-layer-group mr-1"></i>
              Grouped
            </button>
          </div>

          {/* Filter Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
              showFilters || levelFilters.size < 5 || searchText
                ? 'bg-sky-500/20 text-sky-400'
                : 'bg-acme-navy text-acme-gray-300 hover:text-white hover:bg-acme-navy-light'
            }`}
            title="Filter logs"
          >
            <i className="fas fa-filter text-xs"></i>
          </button>

          {/* Auto-scroll Toggle */}
          <button
            onClick={() => setIsAutoScroll(!isAutoScroll)}
            className={`w-8 h-8 rounded-lg flex items-center justify-center transition-all ${
              isAutoScroll
                ? 'bg-emerald-500/20 text-emerald-400'
                : 'bg-acme-navy text-acme-gray-300 hover:text-white hover:bg-acme-navy-light'
            }`}
            title={isAutoScroll ? 'Auto-scroll ON' : 'Auto-scroll OFF'}
          >
            <i className="fas fa-arrow-down text-xs"></i>
          </button>

          {/* Export Button */}
          {logs.length > 0 && (
            <button
              onClick={() => {
                const exportData = { exportedAt: new Date().toISOString(), totalLogs: logs.length, logs };
                const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `logs-${Date.now()}.json`;
                a.click();
                URL.revokeObjectURL(url);
              }}
              className="w-8 h-8 rounded-lg flex items-center justify-center bg-acme-navy text-acme-gray-300 hover:text-white hover:bg-acme-navy-light transition-all"
              title="Export logs as JSON"
            >
              <i className="fas fa-download text-xs"></i>
            </button>
          )}

          {/* Clear Button */}
          {onClear && logs.length > 0 && (
            <button
              onClick={onClear}
              className="w-8 h-8 rounded-lg flex items-center justify-center bg-acme-navy text-acme-gray-300 hover:text-acme-red hover:bg-acme-red/10 transition-all"
              title="Clear logs"
            >
              <i className="fas fa-trash-alt text-xs"></i>
            </button>
          )}
        </div>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="bg-acme-navy-dark/50 border-b border-acme-navy-light/30 px-4 py-3 flex-shrink-0">
          <div className="flex items-center gap-4">
            {/* Search Input */}
            <div className="relative flex-1 max-w-xs">
              <i className="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-acme-gray-400 text-xs"></i>
              <input
                type="text"
                value={searchText}
                onChange={(e) => setSearchText(e.target.value)}
                placeholder="Search logs..."
                className="w-full bg-acme-navy border border-acme-navy-light/50 rounded-lg pl-9 pr-3 py-2 text-xs text-acme-gray-100 placeholder-acme-gray-400 focus:outline-none focus:ring-2 focus:ring-sky-500/30 focus:border-sky-500/50 transition-all"
              />
              {searchText && (
                <button
                  onClick={() => setSearchText('')}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-acme-gray-400 hover:text-white"
                >
                  <i className="fas fa-times text-xs"></i>
                </button>
              )}
            </div>

            {/* Level Filters */}
            <div className="flex items-center gap-1">
              <span className="text-xs text-acme-gray-300 mr-2 uppercase tracking-wider font-medium">Level:</span>
              {(['info', 'success', 'warn', 'error', 'debug'] as LogLevel[]).map((level) => (
                <button
                  key={level}
                  onClick={() => toggleLevelFilter(level)}
                  className={`px-2.5 py-1 text-xs rounded-lg font-medium transition-all ${
                    levelFilters.has(level)
                      ? LEVEL_CONFIG[level].badge
                      : 'text-acme-gray-400 bg-acme-navy hover:bg-acme-navy-light hover:text-acme-gray-200'
                  }`}
                >
                  {level}
                </button>
              ))}
            </div>

            {/* Reset Filters */}
            {(levelFilters.size < 5 || searchText) && (
              <button
                onClick={() => {
                  setLevelFilters(new Set(['info', 'success', 'warn', 'error', 'debug']));
                  setSearchText('');
                }}
                className="text-xs text-acme-gray-300 hover:text-white transition-colors font-medium"
              >
                <i className="fas fa-undo mr-1"></i>
                Reset
              </button>
            )}
          </div>
        </div>
      )}

      {/* Log Content */}
      <div
        ref={scrollRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto font-mono text-xs scrollbar-dark"
      >
        {logs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            {isRunning || isInitializing ? (
              <>
                <div className="w-16 h-16 rounded-2xl bg-acme-navy-dark flex items-center justify-center mb-4 relative">
                  <div className="absolute inset-0 rounded-2xl border-2 border-sky-400/30 animate-pulse"></div>
                  <i className="fas fa-cog text-2xl text-sky-400 animate-spin"></i>
                </div>
                <h3 className="text-sm font-semibold text-acme-gray-300 mb-1">
                  {isInitializing ? 'Initializing Test...' : 'Starting Execution...'}
                </h3>
                <p className="text-xs text-acme-gray-400">
                  {isInitializing ? 'Connecting to browser agent' : 'Preparing test environment'}
                </p>
                <div className="mt-4 flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: '0ms' }}></div>
                  <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: '150ms' }}></div>
                  <div className="w-2 h-2 rounded-full bg-sky-400 animate-bounce" style={{ animationDelay: '300ms' }}></div>
                </div>
              </>
            ) : (
              <>
                <div className="w-16 h-16 rounded-2xl border-2 border-dashed border-acme-navy-light/30 flex items-center justify-center mb-4 animate-borderPulse">
                  <i className="fas fa-terminal text-2xl text-acme-gray-500 animate-float"></i>
                </div>
                <h3 className="text-sm font-semibold text-acme-gray-300 mb-2">Ready to Execute</h3>
                <div className="flex items-center gap-3 text-xs text-acme-gray-400 mb-1">
                  <span className="flex items-center gap-1.5">
                    <span className="w-5 h-5 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center text-[10px] font-bold">1</span>
                    Describe your test
                  </span>
                  <i className="fas fa-arrow-right text-[10px] text-acme-gray-500"></i>
                  <span className="flex items-center gap-1.5">
                    <span className="w-5 h-5 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center text-[10px] font-bold">2</span>
                    Click Run
                  </span>
                  <i className="fas fa-arrow-right text-[10px] text-acme-gray-500"></i>
                  <span className="flex items-center gap-1.5">
                    <span className="w-5 h-5 rounded-full bg-sky-500/20 text-sky-400 flex items-center justify-center text-[10px] font-bold">3</span>
                    See results
                  </span>
                </div>
              </>
            )}
          </div>
        ) : filteredLogs.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-16 h-16 rounded-2xl bg-acme-navy-dark flex items-center justify-center mb-4">
              <i className="fas fa-filter text-2xl text-acme-gray-500"></i>
            </div>
            <h3 className="text-sm font-semibold text-acme-gray-300 mb-1">No Matching Logs</h3>
            <p className="text-xs text-acme-gray-400">Try adjusting your filters</p>
          </div>
        ) : viewMode === 'stream' ? (
          <div>
            {filteredLogs.map((log, i) => renderLogEntry(log, i))}
          </div>
        ) : (
          renderGroupedView()
        )}
      </div>

      {/* Footer Stats Bar */}
      {logs.length > 0 && (
        <div className="px-4 py-2 bg-acme-navy-dark border-t border-acme-navy-light/30 flex items-center justify-between flex-shrink-0">
          <div className="flex items-center gap-4 text-xs">
            <span className="text-acme-gray-300">
              <i className="fas fa-list mr-1.5 text-acme-gray-400"></i>
              <span className="font-semibold text-acme-gray-200">{filteredLogs.length}</span> events
            </span>
            <span className="text-acme-gray-300">
              <i className="fas fa-layer-group mr-1.5 text-acme-gray-400"></i>
              <span className="font-semibold text-acme-gray-200">{groupedLogs.size}</span> steps
            </span>
          </div>

          <div className="flex items-center gap-3 text-xs">
            {successCount > 0 && (
              <span className="flex items-center gap-1.5 text-emerald-400">
                <i className="fas fa-check-circle"></i>
                {successCount}
              </span>
            )}
            {errorCount > 0 && (
              <span className="flex items-center gap-1.5 text-acme-red">
                <i className="fas fa-exclamation-circle"></i>
                {errorCount}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default LogViewer;
