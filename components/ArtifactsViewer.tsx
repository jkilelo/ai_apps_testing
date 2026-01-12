
import React, { useState, useEffect, useCallback, useRef } from 'react';

// Declare Prism as a global (loaded via CDN in index.html)
declare const Prism: {
  highlightAll: () => void;
  highlightElement: (element: Element) => void;
};
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
  const [codeError, setCodeError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<TabType>('screenshots');
  const [lightboxImage, setLightboxImage] = useState<string | null>(null);
  const [lightboxIndex, setLightboxIndex] = useState<number>(0);
  const [isReportFullscreen, setIsReportFullscreen] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const [codeCopied, setCodeCopied] = useState(false);

  // Screenshot gallery settings
  type ThumbnailSize = 'small' | 'medium' | 'large';
  const [thumbnailSize, setThumbnailSize] = useState<ThumbnailSize>('medium');
  const [isSlideshowActive, setIsSlideshowActive] = useState(false);
  const slideshowIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Thumbnail size grid classes
  const thumbnailGridClasses: Record<ThumbnailSize, string> = {
    small: 'grid-cols-4 md:grid-cols-5 lg:grid-cols-6',
    medium: 'grid-cols-2 md:grid-cols-3 lg:grid-cols-4',
    large: 'grid-cols-1 md:grid-cols-2',
  };

  // Slideshow controls
  const startSlideshow = useCallback(() => {
    if (!artifacts?.screenshots?.length) return;
    setIsSlideshowActive(true);
    openLightbox(artifacts.screenshots[0], 0);
  }, [artifacts]);

  const stopSlideshow = useCallback(() => {
    setIsSlideshowActive(false);
    if (slideshowIntervalRef.current) {
      clearInterval(slideshowIntervalRef.current);
      slideshowIntervalRef.current = null;
    }
  }, []);

  // Handle slideshow interval
  useEffect(() => {
    if (isSlideshowActive && lightboxImage && artifacts?.screenshots) {
      slideshowIntervalRef.current = setInterval(() => {
        setLightboxIndex(prev => {
          const newIndex = (prev + 1) % artifacts.screenshots.length;
          setLightboxImage(toAbsoluteUrl(artifacts.screenshots[newIndex]));
          return newIndex;
        });
      }, 3000);

      return () => {
        if (slideshowIntervalRef.current) {
          clearInterval(slideshowIntervalRef.current);
        }
      };
    }
  }, [isSlideshowActive, lightboxImage, artifacts]);

  // Stop slideshow when lightbox closes
  useEffect(() => {
    if (!lightboxImage) {
      stopSlideshow();
    }
  }, [lightboxImage, stopSlideshow]);

  // Fetch artifacts when sessionId changes
  useEffect(() => {
    if (!sessionId) {
      setArtifacts(null);
      setPlaywrightCode(null);
      setCodeError(null);
      return;
    }

    const fetchArtifacts = async () => {
      setLoading(true);
      setError(null);
      setCodeError(null);

      try {
        const artifactsData = await getSessionArtifacts(sessionId);
        setArtifacts(artifactsData);

        let codeData: PlaywrightCode | null = null;
        let lastError: string | null = null;

        for (let attempt = 0; attempt < 3; attempt++) {
          try {
            codeData = await getPlaywrightCode(sessionId);
            break;
          } catch (err) {
            lastError = err instanceof Error ? err.message : 'Failed to load code';
            if (attempt < 2) {
              await new Promise(resolve => setTimeout(resolve, 1000 * (attempt + 1)));
            }
          }
        }

        setPlaywrightCode(codeData);
        if (!codeData && lastError) {
          setCodeError(lastError);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load artifacts');
      } finally {
        setLoading(false);
      }
    };

    fetchArtifacts();
  }, [sessionId]);

  // Handle fullscreen toggle for report
  const toggleReportFullscreen = useCallback(() => {
    setIsReportFullscreen(prev => !prev);
  }, []);

  // Handle escape key to exit fullscreen
  useEffect(() => {
    if (!isReportFullscreen) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setIsReportFullscreen(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isReportFullscreen]);

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

  // Trigger Prism syntax highlighting when code changes
  useEffect(() => {
    if (playwrightCode?.content && typeof Prism !== 'undefined') {
      // Small delay to ensure DOM is updated
      setTimeout(() => {
        Prism.highlightAll();
      }, 100);
    }
  }, [playwrightCode, activeTab]);

  const copyCode = async () => {
    if (playwrightCode?.content) {
      await navigator.clipboard.writeText(playwrightCode.content);
      setCodeCopied(true);
      setTimeout(() => setCodeCopied(false), 2000);
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
    return (
      <div className="h-full flex items-center justify-center bg-acme-gray-50/50">
        <div className="text-center max-w-xs">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-acme-gray-100 flex items-center justify-center">
            <i className="fas fa-folder-open text-2xl text-acme-gray-300"></i>
          </div>
          <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">No Artifacts</h3>
          <p className="text-xs text-acme-gray-600">Run a task to generate screenshots, code, and reports</p>
        </div>
      </div>
    );
  }

  if (!sessionId) {
    return (
      <div className="h-full flex items-center justify-center bg-acme-gray-50/50">
        <div className="text-center max-w-xs">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-acme-gray-100 flex items-center justify-center">
            <i className="fas fa-hourglass-half text-2xl text-acme-gray-300"></i>
          </div>
          <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">Waiting</h3>
          <p className="text-xs text-acme-gray-600">Artifacts will appear after task completion</p>
        </div>
      </div>
    );
  }

  const tabs: { id: TabType; label: string; icon: string; count?: number }[] = [
    { id: 'screenshots', label: 'Screenshots', icon: 'fa-images', count: artifacts?.screenshots?.length },
    { id: 'code', label: 'Code', icon: 'fa-code' },
    { id: 'report', label: 'Reports', icon: 'fa-file-alt' },
    { id: 'downloads', label: 'Downloads', icon: 'fa-download', count: artifacts?.artifacts?.length },
  ];

  return (
    <div className="h-full flex flex-col bg-acme-gray-50/30 overflow-hidden max-w-full">
      {/* Tab Navigation */}
      <div className="px-4 py-3 border-b border-acme-gray-200 flex items-center justify-between flex-shrink-0 bg-white overflow-x-auto">
        <div className="flex items-center gap-1">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`px-4 py-2 flex items-center gap-2 text-xs font-medium rounded-lg transition-all ${
                activeTab === tab.id
                  ? 'text-acme-navy bg-acme-navy/10'
                  : 'text-acme-gray-600 hover:text-acme-gray-800 hover:bg-acme-gray-50'
              }`}
            >
              <i className={`fas ${tab.icon} text-[10px]`}></i>
              {tab.label}
              {tab.count !== undefined && tab.count > 0 && (
                <span className={`px-1.5 py-0.5 rounded-full text-[10px] font-bold ${
                  activeTab === tab.id ? 'bg-acme-navy text-white' : 'bg-acme-gray-200 text-acme-gray-600'
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
        {loading && (
          <div className="flex items-center gap-2 text-xs text-acme-navy">
            <i className="fas fa-spinner fa-spin"></i>
            <span>Loading...</span>
          </div>
        )}
      </div>

      {/* Content */}
      <div className="flex-1 min-h-0 overflow-auto overflow-x-hidden">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-acme-navy/10 flex items-center justify-center">
                <i className="fas fa-spinner fa-spin text-acme-navy text-lg"></i>
              </div>
              <p className="text-xs text-acme-gray-600">Loading artifacts...</p>
            </div>
          </div>
        ) : error ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-xs">
              <div className="w-12 h-12 mx-auto mb-3 rounded-xl bg-acme-red/10 flex items-center justify-center">
                <i className="fas fa-exclamation-triangle text-acme-red text-lg"></i>
              </div>
              <p className="text-sm font-medium text-acme-red mb-2">Error Loading Artifacts</p>
              <p className="text-xs text-acme-gray-600">{error}</p>
            </div>
          </div>
        ) : (
          <div className="p-4">
            {/* Screenshots Tab */}
            {activeTab === 'screenshots' && (
              <div>
                {artifacts?.screenshots && artifacts.screenshots.length > 0 ? (
                  <div className="space-y-4">
                    {/* Gallery Controls */}
                    <div className="flex items-center justify-between bg-white rounded-xl border border-acme-gray-200 p-3">
                      <div className="flex items-center gap-3">
                        {/* Size Toggle */}
                        <div className="flex bg-acme-gray-100 rounded-lg p-0.5">
                          {(['small', 'medium', 'large'] as ThumbnailSize[]).map((size) => (
                            <button
                              key={size}
                              onClick={() => setThumbnailSize(size)}
                              className={`px-3 py-1 text-[10px] rounded-md transition-colors font-medium ${
                                thumbnailSize === size
                                  ? 'bg-white text-acme-navy shadow-sm'
                                  : 'text-acme-gray-600 hover:text-acme-gray-800'
                              }`}
                            >
                              {size === 'small' ? 'S' : size === 'medium' ? 'M' : 'L'}
                            </button>
                          ))}
                        </div>
                        <button
                          onClick={startSlideshow}
                          className="px-3 py-1.5 text-xs bg-acme-navy text-white rounded-lg hover:bg-acme-navy-light transition-colors flex items-center gap-1.5"
                        >
                          <i className="fas fa-play text-[10px]"></i>
                          Slideshow
                        </button>
                      </div>
                      <span className="text-xs text-acme-gray-600">
                        <span className="font-semibold text-acme-gray-800">{artifacts.screenshots.length}</span> screenshots
                      </span>
                    </div>

                    {/* Screenshots Grid */}
                    <div className={`grid ${thumbnailGridClasses[thumbnailSize]} gap-3`}>
                      {artifacts.screenshots.map((screenshot, index) => (
                        <button
                          key={screenshot}
                          onClick={() => openLightbox(screenshot, index)}
                          className="group relative aspect-video bg-white rounded-xl overflow-hidden border border-acme-gray-200 hover:border-acme-navy hover:shadow-lg transition-all"
                        >
                          <img
                            src={toAbsoluteUrl(screenshot)}
                            alt={`Step ${index + 1}`}
                            className="w-full h-full object-cover"
                            loading="lazy"
                          />
                          <div className="absolute inset-0 bg-acme-navy/0 group-hover:bg-acme-navy/10 transition-colors flex items-center justify-center">
                            <div className="w-10 h-10 rounded-full bg-white/90 shadow-lg flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                              <i className="fas fa-expand text-acme-navy text-sm"></i>
                            </div>
                          </div>
                          <div className="absolute bottom-2 left-2 px-2 py-1 bg-acme-navy/90 text-white text-[10px] font-bold rounded-md">
                            {index + 1}
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-12">
                    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-acme-gray-100 flex items-center justify-center">
                      <i className="fas fa-images text-2xl text-acme-gray-300"></i>
                    </div>
                    <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">No Screenshots</h3>
                    <p className="text-xs text-acme-gray-600">Screenshots will appear as the task runs</p>
                  </div>
                )}
              </div>
            )}

            {/* Code Tab */}
            {activeTab === 'code' && (
              <div className="space-y-4">
                {playwrightCode?.content ? (
                  <>
                    {/* Code Stats Bar */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                      <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[10px] font-semibold text-acme-gray-500 uppercase tracking-wider">Language</p>
                            <p className="text-sm font-bold text-acme-gray-800 mt-1">Python</p>
                          </div>
                          <div className="w-9 h-9 rounded-xl bg-yellow-50 flex items-center justify-center">
                            <i className="fab fa-python text-yellow-600"></i>
                          </div>
                        </div>
                      </div>
                      <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[10px] font-semibold text-acme-gray-500 uppercase tracking-wider">Lines</p>
                            <p className="text-sm font-bold text-acme-navy mt-1">{playwrightCode.content.split('\n').length}</p>
                          </div>
                          <div className="w-9 h-9 rounded-xl bg-acme-navy/10 flex items-center justify-center">
                            <i className="fas fa-code text-acme-navy text-sm"></i>
                          </div>
                        </div>
                      </div>
                      <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[10px] font-semibold text-acme-gray-500 uppercase tracking-wider">Framework</p>
                            <p className="text-sm font-bold text-emerald-600 mt-1">Playwright</p>
                          </div>
                          <div className="w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center">
                            <i className="fas fa-theater-masks text-emerald-600 text-sm"></i>
                          </div>
                        </div>
                      </div>
                      <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[10px] font-semibold text-acme-gray-500 uppercase tracking-wider">Type</p>
                            <p className="text-sm font-bold text-violet-600 mt-1">Async</p>
                          </div>
                          <div className="w-9 h-9 rounded-xl bg-violet-50 flex items-center justify-center">
                            <i className="fas fa-bolt text-violet-600 text-sm"></i>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Code Editor Card */}
                    <div className="bg-white rounded-xl border border-acme-gray-200 overflow-hidden shadow-sm">
                      {/* Code Header - Terminal Style */}
                      <div className="flex items-center justify-between px-4 py-3 bg-acme-navy border-b border-acme-navy-dark">
                        <div className="flex items-center gap-3">
                          {/* Traffic lights */}
                          <div className="flex items-center gap-1.5">
                            <div className="w-3 h-3 rounded-full bg-acme-red"></div>
                            <div className="w-3 h-3 rounded-full bg-amber-400"></div>
                            <div className="w-3 h-3 rounded-full bg-emerald-400"></div>
                          </div>
                          {/* File info */}
                          <div className="flex items-center gap-2 text-white/90 bg-white/10 px-3 py-1 rounded-lg">
                            <i className="fab fa-python text-yellow-400 text-sm"></i>
                            <span className="text-xs font-mono font-medium">{playwrightCode.filename}</span>
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-white/60 bg-white/5 px-2 py-1 rounded">
                            {playwrightCode.content.split('\n').length} lines
                          </span>
                          <button
                            onClick={copyCode}
                            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition-all flex items-center gap-1.5 ${
                              codeCopied
                                ? 'bg-emerald-500 text-white'
                                : 'bg-white/10 text-white hover:bg-white/20'
                            }`}
                          >
                            <i className={`fas ${codeCopied ? 'fa-check' : 'fa-copy'}`}></i>
                            {codeCopied ? 'Copied!' : 'Copy Code'}
                          </button>
                          {artifacts && (
                            <button
                              onClick={() => downloadFile(
                                `${API_BASE_URL}/artifacts/${artifacts.session_id}/file/${playwrightCode.path.replace(`${artifacts.session_id}/`, '')}`,
                                playwrightCode.filename
                              )}
                              className="px-3 py-1.5 bg-white text-acme-navy rounded-lg text-xs font-medium hover:bg-white/90 transition-colors flex items-center gap-1.5"
                            >
                              <i className="fas fa-download"></i>
                              Download
                            </button>
                          )}
                        </div>
                      </div>
                      {/* Code Content with Prism Syntax Highlighting */}
                      <div className="overflow-x-auto max-h-[450px] overflow-y-auto bg-[#1d1f21] scrollbar-dark">
                        <pre className="line-numbers p-4 m-0 text-sm">
                          <code className="language-python">
                            {playwrightCode.content}
                          </code>
                        </pre>
                      </div>
                      {/* Code Footer */}
                      <div className="flex items-center justify-between px-4 py-2 bg-acme-gray-50 border-t border-acme-gray-200 text-xs text-acme-gray-600">
                        <div className="flex items-center gap-3">
                          <span className="flex items-center gap-1.5">
                            <i className="fas fa-check-circle text-emerald-500"></i>
                            Ready to run
                          </span>
                          <span className="text-acme-gray-400">|</span>
                          <span>pytest compatible</span>
                        </div>
                        <span className="text-acme-gray-500">
                          Generated by Acme Browser Agent
                        </span>
                      </div>
                    </div>
                  </>
                ) : codeError ? (
                  <div className="bg-white rounded-xl border border-acme-gray-200 p-8 shadow-sm">
                    <div className="text-center max-w-sm mx-auto">
                      <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-amber-50 flex items-center justify-center">
                        <i className="fas fa-exclamation-triangle text-2xl text-amber-500"></i>
                      </div>
                      <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">Failed to Load Code</h3>
                      <p className="text-xs text-acme-gray-600 mb-4">{codeError}</p>
                      <button
                        onClick={() => sessionId && getPlaywrightCode(sessionId).then(setPlaywrightCode).catch(() => {})}
                        className="px-4 py-2 bg-acme-navy text-white rounded-lg text-xs font-medium hover:bg-acme-navy-light transition-colors"
                      >
                        <i className="fas fa-sync-alt mr-2"></i>
                        Retry
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white rounded-xl border border-acme-gray-200 p-8 shadow-sm">
                    <div className="text-center max-w-sm mx-auto">
                      <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-acme-gray-100 flex items-center justify-center">
                        <i className="fas fa-code text-2xl text-acme-gray-300"></i>
                      </div>
                      <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">No Code Generated</h3>
                      <p className="text-xs text-acme-gray-600">Code generation may not be enabled for this task</p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Reports Tab */}
            {activeTab === 'report' && (
              <div className="space-y-4">
                {artifacts?.html_report ? (
                  <>
                    {/* Report Stats */}
                    <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                      <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[10px] font-semibold text-acme-gray-500 uppercase tracking-wider">Report Type</p>
                            <p className="text-sm font-bold text-acme-gray-800 mt-1">HTML</p>
                          </div>
                          <div className="w-9 h-9 rounded-xl bg-orange-50 flex items-center justify-center">
                            <i className="fas fa-file-code text-orange-600"></i>
                          </div>
                        </div>
                      </div>
                      <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[10px] font-semibold text-acme-gray-500 uppercase tracking-wider">Status</p>
                            <p className="text-sm font-bold text-emerald-600 mt-1">Available</p>
                          </div>
                          <div className="w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center">
                            <i className="fas fa-check-circle text-emerald-600 text-sm"></i>
                          </div>
                        </div>
                      </div>
                      <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[10px] font-semibold text-acme-gray-500 uppercase tracking-wider">Video</p>
                            <p className={`text-sm font-bold mt-1 ${artifacts.video ? 'text-sky-600' : 'text-acme-gray-400'}`}>
                              {artifacts.video ? 'Available' : 'N/A'}
                            </p>
                          </div>
                          <div className={`w-9 h-9 rounded-xl flex items-center justify-center ${artifacts.video ? 'bg-sky-50' : 'bg-acme-gray-100'}`}>
                            <i className={`fas fa-video text-sm ${artifacts.video ? 'text-sky-600' : 'text-acme-gray-400'}`}></i>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* HTML Report Card */}
                    <div className="bg-white rounded-xl border border-acme-gray-200 overflow-hidden shadow-sm">
                      {/* Report Header */}
                      <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-acme-navy to-acme-navy-light border-b border-acme-navy-dark">
                        <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
                            <i className="fas fa-chart-bar text-white"></i>
                          </div>
                          <div>
                            <h4 className="text-sm font-semibold text-white">Execution Report</h4>
                            <p className="text-[10px] text-white/70">Interactive test results and screenshots</p>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          <button
                            onClick={toggleReportFullscreen}
                            className="px-3 py-1.5 bg-white/10 hover:bg-white/20 text-white text-xs rounded-lg transition-colors flex items-center gap-1.5"
                          >
                            <i className="fas fa-expand"></i>
                            Fullscreen
                          </button>
                          <a
                            href={toAbsoluteUrl(artifacts.html_report)}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="px-3 py-1.5 bg-white text-acme-navy text-xs rounded-lg transition-colors flex items-center gap-1.5 hover:bg-white/90"
                          >
                            <i className="fas fa-external-link-alt"></i>
                            New Tab
                          </a>
                        </div>
                      </div>
                      {/* Report Preview */}
                      <iframe
                        ref={iframeRef}
                        src={toAbsoluteUrl(artifacts.html_report)}
                        className="w-full h-[450px] bg-white"
                        title="HTML Report"
                      />
                      {/* Report Footer */}
                      <div className="flex items-center justify-between px-4 py-2 bg-acme-gray-50 border-t border-acme-gray-200 text-xs text-acme-gray-600">
                        <span className="flex items-center gap-1.5">
                          <i className="fas fa-info-circle text-acme-gray-400"></i>
                          Scroll within the preview or open in new tab for full view
                        </span>
                        <span className="text-acme-gray-500">Acme Browser Agent Report</span>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="bg-white rounded-xl border border-acme-gray-200 p-8 shadow-sm">
                    <div className="text-center max-w-sm mx-auto">
                      <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-acme-gray-100 flex items-center justify-center">
                        <i className="fas fa-file-alt text-2xl text-acme-gray-300"></i>
                      </div>
                      <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">No Report Available</h3>
                      <p className="text-xs text-acme-gray-600">HTML report will appear after task completion</p>
                    </div>
                  </div>
                )}

                {/* Video Recording Card */}
                {artifacts?.video && (
                  <div className="bg-white rounded-xl border border-acme-gray-200 overflow-hidden shadow-sm">
                    <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-sky-500 to-sky-600 border-b border-sky-600">
                      <div className="flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-white/10 flex items-center justify-center">
                          <i className="fas fa-video text-white"></i>
                        </div>
                        <div>
                          <h4 className="text-sm font-semibold text-white">Recording Playback</h4>
                          <p className="text-[10px] text-white/70">Visual execution recording (GIF)</p>
                        </div>
                      </div>
                      <button
                        onClick={() => downloadFile(toAbsoluteUrl(artifacts.video!), 'recording.gif')}
                        className="px-3 py-1.5 bg-white text-sky-600 text-xs rounded-lg transition-colors flex items-center gap-1.5 hover:bg-white/90"
                      >
                        <i className="fas fa-download"></i>
                        Download GIF
                      </button>
                    </div>
                    <div className="p-6 bg-acme-gray-50 flex justify-center">
                      <div className="relative">
                        <img
                          src={toAbsoluteUrl(artifacts.video)}
                          alt="Test Recording"
                          className="max-w-full max-h-[400px] rounded-xl shadow-lg border border-acme-gray-200"
                        />
                        <div className="absolute top-3 left-3 px-2 py-1 bg-acme-gray-900/80 text-white text-[10px] rounded-lg flex items-center gap-1.5">
                          <i className="fas fa-circle text-acme-red animate-pulse" style={{ fontSize: '6px' }}></i>
                          Recording
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* Downloads Tab */}
            {activeTab === 'downloads' && (
              <div className="space-y-4">
                {artifacts?.artifacts && artifacts.artifacts.length > 0 ? (
                  <>
                    {/* Downloads Stats */}
                    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
                      <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[10px] font-semibold text-acme-gray-500 uppercase tracking-wider">Total Files</p>
                            <p className="text-sm font-bold text-acme-navy mt-1">{artifacts.artifacts.length}</p>
                          </div>
                          <div className="w-9 h-9 rounded-xl bg-acme-navy/10 flex items-center justify-center">
                            <i className="fas fa-folder text-acme-navy text-sm"></i>
                          </div>
                        </div>
                      </div>
                      <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[10px] font-semibold text-acme-gray-500 uppercase tracking-wider">Screenshots</p>
                            <p className="text-sm font-bold text-violet-600 mt-1">
                              {artifacts.artifacts.filter(a => a.type === 'screenshot').length}
                            </p>
                          </div>
                          <div className="w-9 h-9 rounded-xl bg-violet-50 flex items-center justify-center">
                            <i className="fas fa-image text-violet-600 text-sm"></i>
                          </div>
                        </div>
                      </div>
                      <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[10px] font-semibold text-acme-gray-500 uppercase tracking-wider">Code Files</p>
                            <p className="text-sm font-bold text-amber-600 mt-1">
                              {artifacts.artifacts.filter(a => a.type === 'code').length}
                            </p>
                          </div>
                          <div className="w-9 h-9 rounded-xl bg-amber-50 flex items-center justify-center">
                            <i className="fas fa-code text-amber-600 text-sm"></i>
                          </div>
                        </div>
                      </div>
                      <div className="bg-white rounded-xl border border-acme-gray-200 p-3 shadow-sm">
                        <div className="flex items-center justify-between">
                          <div>
                            <p className="text-[10px] font-semibold text-acme-gray-500 uppercase tracking-wider">Reports</p>
                            <p className="text-sm font-bold text-emerald-600 mt-1">
                              {artifacts.artifacts.filter(a => a.type === 'report').length}
                            </p>
                          </div>
                          <div className="w-9 h-9 rounded-xl bg-emerald-50 flex items-center justify-center">
                            <i className="fas fa-file-alt text-emerald-600 text-sm"></i>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Files List Card */}
                    <div className="bg-white rounded-xl border border-acme-gray-200 overflow-hidden shadow-sm">
                      {/* Header */}
                      <div className="flex items-center justify-between px-4 py-3 bg-acme-gray-50 border-b border-acme-gray-200">
                        <div className="flex items-center gap-2">
                          <i className="fas fa-folder-open text-acme-navy"></i>
                          <span className="text-sm font-semibold text-acme-gray-800">Available Files</span>
                          <span className="px-2 py-0.5 bg-acme-navy/10 text-acme-navy text-[10px] font-bold rounded-full">
                            {artifacts.artifacts.length}
                          </span>
                        </div>
                        <button
                          onClick={() => {
                            artifacts.artifacts.forEach(artifact => {
                              downloadFile(toAbsoluteUrl(artifact.url), artifact.name);
                            });
                          }}
                          className="px-3 py-1.5 bg-acme-navy hover:bg-acme-navy-light text-white text-xs rounded-lg transition-colors flex items-center gap-1.5"
                        >
                          <i className="fas fa-download"></i>
                          Download All
                        </button>
                      </div>
                      {/* File List */}
                      <div className="divide-y divide-acme-gray-100 max-h-[400px] overflow-y-auto">
                        {artifacts.artifacts.map((artifact, index) => (
                          <div
                            key={index}
                            className="flex items-center justify-between px-4 py-3 hover:bg-acme-gray-50/50 transition-colors group gap-3 min-w-0"
                          >
                            <div className="flex items-center gap-3 min-w-0 flex-1">
                              <div className={`w-10 h-10 rounded-xl flex items-center justify-center transition-all ${
                                artifact.type === 'screenshot' ? 'bg-violet-100 text-violet-600 group-hover:bg-violet-200' :
                                artifact.type === 'code' ? 'bg-amber-100 text-amber-600 group-hover:bg-amber-200' :
                                artifact.type === 'report' ? 'bg-emerald-100 text-emerald-600 group-hover:bg-emerald-200' :
                                artifact.type === 'video' ? 'bg-sky-100 text-sky-600 group-hover:bg-sky-200' :
                                'bg-acme-gray-100 text-acme-gray-500 group-hover:bg-acme-gray-200'
                              }`}>
                                <i className={`fas ${
                                  artifact.type === 'screenshot' ? 'fa-image' :
                                  artifact.type === 'code' ? 'fa-code' :
                                  artifact.type === 'report' ? 'fa-file-alt' :
                                  artifact.type === 'video' ? 'fa-video' :
                                  'fa-file'
                                }`}></i>
                              </div>
                              <div className="min-w-0 flex-1">
                                <p className="text-sm font-medium text-acme-gray-800 truncate">{artifact.name}</p>
                                <p className="text-[10px] text-acme-gray-500 font-mono truncate">{artifact.path}</p>
                              </div>
                            </div>
                            <div className="flex items-center gap-3 flex-shrink-0">
                              {artifact.size && (
                                <span className="text-xs text-acme-gray-500 bg-acme-gray-100 px-2 py-1 rounded-lg">
                                  {formatFileSize(artifact.size)}
                                </span>
                              )}
                              <span className={`text-[10px] font-medium px-2 py-1 rounded-lg uppercase ${
                                artifact.type === 'screenshot' ? 'bg-violet-100 text-violet-700' :
                                artifact.type === 'code' ? 'bg-amber-100 text-amber-700' :
                                artifact.type === 'report' ? 'bg-emerald-100 text-emerald-700' :
                                artifact.type === 'video' ? 'bg-sky-100 text-sky-700' :
                                'bg-acme-gray-100 text-acme-gray-600'
                              }`}>
                                {artifact.type}
                              </span>
                              <button
                                onClick={() => downloadFile(toAbsoluteUrl(artifact.url), artifact.name)}
                                className="px-3 py-1.5 bg-acme-gray-100 hover:bg-acme-navy hover:text-white text-acme-gray-700 text-xs rounded-lg transition-all flex items-center gap-1.5"
                              >
                                <i className="fas fa-download"></i>
                                Download
                              </button>
                            </div>
                          </div>
                        ))}
                      </div>
                      {/* Footer */}
                      <div className="flex items-center justify-between px-4 py-2 bg-acme-gray-50 border-t border-acme-gray-200 text-xs text-acme-gray-600">
                        <span>{artifacts.artifacts.length} files available</span>
                        <span className="text-acme-gray-500">Acme Browser Agent</span>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="bg-white rounded-xl border border-acme-gray-200 p-8 shadow-sm">
                    <div className="text-center max-w-sm mx-auto">
                      <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-acme-gray-100 flex items-center justify-center">
                        <i className="fas fa-download text-2xl text-acme-gray-300"></i>
                      </div>
                      <h3 className="text-sm font-semibold text-acme-gray-800 mb-1">No Downloads</h3>
                      <p className="text-xs text-acme-gray-600">No artifacts available for download</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Lightbox Modal */}
      {lightboxImage && artifacts && (
        <div
          className="fixed inset-0 z-50 bg-acme-gray-900/95 flex items-center justify-center"
          onClick={() => setLightboxImage(null)}
        >
          {/* Navigation */}
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

          {/* Close */}
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
            className="max-w-[90vw] max-h-[85vh] object-contain rounded-xl shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          />

          {/* Bottom Controls */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex items-center gap-4">
            <button
              onClick={(e) => {
                e.stopPropagation();
                if (isSlideshowActive) {
                  stopSlideshow();
                } else {
                  setIsSlideshowActive(true);
                }
              }}
              className={`w-10 h-10 rounded-full flex items-center justify-center transition-colors ${
                isSlideshowActive
                  ? 'bg-acme-navy text-white'
                  : 'bg-white/10 hover:bg-white/20 text-white'
              }`}
            >
              <i className={`fas ${isSlideshowActive ? 'fa-pause' : 'fa-play'}`}></i>
            </button>

            <div className="px-4 py-2 bg-white/10 rounded-full text-white text-sm font-medium">
              {lightboxIndex + 1} / {artifacts.screenshots.length}
            </div>
          </div>
        </div>
      )}

      {/* Fullscreen Report Modal */}
      {isReportFullscreen && artifacts?.html_report && (
        <div className="fixed inset-0 z-50 bg-white flex flex-col">
          <div className="flex items-center justify-between px-4 py-3 bg-acme-gray-800 border-b border-acme-gray-700">
            <div className="flex items-center gap-3">
              <i className="fas fa-file-code text-orange-500 text-lg"></i>
              <span className="font-medium text-white">HTML Report</span>
            </div>
            <div className="flex items-center gap-2">
              <a
                href={toAbsoluteUrl(artifacts.html_report)}
                target="_blank"
                rel="noopener noreferrer"
                className="px-3 py-1.5 bg-acme-navy hover:bg-acme-navy-light text-white text-sm rounded-lg transition-colors flex items-center gap-1.5"
              >
                <i className="fas fa-external-link-alt"></i>
                Open in New Tab
              </a>
              <button
                onClick={toggleReportFullscreen}
                className="w-10 h-10 rounded-full bg-acme-gray-700 hover:bg-acme-gray-600 text-white flex items-center justify-center transition-colors"
              >
                <i className="fas fa-times text-lg"></i>
              </button>
            </div>
          </div>
          <iframe
            src={toAbsoluteUrl(artifacts.html_report)}
            className="flex-1 w-full bg-white"
            title="HTML Report - Fullscreen"
          />
          <div className="px-4 py-2 bg-acme-gray-800 text-center">
            <span className="text-acme-gray-300 text-sm">
              Press <kbd className="px-2 py-0.5 bg-acme-gray-700 rounded text-acme-gray-200 text-xs mx-1">ESC</kbd> to exit
            </span>
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
