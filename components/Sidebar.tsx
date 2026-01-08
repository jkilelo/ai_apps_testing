
import React from 'react';
import { AppId, AppMetadata } from '../types';

interface SidebarProps {
  apps: AppMetadata[];
  activeAppId: AppId;
  onSelectApp: (id: AppId) => void;
}

const Sidebar: React.FC<SidebarProps> = ({ apps, activeAppId, onSelectApp }) => {
  return (
    <aside className="w-64 bg-slate-900 text-white flex flex-col h-screen fixed left-0 top-0 z-50">
      <div className="p-6 border-b border-slate-800 flex items-center gap-3">
        <div className="w-8 h-8 bg-blue-600 rounded flex items-center justify-center">
          <i className="fas fa-microchip"></i>
        </div>
        <h1 className="font-bold text-lg tracking-tight">AI Workbench</h1>
      </div>
      
      <nav className="flex-1 overflow-y-auto p-4 space-y-2">
        <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 px-2">Workspace</p>
        {apps.map((app) => (
          <button
            key={app.id}
            onClick={() => onSelectApp(app.id)}
            className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm font-medium ${
              activeAppId === app.id 
              ? 'bg-blue-600 text-white shadow-lg shadow-blue-900/20' 
              : 'text-slate-400 hover:bg-slate-800 hover:text-white'
            }`}
          >
            <span className="w-5 text-center">
              <i className={`fas ${app.icon}`}></i>
            </span>
            {app.name}
          </button>
        ))}
      </nav>
      
      <div className="p-4 border-t border-slate-800">
        <div className="flex items-center gap-3 p-2 bg-slate-800/50 rounded-lg">
          <div className="w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center">
            <i className="fas fa-user text-xs"></i>
          </div>
          <div className="overflow-hidden">
            <p className="text-xs font-medium truncate">Senior AI Engineer</p>
            <p className="text-[10px] text-slate-500 truncate">Workspace Admin</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
