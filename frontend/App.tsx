
import React, { useState, useEffect, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import UIAutomator from './apps/UIAutomator';
import { ToastProvider } from './components/Toast';
import { AppId, AppMetadata } from './types';

const APPS: AppMetadata[] = [
  {
    id: AppId.UI_AUTOMATOR,
    name: 'UI Testing',
    icon: 'fa-vial',
    description: 'Automated UI testing with AI'
  },
];

// Keyboard shortcut groups for the overlay
const SHORTCUT_GROUPS = [
  {
    title: 'Execution',
    shortcuts: [
      { keys: ['Ctrl', 'Enter'], description: 'Run task' },
      { keys: ['Esc'], description: 'Stop execution' },
    ],
  },
  {
    title: 'Navigation',
    shortcuts: [
      { keys: ['H'], description: 'Toggle History panel' },
      { keys: ['C'], description: 'Toggle Compare panel' },
    ],
  },
  {
    title: 'View',
    shortcuts: [
      { keys: ['?'], description: 'Show shortcuts' },
    ],
  },
];

const App: React.FC = () => {
  const [activeAppId, setActiveAppId] = useState<AppId>(AppId.UI_AUTOMATOR);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebarCollapsed');
    return saved === 'true';
  });
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [lastRunTime, setLastRunTime] = useState<Date | null>(() => {
    try {
      const saved = localStorage.getItem('lastRunTime');
      return saved ? new Date(saved) : null;
    } catch { return null; }
  });

  // Listen for run events to track last run time
  useEffect(() => {
    const handleRunEvent = () => {
      const now = new Date();
      setLastRunTime(now);
      localStorage.setItem('lastRunTime', now.toISOString());
    };
    window.addEventListener('taskStarted', handleRunEvent);
    return () => window.removeEventListener('taskStarted', handleRunEvent);
  }, []);

  // Persist sidebar state
  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', String(sidebarCollapsed));
  }, [sidebarCollapsed]);

  // Keyboard shortcut: ? to open shortcuts overlay
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // Don't trigger if user is typing in an input/textarea
      const tag = (e.target as HTMLElement).tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || tag === 'SELECT') return;

      if (e.key === '?' || (e.shiftKey && e.key === '/')) {
        e.preventDefault();
        setShowShortcuts(prev => !prev);
      }
      if (e.key === 'Escape' && showShortcuts) {
        setShowShortcuts(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [showShortcuts]);

  // Format relative time for status bar
  const formatRelativeTime = useCallback((date: Date): string => {
    const now = Date.now();
    const diff = now - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  }, []);

  const renderActiveApp = () => {
    switch (activeAppId) {
      case AppId.UI_AUTOMATOR:
        return <UIAutomator />;
      default:
        return <UIAutomator />;
    }
  };

  return (
    <ToastProvider>
      <div className="h-screen flex bg-acme-gray-100 overflow-hidden">
        <Sidebar
          apps={APPS}
          activeAppId={activeAppId}
          onSelectApp={setActiveAppId}
          collapsed={sidebarCollapsed}
          onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        />

        {/* Main Content Area */}
        <main className={`flex-1 flex flex-col min-h-0 transition-all duration-300 ${sidebarCollapsed ? 'ml-16' : 'ml-64'}`}>
          {/* App Content - fills available space */}
          <div className="flex-1 min-h-0 p-4">
            {renderActiveApp()}
          </div>

          {/* Status Bar - Enhanced */}
          <footer className="h-8 px-4 bg-white border-t border-acme-gray-200 flex items-center justify-between text-[11px] text-acme-gray-600 flex-shrink-0">
            <div className="flex items-center gap-5">
              <span className="flex items-center gap-1.5 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Connected
              </span>
              <span className="text-acme-gray-300">|</span>
              <span className="flex items-center gap-3">
                <span><kbd className="px-1.5 py-0.5 bg-acme-gray-100 border border-acme-gray-200 rounded text-[10px] font-mono">Ctrl+Enter</kbd> Run</span>
                <span><kbd className="px-1.5 py-0.5 bg-acme-gray-100 border border-acme-gray-200 rounded text-[10px] font-mono">Esc</kbd> Stop</span>
                <button
                  onClick={() => setShowShortcuts(true)}
                  className="flex items-center gap-1 hover:text-acme-navy transition-colors"
                >
                  <kbd className="px-1.5 py-0.5 bg-acme-gray-100 border border-acme-gray-200 rounded text-[10px] font-mono">?</kbd>
                  <span>Shortcuts</span>
                </button>
              </span>
            </div>
            <div className="flex items-center gap-4">
              {lastRunTime && (
                <span className="flex items-center gap-1.5 text-acme-gray-500">
                  <i className="fas fa-clock text-[10px]"></i>
                  Last run: {formatRelativeTime(lastRunTime)}
                </span>
              )}
              <span className="flex items-center gap-1.5">
                <i className="fas fa-microchip text-acme-navy"></i>
                Gemini 3 Pro
              </span>
              <span className="text-acme-gray-400">v1.0.0</span>
            </div>
          </footer>
        </main>
      </div>

      {/* Keyboard Shortcuts Overlay */}
      {showShortcuts && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center animate-backdropFadeIn"
          onClick={() => setShowShortcuts(false)}
        >
          {/* Backdrop */}
          <div className="absolute inset-0 bg-acme-gray-900/50 backdrop-blur-sm" />

          {/* Modal */}
          <div
            className="relative bg-white rounded-2xl shadow-2xl border border-acme-gray-200 w-full max-w-md mx-4 animate-modalScaleIn"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Header */}
            <div className="flex items-center justify-between px-6 py-4 border-b border-acme-gray-100">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-acme-navy/10 flex items-center justify-center">
                  <i className="fas fa-keyboard text-acme-navy text-sm"></i>
                </div>
                <h2 className="text-sm font-semibold text-acme-gray-900">Keyboard Shortcuts</h2>
              </div>
              <button
                onClick={() => setShowShortcuts(false)}
                className="w-7 h-7 rounded-lg flex items-center justify-center text-acme-gray-400 hover:text-acme-gray-700 hover:bg-acme-gray-100 transition-colors btn-press"
              >
                <i className="fas fa-times text-sm"></i>
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-5">
              {SHORTCUT_GROUPS.map((group) => (
                <div key={group.title}>
                  <h3 className="text-xs font-bold text-acme-gray-500 uppercase tracking-wider mb-2.5">
                    {group.title}
                  </h3>
                  <div className="space-y-2">
                    {group.shortcuts.map((shortcut) => (
                      <div key={shortcut.description} className="flex items-center justify-between py-1.5">
                        <span className="text-sm text-acme-gray-700">{shortcut.description}</span>
                        <div className="flex items-center gap-1">
                          {shortcut.keys.map((key, i) => (
                            <React.Fragment key={key}>
                              {i > 0 && <span className="text-acme-gray-300 text-xs">+</span>}
                              <kbd className="px-2 py-1 bg-acme-gray-50 border border-acme-gray-200 rounded-md text-xs font-mono text-acme-gray-700 shadow-sm min-w-[28px] text-center">
                                {key}
                              </kbd>
                            </React.Fragment>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>

            {/* Footer */}
            <div className="px-6 py-3 bg-acme-gray-50 rounded-b-2xl border-t border-acme-gray-100 text-center">
              <span className="text-[11px] text-acme-gray-500">
                Press <kbd className="px-1.5 py-0.5 bg-white border border-acme-gray-200 rounded text-[10px] font-mono mx-0.5">?</kbd> or <kbd className="px-1.5 py-0.5 bg-white border border-acme-gray-200 rounded text-[10px] font-mono mx-0.5">Esc</kbd> to close
              </span>
            </div>
          </div>
        </div>
      )}
    </ToastProvider>
  );
};

export default App;
