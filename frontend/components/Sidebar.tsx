
import React from 'react';
import { AppId, AppMetadata } from '../types';

interface SidebarProps {
  apps: AppMetadata[];
  activeAppId: AppId;
  onSelectApp: (id: AppId) => void;
  collapsed?: boolean;
  onToggleCollapse?: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({
  apps,
  activeAppId,
  onSelectApp,
  collapsed = false,
  onToggleCollapse
}) => {
  return (
    <aside className={`bg-acme-navy text-white flex flex-col h-screen fixed left-0 top-0 z-50 transition-all duration-300 ${
      collapsed ? 'w-16' : 'w-64'
    }`}>
      {/* Header - Acme Branding */}
      <div className={`p-4 border-b border-acme-navy-light flex items-center ${collapsed ? 'justify-center' : 'gap-3'}`}>
        <div className="flex items-center flex-shrink-0">
          {/* Acme-style logo mark */}
          <div className="relative">
            <span className="text-xl font-bold tracking-tight">acme</span>
            {/* Red arc accent */}
            <div className="absolute -top-0.5 left-[0.65rem] w-3 h-1.5 border-t-2 border-acme-red rounded-t-full"></div>
          </div>
        </div>
        {!collapsed && (
          <div className="border-l border-acme-navy-light pl-3 ml-1">
            <span className="text-sm font-medium text-white/90">Acme UI Testing</span>
          </div>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {!collapsed && (
          <p className="text-xs font-semibold text-white/40 uppercase tracking-wider mb-3 px-2">Applications</p>
        )}
        {apps.map((app) => (
          <div key={app.id} className="relative group">
            <button
              onClick={() => onSelectApp(app.id)}
              className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all text-sm font-medium ${
                collapsed ? 'justify-center' : ''
              } ${
                activeAppId === app.id
                  ? 'bg-white text-acme-navy shadow-lg'
                  : 'text-white/70 hover:bg-acme-navy-light hover:text-white'
              }`}
              title={collapsed ? app.name : undefined}
            >
              <span className="w-5 text-center flex-shrink-0">
                <i className={`fas ${app.icon}`}></i>
              </span>
              {!collapsed && <span className="truncate">{app.name}</span>}
            </button>
            {/* Tooltip on hover when collapsed */}
            {collapsed && (
              <div className="absolute left-full top-1/2 -translate-y-1/2 ml-2 px-2 py-1 bg-acme-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity z-50 shadow-lg">
                {app.name}
              </div>
            )}
          </div>
        ))}
      </nav>

      {/* Collapse Toggle Button */}
      {onToggleCollapse && (
        <button
          onClick={onToggleCollapse}
          className="mx-3 mb-3 p-2 rounded-lg bg-acme-navy-light hover:bg-acme-navy-dark text-white/60 hover:text-white transition-colors flex items-center justify-center"
          title={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
        >
          <i className={`fas ${collapsed ? 'fa-chevron-right' : 'fa-chevron-left'} text-xs`}></i>
          {!collapsed && <span className="ml-2 text-xs">Collapse</span>}
        </button>
      )}

      {/* Footer */}
      <div className={`p-3 border-t border-acme-navy-light ${collapsed ? 'px-2' : ''}`}>
        <div className={`flex items-center gap-3 p-2 bg-acme-navy-light/50 rounded-lg ${collapsed ? 'justify-center' : ''}`}>
          <div className="w-8 h-8 rounded-full bg-acme-navy-light flex items-center justify-center flex-shrink-0">
            <i className="fas fa-user text-xs text-white/70"></i>
          </div>
          {!collapsed && (
            <div className="overflow-hidden">
              <p className="text-xs font-medium truncate text-white/90">Workspace User</p>
              <p className="text-xs text-white/50 truncate">Connected</p>
            </div>
          )}
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
