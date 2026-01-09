
import React, { useState, useRef, useEffect } from 'react';
import {
  streamBasicTask,
  streamExtractData,
  streamResearchTopic,
  streamCompareProducts,
  streamComparePages,
  StreamingEvent,
} from '../services/geminiService';
import LogViewer from '../components/LogViewer';
import { ExecutionLog, AgentMode, EventType, LogLevel } from '../types';

const MODES: { id: AgentMode; name: string; icon: string; description: string }[] = [
  { id: 'basic', name: 'UI Agent (Backend)', icon: 'fa-robot', description: 'Full UI Testing Agent with artifacts & reporting' },
  { id: 'extract', name: 'Data Extraction', icon: 'fa-table', description: 'Extract structured data from a page' },
  { id: 'research', name: 'Research Topic', icon: 'fa-search', description: 'Research a topic across multiple sources' },
  { id: 'compare-products', name: 'Compare Products', icon: 'fa-balance-scale', description: 'Compare products across aspects' },
  { id: 'compare-pages', name: 'Compare Pages', icon: 'fa-columns', description: 'Compare content across web pages' },
];

const UIAutomator: React.FC = () => {
  const [mode, setMode] = useState<AgentMode>('basic');
  const [loading, setLoading] = useState(false);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [result, setResult] = useState<{ success: boolean; summary: string; data?: Record<string, unknown> } | null>(null);
  const [currentStep, setCurrentStep] = useState<number>(0);

  // Cleanup function ref for aborting streams
  const cleanupRef = useRef<(() => void) | null>(null);

  // Basic mode state
  const [prompt, setPrompt] = useState('');

  // Extract mode state
  const [extractUrl, setExtractUrl] = useState('');
  const [extractSchema, setExtractSchema] = useState('{\n  "name": "Product name",\n  "price": "Price in USD"\n}');
  const [extractMaxItems, setExtractMaxItems] = useState(10);

  // Research mode state
  const [researchTopic_, setResearchTopic] = useState('');
  const [researchDepth, setResearchDepth] = useState<'shallow' | 'moderate' | 'deep'>('moderate');
  const [researchMaxSources, setResearchMaxSources] = useState(5);

  // Compare products state
  const [products, setProducts] = useState('');
  const [aspects, setAspects] = useState('price, features, reviews');

  // Compare pages state
  const [pageUrls, setPageUrls] = useState('');
  const [comparisonCriteria, setComparisonCriteria] = useState('');

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (cleanupRef.current) {
        cleanupRef.current();
      }
    };
  }, []);

  const addLog = (
    message: string,
    level: LogLevel = 'info',
    eventType?: EventType,
    step?: number,
    data?: Record<string, unknown>
  ) => {
    setLogs(prev => [...prev, {
      timestamp: new Date().toLocaleTimeString(),
      level,
      message,
      eventType,
      step,
      data
    }]);
  };

  const handleStreamEvent = (event: StreamingEvent) => {
    // Map streaming event level to LogLevel
    const levelMap: Record<string, LogLevel> = {
      'info': 'info',
      'success': 'success',
      'warn': 'warn',
      'error': 'error',
      'debug': 'debug',
    };

    const level = levelMap[event.level] || 'info';
    const eventType = event.type as EventType;

    // Update step counter
    if (event.step !== undefined) {
      setCurrentStep(event.step);
    }

    // Add log entry based on event type with full metadata
    switch (event.type) {
      case 'step_start':
        addLog(`Step ${event.step} started`, 'info', 'step_start', event.step, event.data);
        break;
      case 'step_thinking':
        addLog(event.message, 'info', 'step_thinking', event.step, event.data);
        break;
      case 'step_action':
        addLog(event.message, 'info', 'step_action', event.step, event.data);
        break;
      case 'step_result':
        addLog(event.message, level, 'step_result', event.step, event.data);
        break;
      case 'browser_state':
        addLog(event.message, 'info', 'browser_state', event.step, event.data);
        if (event.data?.url) {
          addLog(`${event.data.url}`, 'info', 'browser_state', event.step);
        }
        break;
      case 'progress':
        addLog(event.message, level, 'progress', event.step, event.data);
        break;
      case 'error':
        addLog(event.message, 'error', 'error', event.step, event.data);
        break;
      case 'done':
        addLog(event.message, event.data?.success ? 'success' : 'error', 'done', event.step, event.data);
        setResult({
          success: event.data?.success as boolean ?? true,
          summary: event.message,
          data: event.data,
        });
        setLoading(false);
        break;
      default:
        addLog(event.message, level, eventType, event.step, event.data);
    }
  };

  const handleError = (error: Error) => {
    addLog(`Error: ${error.message}`, 'error', 'error');
    setLoading(false);
  };

  const handleComplete = () => {
    setLoading(false);
    cleanupRef.current = null;
  };

  const handleStop = () => {
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
      addLog('Task cancelled by user', 'warn', 'system');
      setLoading(false);
    }
  };

  const handleRun = () => {
    // Cancel any existing stream
    if (cleanupRef.current) {
      cleanupRef.current();
    }

    setLoading(true);
    setLogs([]);
    setResult(null);
    setCurrentStep(0);

    addLog(`Starting ${MODES.find(m => m.id === mode)?.name} task...`, 'info', 'system');

    let cleanup: (() => void) | null = null;

    switch (mode) {
      case 'basic':
        if (!prompt.trim()) {
          addLog('Please enter a task instruction', 'error', 'system');
          setLoading(false);
          return;
        }
        cleanup = streamBasicTask(
          { task: prompt },
          handleStreamEvent,
          handleError,
          handleComplete,
        );
        break;

      case 'extract':
        if (!extractUrl.trim()) {
          addLog('Please enter a URL', 'error', 'system');
          setLoading(false);
          return;
        }
        let schema: Record<string, string>;
        try {
          schema = JSON.parse(extractSchema);
        } catch {
          addLog('Invalid JSON schema', 'error', 'system');
          setLoading(false);
          return;
        }
        cleanup = streamExtractData(
          { url: extractUrl, data_schema: schema, max_items: extractMaxItems },
          handleStreamEvent,
          handleError,
          handleComplete,
        );
        break;

      case 'research':
        if (!researchTopic_.trim()) {
          addLog('Please enter a research topic', 'error', 'system');
          setLoading(false);
          return;
        }
        cleanup = streamResearchTopic(
          { topic: researchTopic_, depth: researchDepth, max_sources: researchMaxSources },
          handleStreamEvent,
          handleError,
          handleComplete,
        );
        break;

      case 'compare-products':
        if (!products.trim()) {
          addLog('Please enter products to compare', 'error', 'system');
          setLoading(false);
          return;
        }
        const productList = products.split(',').map(p => p.trim()).filter(Boolean);
        const aspectList = aspects.split(',').map(a => a.trim()).filter(Boolean);
        cleanup = streamCompareProducts(
          { products: productList, aspects: aspectList },
          handleStreamEvent,
          handleError,
          handleComplete,
        );
        break;

      case 'compare-pages':
        if (!pageUrls.trim() || !comparisonCriteria.trim()) {
          addLog('Please enter URLs and comparison criteria', 'error', 'system');
          setLoading(false);
          return;
        }
        const urls = pageUrls.split('\n').map(u => u.trim()).filter(Boolean);
        cleanup = streamComparePages(
          { urls, comparison_criteria: comparisonCriteria },
          handleStreamEvent,
          handleError,
          handleComplete,
        );
        break;

      default:
        addLog('Unknown mode', 'error', 'system');
        setLoading(false);
        return;
    }

    cleanupRef.current = cleanup;
  };

  const renderModeInput = () => {
    switch (mode) {
      case 'basic':
        return (
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="Go to Amazon, search for 'Macbook M3', and find the lowest price..."
            className="w-full min-h-[100px] p-4 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent transition-all outline-none"
          />
        );

      case 'extract':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">URL</label>
              <input
                type="url"
                value={extractUrl}
                onChange={(e) => setExtractUrl(e.target.value)}
                placeholder="https://example.com/products"
                className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Data Schema (JSON)</label>
              <textarea
                value={extractSchema}
                onChange={(e) => setExtractSchema(e.target.value)}
                className="w-full min-h-[80px] p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm font-mono focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Max Items</label>
              <input
                type="number"
                value={extractMaxItems}
                onChange={(e) => setExtractMaxItems(parseInt(e.target.value) || 10)}
                min={1}
                max={100}
                className="w-32 p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
          </div>
        );

      case 'research':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Research Topic</label>
              <input
                type="text"
                value={researchTopic_}
                onChange={(e) => setResearchTopic(e.target.value)}
                placeholder="Latest trends in AI development"
                className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
            <div className="flex gap-4">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Depth</label>
                <select
                  value={researchDepth}
                  onChange={(e) => setResearchDepth(e.target.value as 'shallow' | 'moderate' | 'deep')}
                  className="p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                >
                  <option value="shallow">Shallow</option>
                  <option value="moderate">Moderate</option>
                  <option value="deep">Deep</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1">Max Sources</label>
                <input
                  type="number"
                  value={researchMaxSources}
                  onChange={(e) => setResearchMaxSources(parseInt(e.target.value) || 5)}
                  min={1}
                  max={20}
                  className="w-24 p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
                />
              </div>
            </div>
          </div>
        );

      case 'compare-products':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Products (comma-separated)</label>
              <input
                type="text"
                value={products}
                onChange={(e) => setProducts(e.target.value)}
                placeholder="iPhone 15 Pro, Samsung Galaxy S24, Pixel 8 Pro"
                className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Comparison Aspects (comma-separated)</label>
              <input
                type="text"
                value={aspects}
                onChange={(e) => setAspects(e.target.value)}
                placeholder="price, features, reviews, battery life"
                className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
          </div>
        );

      case 'compare-pages':
        return (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">Page URLs (one per line)</label>
              <textarea
                value={pageUrls}
                onChange={(e) => setPageUrls(e.target.value)}
                placeholder="https://example1.com&#10;https://example2.com"
                className="w-full min-h-[80px] p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1">What to Compare</label>
              <input
                type="text"
                value={comparisonCriteria}
                onChange={(e) => setComparisonCriteria(e.target.value)}
                placeholder="pricing tiers, features, customer reviews"
                className="w-full p-3 bg-slate-50 border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              />
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  const renderResult = () => {
    if (!result) return null;

    return (
      <div className={`${result.success ? 'bg-emerald-50 border-emerald-100' : 'bg-red-50 border-red-100'} border p-6 rounded-xl animate-in fade-in slide-in-from-bottom-4`}>
        <h3 className={`${result.success ? 'text-emerald-900' : 'text-red-900'} font-semibold mb-4 flex items-center gap-2`}>
          <i className={`fas ${result.success ? 'fa-check-circle' : 'fa-times-circle'}`}></i>
          {result.success ? 'Task Completed' : 'Task Failed'}
        </h3>

        <p className={`${result.success ? 'text-emerald-800' : 'text-red-800'} text-sm leading-relaxed`}>{result.summary}</p>

        {result.data && Object.keys(result.data).length > 0 && (
          <details className="mt-3">
            <summary className={`text-xs ${result.success ? 'text-emerald-600' : 'text-red-600'} cursor-pointer hover:opacity-80`}>
              View Details
            </summary>
            <pre className="mt-2 p-3 bg-white/50 rounded text-xs overflow-auto max-h-48">
              {JSON.stringify(result.data, null, 2)}
            </pre>
          </details>
        )}

        <div className="mt-4 pt-4 border-t border-opacity-50 flex gap-4">
          <div className="bg-white/50 px-3 py-1.5 rounded text-[10px] font-mono">
            MODE: {mode.toUpperCase()}
          </div>
          <div className="bg-white/50 px-3 py-1.5 rounded text-[10px] font-mono">
            STEPS: {currentStep}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Mode Selector */}
      <div className="bg-white p-4 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-sm font-semibold mb-3 text-slate-600">Select Mode</h2>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-5 gap-2">
          {MODES.map((m) => (
            <button
              key={m.id}
              onClick={() => setMode(m.id)}
              disabled={loading}
              className={`p-3 rounded-lg text-left transition-all ${mode === m.id
                  ? 'bg-blue-50 border-2 border-blue-500 text-blue-700'
                  : 'bg-slate-50 border border-slate-200 text-slate-600 hover:bg-slate-100'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
            >
              <i className={`fas ${m.icon} text-lg mb-1`}></i>
              <div className="text-xs font-medium">{m.name}</div>
            </button>
          ))}
        </div>
        <p className="mt-3 text-xs text-slate-500">
          {MODES.find(m => m.id === mode)?.description}
        </p>
      </div>

      {/* Task Input */}
      <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <i className={`fas ${MODES.find(m => m.id === mode)?.icon} text-blue-500`}></i>
          {MODES.find(m => m.id === mode)?.name}
        </h2>

        {renderModeInput()}

        <div className="mt-4 flex justify-between items-center">
          <div className="text-xs text-slate-500 flex items-center gap-2">
            <span className={`w-2 h-2 rounded-full ${loading ? 'bg-amber-500 animate-pulse' : 'bg-emerald-500'}`}></span>
            {loading ? `Running... Step ${currentStep}` : 'Ready'}
          </div>
          <div className="flex gap-2">
            {loading && (
              <button
                onClick={handleStop}
                className="px-4 py-2.5 rounded-lg font-medium transition-all bg-red-100 text-red-700 hover:bg-red-200 active:scale-95 flex items-center gap-2"
              >
                <i className="fas fa-stop"></i>
                Stop
              </button>
            )}
            <button
              onClick={handleRun}
              disabled={loading}
              className={`px-6 py-2.5 rounded-lg font-medium transition-all flex items-center gap-2 ${loading
                  ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
                  : 'bg-blue-600 text-white hover:bg-blue-700 active:scale-95'
                }`}
            >
              {loading ? <i className="fas fa-spinner fa-spin"></i> : <i className="fas fa-play"></i>}
              {loading ? 'Running...' : 'Run'}
            </button>
          </div>
        </div>
      </div>

      <LogViewer logs={logs} maxSteps={30} currentStep={currentStep} />

      {renderResult()}
    </div>
  );
};

export default UIAutomator;
