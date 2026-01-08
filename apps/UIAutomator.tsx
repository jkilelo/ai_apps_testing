
import React, { useState } from 'react';
import { runUIAutomator } from '../services/geminiService';
import LogViewer from '../components/LogViewer';
import { ExecutionLog } from '../types';

const UIAutomator: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [result, setResult] = useState<any>(null);

  const addLog = (message: string, level: ExecutionLog['level'] = 'info') => {
    setLogs(prev => [...prev, {
      timestamp: new Date().toLocaleTimeString(),
      level,
      message
    }]);
  };

  const handleRun = async () => {
    if (!prompt.trim()) return;
    
    setLoading(true);
    setLogs([]);
    setResult(null);
    
    addLog(`Initializing browser environment...`);
    addLog(`Navigating to target domain context...`);
    
    try {
      const data = await runUIAutomator(prompt);
      
      // Simulate step-by-step logs
      for (const step of data.steps) {
        addLog(`Executing: ${step.action}...`);
        await new Promise(r => setTimeout(r, 800));
        addLog(`Action completed: ${step.action}`, step.status === 'done' ? 'success' : 'error');
      }
      
      setResult(data);
      addLog(`Task finished successfully.`, 'success');
    } catch (error) {
      addLog(`Execution failed: ${error}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <i className="fas fa-robot text-blue-500"></i>
          Agent Instructions
        </h2>
        <div className="flex gap-3">
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Go to Amazon, search for 'Macbook M3', and find the lowest price..."
            className="flex-1 min-h-[100px] p-4 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
          />
        </div>
        <div className="mt-4 flex justify-between items-center">
          <div className="text-xs text-slate-500">
            Uses <code className="bg-slate-100 px-1 py-0.5 rounded">browser-use</code> agent core.
          </div>
          <button
            onClick={handleRun}
            disabled={loading}
            className={`px-6 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2 ${
              loading 
              ? 'bg-slate-100 text-slate-400 cursor-not-allowed' 
              : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-95'
            }`}
          >
            {loading ? <i className="fas fa-spinner fa-spin"></i> : <i className="fas fa-play"></i>}
            {loading ? 'Executing Task...' : 'Run Agent'}
          </button>
        </div>
      </div>

      <LogViewer logs={logs} />

      {result && (
        <div className="bg-emerald-50 border border-emerald-100 p-6 rounded-xl animate-in fade-in slide-in-from-bottom-4">
          <h3 className="text-emerald-900 font-semibold mb-2 flex items-center gap-2">
            <i className="fas fa-check-circle"></i>
            Final Result Summary
          </h3>
          <p className="text-emerald-800 text-sm leading-relaxed">{result.summary}</p>
          <div className="mt-4 pt-4 border-t border-emerald-200/50 flex gap-4">
             <div className="bg-white/50 px-3 py-1.5 rounded text-[10px] text-emerald-700 font-mono">
               RUNTIME: {(logs.length * 0.8).toFixed(1)}s
             </div>
             <div className="bg-white/50 px-3 py-1.5 rounded text-[10px] text-emerald-700 font-mono">
               STEPS: {result.steps.length}
             </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default UIAutomator;
