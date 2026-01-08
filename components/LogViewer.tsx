
import React, { useEffect, useRef } from 'react';
import { ExecutionLog } from '../types';

interface LogViewerProps {
  logs: ExecutionLog[];
}

const LogViewer: React.FC<LogViewerProps> = ({ logs }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  const getLevelColor = (level: string) => {
    switch (level) {
      case 'success': return 'text-emerald-400';
      case 'error': return 'text-rose-400';
      case 'warn': return 'text-amber-400';
      default: return 'text-blue-400';
    }
  };

  return (
    <div className="bg-slate-950 rounded-lg border border-slate-800 overflow-hidden flex flex-col h-64 shadow-inner">
      <div className="bg-slate-900 px-4 py-2 border-b border-slate-800 flex justify-between items-center">
        <span className="text-xs font-mono text-slate-400 uppercase tracking-widest">Execution Terminal</span>
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-rose-500/30"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-amber-500/30"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-emerald-500/30"></div>
        </div>
      </div>
      <div 
        ref={scrollRef}
        className="flex-1 p-4 font-mono text-xs overflow-y-auto space-y-1 scrollbar-hide"
      >
        {logs.length === 0 ? (
          <span className="text-slate-700 animate-pulse">Waiting for execution context...</span>
        ) : (
          logs.map((log, i) => (
            <div key={i} className="flex gap-3">
              <span className="text-slate-600 shrink-0">{log.timestamp}</span>
              <span className={`${getLevelColor(log.level)} font-bold uppercase shrink-0`}>[{log.level}]</span>
              <span className="text-slate-300 break-all">{log.message}</span>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default LogViewer;
