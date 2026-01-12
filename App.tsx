
import React, { useState, useEffect } from 'react';
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

const App: React.FC = () => {
  const [activeAppId, setActiveAppId] = useState<AppId>(AppId.UI_AUTOMATOR);
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    const saved = localStorage.getItem('sidebarCollapsed');
    return saved === 'true';
  });

  // Persist sidebar state
  useEffect(() => {
    localStorage.setItem('sidebarCollapsed', String(sidebarCollapsed));
  }, [sidebarCollapsed]);

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

          {/* Status Bar - Acme styled */}
          <footer className="h-8 px-4 bg-white border-t border-acme-gray-200 flex items-center justify-between text-[11px] text-acme-gray-600 flex-shrink-0">
            <div className="flex items-center gap-5">
              <span className="flex items-center gap-1.5 font-medium">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></span>
                Connected
              </span>
              <span className="text-acme-gray-300">|</span>
              <span className="flex items-center gap-3">
                <span><kbd className="px-1.5 py-0.5 bg-acme-gray-100 border border-acme-gray-200 rounded text-[10px] font-mono">⌘↵</kbd> Run</span>
                <span><kbd className="px-1.5 py-0.5 bg-acme-gray-100 border border-acme-gray-200 rounded text-[10px] font-mono">Esc</kbd> Stop</span>
              </span>
            </div>
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1.5">
                <i className="fas fa-microchip text-acme-navy"></i>
                Gemini 2.5 Pro
              </span>
              <span className="text-acme-gray-400">v1.0.0</span>
            </div>
          </footer>
        </main>
      </div>
    </ToastProvider>
  );
};

export default App;
