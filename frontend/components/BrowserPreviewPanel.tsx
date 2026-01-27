import React from 'react';

export interface BrowserState {
  url: string;
  title: string;
  currentStep: number;
  currentAction?: string;
  actionParams?: Record<string, unknown>;
}

interface BrowserPreviewPanelProps {
  browserState: BrowserState | null;
  isRunning: boolean;
  isInitializing: boolean;
  maxSteps: number;
  onCollapse?: () => void;
  collapsed?: boolean;
}

const BrowserPreviewPanel: React.FC<BrowserPreviewPanelProps> = ({
  browserState,
  isRunning,
  isInitializing,
  maxSteps,
  onCollapse,
  collapsed = false,
}) => {
  if (!isRunning || collapsed) {
    return null;
  }

  // Extract domain from URL for display
  const getDomain = (url: string): string => {
    try {
      const urlObj = new URL(url);
      return urlObj.hostname;
    } catch {
      return url;
    }
  };

  // Get favicon URL
  const getFaviconUrl = (url: string): string => {
    try {
      const urlObj = new URL(url);
      return `https://www.google.com/s2/favicons?domain=${urlObj.hostname}&sz=32`;
    } catch {
      return '';
    }
  };

  // Get action icon and color
  const getActionStyle = (action?: string) => {
    const styles: Record<string, { icon: string; bg: string; text: string }> = {
      go_to_url: { icon: 'fa-globe', bg: 'bg-blue-100', text: 'text-blue-600' },
      navigate: { icon: 'fa-globe', bg: 'bg-blue-100', text: 'text-blue-600' },
      click: { icon: 'fa-mouse-pointer', bg: 'bg-purple-100', text: 'text-purple-600' },
      type: { icon: 'fa-keyboard', bg: 'bg-amber-100', text: 'text-amber-600' },
      input_text: { icon: 'fa-keyboard', bg: 'bg-amber-100', text: 'text-amber-600' },
      scroll: { icon: 'fa-arrows-alt-v', bg: 'bg-cyan-100', text: 'text-cyan-600' },
      wait: { icon: 'fa-clock', bg: 'bg-gray-100', text: 'text-gray-600' },
      screenshot: { icon: 'fa-camera', bg: 'bg-pink-100', text: 'text-pink-600' },
      extract: { icon: 'fa-search', bg: 'bg-emerald-100', text: 'text-emerald-600' },
      done: { icon: 'fa-check-circle', bg: 'bg-green-100', text: 'text-green-600' },
    };
    return styles[action || ''] || { icon: 'fa-cog', bg: 'bg-gray-100', text: 'text-gray-600' };
  };

  const actionStyle = getActionStyle(browserState?.currentAction);
  const progress = browserState ? (browserState.currentStep / maxSteps) * 100 : 0;

  return (
    <div className="bg-gradient-to-r from-acme-gray-900 to-acme-gray-800 rounded-xl border border-acme-gray-700 shadow-lg overflow-hidden animate-fadeIn">
      {/* Browser Chrome */}
      <div className="px-3 py-2 bg-acme-gray-800/50 border-b border-acme-gray-700 flex items-center gap-3">
        {/* Traffic lights */}
        <div className="flex items-center gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-red-500/80"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-yellow-500/80"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-green-500/80"></div>
        </div>

        {/* URL Bar */}
        <div className="flex-1 flex items-center gap-2 bg-acme-gray-700/50 rounded-lg px-3 py-1.5">
          {browserState?.url ? (
            <>
              <img
                src={getFaviconUrl(browserState.url)}
                alt=""
                className="w-4 h-4"
                onError={(e) => {
                  (e.target as HTMLImageElement).style.display = 'none';
                }}
              />
              <div className="flex items-center gap-1.5 overflow-hidden">
                <i className="fas fa-lock text-[10px] text-emerald-400"></i>
                <span className="text-xs text-acme-gray-300 font-medium truncate">
                  {getDomain(browserState.url)}
                </span>
              </div>
            </>
          ) : (
            <span className="text-xs text-acme-gray-500 italic">Connecting...</span>
          )}
        </div>

        {/* Collapse button */}
        {onCollapse && (
          <button
            onClick={onCollapse}
            className="w-6 h-6 flex items-center justify-center text-acme-gray-500 hover:text-acme-gray-300 transition-colors"
            title="Hide preview"
          >
            <i className="fas fa-chevron-up text-xs"></i>
          </button>
        )}
      </div>

      {/* Content Area */}
      <div className="p-4">
        {isInitializing ? (
          /* Initializing State */
          <div className="flex flex-col items-center justify-center py-6">
            <div className="w-12 h-12 rounded-full bg-acme-navy/20 flex items-center justify-center mb-3 animate-pulse">
              <i className="fas fa-satellite-dish text-xl text-acme-navy"></i>
            </div>
            <p className="text-sm text-acme-gray-400 font-medium">Connecting to browser agent...</p>
            <div className="flex items-center gap-2 mt-2">
              <div className="w-1.5 h-1.5 rounded-full bg-acme-navy animate-bounce" style={{ animationDelay: '0ms' }}></div>
              <div className="w-1.5 h-1.5 rounded-full bg-acme-navy animate-bounce" style={{ animationDelay: '150ms' }}></div>
              <div className="w-1.5 h-1.5 rounded-full bg-acme-navy animate-bounce" style={{ animationDelay: '300ms' }}></div>
            </div>
          </div>
        ) : (
          /* Active State */
          <div className="flex items-start gap-4">
            {/* Current Action Indicator */}
            <div className={`w-12 h-12 rounded-xl ${actionStyle.bg} flex items-center justify-center flex-shrink-0 relative`}>
              <i className={`fas ${actionStyle.icon} text-lg ${actionStyle.text}`}></i>
              {/* Pulsing ring */}
              <div className={`absolute inset-0 rounded-xl ${actionStyle.bg} animate-ping opacity-30`}></div>
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
              {/* Page Title */}
              <h4 className="text-sm font-semibold text-white truncate mb-1">
                {browserState?.title || 'Waiting for page...'}
              </h4>

              {/* Current Action */}
              <div className="flex items-center gap-2 mb-2">
                <span className={`px-2 py-0.5 rounded text-xs font-semibold ${actionStyle.bg} ${actionStyle.text}`}>
                  {browserState?.currentAction?.replace(/_/g, ' ').toUpperCase() || 'PROCESSING'}
                </span>
                {browserState?.actionParams?.text && (
                  <span className="text-xs text-acme-gray-400 truncate max-w-[200px]">
                    "{browserState.actionParams.text}"
                  </span>
                )}
              </div>

              {/* Full URL */}
              <p className="text-xs text-acme-gray-500 truncate font-mono">
                {browserState?.url || 'about:blank'}
              </p>
            </div>

            {/* Step Counter */}
            <div className="flex-shrink-0 text-right">
              <div className="text-2xl font-bold text-white">
                {browserState?.currentStep || 0}
                <span className="text-acme-gray-500 text-sm">/{maxSteps}</span>
              </div>
              <p className="text-xs text-acme-gray-500 font-medium">STEP</p>
            </div>
          </div>
        )}
      </div>

      {/* Progress Bar */}
      <div className="h-1 bg-acme-gray-700">
        <div
          className="h-full bg-gradient-to-r from-acme-navy to-blue-400 transition-all duration-300 relative"
          style={{ width: `${progress}%` }}
        >
          {/* Shimmer effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"></div>
        </div>
      </div>
    </div>
  );
};

export default BrowserPreviewPanel;
