
import React, { useState, useEffect, useCallback } from 'react';
import {
  getSessionArtifacts,
  getPlaywrightCode,
  SessionArtifacts,
  PlaywrightCode,
} from '../services/geminiService';

// API base URL for building absolute URLs
const API_BASE_URL = 'http://localhost:8001';

// Helper to convert backend relative URLs to absolute URLs
const toAbsoluteUrl = (relativePath: string): string => {
  if (relativePath.startsWith('http')) {
    return relativePath;
  }
  return `${API_BASE_URL}${relativePath}`;
};

interface ArtifactsViewerProps {
  sessionId: string | null;
  outputDirectory?: string;
}

type TabType = 'screenshots' | 'code' | 'report' | 'downloads';

const ArtifactsViewer: React.FC<ArtifactsViewerProps> = ({
  sessionId,
  outputDirectory,
}) => {
  const [artifacts, setArtifacts] = useState<SessionArtifacts | null>(null);
  const [playwrightCode, setPlaywrightCode] = useState<PlaywrightCode | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('screenshots');
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);
  const [lightboxIndex, setLightboxIndex] = useState<number>(0);

  // Fetch artifacts when sessionId changes
  useEffect(() => {
    if (!sessionId) {
      setArtifacts(null);
      setPlaywrightCode(null);
      return;
    }

    const fetchArtifacts = async () => {
      setLoading(true);
      setError(null);

      try {
        const [artifactsData, codeData] = await Promise.all([
          getSessionArtifacts(sessionId),
          getPlaywrightCode(sessionId).catch(() => null),
        ]);

        setArtifacts(artifactsData);
        setPlaywrightCode(codeData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load artifacts');
      } finally {
        setLoading(false);
      }
    };

    fetchArtifacts();
  }, [sessionId]);

  // Keyboard navigation for lightbox
  useEffect(() => {
    if (!lightboxImage || !artifacts) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setLightboxImage(null);
      } else if (e.key === 'ArrowLeft') {
        navigateLightbox(-1);
      } else if (e.key === 'ArrowRight') {
        navigateLightbox(1);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [lightboxImage, artifacts, lightboxIndex]);

  const navigateLightbox = useCallback((direction: number) => {
    if (!artifacts?.screenshots) return;
    const newIndex = (lightboxIndex + direction + artifacts.screenshots.length) % artifacts.screenshots.length;
    setLightboxIndex(newIndex);
    setLightboxImage(toAbsoluteUrl(artifacts.screenshots[newIndex]));
  }, [artifacts, lightboxIndex]);

  const openLightbox = (screenshot: string, index: number) => {
    if (!artifacts) return;
    setLightboxIndex(index);
    setLightboxImage(toAbsoluteUrl(screenshot));
  };

  const copyCode = async () => {
    if (playwrightCode?.content) {
      await navigator.clipboard.writeText(playwrightCode.content);
    }
  };

  const downloadFile = (url: string, filename: string) => {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    link.target = '_blank';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  // Don't render if no session
  if (!sessionId && !outputDirectory) {
    return null;
  }

  // Show loading or waiting state
  if (!sessionId) {
    return (
      <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
        <div className="flex items-center gap-3 text-slate-500">
          <i className="fas fa-clock text-lg"></i>
          <span>Artifacts will be available after task completion</span>
        </div>
      </div>
    );
  }

  const tabs: { id: TabType; label: string; icon: string; count?: number }[] = [
    { id: 'screenshots', label: 'Screenshots', icon: 'fa-images', count: artifacts?.screenshots?.length },
    { id: 'code', label: 'Playwright Code', icon: 'fa-code' },
    { id: 'report', label: 'Reports', icon: 'fa-file-alt' },
    { id: 'downloads', label: 'Downloads', icon: 'fa-download', count: artifacts?.artifacts?.length },
  ];

  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-50 to-slate-100 px-6 py-4 border-b border-slate-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-slate-800 flex items-center gap-2">
            <i className="fas fa-folder-open text-amber-500"></i>
            Generated Artifacts
          </h3>
          {loading && (
            <span className="flex items-center gap-2 text-sm text-blue-600">
              <i className="fas fa-spinner fa-spin"></i>
              Loading...
            </span>
          )}
        </div>
        {outputDirectory && (
          <p className="text-xs text-slate-500 mt-1 font-mono">
            <i className="fas fa-folder mr-1"></i>
            {outputDirectory}
          </p>
        )}
      </div>

      {/* Tabs */}
      <div className="flex border-b border-slate-200 bg-slate-50">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-3 flex items-center gap-2 text-sm font-medium transition-colors border-b-2 -mb-px ${
              activeTab === tab.id
                ? 'text-blue-600 border-blue-600 bg-white'
                : 'text-slate-500 border-transparent hover:text-slate-700 hover:bg-slate-100'
            }`}
          >
            <i className={`fas ${tab.icon}`}></i>
            {tab.label}
            {tab.count !== undefined && tab.count > 0 && (
              <span className={`px-1.5 py-0.5 rounded text-xs ${
                activeTab === tab.id ? 'bg-blue-100 text-blue-700' : 'bg-slate-200 text-slate-600'
              }`}>
                {tab.count}
              </span>
            )}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-6">
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center">
              <i className="fas fa-spinner fa-spin text-3xl text-blue-500 mb-3"></i>
              <p className="text-slate-500">Loading artifacts...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center py-12">
            <div className="text-center text-rose-500">
              <i className="fas fa-exclamation-triangle text-3xl mb-3"></i>
              <p>{error}</p>
            </div>
          </div>
        ) : (
          <>
            {/* Screenshots Tab */}
            {activeTab === 'screenshots' && (
              <div>
                {artifacts?.screenshots && artifacts.screenshots.length > 0 ? (
                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {artifacts.screenshots.map((screenshot, index) => (
                      <button
                        key={screenshot}
                        onClick={() => openLightbox(screenshot, index)}
                        className="group relative aspect-video bg-slate-100 rounded-lg overflow-hidden border border-slate-200 hover:border-blue-400 transition-all hover:shadow-lg"
                      >
                        <img
                          src={toAbsoluteUrl(screenshot)}
                          alt={`Step ${index + 1}`}
                          className="w-full h-full object-cover"
                          loading="lazy"
                        />
                        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition-colors flex items-center justify-center">
                          <i className="fas fa-search-plus text-white text-xl opacity-0 group-hover:opacity-100 transition-opacity"></i>
                        </div>
                        <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/60 to-transparent px-2 py-1">
                          <span className="text-xs text-white font-mono">
                            Step {index + 1}
                          </span>
                        </div>
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-400">
                    <i className="fas fa-images text-4xl mb-3"></i>
                    <p>No screenshots available</p>
                  </div>
                )}
              </div>
            )}

            {/* Code Tab */}
            {activeTab === 'code' && (
              <div>
                {playwrightCode?.content ? (
                  <div className="relative">
                    <div className="absolute top-2 right-2 z-10 flex gap-2">
                      <button
                        onClick={copyCode}
                        className="px-3 py-1.5 bg-slate-700 hover:bg-slate-600 text-white text-xs rounded-md transition-colors flex items-center gap-1.5"
                      >
                        <i className="fas fa-copy"></i>
                        Copy
                      </button>
                      {artifacts && (
                        <button
                          onClick={() => downloadFile(
                            `${API_BASE_URL}/artifacts/${artifacts.session_id}/file/${playwrightCode.path.replace(`${artifacts.session_id}/`, '')}`,
                            playwrightCode.filename
                          )}
                          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded-md transition-colors flex items-center gap-1.5"
                        >
                          <i className="fas fa-download"></i>
                          Download
                        </button>
                      )}
                    </div>
                    <div className="bg-slate-900 rounded-lg overflow-hidden">
                      <div className="flex items-center gap-2 px-4 py-2 bg-slate-800 border-b border-slate-700">
                        <i className="fab fa-python text-yellow-400"></i>
                        <span className="text-sm text-slate-300 font-mono">{playwrightCode.filename}</span>
                      </div>
                      <pre className="p-4 overflow-x-auto max-h-[500px] overflow-y-auto">
                        <code className="text-sm text-slate-100 font-mono whitespace-pre">
                          {playwrightCode.content}
                        </code>
                      </pre>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-400">
                    <i className="fas fa-code text-4xl mb-3"></i>
                    <p>No Playwright code generated</p>
                  </div>
                )}
              </div>
            )}

            {/* Reports Tab */}
            {activeTab === 'report' && (
              <div className="space-y-4">
                {artifacts?.html_report ? (
                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-200">
                      <div className="flex items-center gap-2">
                        <i className="fas fa-file-code text-orange-500"></i>
                        <span className="font-medium text-slate-700">HTML Report</span>
                      </div>
                      <div className="flex gap-2">
                        <a
                          href={toAbsoluteUrl(artifacts.html_report)}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 text-white text-xs rounded-md transition-colors flex items-center gap-1.5"
                        >
                          <i className="fas fa-external-link-alt"></i>
                          Open in New Tab
                        </a>
                      </div>
                    </div>
                    <iframe
                      src={toAbsoluteUrl(artifacts.html_report)}
                      className="w-full h-[400px] bg-white"
                      title="HTML Report"
                    />
                  </div>
                ) : (
                  <div className="text-center py-8 text-slate-400 border border-dashed border-slate-300 rounded-lg">
                    <i className="fas fa-file-code text-3xl mb-2"></i>
                    <p>No HTML report available</p>
                  </div>
                )}

                {artifacts?.json_report && (
                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-200">
                      <div className="flex items-center gap-2">
                        <i className="fas fa-file-alt text-green-500"></i>
                        <span className="font-medium text-slate-700">JSON Report</span>
                      </div>
                      <button
                        onClick={() => downloadFile(
                          toAbsoluteUrl(artifacts.json_report!),
                          'report.json'
                        )}
                        className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-500 text-white text-xs rounded-md transition-colors flex items-center gap-1.5"
                      >
                        <i className="fas fa-download"></i>
                        Download JSON
                      </button>
                    </div>
                  </div>
                )}

                {artifacts?.video && (
                  <div className="border border-slate-200 rounded-lg overflow-hidden">
                    <div className="flex items-center justify-between px-4 py-3 bg-slate-50 border-b border-slate-200">
                      <div className="flex items-center gap-2">
                        <i className="fas fa-video text-purple-500"></i>
                        <span className="font-medium text-slate-700">Recording (GIF)</span>
                      </div>
                      <button
                        onClick={() => downloadFile(
                          toAbsoluteUrl(artifacts.video!),
                          'recording.gif'
                        )}
                        className="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 text-white text-xs rounded-md transition-colors flex items-center gap-1.5"
                      >
                        <i className="fas fa-download"></i>
                        Download
                      </button>
                    </div>
                    <div className="p-4 bg-slate-100 flex justify-center">
                      <img
                        src={toAbsoluteUrl(artifacts.video)}
                        alt="Test Recording"
                        className="max-w-full max-h-[400px] rounded shadow-lg"
                      />
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Downloads Tab */}
            {activeTab === 'downloads' && (
              <div>
                {artifacts?.artifacts && artifacts.artifacts.length > 0 ? (
                  <div className="divide-y divide-slate-100">
                    {artifacts.artifacts.map((artifact, index) => (
                      <div
                        key={index}
                        className="flex items-center justify-between py-3 px-2 hover:bg-slate-50 rounded transition-colors"
                      >
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                            artifact.type === 'screenshot' ? 'bg-blue-100 text-blue-600' :
                            artifact.type === 'code' ? 'bg-amber-100 text-amber-600' :
                            artifact.type === 'report' ? 'bg-emerald-100 text-emerald-600' :
                            artifact.type === 'video' ? 'bg-purple-100 text-purple-600' :
                            'bg-slate-100 text-slate-600'
                          }`}>
                            <i className={`fas ${
                              artifact.type === 'screenshot' ? 'fa-image' :
                              artifact.type === 'code' ? 'fa-code' :
                              artifact.type === 'report' ? 'fa-file-alt' :
                              artifact.type === 'video' ? 'fa-video' :
                              'fa-file'
                            }`}></i>
                          </div>
                          <div>
                            <div className="font-medium text-slate-700 text-sm">{artifact.name}</div>
                            <div className="text-xs text-slate-400 font-mono">{artifact.path}</div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {artifact.size && (
                            <span className="text-xs text-slate-400">
                              {formatFileSize(artifact.size)}
                            </span>
                          )}
                          <button
                            onClick={() => downloadFile(toAbsoluteUrl(artifact.url), artifact.name)}
                            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs rounded-md transition-colors flex items-center gap-1.5"
                          >
                            <i className="fas fa-download"></i>
                            Download
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-12 text-slate-400">
                    <i className="fas fa-download text-4xl mb-3"></i>
                    <p>No artifacts available for download</p>
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Lightbox Modal */}
      {lightboxImage && artifacts && (
        <div
          className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center"
          onClick={() => setLightboxImage(null)}
        >
          {/* Navigation buttons */}
          <button
            onClick={(e) => { e.stopPropagation(); navigateLightbox(-1); }}
            className="absolute left-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors"
          >
            <i className="fas fa-chevron-left text-xl"></i>
          </button>
          <button
            onClick={(e) => { e.stopPropagation(); navigateLightbox(1); }}
            className="absolute right-4 top-1/2 -translate-y-1/2 w-12 h-12 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors"
          >
            <i className="fas fa-chevron-right text-xl"></i>
          </button>

          {/* Close button */}
          <button
            onClick={() => setLightboxImage(null)}
            className="absolute top-4 right-4 w-10 h-10 rounded-full bg-white/10 hover:bg-white/20 text-white flex items-center justify-center transition-colors"
          >
            <i className="fas fa-times text-xl"></i>
          </button>

          {/* Image */}
          <img
            src={lightboxImage}
            alt={`Screenshot ${lightboxIndex + 1}`}
            className="max-w-[90vw] max-h-[90vh] object-contain rounded-lg shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />

          {/* Counter */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 px-4 py-2 bg-white/10 rounded-full text-white text-sm">
            {lightboxIndex + 1} / {artifacts.screenshots.length}
          </div>
        </div>
      )}
    </div>
  );
};

// Helper function to format file size
function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

export default ArtifactsViewer;
