
import React, { useState } from 'react';
import Sidebar from './components/Sidebar';
import UIAutomator from './apps/UIAutomator';
import DataProfiler from './apps/DataProfiler';
import QualityChecker from './apps/QualityChecker';
import { AppId, AppMetadata } from './types';

const APPS: AppMetadata[] = [
  {
    id: AppId.UI_AUTOMATOR,
    name: 'AI UI Automator',
    icon: 'fa-globe',
    description: 'Browser automation powered by Gemini & browser-use'
  },
  {
    id: AppId.DATA_PROFILER,
    name: 'AI Data Profiler',
    icon: 'fa-chart-pie',
    description: 'Deep data analysis and profiling engine'
  },
  {
    id: AppId.QUALITY_CHECKER,
    name: 'Quality Checker',
    icon: 'fa-clipboard-check',
    description: 'Rule-based data validation and auditing'
  },
];

const App: React.FC = () => {
  const [activeAppId, setActiveAppId] = useState<AppId>(AppId.UI_AUTOMATOR);

  const renderActiveApp = () => {
    switch (activeAppId) {
      case AppId.UI_AUTOMATOR:
        return <UIAutomator />;
      case AppId.DATA_PROFILER:
        return <DataProfiler />;
      case AppId.QUALITY_CHECKER:
        return <QualityChecker />;
      default:
        return <UIAutomator />;
    }
  };

  const activeAppMetadata = APPS.find(app => app.id === activeAppId);

  return (
    <div className="min-h-screen flex bg-slate-50">
      <Sidebar 
        apps={APPS} 
        activeAppId={activeAppId} 
        onSelectApp={setActiveAppId} 
      />
      
      <main className="flex-1 ml-64 p-8 transition-all">
        <header className="mb-10 flex justify-between items-start">
          <div>
            <div className="flex items-center gap-2 text-blue-600 mb-2">
              <span className="text-xs font-bold uppercase tracking-widest px-2 py-0.5 bg-blue-100 rounded">AI Module</span>
              <span className="text-slate-300">/</span>
              <span className="text-xs font-medium text-slate-400">{activeAppId.replace('-', ' ')}</span>
            </div>
            <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">
              {activeAppMetadata?.name}
            </h1>
            <p className="text-slate-500 mt-2 max-w-2xl">{activeAppMetadata?.description}</p>
          </div>
          
          <div className="flex items-center gap-4">
            <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors">
              <i className="fas fa-bell"></i>
            </button>
            <button className="p-2 text-slate-400 hover:text-slate-600 transition-colors">
              <i className="fas fa-cog"></i>
            </button>
            <div className="h-8 w-[1px] bg-slate-200 mx-2"></div>
            <div className="flex items-center gap-3 bg-white px-3 py-1.5 rounded-full border border-slate-200 shadow-sm">
              <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse"></div>
              <span className="text-xs font-semibold text-slate-600">Gemini 3 Pro</span>
            </div>
          </div>
        </header>

        <section className="max-w-6xl">
          {renderActiveApp()}
        </section>
        
        <footer className="mt-20 py-8 border-t border-slate-200 text-center">
          <p className="text-xs text-slate-400">
            AI Agent Workbench &copy; 2024 • Modular Plugin Architecture v1.0.4
          </p>
        </footer>
      </main>
    </div>
  );
};

export default App;
