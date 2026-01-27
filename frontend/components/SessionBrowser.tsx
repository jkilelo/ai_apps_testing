
import React, { useState, useEffect, useMemo, useRef } from 'react';
import {
  listSessions,
  SessionInfo,
  listReplaySessions,
  ReplaySessionInfo,
  streamReplay,
  ReplayStreamEvent,
  ReplayResult,
  getSessionArtifacts,
} from '../services/geminiService';
import ArtifactsViewer from './ArtifactsViewer';

interface SessionBrowserProps {
  onClose?: () => void;
  onRerun?: (task: string) => void;
}

type SortOption = 'newest' | 'oldest' | 'has_report';
type ViewMode = 'sessions' | 'replay';
type ViewStyle = 'list' | 'grid';

// Cache for session thumbnails
const thumbnailCache: Record<string, string | null> = {};

// Thumbnail component that lazily loads session screenshot
const SessionThumbnail: React.FC<{ sessionId: string; className?: string }> = ({ sessionId, className = '' }) => {
  const [thumbnail, setThumbnail] = useState<string | null>(thumbnailCache[sessionId] ?? null);
  const [loading, setLoading] = useState(thumbnailCache[sessionId] === undefined);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (thumbnailCache[sessionId] !== undefined) {
      setThumbnail(thumbnailCache[sessionId]);
      setLoading(false);
      return;
    }

    const fetchThumbnail = async () => {
      try {
        const artifacts = await getSessionArtifacts(sessionId);
        if (artifacts.screenshots && artifacts.screenshots.length > 0) {
          // Get the first screenshot URL
          const firstScreenshot = artifacts.screenshots[0];
          // Convert relative path to absolute URL
          const url = firstScreenshot.startsWith('http')
            ? firstScreenshot
            : `http://localhost:8000${firstScreenshot.startsWith('/') ? '' : '/'}${firstScreenshot}`;
          thumbnailCache[sessionId] = url;
          setThumbnail(url);
        } else {
          thumbnailCache[sessionId] = null;
          setThumbnail(null);
        }
      } catch {
        thumbnailCache[sessionId] = null;
        setError(true);
      } finally {
        setLoading(false);
      }
    };

    fetchThumbnail();
  }, [sessionId]);

  if (loading) {
    return (
      <div className={`${className} bg-acme-gray-100 flex items-center justify-center animate-pulse`}>
        <i className="fas fa-image text-acme-gray-300"></i>
      </div>
    );
  }

  if (error || !thumbnail) {
    return (
      <div className={`${className} bg-gradient-to-br from-acme-gray-100 to-acme-gray-200 flex items-center justify-center`}>
        <i className="fas fa-desktop text-acme-gray-300 text-lg"></i>
      </div>
    );
  }

  return (
    <img
      src={thumbnail}
      alt="Session thumbnail"
      className={`${className} object-cover object-top`}
      onError={() => setError(true)}
    />
  );
};

const SessionBrowser: React.FC<SessionBrowserProps> = ({ onClose, onRerun }) => {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<SortOption>('newest');
  const [searchQuery, setSearchQuery] = useState('');
  const [viewStyle, setViewStyle] = useState<ViewStyle>('list');

  // View mode: regular sessions or replay sessions
  const [viewMode, setViewMode] = useState<ViewMode>('sessions');

  // Replay state
  const [replaySessions, setReplaySessions] = useState<ReplaySessionInfo[]>([]);
  const [replayLoading, setReplayLoading] = useState(false);
  const [replayRunning, setReplayRunning] = useState<string | null>(null);
  const [replayProgress, setReplayProgress] = useState<{ step: number; total: number } | null>(null);
  const [replayResult, setReplayResult] = useState<ReplayResult | null>(null);
  const [replayHeadless, setReplayHeadless] = useState(true);
  const replayCleanupRef = useRef<(() => void) | null>(null);

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

  useEffect(() => {
    if (viewMode === 'replay') {
      fetchReplaySessions();
    }
  }, [viewMode]);

  // Cleanup replay stream on unmount
  useEffect(() => {
    return () => {
      if (replayCleanupRef.current) {
        replayCleanupRef.current();
      }
    };
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

  const fetchReplaySessions = async () => {
    setReplayLoading(true);
    setError(null);
    try {
      const data = await listReplaySessions();
      setReplaySessions(data.sessions);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load replay sessions');
    } finally {
      setReplayLoading(false);
    }
  };

  const handleRunReplay = (sessionId: string) => {
    if (replayCleanupRef.current) {
      replayCleanupRef.current();
    }

    setReplayRunning(sessionId);
    setReplayProgress(null);
    setReplayResult(null);

    const cleanup = streamReplay(
      sessionId,
      { headless: replayHeadless },
      (event: ReplayStreamEvent) => {
        if (event.type === 'started') {
          setReplayProgress({ step: 0, total: event.total_actions || 0 });
        } else if (event.type === 'step_start') {
          setReplayProgress(prev => prev ? { ...prev, step: event.step || 0 } : null);
        } else if (event.type === 'step_complete') {
          // Progress already updated by step_start
        } else if (event.type === 'complete') {
          setReplayResult({
            success: event.success || false,
            session_id: sessionId,
            actions_total: event.actions_total || 0,
            actions_succeeded: event.actions_succeeded || 0,
            actions_failed: event.actions_failed || 0,
            failed_steps: event.failed_steps || [],
            errors: event.errors || [],
            duration_seconds: event.duration_seconds || 0,
          });
          setReplayRunning(null);
          setReplayProgress(null);
        } else if (event.type === 'error') {
          setReplayResult({
            success: false,
            session_id: sessionId,
            actions_total: 0,
            actions_succeeded: 0,
            actions_failed: 1,
            failed_steps: [],
            errors: [event.message || 'Unknown error'],
            duration_seconds: 0,
          });
          setReplayRunning(null);
          setReplayProgress(null);
        }
      },
      (error) => {
        setReplayResult({
          success: false,
          session_id: sessionId,
          actions_total: 0,
          actions_succeeded: 0,
          actions_failed: 1,
          failed_steps: [],
          errors: [error.message],
          duration_seconds: 0,
        });
        setReplayRunning(null);
        setReplayProgress(null);
      },
      () => {
        replayCleanupRef.current = null;
      }
    );

    replayCleanupRef.current = cleanup;
  };

  const handleStopReplay = () => {
    if (replayCleanupRef.current) {
      replayCleanupRef.current();
      replayCleanupRef.current = null;
    }
    setReplayRunning(null);
    setReplayProgress(null);
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
      <div className="h-full flex flex-col overflow-hidden">
        {/* Compact back button header */}
        <div className="flex items-center justify-between px-3 py-2 border-b border-acme-gray-100 flex-shrink-0">
          <button
            onClick={() => setSelectedSession(null)}
            className="flex items-center gap-2 text-xs font-medium text-acme-gray-700 hover:text-acme-navy transition-colors"
          >
            <i className="fas fa-arrow-left text-[10px]"></i>
            <span>Back</span>
          </button>
          <span className="text-[10px] font-mono text-acme-gray-500 bg-acme-gray-50 px-2 py-0.5 rounded">
            {selectedSession.substring(0, 12)}...
          </span>
        </div>

        {/* Artifacts viewer for selected session */}
        <div className="flex-1 min-h-0 overflow-hidden">
          <ArtifactsViewer sessionId={selectedSession} />
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col overflow-hidden">
      {/* Header with Mode Tabs */}
      <div className="px-3 py-2.5 border-b border-acme-gray-100 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {/* Mode Tabs */}
            <div className="flex items-center gap-1 bg-acme-gray-100 rounded-lg p-0.5">
              <button
                onClick={() => setViewMode('sessions')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  viewMode === 'sessions'
                    ? 'bg-white text-acme-navy shadow-sm'
                    : 'text-acme-gray-600 hover:text-acme-gray-800'
                }`}
              >
                <i className="fas fa-history mr-1.5"></i>
                Sessions
              </button>
              <button
                onClick={() => setViewMode('replay')}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${
                  viewMode === 'replay'
                    ? 'bg-white text-acme-navy shadow-sm'
                    : 'text-acme-gray-600 hover:text-acme-gray-800'
                }`}
              >
                <i className="fas fa-play-circle mr-1.5"></i>
                Replay
              </button>
            </div>
            <span className="text-[10px] text-acme-gray-500 hidden lg:inline">
              {viewMode === 'sessions'
                ? `${stats.total} sessions`
                : `${replaySessions.length} recordings`}
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            {viewMode === 'replay' && (
              <button
                onClick={() => setReplayHeadless(!replayHeadless)}
                className={`px-2 py-1 rounded-lg flex items-center gap-1 text-[10px] font-medium transition-all ${
                  replayHeadless
                    ? 'bg-acme-navy/10 text-acme-navy'
                    : 'bg-acme-gray-50 text-acme-gray-600 hover:bg-acme-gray-100'
                }`}
                title={replayHeadless ? 'Browser hidden' : 'Browser visible'}
              >
                <i className={`fas ${replayHeadless ? 'fa-eye-slash' : 'fa-eye'} text-[9px]`}></i>
                {replayHeadless ? 'Headless' : 'Visible'}
              </button>
            )}
            <button
              onClick={viewMode === 'sessions' ? fetchSessions : fetchReplaySessions}
              disabled={loading || replayLoading}
              className="w-7 h-7 rounded-lg flex items-center justify-center bg-acme-gray-50 hover:bg-acme-gray-100 text-acme-gray-500 hover:text-acme-gray-700 transition-all"
              title="Refresh"
            >
              <i className={`fas fa-sync-alt text-[10px] ${(loading || replayLoading) ? 'fa-spin' : ''}`}></i>
            </button>
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

          {/* View Style Toggle */}
          <div className="flex items-center bg-acme-gray-100 rounded-lg p-0.5">
            <button
              onClick={() => setViewStyle('list')}
              className={`w-8 h-8 rounded-md flex items-center justify-center transition-all ${
                viewStyle === 'list'
                  ? 'bg-white text-acme-navy shadow-sm'
                  : 'text-acme-gray-500 hover:text-acme-gray-700'
              }`}
              title="List view"
            >
              <i className="fas fa-list text-xs"></i>
            </button>
            <button
              onClick={() => setViewStyle('grid')}
              className={`w-8 h-8 rounded-md flex items-center justify-center transition-all ${
                viewStyle === 'grid'
                  ? 'bg-white text-acme-navy shadow-sm'
                  : 'text-acme-gray-500 hover:text-acme-gray-700'
              }`}
              title="Grid view"
            >
              <i className="fas fa-th-large text-xs"></i>
            </button>
          </div>
        </div>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto p-3">
        {viewMode === 'sessions' ? (
          /* Regular Sessions View */
          loading ? (
            <div className="space-y-2">
              {[...Array(5)].map((_, i) => (
                <div key={i} className="w-full flex items-center gap-3 p-3 bg-white rounded-xl border border-acme-gray-200 animate-pulse">
                  {/* Thumbnail skeleton */}
                  <div className="w-16 h-12 rounded-lg bg-acme-gray-200 flex-shrink-0" />
                  {/* Content skeleton */}
                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="flex items-center gap-2">
                      <div className="w-16 h-4 rounded-full bg-acme-gray-200" />
                      <div className="w-12 h-3 rounded bg-acme-gray-100" />
                    </div>
                    <div className="w-3/4 h-3.5 rounded bg-acme-gray-200" />
                  </div>
                  {/* Actions skeleton */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <div className="w-14 h-5 rounded-lg bg-acme-gray-100" />
                    <div className="w-8 h-8 rounded-lg bg-acme-gray-100" />
                  </div>
                </div>
              ))}
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
          ) : viewStyle === 'list' ? (
            /* List View */
            <div className="space-y-2">
              {sortedSessions.map((session) => (
                <button
                  key={session.session_id}
                  onClick={() => setSelectedSession(session.session_id)}
                  className="w-full flex items-center gap-3 p-3 bg-white hover:bg-acme-gray-50 rounded-xl border border-acme-gray-200 hover:border-acme-navy/30 transition-all text-left group shadow-sm hover:shadow-md btn-press"
                >
                  {/* Thumbnail */}
                  <div className="w-16 h-12 rounded-lg overflow-hidden flex-shrink-0 border border-acme-gray-200">
                    <SessionThumbnail sessionId={session.session_id} className="w-full h-full" />
                  </div>

                  {/* Session Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      {/* Status Badge */}
                      {session.has_report ? (
                        <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-[10px] font-semibold rounded-full flex items-center gap-1">
                          <i className="fas fa-check-circle text-[8px]"></i>
                          Complete
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 bg-amber-100 text-amber-700 text-[10px] font-semibold rounded-full flex items-center gap-1">
                          <i className="fas fa-clock text-[8px]"></i>
                          Pending
                        </span>
                      )}
                      <span className="text-[10px] font-mono text-acme-gray-500">
                        {session.session_id.substring(0, 8)}
                      </span>
                    </div>
                    {session.task ? (
                      <p className="text-xs text-acme-gray-800 font-medium truncate">
                        {session.task.length > 60 ? session.task.substring(0, 60) + '...' : session.task}
                      </p>
                    ) : (
                      <p className="text-xs text-acme-gray-500 italic">No task description</p>
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
          ) : (
            /* Grid View */
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-3">
              {sortedSessions.map((session) => (
                <button
                  key={session.session_id}
                  onClick={() => setSelectedSession(session.session_id)}
                  className="flex flex-col bg-white rounded-xl border border-acme-gray-200 hover:border-acme-navy/30 transition-all text-left group shadow-sm hover:shadow-lg overflow-hidden"
                >
                  {/* Thumbnail */}
                  <div className="relative w-full aspect-video bg-acme-gray-100">
                    <SessionThumbnail sessionId={session.session_id} className="w-full h-full" />
                    {/* Status Badge Overlay */}
                    <div className="absolute top-2 left-2">
                      {session.has_report ? (
                        <span className="px-2 py-0.5 bg-emerald-500 text-white text-[10px] font-semibold rounded-full flex items-center gap-1 shadow-sm">
                          <i className="fas fa-check text-[8px]"></i>
                          Pass
                        </span>
                      ) : (
                        <span className="px-2 py-0.5 bg-amber-500 text-white text-[10px] font-semibold rounded-full flex items-center gap-1 shadow-sm">
                          <i className="fas fa-clock text-[8px]"></i>
                          Pending
                        </span>
                      )}
                    </div>
                    {/* Hover Overlay */}
                    <div className="absolute inset-0 bg-acme-navy/0 group-hover:bg-acme-navy/10 transition-colors flex items-center justify-center">
                      <div className="w-10 h-10 rounded-full bg-white/0 group-hover:bg-white/90 flex items-center justify-center transition-all scale-0 group-hover:scale-100">
                        <i className="fas fa-eye text-acme-navy"></i>
                      </div>
                    </div>
                  </div>

                  {/* Card Content */}
                  <div className="p-3">
                    <p className="text-xs text-acme-gray-800 font-medium line-clamp-2 mb-2 min-h-[2.5rem]">
                      {session.task || 'No task description'}
                    </p>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] text-acme-gray-500 font-mono">
                        {session.session_id.substring(0, 8)}
                      </span>
                      <span className="text-[10px] text-acme-gray-500">
                        {formatRelativeTime(session.created_at)}
                      </span>
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )
        ) : (
          /* Replay Sessions View */
          replayLoading ? (
            <div className="space-y-2">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="w-full flex items-center gap-3 p-3 bg-white rounded-xl border border-acme-gray-200 animate-pulse">
                  <div className="w-10 h-10 rounded-xl bg-acme-gray-200 flex-shrink-0" />
                  <div className="flex-1 min-w-0 space-y-2">
                    <div className="w-2/3 h-3.5 rounded bg-acme-gray-200" />
                    <div className="w-1/2 h-3 rounded bg-acme-gray-100" />
                  </div>
                  <div className="w-16 h-8 rounded-lg bg-acme-gray-200 flex-shrink-0" />
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="w-16 h-16 rounded-2xl bg-acme-red/10 flex items-center justify-center mb-4">
                <i className="fas fa-exclamation-triangle text-2xl text-acme-red"></i>
              </div>
              <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">Failed to Load</h3>
              <p className="text-xs text-acme-gray-600 mb-4">{error}</p>
              <button
                onClick={fetchReplaySessions}
                className="px-4 py-2 text-xs font-medium bg-acme-navy text-white rounded-lg hover:bg-acme-navy-dark transition-colors"
              >
                Try Again
              </button>
            </div>
          ) : replaySessions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full">
              <div className="w-16 h-16 rounded-2xl bg-acme-gray-100 flex items-center justify-center mb-4">
                <i className="fas fa-play-circle text-2xl text-acme-gray-300"></i>
              </div>
              <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">No Replay Recordings</h3>
              <p className="text-xs text-acme-gray-600 text-center max-w-xs">
                Run a UI test task to automatically record actions for replay.
                Recordings enable zero-LLM-cost test re-runs.
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {/* Replay Result Banner */}
              {replayResult && (
                <div className={`p-3 rounded-xl border ${
                  replayResult.success
                    ? 'bg-emerald-50 border-emerald-200'
                    : 'bg-red-50 border-red-200'
                }`}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <i className={`fas ${replayResult.success ? 'fa-check-circle text-emerald-600' : 'fa-times-circle text-red-600'}`}></i>
                      <span className={`text-xs font-semibold ${replayResult.success ? 'text-emerald-800' : 'text-red-800'}`}>
                        {replayResult.success ? 'Replay Passed' : 'Replay Failed'}
                      </span>
                    </div>
                    <div className="flex items-center gap-3 text-[10px]">
                      <span className={replayResult.success ? 'text-emerald-700' : 'text-red-700'}>
                        {replayResult.actions_succeeded}/{replayResult.actions_total} actions
                      </span>
                      <span className={replayResult.success ? 'text-emerald-600' : 'text-red-600'}>
                        {replayResult.duration_seconds.toFixed(1)}s
                      </span>
                      <button
                        onClick={() => setReplayResult(null)}
                        className="text-acme-gray-500 hover:text-acme-gray-700"
                      >
                        <i className="fas fa-times"></i>
                      </button>
                    </div>
                  </div>
                  {replayResult.errors.length > 0 && (
                    <div className="mt-2 text-[10px] text-red-700">
                      {replayResult.errors.slice(0, 2).map((err, i) => (
                        <div key={i} className="truncate">{err}</div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Replay Sessions List */}
              {replaySessions.map((session) => (
                <div
                  key={session.session_id}
                  className={`w-full flex items-center gap-3 p-3 bg-white rounded-xl border transition-all text-left ${
                    replayRunning === session.session_id
                      ? 'border-acme-navy shadow-md'
                      : 'border-acme-gray-200 hover:border-acme-navy/30 hover:shadow-md'
                  }`}
                >
                  {/* Play Icon */}
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center flex-shrink-0 ${
                    replayRunning === session.session_id
                      ? 'bg-acme-navy text-white'
                      : 'bg-acme-navy/10 text-acme-navy'
                  }`}>
                    {replayRunning === session.session_id ? (
                      <i className="fas fa-circle-notch fa-spin"></i>
                    ) : (
                      <i className="fas fa-play"></i>
                    )}
                  </div>

                  {/* Session Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-medium text-acme-gray-800 truncate">
                        {session.task.length > 50 ? session.task.substring(0, 50) + '...' : session.task}
                      </span>
                    </div>
                    <div className="flex items-center gap-2 text-[10px] text-acme-gray-500">
                      <span>{session.action_count} actions</span>
                      <span>•</span>
                      <span className="truncate">{session.initial_url}</span>
                    </div>
                    {/* Progress Bar */}
                    {replayRunning === session.session_id && replayProgress && (
                      <div className="mt-2">
                        <div className="flex items-center gap-2">
                          <div className="flex-1 h-1.5 bg-acme-gray-100 rounded-full overflow-hidden">
                            <div
                              className="h-full bg-acme-navy transition-all duration-300"
                              style={{ width: `${(replayProgress.step / replayProgress.total) * 100}%` }}
                            />
                          </div>
                          <span className="text-[10px] font-medium text-acme-navy">
                            {replayProgress.step}/{replayProgress.total}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center gap-2 flex-shrink-0">
                    {replayRunning === session.session_id ? (
                      <button
                        onClick={handleStopReplay}
                        className="h-8 px-3 rounded-lg flex items-center gap-1.5 bg-red-500 text-white hover:bg-red-600 text-xs font-medium transition-all"
                      >
                        <i className="fas fa-stop text-[9px]"></i>
                        Stop
                      </button>
                    ) : (
                      <button
                        onClick={() => handleRunReplay(session.session_id)}
                        disabled={replayRunning !== null}
                        className={`h-8 px-3 rounded-lg flex items-center gap-1.5 text-xs font-medium transition-all ${
                          replayRunning !== null
                            ? 'bg-acme-gray-100 text-acme-gray-400 cursor-not-allowed'
                            : 'bg-acme-navy text-white hover:bg-acme-navy-dark'
                        }`}
                      >
                        <i className="fas fa-play text-[9px]"></i>
                        Run
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )
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
