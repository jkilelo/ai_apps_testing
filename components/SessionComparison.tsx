
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
  const [selectedScreenshot, setSelectedScreenshot] = useState<{ url: string; session: 'A' | 'B'; index: number } | null>(null);

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

  const formatShortDate = (timestamp: number): string => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleDateString();
  };

  return (
    <div className="h-full flex flex-col bg-white rounded-xl border border-acme-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-4 py-3 border-b border-acme-gray-100 flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-xl bg-acme-navy/10 flex items-center justify-center">
              <i className="fas fa-columns text-acme-navy"></i>
            </div>
            <div>
              <h3 className="text-sm font-semibold text-acme-gray-800">Compare Sessions</h3>
              <p className="text-[10px] text-acme-gray-600">
                Side-by-side session comparison
              </p>
            </div>
          </div>
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

      {/* Session Selectors */}
      <div className="px-4 py-4 bg-acme-gray-50/50 border-b border-acme-gray-100 flex-shrink-0">
        <div className="grid grid-cols-2 gap-4">
          {/* Session A */}
          <div className="bg-white rounded-xl border border-acme-gray-200 p-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 rounded-lg bg-acme-navy flex items-center justify-center">
                <span className="text-[10px] font-bold text-white">A</span>
              </div>
              <label className="text-xs font-medium text-acme-gray-700">
                Baseline Session
              </label>
            </div>
            <select
              value={sessionA || ''}
              onChange={(e) => setSessionA(e.target.value || null)}
              className="w-full p-2.5 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs focus:ring-2 focus:ring-acme-navy/20 focus:border-acme-navy outline-none transition-all cursor-pointer"
              disabled={loading}
            >
              <option value="">Select session...</option>
              {sessions.map((s) => (
                <option key={s.session_id} value={s.session_id} disabled={s.session_id === sessionB}>
                  {s.session_id.substring(0, 16)}... - {formatShortDate(s.created_at)}
                </option>
              ))}
            </select>
          </div>

          {/* Session B */}
          <div className="bg-white rounded-xl border border-acme-gray-200 p-3">
            <div className="flex items-center gap-2 mb-2">
              <div className="w-6 h-6 rounded-lg bg-sky-500 flex items-center justify-center">
                <span className="text-[10px] font-bold text-white">B</span>
              </div>
              <label className="text-xs font-medium text-acme-gray-700">
                Compare Session
              </label>
            </div>
            <select
              value={sessionB || ''}
              onChange={(e) => setSessionB(e.target.value || null)}
              className="w-full p-2.5 bg-acme-gray-50 border border-acme-gray-200 rounded-lg text-xs focus:ring-2 focus:ring-acme-navy/20 focus:border-acme-navy outline-none transition-all cursor-pointer"
              disabled={loading}
            >
              <option value="">Select session...</option>
              {sessions.map((s) => (
                <option key={s.session_id} value={s.session_id} disabled={s.session_id === sessionA}>
                  {s.session_id.substring(0, 16)}... - {formatShortDate(s.created_at)}
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
          <div className="flex px-4 py-3 border-b border-acme-gray-100 gap-2 flex-shrink-0">
            <button
              onClick={() => setActiveTab('summary')}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
                activeTab === 'summary'
                  ? 'bg-acme-navy text-white shadow-sm'
                  : 'text-acme-gray-600 hover:bg-acme-gray-100'
              }`}
            >
              <i className="fas fa-chart-bar text-[10px]"></i>
              Summary
            </button>
            <button
              onClick={() => setActiveTab('screenshots')}
              className={`px-4 py-2 rounded-lg text-xs font-medium transition-all flex items-center gap-2 ${
                activeTab === 'screenshots'
                  ? 'bg-acme-navy text-white shadow-sm'
                  : 'text-acme-gray-600 hover:bg-acme-gray-100'
              }`}
            >
              <i className="fas fa-images text-[10px]"></i>
              Screenshots
              {artifactsA && artifactsB && (
                <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${
                  activeTab === 'screenshots' ? 'bg-white/20' : 'bg-acme-gray-200'
                }`}>
                  {artifactsA.screenshots.length + artifactsB.screenshots.length}
                </span>
              )}
            </button>
          </div>

          {loadingArtifacts ? (
            <div className="flex-1 flex flex-col items-center justify-center">
              <div className="w-16 h-16 rounded-2xl bg-acme-gray-100 flex items-center justify-center mb-4">
                <i className="fas fa-spinner fa-spin text-2xl text-acme-navy"></i>
              </div>
              <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">Loading Comparison</h3>
              <p className="text-xs text-acme-gray-600">Fetching session data...</p>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-4">
              {activeTab === 'summary' && artifactsA && artifactsB && (
                <div className="space-y-4">
                  {/* Comparison Stats - Widget Style */}
                  <div className="grid grid-cols-3 gap-3">
                    {/* Screenshots Comparison */}
                    <div className="bg-white rounded-xl border border-acme-gray-200 p-4 shadow-sm">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-[10px] font-semibold text-acme-gray-600 uppercase tracking-wider">Screenshots</span>
                        <div className="w-7 h-7 rounded-lg bg-violet-50 flex items-center justify-center">
                          <i className="fas fa-camera text-violet-600 text-xs"></i>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="text-center">
                          <div className="text-lg font-bold text-acme-navy">{artifactsA.screenshots.length}</div>
                          <div className="text-[10px] text-acme-gray-500">Session A</div>
                        </div>
                        <div className={`px-2 py-1 rounded-full text-[10px] font-medium ${
                          artifactsA.screenshots.length === artifactsB.screenshots.length
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}>
                          {artifactsA.screenshots.length === artifactsB.screenshots.length
                            ? 'Equal'
                            : `${Math.abs(artifactsA.screenshots.length - artifactsB.screenshots.length)} diff`}
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-bold text-sky-500">{artifactsB.screenshots.length}</div>
                          <div className="text-[10px] text-acme-gray-500">Session B</div>
                        </div>
                      </div>
                    </div>

                    {/* Artifacts Comparison */}
                    <div className="bg-white rounded-xl border border-acme-gray-200 p-4 shadow-sm">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-[10px] font-semibold text-acme-gray-600 uppercase tracking-wider">Total Files</span>
                        <div className="w-7 h-7 rounded-lg bg-amber-50 flex items-center justify-center">
                          <i className="fas fa-folder text-amber-600 text-xs"></i>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="text-center">
                          <div className="text-lg font-bold text-acme-navy">{artifactsA.artifacts.length}</div>
                          <div className="text-[10px] text-acme-gray-500">Session A</div>
                        </div>
                        <div className={`px-2 py-1 rounded-full text-[10px] font-medium ${
                          artifactsA.artifacts.length === artifactsB.artifacts.length
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}>
                          {artifactsA.artifacts.length === artifactsB.artifacts.length
                            ? 'Equal'
                            : `${Math.abs(artifactsA.artifacts.length - artifactsB.artifacts.length)} diff`}
                        </div>
                        <div className="text-center">
                          <div className="text-lg font-bold text-sky-500">{artifactsB.artifacts.length}</div>
                          <div className="text-[10px] text-acme-gray-500">Session B</div>
                        </div>
                      </div>
                    </div>

                    {/* Reports Status */}
                    <div className="bg-white rounded-xl border border-acme-gray-200 p-4 shadow-sm">
                      <div className="flex items-center justify-between mb-3">
                        <span className="text-[10px] font-semibold text-acme-gray-600 uppercase tracking-wider">Reports</span>
                        <div className="w-7 h-7 rounded-lg bg-emerald-50 flex items-center justify-center">
                          <i className="fas fa-file-alt text-emerald-600 text-xs"></i>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="text-center">
                          <div className={`text-lg font-bold ${artifactsA.html_report ? 'text-emerald-600' : 'text-acme-gray-300'}`}>
                            {artifactsA.html_report ? 'Yes' : 'No'}
                          </div>
                          <div className="text-[10px] text-acme-gray-500">Session A</div>
                        </div>
                        <div className={`px-2 py-1 rounded-full text-[10px] font-medium ${
                          artifactsA.html_report && artifactsB.html_report
                            ? 'bg-emerald-100 text-emerald-700'
                            : !artifactsA.html_report && !artifactsB.html_report
                              ? 'bg-acme-gray-100 text-acme-gray-500'
                              : 'bg-amber-100 text-amber-700'
                        }`}>
                          {artifactsA.html_report && artifactsB.html_report
                            ? 'Both'
                            : !artifactsA.html_report && !artifactsB.html_report
                              ? 'None'
                              : 'Partial'}
                        </div>
                        <div className="text-center">
                          <div className={`text-lg font-bold ${artifactsB.html_report ? 'text-emerald-600' : 'text-acme-gray-300'}`}>
                            {artifactsB.html_report ? 'Yes' : 'No'}
                          </div>
                          <div className="text-[10px] text-acme-gray-500">Session B</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Session Details Cards */}
                  <div className="grid grid-cols-2 gap-4">
                    {/* Session A Card */}
                    <div className="bg-gradient-to-br from-acme-navy/5 to-acme-navy/10 rounded-xl border border-acme-navy/20 p-4">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-xl bg-acme-navy text-white flex items-center justify-center text-sm font-bold">
                          A
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-semibold text-acme-navy truncate">{sessionA}</h4>
                          <p className="text-[10px] text-acme-gray-600">Baseline Session</p>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center py-2 border-b border-acme-navy/10">
                          <span className="text-xs text-acme-gray-600">Screenshots</span>
                          <span className="text-xs font-medium text-acme-gray-800">{artifactsA.screenshots.length}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-acme-navy/10">
                          <span className="text-xs text-acme-gray-600">Total Files</span>
                          <span className="text-xs font-medium text-acme-gray-800">{artifactsA.artifacts.length}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-acme-navy/10">
                          <span className="text-xs text-acme-gray-600">Has Report</span>
                          <span className={`text-xs font-medium ${artifactsA.html_report ? 'text-emerald-600' : 'text-acme-gray-400'}`}>
                            {artifactsA.html_report ? 'Yes' : 'No'}
                          </span>
                        </div>
                        <div className="flex justify-between items-center py-2">
                          <span className="text-xs text-acme-gray-600">Has Video</span>
                          <span className={`text-xs font-medium ${artifactsA.video ? 'text-emerald-600' : 'text-acme-gray-400'}`}>
                            {artifactsA.video ? 'Yes' : 'No'}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Session B Card */}
                    <div className="bg-gradient-to-br from-sky-50 to-sky-100/50 rounded-xl border border-sky-200 p-4">
                      <div className="flex items-center gap-3 mb-4">
                        <div className="w-10 h-10 rounded-xl bg-sky-500 text-white flex items-center justify-center text-sm font-bold">
                          B
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-semibold text-sky-700 truncate">{sessionB}</h4>
                          <p className="text-[10px] text-acme-gray-600">Compare Session</p>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex justify-between items-center py-2 border-b border-sky-200/50">
                          <span className="text-xs text-acme-gray-600">Screenshots</span>
                          <span className="text-xs font-medium text-acme-gray-800">{artifactsB.screenshots.length}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-sky-200/50">
                          <span className="text-xs text-acme-gray-600">Total Files</span>
                          <span className="text-xs font-medium text-acme-gray-800">{artifactsB.artifacts.length}</span>
                        </div>
                        <div className="flex justify-between items-center py-2 border-b border-sky-200/50">
                          <span className="text-xs text-acme-gray-600">Has Report</span>
                          <span className={`text-xs font-medium ${artifactsB.html_report ? 'text-emerald-600' : 'text-acme-gray-400'}`}>
                            {artifactsB.html_report ? 'Yes' : 'No'}
                          </span>
                        </div>
                        <div className="flex justify-between items-center py-2">
                          <span className="text-xs text-acme-gray-600">Has Video</span>
                          <span className={`text-xs font-medium ${artifactsB.video ? 'text-emerald-600' : 'text-acme-gray-400'}`}>
                            {artifactsB.video ? 'Yes' : 'No'}
                          </span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {activeTab === 'screenshots' && artifactsA && artifactsB && (
                <div className="grid grid-cols-2 gap-4">
                  {/* Session A Screenshots */}
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-6 h-6 rounded-lg bg-acme-navy text-white flex items-center justify-center text-[10px] font-bold">A</div>
                      <h4 className="text-xs font-semibold text-acme-gray-700">
                        Session A
                        <span className="ml-2 font-normal text-acme-gray-500">({artifactsA.screenshots.length} screenshots)</span>
                      </h4>
                    </div>
                    <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                      {artifactsA.screenshots.map((screenshot, index) => (
                        <div
                          key={screenshot}
                          className="relative group cursor-pointer"
                          onClick={() => setSelectedScreenshot({ url: toAbsoluteUrl(screenshot), session: 'A', index })}
                        >
                          <img
                            src={toAbsoluteUrl(screenshot)}
                            alt={`A Step ${index + 1}`}
                            className="w-full rounded-xl border border-acme-gray-200 shadow-sm group-hover:shadow-md transition-all"
                            loading="lazy"
                          />
                          <div className="absolute top-2 left-2 px-2 py-1 bg-acme-navy text-white text-[10px] font-medium rounded-lg shadow">
                            Step {index + 1}
                          </div>
                          <div className="absolute inset-0 bg-acme-navy/0 group-hover:bg-acme-navy/10 rounded-xl transition-colors flex items-center justify-center">
                            <div className="w-10 h-10 rounded-full bg-white/90 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-lg">
                              <i className="fas fa-expand text-acme-navy text-xs"></i>
                            </div>
                          </div>
                        </div>
                      ))}
                      {artifactsA.screenshots.length === 0 && (
                        <div className="text-center py-12 text-acme-gray-500">
                          <i className="fas fa-images text-2xl mb-2 opacity-50"></i>
                          <p className="text-xs">No screenshots</p>
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Session B Screenshots */}
                  <div>
                    <div className="flex items-center gap-2 mb-3">
                      <div className="w-6 h-6 rounded-lg bg-sky-500 text-white flex items-center justify-center text-[10px] font-bold">B</div>
                      <h4 className="text-xs font-semibold text-acme-gray-700">
                        Session B
                        <span className="ml-2 font-normal text-acme-gray-500">({artifactsB.screenshots.length} screenshots)</span>
                      </h4>
                    </div>
                    <div className="space-y-3 max-h-[500px] overflow-y-auto pr-2">
                      {artifactsB.screenshots.map((screenshot, index) => (
                        <div
                          key={screenshot}
                          className="relative group cursor-pointer"
                          onClick={() => setSelectedScreenshot({ url: toAbsoluteUrl(screenshot), session: 'B', index })}
                        >
                          <img
                            src={toAbsoluteUrl(screenshot)}
                            alt={`B Step ${index + 1}`}
                            className="w-full rounded-xl border border-acme-gray-200 shadow-sm group-hover:shadow-md transition-all"
                            loading="lazy"
                          />
                          <div className="absolute top-2 left-2 px-2 py-1 bg-sky-500 text-white text-[10px] font-medium rounded-lg shadow">
                            Step {index + 1}
                          </div>
                          <div className="absolute inset-0 bg-sky-500/0 group-hover:bg-sky-500/10 rounded-xl transition-colors flex items-center justify-center">
                            <div className="w-10 h-10 rounded-full bg-white/90 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity shadow-lg">
                              <i className="fas fa-expand text-sky-500 text-xs"></i>
                            </div>
                          </div>
                        </div>
                      ))}
                      {artifactsB.screenshots.length === 0 && (
                        <div className="text-center py-12 text-acme-gray-500">
                          <i className="fas fa-images text-2xl mb-2 opacity-50"></i>
                          <p className="text-xs">No screenshots</p>
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
        <div className="flex-1 flex flex-col items-center justify-center">
          <div className="w-20 h-20 rounded-2xl bg-acme-gray-100 flex items-center justify-center mb-4">
            <i className="fas fa-columns text-3xl text-acme-gray-300"></i>
          </div>
          <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">Select Sessions to Compare</h3>
          <p className="text-xs text-acme-gray-600 text-center max-w-xs">
            Choose two sessions from the dropdowns above to see a detailed side-by-side comparison
          </p>
        </div>
      )}

      {/* Screenshot Lightbox */}
      {selectedScreenshot && (
        <div
          className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-8"
          onClick={() => setSelectedScreenshot(null)}
        >
          <div className="relative max-w-5xl max-h-full">
            <img
              src={selectedScreenshot.url}
              alt={`Session ${selectedScreenshot.session} Step ${selectedScreenshot.index + 1}`}
              className="max-w-full max-h-[85vh] rounded-xl shadow-2xl"
            />
            <div className={`absolute top-4 left-4 px-3 py-1.5 ${
              selectedScreenshot.session === 'A' ? 'bg-acme-navy' : 'bg-sky-500'
            } text-white text-xs font-medium rounded-lg shadow`}>
              Session {selectedScreenshot.session} - Step {selectedScreenshot.index + 1}
            </div>
            <button
              onClick={(e) => {
                e.stopPropagation();
                setSelectedScreenshot(null);
              }}
              className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/90 text-acme-gray-700 hover:bg-white flex items-center justify-center shadow-lg transition-all"
            >
              <i className="fas fa-times"></i>
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default SessionComparison;
