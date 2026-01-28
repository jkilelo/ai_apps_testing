
import React, { useState, useRef, useEffect } from 'react';
import {
  streamBasicTask,
  streamExtractData,
  streamResearchTopic,
  streamCompareProducts,
  streamComparePages,
  streamA11yAudit,
  StreamingEvent,
} from '../services/geminiService';
import LogViewer from '../components/LogViewer';
import TestResultsPanel from '../components/TestResultsPanel';
import ArtifactsViewer from '../components/ArtifactsViewer';
import SessionBrowser from '../components/SessionBrowser';
import SessionComparison from '../components/SessionComparison';
import BrowserPreviewPanel, { BrowserState } from '../components/BrowserPreviewPanel';
import { useToast } from '../components/Toast';
import { ExecutionLog, AgentMode, EventType, LogLevel } from '../types';

const MODES: { id: AgentMode; name: string; icon: string; description: string; placeholder: string; suggestedSteps: number }[] = [
  {
    id: 'basic',
    name: 'UI Test',
    icon: 'fa-vial',
    description: 'Run automated UI testing scenarios',
    placeholder: 'Describe the UI test scenario...\n\nExample: Go to Amazon, search for "MacBook Pro M3", verify search results appear, and capture the product listing page.',
    suggestedSteps: 30
  },
  {
    id: 'extract',
    name: 'Extract',
    icon: 'fa-database',
    description: 'Extract structured data from web pages',
    placeholder: '',
    suggestedSteps: 40
  },
  {
    id: 'research',
    name: 'Research',
    icon: 'fa-microscope',
    description: 'Research topics across multiple sources',
    placeholder: '',
    suggestedSteps: 50
  },
  {
    id: 'compare-products',
    name: 'Compare',
    icon: 'fa-balance-scale',
    description: 'Compare products or services',
    placeholder: '',
    suggestedSteps: 60
  },
  {
    id: 'compare-pages',
    name: 'Analyze',
    icon: 'fa-chart-line',
    description: 'Analyze and compare web pages',
    placeholder: '',
    suggestedSteps: 30
  },
  {
    id: 'a11y-audit',
    name: 'A11y',
    icon: 'fa-universal-access',
    description: 'Accessibility audit with WCAG scoring',
    placeholder: '',
    suggestedSteps: 40
  },
];

const UIAutomator: React.FC = () => {
  const { addToast } = useToast();
  const [mode, setMode] = useState<AgentMode>('basic');
  const [loading, setLoading] = useState(false);
  const [isInitializing, setIsInitializing] = useState(false);
  const [logs, setLogs] = useState<ExecutionLog[]>([]);
  const [result, setResult] = useState<{ success: boolean; summary: string; data?: Record<string, unknown> } | null>(null);
  const [currentStep, setCurrentStep] = useState<number>(0);
  const [browserState, setBrowserState] = useState<BrowserState | null>(null);
  const [previewCollapsed, setPreviewCollapsed] = useState(false);

  // Side panel state — only one panel open at a time
  type SidePanelType = 'sessions' | 'comparison' | null;
  const [sidePanel, setSidePanel] = useState<SidePanelType>(null);

  // Success/failure ceremony state
  const [ceremony, setCeremony] = useState<'success' | 'failure' | null>(null);

  // Drag-to-resize side panel
  const [sidePanelWidth, setSidePanelWidth] = useState<number>(() => {
    try {
      const saved = localStorage.getItem('sidePanelWidth');
      return saved ? Math.min(600, Math.max(320, parseInt(saved))) : 420;
    } catch { return 420; }
  });
  const isDraggingRef = useRef(false);
  const dragStartXRef = useRef(0);
  const dragStartWidthRef = useRef(420);

  // Cleanup function ref for aborting streams
  const cleanupRef = useRef<(() => void) | null>(null);

  // Global settings
  const [maxSteps, setMaxSteps] = useState(30);
  const [headless, setHeadless] = useState(false);

  // Recent tasks (stored in localStorage)
  const [recentTasks, setRecentTasks] = useState<string[]>(() => {
    try {
      const saved = localStorage.getItem('recentTasks');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });
  const [showRecentTasks, setShowRecentTasks] = useState(false);

  // Save recent task to localStorage
  const saveRecentTask = (task: string) => {
    if (!task.trim()) return;
    setRecentTasks(prev => {
      // Remove duplicates and add to front, keep max 10
      const newTasks = [task, ...prev.filter(t => t !== task)].slice(0, 10);
      localStorage.setItem('recentTasks', JSON.stringify(newTasks));
      return newTasks;
    });
  };

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

  // A11y audit state
  const [a11yUrl, setA11yUrl] = useState('');
  const [skipBehavioral, setSkipBehavioral] = useState(false);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (cleanupRef.current) {
        cleanupRef.current();
      }
    };
  }, []);

  // Keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Ctrl+Enter or Cmd+Enter to run
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter' && !loading) {
        e.preventDefault();
        handleRun();
      }
      // Escape to stop
      if (e.key === 'Escape' && loading) {
        e.preventDefault();
        handleStop();
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [loading, mode, prompt, extractUrl, extractSchema, researchTopic_, products, aspects, pageUrls, comparisonCriteria, a11yUrl, maxSteps]);

  // Drag-to-resize side panel handlers
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (!isDraggingRef.current) return;
      const delta = dragStartXRef.current - e.clientX;
      const newWidth = Math.min(600, Math.max(320, dragStartWidthRef.current + delta));
      setSidePanelWidth(newWidth);
    };
    const handleMouseUp = () => {
      if (isDraggingRef.current) {
        isDraggingRef.current = false;
        document.body.style.cursor = '';
        document.body.style.userSelect = '';
        localStorage.setItem('sidePanelWidth', String(sidePanelWidth));
      }
    };
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [sidePanelWidth]);

  const startDragResize = (e: React.MouseEvent) => {
    isDraggingRef.current = true;
    dragStartXRef.current = e.clientX;
    dragStartWidthRef.current = sidePanelWidth;
    document.body.style.cursor = 'col-resize';
    document.body.style.userSelect = 'none';
  };

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
        // Update browser preview with current action
        if (event.data?.action) {
          const actionData = event.data.action as { action?: string; params?: Record<string, unknown> };
          setBrowserState(prev => ({
            url: prev?.url || '',
            title: prev?.title || '',
            currentStep: event.step ?? prev?.currentStep ?? 0,
            currentAction: actionData.action || (typeof event.data?.action === 'string' ? event.data.action : undefined),
            actionParams: actionData.params,
          }));
        }
        break;
      case 'step_result':
        addLog(event.message, level, 'step_result', event.step, event.data);
        break;
      case 'browser_state':
        addLog(event.message, 'info', 'browser_state', event.step, event.data);
        if (event.data?.url) {
          addLog(`${event.data.url}`, 'info', 'browser_state', event.step);
          // Update browser preview state
          setBrowserState(prev => ({
            url: event.data?.url as string || prev?.url || '',
            title: event.data?.title as string || prev?.title || '',
            currentStep: event.step ?? prev?.currentStep ?? 0,
            currentAction: prev?.currentAction,
            actionParams: prev?.actionParams,
          }));
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
        // Trigger ceremony animation
        setCeremony(event.data?.success ? 'success' : 'failure');
        setTimeout(() => setCeremony(null), 1500);
        // Show toast notification
        if (event.data?.success) {
          addToast('success', 'Task completed successfully!');
        } else {
          addToast('error', 'Task failed. Check logs for details.');
        }
        break;
      default:
        addLog(event.message, level, eventType, event.step, event.data);
    }
  };

  const handleError = (error: Error) => {
    addLog(`Error: ${error.message}`, 'error', 'error');
    setLoading(false);
    setIsInitializing(false);
    addToast('error', `Error: ${error.message}`);
  };

  const handleComplete = () => {
    setLoading(false);
    setIsInitializing(false);
    cleanupRef.current = null;
  };

  const handleStop = () => {
    if (cleanupRef.current) {
      cleanupRef.current();
      cleanupRef.current = null;
      addLog('Task cancelled by user', 'warn', 'system');
      setLoading(false);
      setIsInitializing(false);
      addToast('warning', 'Task cancelled');
    }
  };

  const handleRun = () => {
    // Cancel any existing stream
    if (cleanupRef.current) {
      cleanupRef.current();
    }

    // Immediate feedback - show initializing state right away
    setLoading(true);
    setIsInitializing(true);
    setLogs([]);
    setResult(null);
    setCurrentStep(0);
    setBrowserState(null);
    setPreviewCollapsed(false);

    const modeName = MODES.find(m => m.id === mode)?.name || 'Task';

    // Add immediate feedback logs
    addLog(`Initializing ${modeName}...`, 'info', 'system');

    // Simulate connection steps with slight delays for visual feedback
    setTimeout(() => {
      if (cleanupRef.current) { // Only add if still running
        addLog('Connecting to browser agent...', 'info', 'system');
      }
    }, 100);

    setTimeout(() => {
      if (cleanupRef.current) { // Only add if still running
        addLog('Preparing test environment...', 'info', 'system');
        setIsInitializing(false);
      }
    }, 300);

    let cleanup: (() => void) | null = null;

    switch (mode) {
      case 'basic':
        if (!prompt.trim()) {
          addLog('Please enter a task instruction', 'error', 'system');
          setLoading(false);
          return;
        }
        saveRecentTask(prompt);
        cleanup = streamBasicTask(
          { task: prompt, max_steps: maxSteps, headless },
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
          { url: extractUrl, data_schema: schema, max_items: extractMaxItems, max_steps: maxSteps, headless },
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
          { topic: researchTopic_, depth: researchDepth, max_sources: researchMaxSources, max_steps: maxSteps, headless },
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
          { products: productList, aspects: aspectList, max_steps: maxSteps, headless },
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
          { urls, comparison_criteria: comparisonCriteria, max_steps: maxSteps, headless },
          handleStreamEvent,
          handleError,
          handleComplete,
        );
        break;

      case 'a11y-audit':
        if (!a11yUrl.trim()) {
          addLog('Please enter a URL to audit', 'error', 'system');
          setLoading(false);
          return;
        }
        cleanup = streamA11yAudit(
          { url: a11yUrl, max_steps: maxSteps, headless, skip_behavioral: skipBehavioral },
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
          <div className={`space-y-3 ${loading ? 'opacity-60 pointer-events-none' : ''}`}>
            {/* Main Input Area */}
            <div className="relative group">
              {/* Textarea with enhanced styling */}
              <div className={`relative rounded-xl overflow-hidden transition-all duration-200 ${
                loading ? 'ring-1 ring-acme-gray-200 bg-acme-gray-100' :
                prompt ? 'ring-2 ring-acme-navy/20' : 'ring-1 ring-acme-gray-200 hover:ring-acme-gray-300'
              }`}>
                {/* Left accent bar */}
                <div className={`absolute left-0 top-0 bottom-0 w-1 transition-colors ${
                  loading ? 'bg-acme-gray-300' :
                  prompt ? 'bg-acme-navy' : 'bg-acme-gray-200 group-hover:bg-acme-gray-300'
                }`}></div>

                <textarea
                  value={prompt}
                  onChange={(e) => setPrompt(e.target.value)}
                  onFocus={() => setShowRecentTasks(false)}
                  disabled={loading}
                  placeholder="Example: Navigate to the login page, verify the username and password fields are present, attempt login with invalid credentials, and verify the error message is displayed correctly..."
                  className={`w-full h-[80px] pl-4 pr-10 py-3 text-sm text-acme-gray-900 placeholder:text-acme-gray-500 transition-all outline-none resize-none leading-relaxed ${
                    loading ? 'bg-acme-gray-100 cursor-not-allowed' : 'bg-acme-gray-50/50 focus:bg-white'
                  }`}
                />

                {/* Clear button */}
                {prompt && (
                  <button
                    onClick={() => setPrompt('')}
                    className="absolute top-2 right-2 w-6 h-6 flex items-center justify-center rounded-lg bg-acme-gray-200/80 hover:bg-acme-red/10 text-acme-gray-600 hover:text-acme-red transition-colors"
                    title="Clear"
                  >
                    <i className="fas fa-times text-[10px]"></i>
                  </button>
                )}

                {/* Character count */}
                <div className="absolute bottom-2 right-2 text-xs text-acme-gray-400">
                  {prompt.length > 0 && <span>{prompt.length} chars</span>}
                </div>
              </div>
            </div>

            {/* Bottom Actions Bar */}
            <div className="flex items-center justify-between">
              {/* Left: Quick Actions */}
              <div className="flex items-center gap-2">
                {/* Recent Tasks Dropdown */}
                {recentTasks.length > 0 && (
                  <div className="relative">
                    <button
                      onClick={() => setShowRecentTasks(!showRecentTasks)}
                      className={`h-8 px-3 rounded-lg flex items-center gap-2 text-xs font-medium transition-all ${
                        showRecentTasks
                          ? 'bg-acme-navy text-white'
                          : 'bg-acme-gray-100 text-acme-gray-700 hover:bg-acme-gray-200 hover:text-acme-gray-900'
                      }`}
                    >
                      <i className="fas fa-clock-rotate-left text-[11px]"></i>
                      <span>Recent</span>
                      <span className={`px-1.5 py-0.5 rounded text-[11px] font-semibold ${
                        showRecentTasks ? 'bg-white/20' : 'bg-acme-gray-200 text-acme-gray-600'
                      }`}>{recentTasks.length}</span>
                    </button>
                    {showRecentTasks && (
                      <div className="absolute top-full left-0 mt-1 w-80 max-h-52 overflow-y-auto bg-white border border-acme-gray-200 rounded-xl shadow-xl z-20">
                        <div className="p-2 border-b border-acme-gray-100 flex items-center justify-between sticky top-0 bg-white">
                          <span className="text-xs font-semibold text-acme-gray-800 flex items-center gap-2">
                            <i className="fas fa-history text-acme-gray-500"></i>
                            Recent Tasks
                          </span>
                          <button
                            onClick={(e) => {
                              e.stopPropagation();
                              setRecentTasks([]);
                              localStorage.removeItem('recentTasks');
                              setShowRecentTasks(false);
                            }}
                            className="text-xs text-acme-gray-600 hover:text-acme-red px-2 py-1 rounded hover:bg-acme-red/5 transition-colors font-medium"
                          >
                            Clear All
                          </button>
                        </div>
                        <div className="p-1">
                          {recentTasks.map((task, index) => (
                            <button
                              key={index}
                              onClick={() => {
                                setPrompt(task);
                                setShowRecentTasks(false);
                              }}
                              className="w-full text-left px-3 py-2 text-xs text-acme-gray-800 hover:bg-acme-navy/5 hover:text-acme-navy rounded-lg transition-colors group"
                            >
                              <div className="flex items-start gap-2">
                                <i className="fas fa-arrow-turn-up fa-rotate-90 text-[10px] text-acme-gray-400 group-hover:text-acme-navy mt-0.5"></i>
                                <span className="line-clamp-2 leading-relaxed">{task}</span>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Example scenarios hint */}
                <div className="hidden md:flex items-center gap-1.5 text-xs text-acme-gray-500">
                  <i className="fas fa-lightbulb text-amber-500"></i>
                  <span>Tip: Be specific about elements, actions, and expected outcomes</span>
                </div>
              </div>

              {/* Right: Status indicator */}
              <div className="flex items-center gap-2">
                {prompt && (
                  <span className="text-xs text-emerald-700 font-medium bg-emerald-50 px-2 py-1 rounded-lg flex items-center gap-1">
                    <i className="fas fa-check-circle"></i>
                    Ready
                  </span>
                )}
              </div>
            </div>
          </div>
        );

      case 'extract':
        return (
          <div className="flex gap-2 items-start">
            <div className="flex-1 grid grid-cols-4 gap-2">
              <input
                type="url"
                value={extractUrl}
                onChange={(e) => setExtractUrl(e.target.value)}
                placeholder="Target URL (https://...)"
                className="col-span-2 p-2 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs focus:ring-1 focus:ring-acme-navy outline-none"
              />
              <textarea
                value={extractSchema}
                onChange={(e) => setExtractSchema(e.target.value)}
                placeholder='{"name": "...", "price": "..."}'
                className="col-span-1 row-span-2 p-2 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs font-mono focus:ring-1 focus:ring-acme-navy outline-none resize-none h-[52px]"
              />
              <div className="flex items-center gap-1">
                <span className="text-xs text-acme-gray-600 font-medium">Max:</span>
                <input
                  type="number"
                  value={extractMaxItems}
                  onChange={(e) => setExtractMaxItems(parseInt(e.target.value) || 10)}
                  min={1}
                  max={100}
                  className="w-14 p-2 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs focus:ring-1 focus:ring-acme-navy outline-none"
                />
              </div>
            </div>
          </div>
        );

      case 'research':
        return (
          <div className="flex gap-2 items-center">
            <input
              type="text"
              value={researchTopic_}
              onChange={(e) => setResearchTopic(e.target.value)}
              placeholder="Research topic (e.g., Latest trends in AI development)"
              className="flex-1 p-2 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs focus:ring-1 focus:ring-acme-navy outline-none"
            />
            <select
              value={researchDepth}
              onChange={(e) => setResearchDepth(e.target.value as 'shallow' | 'moderate' | 'deep')}
              className="w-28 p-2 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs focus:ring-1 focus:ring-acme-navy outline-none"
            >
              <option value="shallow">Quick</option>
              <option value="moderate">Moderate</option>
              <option value="deep">Deep</option>
            </select>
            <div className="flex items-center gap-1">
              <span className="text-xs text-acme-gray-600 font-medium">Sources:</span>
              <input
                type="number"
                value={researchMaxSources}
                onChange={(e) => setResearchMaxSources(parseInt(e.target.value) || 5)}
                min={1}
                max={20}
                className="w-12 p-2 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs focus:ring-1 focus:ring-acme-navy outline-none"
              />
            </div>
          </div>
        );

      case 'compare-products':
        return (
          <div className="flex gap-2 items-center">
            <input
              type="text"
              value={products}
              onChange={(e) => setProducts(e.target.value)}
              placeholder="Products to compare (comma separated)"
              className="flex-1 p-2 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs focus:ring-1 focus:ring-acme-navy outline-none"
            />
            <input
              type="text"
              value={aspects}
              onChange={(e) => setAspects(e.target.value)}
              placeholder="Criteria (price, features...)"
              className="w-48 p-2 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs focus:ring-1 focus:ring-acme-navy outline-none"
            />
          </div>
        );

      case 'compare-pages':
        return (
          <div className="flex gap-2 items-start">
            <textarea
              value={pageUrls}
              onChange={(e) => setPageUrls(e.target.value)}
              placeholder="URLs to compare (one per line)"
              className="flex-1 h-[52px] p-2 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs focus:ring-1 focus:ring-acme-navy outline-none resize-none"
            />
            <input
              type="text"
              value={comparisonCriteria}
              onChange={(e) => setComparisonCriteria(e.target.value)}
              placeholder="What to analyze"
              className="w-48 p-2 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs focus:ring-1 focus:ring-acme-navy outline-none"
            />
          </div>
        );

      case 'a11y-audit':
        return (
          <div className="flex gap-2 items-center">
            <input
              type="url"
              value={a11yUrl}
              onChange={(e) => setA11yUrl(e.target.value)}
              placeholder="URL to audit (https://example.com)"
              className="flex-1 p-2 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs focus:ring-1 focus:ring-acme-navy outline-none"
            />
            <label className="flex items-center gap-2 px-3 py-2 bg-acme-gray-50 border border-acme-gray-200 rounded-lg cursor-pointer hover:bg-acme-gray-100 transition-colors">
              <input
                type="checkbox"
                checked={skipBehavioral}
                onChange={(e) => setSkipBehavioral(e.target.checked)}
                className="w-3.5 h-3.5 rounded border-acme-gray-300 text-acme-navy focus:ring-acme-navy"
              />
              <span className="text-xs text-acme-gray-700 font-medium whitespace-nowrap">Scan only</span>
            </label>
            {a11yUrl && (
              <span className="text-xs text-emerald-700 font-medium bg-emerald-50 px-2 py-1 rounded-lg flex items-center gap-1">
                <i className="fas fa-check-circle"></i>
                Ready
              </span>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  // Output tab state
  const [outputTab, setOutputTab] = useState<'logs' | 'results' | 'artifacts'>('logs');

  const currentMode = MODES.find(m => m.id === mode);

  return (
    <div className="h-full flex flex-col gap-2">
      {/* TOOLBAR - Compact */}
      <div className="bg-white rounded-lg border border-acme-gray-200 shadow-sm flex-shrink-0">
        <div className="px-3 py-1.5 flex items-center justify-between gap-3">
          {/* Left: Mode Selector with sliding pill */}
          <div className="relative flex items-center bg-acme-gray-50 rounded-lg p-0.5">
            {/* Sliding pill background */}
            <div
              className="absolute top-0.5 bottom-0.5 bg-acme-navy rounded-md shadow-sm transition-all duration-200 ease-out"
              style={{
                left: `${MODES.findIndex(m => m.id === mode) * (100 / MODES.length)}%`,
                width: `${100 / MODES.length}%`,
              }}
            />
            {MODES.map((m) => (
              <button
                key={m.id}
                onClick={() => setMode(m.id)}
                disabled={loading}
                title={m.description}
                className={`relative z-10 px-2.5 py-1 rounded-md text-xs font-medium transition-colors duration-200 flex items-center gap-1.5 btn-press ${
                  mode === m.id
                    ? 'text-white'
                    : 'text-acme-gray-700 hover:text-acme-gray-900'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
              >
                <i className={`fas ${m.icon} text-[10px]`}></i>
                <span>{m.name}</span>
              </button>
            ))}
          </div>

          {/* Center: Settings (compact) */}
          <div className="flex items-center gap-2 text-xs">
            <div className="flex items-center gap-2 px-2.5 py-1.5 bg-acme-gray-50 rounded-lg border border-acme-gray-200">
              <span className="text-acme-gray-700 text-xs font-semibold">Max Steps</span>
              <input
                type="number" min="5" max="200" step="5" value={maxSteps}
                onChange={(e) => {
                  const val = parseInt(e.target.value);
                  setMaxSteps(isNaN(val) ? 30 : Math.min(200, Math.max(5, val)));
                }}
                disabled={loading}
                className="w-14 h-6 bg-white text-acme-gray-800 font-semibold text-xs text-center rounded-md border border-acme-gray-300 focus:outline-none focus:ring-2 focus:ring-acme-navy/30 focus:border-acme-navy"
              />
              {maxSteps !== currentMode?.suggestedSteps && (
                <button
                  onClick={() => setMaxSteps(currentMode?.suggestedSteps || 30)}
                  disabled={loading}
                  className="text-[11px] text-acme-navy hover:text-acme-navy-light font-medium px-1.5 py-0.5 bg-acme-navy/5 hover:bg-acme-navy/10 rounded transition-colors"
                  title={`Reset to suggested value for ${currentMode?.name}`}
                >
                  Use {currentMode?.suggestedSteps}
                </button>
              )}
            </div>
            <div className="flex items-center gap-0.5 bg-acme-gray-100 rounded-lg p-0.5">
              <button
                onClick={() => setHeadless(false)}
                disabled={loading}
                className={`px-2 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition-all ${
                  !headless
                    ? 'bg-white text-acme-navy shadow-sm'
                    : 'text-acme-gray-500 hover:text-acme-gray-700'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                title="Browser window visible"
              >
                <i className="fas fa-eye text-[10px]"></i>
                Visible
              </button>
              <button
                onClick={() => setHeadless(true)}
                disabled={loading}
                className={`px-2 py-1 rounded-md text-xs font-medium flex items-center gap-1.5 transition-all ${
                  headless
                    ? 'bg-white text-acme-navy shadow-sm'
                    : 'text-acme-gray-500 hover:text-acme-gray-700'
                } ${loading ? 'opacity-50 cursor-not-allowed' : ''}`}
                title="Browser hidden"
              >
                <i className="fas fa-eye-slash text-[10px]"></i>
                Hidden
              </button>
            </div>
          </div>

          {/* Right: Actions */}
          <div className="flex items-center gap-1.5">
            <button
              onClick={() => setSidePanel(sidePanel === 'sessions' ? null : 'sessions')}
              className={`w-7 h-7 rounded-md flex items-center justify-center transition-all ${
                sidePanel === 'sessions'
                  ? 'bg-acme-navy text-white'
                  : 'text-acme-gray-600 hover:bg-acme-gray-100 hover:text-acme-gray-800'
              }`}
              title="History"
            >
              <i className="fas fa-clock-rotate-left text-xs"></i>
            </button>
            <button
              onClick={() => setSidePanel(sidePanel === 'comparison' ? null : 'comparison')}
              className={`w-7 h-7 rounded-md flex items-center justify-center transition-all ${
                sidePanel === 'comparison'
                  ? 'bg-acme-navy text-white'
                  : 'text-acme-gray-600 hover:bg-acme-gray-100 hover:text-acme-gray-800'
              }`}
              title="Compare"
            >
              <i className="fas fa-code-compare text-xs"></i>
            </button>
            <div className="w-px h-5 bg-acme-gray-200"></div>
            {loading ? (
              <button
                onClick={handleStop}
                className="h-7 px-3 rounded-md text-xs font-semibold bg-acme-red text-white hover:bg-acme-red-light transition-all flex items-center gap-1.5 relative overflow-hidden btn-press animate-pulseBorder"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
                <i className="fas fa-circle-notch fa-spin text-[10px]"></i>
                <span>Stop</span>
              </button>
            ) : (
              <button
                onClick={handleRun}
                className="h-7 px-4 rounded-md text-xs font-semibold bg-gradient-to-r from-acme-navy to-acme-navy-light text-white hover:shadow-[0_0_15px_rgba(0,59,112,0.3)] transition-all flex items-center gap-1.5 btn-press relative overflow-hidden group"
              >
                <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent opacity-0 group-hover:opacity-100 group-hover:animate-shimmer"></div>
                <i className="fas fa-play text-[10px] relative z-10"></i>
                <span className="relative z-10">Run</span>
              </button>
            )}
          </div>
        </div>

        {/* Status Bar - only show when running */}
        {loading && (
          <div className="px-3 pb-1.5">
            <div className="flex items-center gap-2">
              <div className="w-1.5 h-1.5 rounded-full bg-acme-navy animate-pulse"></div>
              <div className="flex-1 h-1 bg-acme-gray-100 rounded-full overflow-hidden">
                <div
                  className="h-full bg-acme-navy transition-all duration-300"
                  style={{ width: `${Math.min((currentStep / maxSteps) * 100, 100)}%` }}
                />
              </div>
              <span className="text-xs font-semibold text-acme-gray-700">
                {currentStep}/{maxSteps}
              </span>
            </div>
          </div>
        )}
      </div>

      {/* BODY: Horizontal split — main content + optional side panel */}
      <div className="flex-1 min-h-0 flex gap-2">

        {/* LEFT: Primary workspace */}
        <div className="flex-1 min-w-0 flex flex-col gap-2 transition-all duration-200">

          {/* Live Browser Preview - Shows during execution */}
          {loading && !previewCollapsed && (
            <div className="flex-shrink-0">
              <BrowserPreviewPanel
                browserState={browserState}
                isRunning={loading}
                isInitializing={isInitializing}
                maxSteps={maxSteps}
                onCollapse={() => setPreviewCollapsed(true)}
                collapsed={previewCollapsed}
              />
            </div>
          )}

          {/* Collapsed Preview Toggle */}
          {loading && previewCollapsed && (
            <button
              onClick={() => setPreviewCollapsed(false)}
              className="flex-shrink-0 w-full py-1.5 bg-acme-gray-800 hover:bg-acme-gray-700 rounded-lg flex items-center justify-center gap-2 text-xs text-acme-gray-400 hover:text-white transition-colors"
            >
              <i className="fas fa-chevron-down text-[10px]"></i>
              <span>Show Browser Preview</span>
              <span className="text-acme-gray-500">•</span>
              <span className="font-mono">{browserState?.url ? (() => { try { return new URL(browserState.url).hostname; } catch { return browserState.url; } })() : 'Connecting...'}</span>
            </button>
          )}

          {/* Task Input Panel */}
          <div className="bg-white rounded-xl border border-acme-gray-200 shadow-sm flex-shrink-0 overflow-hidden">
            {/* Gradient Accent Bar */}
            <div className="h-1 bg-gradient-to-r from-acme-navy via-acme-navy-light to-acme-navy"></div>

            {/* Input Header */}
            <div className="px-4 py-2.5 border-b border-acme-gray-100 flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-acme-navy to-acme-navy-light flex items-center justify-center shadow-sm">
                  <i className="fas fa-vial text-white text-xs"></i>
                </div>
                <div>
                  <h3 className="text-sm font-semibold text-acme-gray-900">Test Scenario</h3>
                  <p className="text-xs text-acme-gray-500">Describe what you want the AI agent to test</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-acme-gray-500 hidden sm:inline">
                  <kbd className="px-1.5 py-0.5 bg-acme-gray-100 border border-acme-gray-200 rounded text-[11px] font-mono text-acme-gray-700">⌘↵</kbd> to run
                </span>
              </div>
            </div>

            {/* Input Content */}
            <div className="p-4">
              {renderModeInput()}
            </div>
          </div>

          {/* OUTPUT SECTION */}
          <div className={`flex-1 min-h-0 bg-white rounded-lg border border-acme-gray-200 shadow-sm flex flex-col overflow-hidden relative ${
            ceremony === 'failure' ? 'animate-shake' : ''
          }`}>
            {/* Success ceremony overlay */}
            {ceremony === 'success' && (
              <div className="absolute inset-0 z-20 pointer-events-none">
                <div className="absolute inset-0 bg-emerald-500/10 animate-successPulse" />
                {/* Animated checkmark */}
                <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2">
                  <svg width="48" height="48" viewBox="0 0 48 48" className="drop-shadow-lg">
                    <circle cx="24" cy="24" r="22" fill="rgba(16,185,129,0.15)" stroke="#10b981" strokeWidth="2" />
                    <path d="M14 24 L21 31 L34 18" fill="none" stroke="#10b981" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"
                      strokeDasharray="24" strokeDashoffset="24" className="animate-checkDraw" />
                  </svg>
                </div>
                {/* Confetti dots */}
                {[...Array(8)].map((_, i) => (
                  <div
                    key={i}
                    className="absolute top-1/2 left-1/2 w-2 h-2 rounded-full animate-confettiBurst"
                    style={{
                      background: ['#10b981', '#f59e0b', '#3b82f6', '#ec4899', '#8b5cf6', '#06b6d4', '#f97316', '#14b8a6'][i],
                      transform: `rotate(${i * 45}deg) translateY(-30px)`,
                      animationDelay: `${i * 0.05}s`,
                    }}
                  />
                ))}
              </div>
            )}
            {/* Failure ceremony overlay */}
            {ceremony === 'failure' && (
              <div className="absolute inset-0 z-20 pointer-events-none">
                <div className="absolute inset-0 bg-red-500/10 animate-successPulse" />
              </div>
            )}

            {/* Tab Header */}
            <div className="px-2 py-1.5 border-b border-acme-gray-100 flex items-center justify-between flex-shrink-0">
              <div className="relative flex items-center gap-0.5">
                {/* Output tab sliding pill */}
                {(() => {
                  const tabs = ['logs', 'results', 'artifacts'] as const;
                  const activeIdx = tabs.indexOf(outputTab);
                  return (
                    <div
                      className="absolute top-0 bottom-0 bg-acme-navy rounded-md transition-all duration-200 ease-out"
                      style={{
                        left: `${activeIdx * 33.33}%`,
                        width: '33.33%',
                      }}
                    />
                  );
                })()}
                <button
                  onClick={() => setOutputTab('logs')}
                  className={`relative z-10 px-2.5 py-1 rounded-md text-xs font-medium transition-colors duration-200 flex items-center gap-1.5 btn-press ${
                    outputTab === 'logs'
                      ? 'text-white'
                      : 'text-acme-gray-700 hover:text-acme-gray-900'
                  }`}
                >
                  <i className="fas fa-terminal text-[10px]"></i>
                  Logs
                  {logs.length > 0 && (
                    <span className={`px-1 py-0.5 rounded text-[10px] font-bold ${
                      outputTab === 'logs' ? 'bg-white/20' : 'bg-acme-gray-200 text-acme-gray-600'
                    }`}>{logs.length}</span>
                  )}
                </button>
                <button
                  onClick={() => setOutputTab('results')}
                  className={`relative z-10 px-2.5 py-1 rounded-md text-xs font-medium transition-colors duration-200 flex items-center gap-1.5 btn-press ${
                    outputTab === 'results'
                      ? 'text-white'
                      : 'text-acme-gray-700 hover:text-acme-gray-900'
                  }`}
                >
                  <i className="fas fa-chart-bar text-[10px]"></i>
                  Results
                  {result && (
                    <span className={`w-1.5 h-1.5 rounded-full ${result.success ? 'bg-emerald-400' : 'bg-acme-red'}`}></span>
                  )}
                </button>
                <button
                  onClick={() => setOutputTab('artifacts')}
                  className={`relative z-10 px-2.5 py-1 rounded-md text-xs font-medium transition-colors duration-200 flex items-center gap-1.5 btn-press ${
                    outputTab === 'artifacts'
                      ? 'text-white'
                      : 'text-acme-gray-700 hover:text-acme-gray-900'
                  }`}
                >
                  <i className="fas fa-folder-open text-[10px]"></i>
                  Artifacts
                </button>
              </div>
              {outputTab === 'logs' && logs.length > 0 && (
                <button
                  onClick={() => !loading && setLogs([])}
                  disabled={loading}
                  className="px-2 py-1 text-xs text-acme-gray-600 hover:text-acme-red hover:bg-acme-red/5 rounded transition-all disabled:opacity-50 flex items-center gap-1"
                >
                  <i className="fas fa-trash-alt"></i>
                  Clear
                </button>
              )}
            </div>

            {/* Tab Content with crossfade */}
            <div className="flex-1 min-h-0 overflow-auto">
              <div key={outputTab} className="h-full tab-content-enter">
                {outputTab === 'logs' && (
                  <LogViewer
                    logs={logs}
                    maxSteps={maxSteps}
                    currentStep={currentStep}
                    isInitializing={isInitializing}
                    isRunning={loading}
                  />
                )}
                {outputTab === 'results' && (
                  <TestResultsPanel
                    logs={logs}
                    result={result}
                    isRunning={loading}
                    currentStep={currentStep}
                    maxSteps={maxSteps}
                  />
                )}
                {outputTab === 'artifacts' && result && (
                  <ArtifactsViewer
                    sessionId={result.data?.session_id as string | null}
                    outputDirectory={result.data?.output_directory as string | undefined}
                  />
                )}
                {outputTab === 'artifacts' && !result && (
                  <div className="flex flex-col items-center justify-center h-full">
                    <div className="w-16 h-16 rounded-2xl border-2 border-dashed border-acme-gray-200 flex items-center justify-center mb-4 animate-borderPulse">
                      <i className="fas fa-images text-2xl text-acme-gray-300 animate-float"></i>
                    </div>
                    <h3 className="text-sm font-semibold text-acme-gray-800 mb-2">No Artifacts Yet</h3>
                    <div className="flex items-center gap-3 text-xs text-acme-gray-500">
                      <span className="flex items-center gap-1.5"><span className="w-5 h-5 rounded-full bg-acme-navy/10 text-acme-navy flex items-center justify-center text-[10px] font-bold">1</span>Describe your test</span>
                      <i className="fas fa-arrow-right text-[10px] text-acme-gray-300"></i>
                      <span className="flex items-center gap-1.5"><span className="w-5 h-5 rounded-full bg-acme-navy/10 text-acme-navy flex items-center justify-center text-[10px] font-bold">2</span>Click Run</span>
                      <i className="fas fa-arrow-right text-[10px] text-acme-gray-300"></i>
                      <span className="flex items-center gap-1.5"><span className="w-5 h-5 rounded-full bg-acme-navy/10 text-acme-navy flex items-center justify-center text-[10px] font-bold">3</span>See results</span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* RIGHT: Side Panel — Sessions / Comparison */}
        {sidePanel && (
          <div
            className="flex-shrink-0 flex flex-col bg-white rounded-xl border border-acme-gray-200 shadow-sm overflow-hidden animate-slideInRight relative"
            style={{ width: sidePanelWidth }}
          >
            {/* Drag handle */}
            <div
              onMouseDown={startDragResize}
              className="absolute left-0 top-0 bottom-0 w-1 cursor-col-resize z-10 group hover:bg-acme-navy/20 transition-colors"
            >
              <div className="absolute left-0 top-1/2 -translate-y-1/2 w-1 h-8 rounded-full bg-acme-gray-300 opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>
            {/* Panel Header */}
            <div className="px-3 py-2.5 border-b border-acme-gray-200 flex items-center justify-between flex-shrink-0 bg-acme-gray-50">
              <div className="flex items-center gap-2">
                {/* Panel Tab Switcher */}
                <button
                  onClick={() => setSidePanel('sessions')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                    sidePanel === 'sessions'
                      ? 'bg-acme-navy text-white shadow-sm'
                      : 'text-acme-gray-600 hover:text-acme-gray-800 hover:bg-white'
                  }`}
                >
                  <i className="fas fa-clock-rotate-left text-xs"></i>
                  Sessions
                </button>
                <button
                  onClick={() => setSidePanel('comparison')}
                  className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                    sidePanel === 'comparison'
                      ? 'bg-acme-navy text-white shadow-sm'
                      : 'text-acme-gray-600 hover:text-acme-gray-800 hover:bg-white'
                  }`}
                >
                  <i className="fas fa-code-compare text-xs"></i>
                  Compare
                </button>
              </div>
              <button
                onClick={() => setSidePanel(null)}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-acme-gray-400 hover:text-acme-gray-700 hover:bg-acme-gray-200 transition-colors"
                title="Close panel"
              >
                <i className="fas fa-xmark text-sm"></i>
              </button>
            </div>

            {/* Panel Content */}
            <div className="flex-1 min-h-0 overflow-hidden">
              {sidePanel === 'sessions' && (
                <SessionBrowser
                  onClose={() => setSidePanel(null)}
                  onRerun={(task) => { setPrompt(task); setMode('basic'); setSidePanel(null); }}
                />
              )}
              {sidePanel === 'comparison' && (
                <SessionComparison onClose={() => setSidePanel(null)} />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default UIAutomator;
