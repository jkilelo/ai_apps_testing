
import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';

// Toast types
export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
  id: string;
  type: ToastType;
  message: string;
  duration?: number;
}

interface ToastContextType {
  toasts: Toast[];
  addToast: (type: ToastType, message: string, duration?: number) => void;
  removeToast: (id: string) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

// Toast Provider
export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const addToast = useCallback((type: ToastType, message: string, duration = 4000) => {
    const id = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
    setToasts(prev => [...prev, { id, type, message, duration }]);

    // Auto-remove after duration
    if (duration > 0) {
      setTimeout(() => {
        setToasts(prev => prev.filter(t => t.id !== id));
      }, duration);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast }}>
      {children}
      <ToastContainer toasts={toasts} onRemove={removeToast} />
    </ToastContext.Provider>
  );
};

// Hook to use toast
export const useToast = () => {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return context;
};

// Toast config
const TOAST_CONFIG: Record<ToastType, { icon: string; bgColor: string; borderColor: string; textColor: string; progressColor: string }> = {
  success: {
    icon: 'fa-check-circle',
    bgColor: 'bg-emerald-50',
    borderColor: 'border-emerald-200',
    textColor: 'text-emerald-700',
    progressColor: 'bg-emerald-500',
  },
  error: {
    icon: 'fa-exclamation-circle',
    bgColor: 'bg-acme-red/10',
    borderColor: 'border-acme-red/30',
    textColor: 'text-acme-red',
    progressColor: 'bg-acme-red',
  },
  warning: {
    icon: 'fa-exclamation-triangle',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    textColor: 'text-amber-700',
    progressColor: 'bg-amber-500',
  },
  info: {
    icon: 'fa-info-circle',
    bgColor: 'bg-acme-navy/10',
    borderColor: 'border-acme-navy/30',
    textColor: 'text-acme-navy',
    progressColor: 'bg-acme-navy',
  },
};

// Individual Toast Item
const ToastItem: React.FC<{ toast: Toast; onRemove: (id: string) => void; index: number }> = ({ toast, onRemove, index }) => {
  const config = TOAST_CONFIG[toast.type];
  const [isExiting, setIsExiting] = useState(false);
  const progressRef = useRef<HTMLDivElement>(null);

  const handleRemove = useCallback(() => {
    setIsExiting(true);
    setTimeout(() => onRemove(toast.id), 200);
  }, [toast.id, onRemove]);

  // Start progress bar animation after mount
  useEffect(() => {
    if (progressRef.current && toast.duration && toast.duration > 0) {
      // Force reflow then start animation
      progressRef.current.style.width = '100%';
      requestAnimationFrame(() => {
        if (progressRef.current) {
          progressRef.current.style.transition = `width ${toast.duration}ms linear`;
          progressRef.current.style.width = '0%';
        }
      });
    }
  }, [toast.duration]);

  return (
    <div
      className={`relative flex items-start gap-3 p-4 rounded-lg border shadow-lg overflow-hidden ${
        config.bgColor
      } ${config.borderColor} ${isExiting ? 'animate-toastSlideOut' : 'animate-toastSlideIn'}`}
      style={{
        // Stacked offset effect
        transform: `translateY(${index * 2}px)`,
        zIndex: 100 - index,
      }}
      role="alert"
    >
      <i className={`fas ${config.icon} ${config.textColor} mt-0.5`}></i>
      <p className={`flex-1 text-sm font-medium ${config.textColor}`}>{toast.message}</p>
      <button
        onClick={handleRemove}
        className={`${config.textColor} hover:opacity-70 transition-opacity`}
        aria-label="Dismiss"
      >
        <i className="fas fa-times text-sm"></i>
      </button>
      {/* Auto-dismiss progress bar */}
      {toast.duration && toast.duration > 0 && (
        <div className="absolute bottom-0 left-0 right-0 h-0.5">
          <div
            ref={progressRef}
            className={`h-full ${config.progressColor} opacity-40`}
            style={{ width: '100%' }}
          />
        </div>
      )}
    </div>
  );
};

// Toast Container
const ToastContainer: React.FC<{ toasts: Toast[]; onRemove: (id: string) => void }> = ({ toasts, onRemove }) => {
  if (toasts.length === 0) return null;

  return (
    <div className="fixed top-4 right-4 z-[100] flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)]">
      {toasts.map((toast, index) => (
        <ToastItem key={toast.id} toast={toast} onRemove={onRemove} index={index} />
      ))}
    </div>
  );
};

export default ToastProvider;
