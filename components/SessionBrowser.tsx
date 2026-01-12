
import React, { useState, useEffect, useMemo } from 'react';
import { listSessions, SessionInfo } from '../services/geminiService';
import ArtifactsViewer from './ArtifactsViewer';

interface SessionBrowserProps {
  onClose?: () => void;
  onRerun?: (task: string) => void;
}

type SortOption = 'newest' | 'oldest' | 'has_report';

const SessionBrowser: React.FC<SessionBrowserProps> = ({ onClose, onRerun }) => {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [searchQuery, setSearchQuery] = useState('');

  // Filter sessions based on search query
  const filteredSessions = useMemo(() => {
    if (!searchQuery.trim()) return sessions;
    const query = searchQuery.toLowerCase();
    return sessions.filter(session => {
      if (session.session_id.toLowerCase().includes(query)) return true;
      if (session.task?.toLowerCase().includes(query)) return true;
      return false;
    });
  }, [sessions, searchQuery]);

  // Sort sessions based on selected option
  const sortedSessions = [...filteredSessions].sort((a, b) => {
    switch (sortBy) {
      case 'newest':
        return b.created_at - a.created_at;
      case 'oldest':
        return a.created_at - b.created_at;
      case 'has_report':
        if (a.has_report === b.has_report) return b.created_at - a.created_at;
        return a.has_report ? -1 : 1;
      default:
        return 0;
    }
  });

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listSessions();
      setSessions(data.sessions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sessions');
    } finally {
      setLoading(false);
    }
  };

  const formatDate = (timestamp: number): string => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  const formatRelativeTime = (timestamp: number): string => {
    const now = Date.now();
    const diff = now - (timestamp * 1000);
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;
    return new Date(timestamp * 1000).toLocaleDateString();
  };

  // Stats for header
  const stats = useMemo(() => {
    const withReports = sessions.filter(s => s.has_report).length;
    return { total: sessions.length, withReports };
  }, [sessions]);

  if (selectedSession) {
    return (
      <div className="h-full flex flex-col">
        {/* Compact back button header */}
        <div className="flex items-center justify-between bg-white rounded-xl border border-acme-gray-200 px-4 py-3 mb-3 shadow-sm">
          <button
            onClick={() => setSelectedSession(null)}
            className="flex items-center gap-2 text-xs font-medium text-acme-gray-700 hover:text-acme-navy transition-colors"
          >
            <div className="w-7 h-7 rounded-lg bg-acme-gray-100 flex items-center justify-center">
              <i className="fas fa-arrow-left text-[10px]"></i>
            </div>
            Back to Sessions
          </button>
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono text-acme-gray-600 bg-acme-gray-50 px-2 py-1 rounded-lg">
              {selectedSession}
            </span>
          </div>
        </div>

        {/* Artifacts viewer for selected session */}
        <div className="flex-1 min-h-0">
          <ArtifactsViewer sessionId={selectedSession} />
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-white rounded-xl border border-acme-gray-200 shadow-sm overflow-hidden">
      {/* Header with Stats */}
      <div className="px-4 py-3 border-b border-acme-gray-100 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-acme-navy/10 flex items-center justify-center">
              <i className="fas fa-history text-acme-navy"></i>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-acme-gray-800">Session History</h3>
              <p className="text-[10px] text-acme-gray-600">
                {stats.total} sessions • {stats.withReports} with reports
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={fetchSessions}
              disabled={loading}
              className="w-8 h-8 rounded-lg flex items-center justify-center bg-acme-gray-50 hover:bg-acme-gray-100 text-acme-gray-600 hover:text-acme-gray-800 border border-acme-gray-200 transition-all"
              title="Refresh"
            >
              <i className={`fas fa-sync-alt text-xs ${loading ? 'fa-spin' : ''}`}></i>
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="w-8 h-8 rounded-lg flex items-center justify-center bg-acme-gray-50 hover:bg-acme-gray-100 text-acme-gray-600 hover:text-acme-gray-800 border border-acme-gray-200 transition-all"
              >
                <i className="fas fa-times text-xs"></i>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Search and Filter Bar */}
      <div className="px-4 py-3 bg-acme-gray-50/50 border-b border-acme-gray-100 flex-shrink-0">
        <div className="flex items-center gap-3">
          {/* Search */}
          <div className="relative flex-1 max-w-xs">
            <i className="fas fa-search absolute left-3 top-1/2 -translate-y-1/2 text-acme-gray-400 text-xs"></i>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search sessions..."
              className="w-full pl-9 pr-8 py-2 text-xs bg-white border border-acme-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-acme-navy/20 focus:border-acme-navy transition-all"
            />
            {searchQuery && (
              <button
                onClick={() => setSearchQuery('')}
                className="absolute right-2.5 top-1/2 -translate-y-1/2 text-acme-gray-400 hover:text-acme-gray-600"
              >
                <i className="fas fa-times text-xs"></i>
              </button>
            )}
          </div>

          {/* Sort Dropdown */}
          <div className="flex items-center gap-2">
            <span className="text-[10px] text-acme-gray-600 uppercase tracking-wider font-medium">Sort:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as SortOption)}
              className="px-3 py-2 text-xs bg-white border border-acme-gray-200 text-acme-gray-700 rounded-lg focus:outline-none focus:ring-2 focus:ring-acme-navy/20 cursor-pointer"
            >
              <option value="newest">Newest First</option>
              <option value="oldest">Oldest First</option>
              <option value="has_report">Has Report</option>
            </select>
          </div>
        </div>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto p-3">
        {loading ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-16 h-16 rounded-2xl bg-acme-gray-100 flex items-center justify-center mb-4">
              <i className="fas fa-spinner fa-spin text-2xl text-acme-navy"></i>
            </div>
            <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">Loading Sessions</h3>
            <p className="text-xs text-acme-gray-600">Please wait...</p>
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-16 h-16 rounded-2xl bg-acme-red/10 flex items-center justify-center mb-4">
              <i className="fas fa-exclamation-triangle text-2xl text-acme-red"></i>
            </div>
            <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">Failed to Load</h3>
            <p className="text-xs text-acme-gray-600 mb-4">{error}</p>
            <button
              onClick={fetchSessions}
              className="px-4 py-2 text-xs font-medium bg-acme-navy text-white rounded-lg hover:bg-acme-navy-dark transition-colors"
            >
              Try Again
            </button>
          </div>
        ) : sessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-16 h-16 rounded-2xl bg-acme-gray-100 flex items-center justify-center mb-4">
              <i className="fas fa-folder-open text-2xl text-acme-gray-300"></i>
            </div>
            <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">No Sessions Yet</h3>
            <p className="text-xs text-acme-gray-600">Run a task to create your first session</p>
          </div>
        ) : sortedSessions.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-16 h-16 rounded-2xl bg-acme-gray-100 flex items-center justify-center mb-4">
              <i className="fas fa-search text-2xl text-acme-gray-300"></i>
            </div>
            <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">No Results Found</h3>
            <p className="text-xs text-acme-gray-600 mb-4">No sessions match "{searchQuery}"</p>
            <button
              onClick={() => setSearchQuery('')}
              className="px-4 py-2 text-xs font-medium bg-acme-navy/10 text-acme-navy rounded-lg hover:bg-acme-navy/20 transition-colors"
            >
              Clear Search
            </button>
          </div>
        ) : (
          <div className="space-y-2">
            {sortedSessions.map((session) => (
              <button
                key={session.session_id}
                onClick={() => setSelectedSession(session.session_id)}
                className="w-full flex items-center gap-3 p-3 bg-white hover:bg-acme-gray-50 rounded-xl border border-acme-gray-200 hover:border-acme-navy/30 transition-all text-left group shadow-sm hover:shadow-md"
              >
                {/* Status Icon */}
                <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                  session.has_report
                    ? 'bg-emerald-50 text-emerald-600'
                    : 'bg-acme-gray-100 text-acme-gray-400'
                }`}>
                  <i className={`fas ${session.has_report ? 'fa-check-circle' : 'fa-clock'}`}></i>
                </div>

                {/* Session Info */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-xs font-mono font-medium text-acme-gray-800 truncate">
                      {session.session_id.length > 24 ? session.session_id.substring(0, 24) + '...' : session.session_id}
                    </span>
                    {session.has_report && (
                      <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-[10px] font-medium rounded-full">
                        <i className="fas fa-file-alt mr-1"></i>
                        Report
                      </span>
                    )}
                  </div>
                  {session.task && (
                    <p className="text-xs text-acme-gray-600 truncate">
                      {session.task.length > 60 ? session.task.substring(0, 60) + '...' : session.task}
                    </p>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <span className="text-[10px] text-acme-gray-600 bg-acme-gray-50 px-2 py-1 rounded-lg">
                    {formatRelativeTime(session.created_at)}
                  </span>
                  {onRerun && session.task && (
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        onRerun(session.task!);
                      }}
                      className="w-8 h-8 rounded-lg flex items-center justify-center bg-acme-navy/10 text-acme-navy hover:bg-acme-navy hover:text-white text-xs transition-all"
                      title="Re-run task"
                    >
                      <i className="fas fa-redo"></i>
                    </button>
                  )}
                  <div className="w-8 h-8 rounded-lg flex items-center justify-center bg-acme-gray-50 text-acme-gray-300 group-hover:bg-acme-navy group-hover:text-white transition-all">
                    <i className="fas fa-chevron-right text-xs"></i>
                  </div>
                </div>
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {sortedSessions.length > 0 && (
        <div className="px-4 py-2 bg-acme-gray-50 border-t border-acme-gray-100 flex items-center justify-between text-[10px] text-acme-gray-600 flex-shrink-0">
          <span>
            Showing {sortedSessions.length} of {sessions.length} sessions
          </span>
          <span>
            {new Date().toLocaleTimeString()}
          </span>
        </div>
      )}
    </div>
  );
};

export default SessionBrowser;
