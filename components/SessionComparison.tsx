
import React, { useState, useEffect } from 'react';
import {
  listSessions,
  getSessionArtifacts,
  SessionInfo,
  SessionArtifacts,
} from '../services/geminiService';

// API base URL for building absolute URLs
const API_BASE_URL = 'http://localhost:8001';

const toAbsoluteUrl = (relativePath: string): string => {
  if (relativePath.startsWith('http')) {
    return relativePath;
  }
  return `${API_BASE_URL}${relativePath}`;
};

interface SessionComparisonProps {
  onClose?: () => void;
}

const SessionComparison: React.FC<SessionComparisonProps> = ({ onClose }) => {
  const [sessions, setSessions] = useState<SessionInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [sessionA, setSessionA] = useState<string | null>(null);
  const [sessionB, setSessionB] = useState<string | null>(null);
  const [artifactsA, setArtifactsA] = useState<SessionArtifacts | null>(null);
  const [artifactsB, setArtifactsB] = useState<SessionArtifacts | null>(null);
  const [loadingArtifacts, setLoadingArtifacts] = useState(false);
  const [activeTab, setActiveTab] = useState<'screenshots' | 'summary'>('summary');

  useEffect(() => {
    fetchSessions();
  }, []);

  useEffect(() => {
    if (sessionA && sessionB) {
      loadArtifacts();
    }
  }, [sessionA, sessionB]);

  const fetchSessions = async () => {
    setLoading(true);
    try {
      const data = await listSessions();
      setSessions(data.sessions);
    } catch (err) {
      console.error('Failed to load sessions:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadArtifacts = async () => {
    if (!sessionA || !sessionB) return;

    setLoadingArtifacts(true);
    try {
      const [a, b] = await Promise.all([
        getSessionArtifacts(sessionA),
        getSessionArtifacts(sessionB),
      ]);
      setArtifactsA(a);
      setArtifactsB(b);
    } catch (err) {
      console.error('Failed to load artifacts:', err);
    } finally {
      setLoadingArtifacts(false);
    }
  };

  const formatDate = (timestamp: number): string => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleString();
  };

  const getSessionLabel = (session: SessionInfo): string => {
    if (session.task) {
      return session.task.length > 40 ? session.task.substring(0, 40) + '...' : session.task;
    }
    return session.session_id;
  };

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-50 to-slate-100 px-6 py-4 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <i className="fas fa-columns text-purple-500"></i>
            Compare Sessions
          </h3>
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

      {/* Session Selectors */}
      <div className="p-4 bg-slate-50 border-b border-slate-200">
        <div className="grid grid-cols-2 gap-4">
          {/* Session A */}
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Session A
            </label>
            <select
              value={sessionA || ''}
              onChange={(e) => setSessionA(e.target.value || null)}
              className="w-full p-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              disabled={loading}
            >
              <option value="">Select session...</option>
              {sessions.map((s) => (
                <option key={s.session_id} value={s.session_id} disabled={s.session_id === sessionB}>
                  {s.session_id} - {formatDate(s.created_at)}
                </option>
              ))}
            </select>
          </div>

          {/* Session B */}
          <div>
            <label className="block text-xs font-medium text-slate-600 mb-1">
              Session B
            </label>
            <select
              value={sessionB || ''}
              onChange={(e) => setSessionB(e.target.value || null)}
              className="w-full p-2 bg-white border border-slate-200 rounded-lg text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent outline-none"
              disabled={loading}
            >
              <option value="">Select session...</option>
              {sessions.map((s) => (
                <option key={s.session_id} value={s.session_id} disabled={s.session_id === sessionA}>
                  {s.session_id} - {formatDate(s.created_at)}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>

      {/* Comparison Content */}
      {sessionA && sessionB ? (
        <>
          {/* Tabs */}
          <div className="flex border-b border-slate-200 bg-slate-50">
            <button
              onClick={() => setActiveTab('summary')}
              className={`px-4 py-3 flex items-center gap-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === 'summary'
                  ? 'text-blue-600 border-blue-600 bg-white'
                  : 'text-slate-500 border-transparent hover:text-slate-700'
              }`}
            >
              <i className="fas fa-chart-bar"></i>
              Summary
            </button>
            <button
              onClick={() => setActiveTab('screenshots')}
              className={`px-4 py-3 flex items-center gap-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
                activeTab === 'screenshots'
                  ? 'text-blue-600 border-blue-600 bg-white'
                  : 'text-slate-500 border-transparent hover:text-slate-700'
              }`}
            >
              <i className="fas fa-images"></i>
              Screenshots
            </button>
          </div>

          {loadingArtifacts ? (
            <div className="flex items-center justify-center py-12">
              <div className="text-center">
                <i className="fas fa-spinner fa-spin text-3xl text-blue-500 mb-3"></i>
                <p className="text-slate-500">Loading comparison...</p>
              </div>
            </div>
          ) : (
            <div className="p-4">
              {activeTab === 'summary' && artifactsA && artifactsB && (
                <div className="grid grid-cols-2 gap-4">
                  {/* Session A Summary */}
                  <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                    <h4 className="font-semibold text-blue-800 mb-3 flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs">A</div>
                      {sessionA}
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600">Screenshots:</span>
                        <span className="font-medium">{artifactsA.screenshots.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Total Files:</span>
                        <span className="font-medium">{artifactsA.artifacts.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Has Report:</span>
                        <span className={`font-medium ${artifactsA.html_report ? 'text-emerald-600' : 'text-slate-400'}`}>
                          {artifactsA.html_report ? 'Yes' : 'No'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Has Video:</span>
                        <span className={`font-medium ${artifactsA.video ? 'text-emerald-600' : 'text-slate-400'}`}>
                          {artifactsA.video ? 'Yes' : 'No'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Session B Summary */}
                  <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
                    <h4 className="font-semibold text-purple-800 mb-3 flex items-center gap-2">
                      <div className="w-6 h-6 rounded-full bg-purple-500 text-white flex items-center justify-center text-xs">B</div>
                      {sessionB}
                    </h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-slate-600">Screenshots:</span>
                        <span className="font-medium">{artifactsB.screenshots.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Total Files:</span>
                        <span className="font-medium">{artifactsB.artifacts.length}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Has Report:</span>
                        <span className={`font-medium ${artifactsB.html_report ? 'text-emerald-600' : 'text-slate-400'}`}>
                          {artifactsB.html_report ? 'Yes' : 'No'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-600">Has Video:</span>
                        <span className={`font-medium ${artifactsB.video ? 'text-emerald-600' : 'text-slate-400'}`}>
                          {artifactsB.video ? 'Yes' : 'No'}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Comparison Stats */}
                  <div className="col-span-2 bg-slate-50 rounded-lg p-4 border border-slate-200">
                    <h4 className="font-semibold text-slate-700 mb-3">Comparison</h4>
                    <div className="grid grid-cols-3 gap-4 text-center">
                      <div>
                        <div className="text-2xl font-bold text-slate-800">
                          {Math.abs(artifactsA.screenshots.length - artifactsB.screenshots.length)}
                        </div>
                        <div className="text-xs text-slate-500">Screenshot Diff</div>
                      </div>
                      <div>
                        <div className="text-2xl font-bold text-slate-800">
                          {Math.abs(artifactsA.artifacts.length - artifactsB.artifacts.length)}
                        </div>
                        <div className="text-xs text-slate-500">Artifact Diff</div>
                      </div>
                      <div>
                        <div className={`text-2xl font-bold ${
                          artifactsA.html_report && artifactsB.html_report ? 'text-emerald-600' : 'text-amber-600'
                        }`}>
                          {artifactsA.html_report && artifactsB.html_report ? 'Both' : 'Partial'}
                        </div>
                        <div className="text-xs text-slate-500">Reports</div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'screenshots' && artifactsA && artifactsB && (
                <div className="grid grid-cols-2 gap-4">
                  {/* Session A Screenshots */}
                  <div>
                    <h4 className="font-medium text-slate-700 mb-2 flex items-center gap-2">
                      <div className="w-5 h-5 rounded-full bg-blue-500 text-white flex items-center justify-center text-xs">A</div>
                      Session A ({artifactsA.screenshots.length} screenshots)
                    </h4>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {artifactsA.screenshots.map((screenshot, index) => (
                        <div key={screenshot} className="relative">
                          <img
                            src={toAbsoluteUrl(screenshot)}
                            alt={`A Step ${index + 1}`}
                            className="w-full rounded border border-slate-200"
                            loading="lazy"
                          />
                          <div className="absolute top-2 left-2 px-2 py-0.5 bg-blue-500 text-white text-xs rounded">
                            Step {index + 1}
                          </div>
                        </div>
                      ))}
                      {artifactsA.screenshots.length === 0 && (
                        <div className="text-center py-8 text-slate-400 text-sm">
                          No screenshots
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Session B Screenshots */}
                  <div>
                    <h4 className="font-medium text-slate-700 mb-2 flex items-center gap-2">
                      <div className="w-5 h-5 rounded-full bg-purple-500 text-white flex items-center justify-center text-xs">B</div>
                      Session B ({artifactsB.screenshots.length} screenshots)
                    </h4>
                    <div className="space-y-2 max-h-96 overflow-y-auto">
                      {artifactsB.screenshots.map((screenshot, index) => (
                        <div key={screenshot} className="relative">
                          <img
                            src={toAbsoluteUrl(screenshot)}
                            alt={`B Step ${index + 1}`}
                            className="w-full rounded border border-slate-200"
                            loading="lazy"
                          />
                          <div className="absolute top-2 left-2 px-2 py-0.5 bg-purple-500 text-white text-xs rounded">
                            Step {index + 1}
                          </div>
                        </div>
                      ))}
                      {artifactsB.screenshots.length === 0 && (
                        <div className="text-center py-8 text-slate-400 text-sm">
                          No screenshots
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
        </>
      ) : (
        <div className="flex items-center justify-center py-12">
          <div className="text-center text-slate-400">
            <i className="fas fa-columns text-4xl mb-3"></i>
            <p>Select two sessions to compare</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionComparison;
