
import React, { useState, useEffect } from 'react';
import { listSessions, SessionInfo } from '../services/geminiService';
import ArtifactsViewer from './ArtifactsViewer';

interface SessionBrowserProps {
  onClose?: () => void;
  onRerun?: (task: string) => void;
}

const SessionBrowser: React.FC<SessionBrowserProps> = ({ onClose, onRerun }) => {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedSession, setSelectedSession] = useState<string | null>(null);

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

  const formatSessionId = (sessionId: string): string => {
    // Extract timestamp if present in session ID format
    if (sessionId.includes('_')) {
      const parts = sessionId.split('_');
      return parts[0].substring(0, 8) + '...';
    }
    return sessionId.length > 12 ? sessionId.substring(0, 12) + '...' : sessionId;
  };

  if (selectedSession) {
    return (
      <div className="space-y-4">
        {/* Back button */}
        <button
          onClick={() => setSelectedSession(null)}
          className="flex items-center gap-2 text-sm text-slate-600 hover:text-slate-800 transition-colors"
        >
          <i className="fas fa-arrow-left"></i>
          Back to Sessions
        </button>

        {/* Session info header */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                <i className="fas fa-history text-blue-600"></i>
              </div>
              <div>
                <h3 className="font-semibold text-slate-800">Session: {selectedSession}</h3>
                <p className="text-xs text-slate-500">Viewing archived test session</p>
              </div>
            </div>
          </div>
        </div>

        {/* Artifacts viewer for selected session */}
        <ArtifactsViewer sessionId={selectedSession} />
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-50 to-slate-100 px-6 py-4 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <i className="fas fa-history text-blue-500"></i>
            Session History
          </h3>
          <div className="flex items-center gap-2">
            <button
              onClick={fetchSessions}
              disabled={loading}
              className="px-3 py-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-md transition-colors flex items-center gap-1.5"
            >
              <i className={`fas fa-sync-alt ${loading ? 'fa-spin' : ''}`}></i>
              Refresh
            </button>
            {onClose && (
              <button
                onClick={onClose}
                className="px-3 py-1.5 text-xs bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-md transition-colors"
              >
                <i className="fas fa-times"></i>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-4">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <i className="fas fa-spinner fa-spin text-3xl text-blue-500 mb-3"></i>
              <p className="text-slate-500">Loading sessions...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center text-rose-500">
              <i className="fas fa-exclamation-triangle text-3xl mb-3"></i>
              <p>{error}</p>
              <button
                onClick={fetchSessions}
                className="mt-3 px-4 py-2 text-sm bg-rose-100 hover:bg-rose-200 text-rose-700 rounded-md transition-colors"
              >
                Try Again
              </button>
            </div>
          </div>
        ) : sessions.length === 0 ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center text-slate-400">
              <i className="fas fa-folder-open text-4xl mb-3"></i>
              <p>No test sessions found</p>
              <p className="text-xs mt-1">Run a test to create your first session</p>
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            {sessions.map((session) => (
              <div
                key={session.session_id}
                className="bg-slate-50 rounded-lg border border-slate-200 overflow-hidden"
              >
                <button
                  onClick={() => setSelectedSession(session.session_id)}
                  className="w-full flex items-center gap-4 p-4 hover:bg-blue-50 transition-all text-left group"
                >
                  {/* Session icon */}
                  <div className={`w-12 h-12 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    session.has_report ? 'bg-emerald-100 text-emerald-600' : 'bg-slate-200 text-slate-500'
                  }`}>
                    <i className={`fas ${session.has_report ? 'fa-check-circle' : 'fa-clock'} text-xl`}></i>
                  </div>

                  {/* Session info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="font-medium text-slate-800 font-mono text-sm">
                        {session.session_id}
                      </span>
                      {session.has_report && (
                        <span className="px-2 py-0.5 bg-emerald-100 text-emerald-700 text-xs rounded-full">
                          Has Report
                        </span>
                      )}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">
                      <i className="fas fa-calendar-alt mr-1"></i>
                      {formatDate(session.created_at)}
                    </div>
                  </div>

                  {/* Arrow */}
                  <div className="text-slate-300 group-hover:text-blue-500 transition-colors">
                    <i className="fas fa-chevron-right"></i>
                  </div>
                </button>

                {/* Task preview and re-run button */}
                {session.task && (
                  <div className="px-4 pb-3 pt-0 flex items-center gap-3 border-t border-slate-100">
                    <div className="flex-1 min-w-0">
                      <p className="text-xs text-slate-500 truncate" title={session.task}>
                        <i className="fas fa-terminal mr-1 text-slate-400"></i>
                        {session.task.length > 80 ? session.task.substring(0, 80) + '...' : session.task}
                      </p>
                    </div>
                    {onRerun && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onRerun(session.task!);
                        }}
                        className="px-3 py-1.5 bg-blue-100 hover:bg-blue-200 text-blue-700 text-xs rounded-md transition-colors flex items-center gap-1.5 flex-shrink-0"
                      >
                        <i className="fas fa-redo"></i>
                        Re-run
                      </button>
                    )}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Footer */}
      {sessions.length > 0 && (
        <div className="px-6 py-3 bg-slate-50 border-t border-slate-200 text-xs text-slate-500">
          <i className="fas fa-info-circle mr-1"></i>
          {sessions.length} session{sessions.length !== 1 ? 's' : ''} available
        </div>
      )}
    </div>
  );
};

export default SessionBrowser;
