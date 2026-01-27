const API_BASE_URL = 'http://localhost:8001';

// ============== SSE Streaming Services ==============

export interface StreamingEvent {
    type: 'step_start' | 'step_thinking' | 'step_action' | 'step_result' | 'browser_state' | 'error' | 'done' | 'progress';
    level: 'info' | 'success' | 'warn' | 'error' | 'debug';
    message: string;
    timestamp: string;
    step?: number;
    data?: Record<string, unknown>;
}

export type StreamingEventHandler = (event: StreamingEvent) => void;

/**
 * Create an SSE connection for streaming task execution.
 * Returns a cleanup function to close the connection.
 */
export const createStreamingConnection = (
    endpoint: string,
    body: Record<string, unknown>,
    onEvent: StreamingEventHandler,
    onError?: (error: Error) => void,
    onComplete?: () => void,
): (() => void) => {
    const abortController = new AbortController();

    const startStream = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}${endpoint}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(body),
                signal: abortController.signal,
            });

            if (!response.ok) {
                throw new Error(`Backend error: ${response.statusText}`);
            }

            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error('No response body');
            }

            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    onComplete?.();
                    break;
                }

                buffer += decoder.decode(value, { stream: true });

                // Process complete SSE messages
                const lines = buffer.split('\n');
                buffer = lines.pop() || ''; // Keep incomplete line in buffer

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const eventData = JSON.parse(line.slice(6));
                            onEvent(eventData as StreamingEvent);

                            // Check if this is the done event
                            if (eventData.type === 'done') {
                                onComplete?.();
                            }
                        } catch (e) {
                            // Skip invalid JSON (might be heartbeat)
                        }
                    }
                }
            }
        } catch (error) {
            if ((error as Error).name !== 'AbortError') {
                onError?.(error as Error);
            }
        }
    };

    startStream();

    // Return cleanup function
    return () => {
        abortController.abort();
    };
};

// Streaming API functions for each task type

export interface StreamingBasicTaskParams {
    task: string;
    max_steps?: number;
    headless?: boolean;
}

export const streamBasicTask = (
    params: StreamingBasicTaskParams,
    onEvent: StreamingEventHandler,
    onError?: (error: Error) => void,
    onComplete?: () => void,
) => {
    return createStreamingConnection(
        '/stream/basic-task',
        {
            task: params.task,
            max_steps: params.max_steps ?? 30,
            headless: params.headless ?? false,
        },
        onEvent,
        onError,
        onComplete,
    );
};

export interface StreamingExtractDataParams {
    url: string;
    data_schema: Record<string, string>;
    max_items?: number;
    max_steps?: number;
    headless?: boolean;
}

export const streamExtractData = (
    params: StreamingExtractDataParams,
    onEvent: StreamingEventHandler,
    onError?: (error: Error) => void,
    onComplete?: () => void,
) => {
    return createStreamingConnection(
        '/stream/extract-data',
        {
            url: params.url,
            data_schema: params.data_schema,
            max_items: params.max_items,
            max_steps: params.max_steps ?? 40,
            headless: params.headless ?? false,
        },
        onEvent,
        onError,
        onComplete,
    );
};

export interface StreamingResearchParams {
    topic: string;
    depth?: 'shallow' | 'moderate' | 'deep';
    max_sources?: number;
    max_steps?: number;
    headless?: boolean;
}

export const streamResearchTopic = (
    params: StreamingResearchParams,
    onEvent: StreamingEventHandler,
    onError?: (error: Error) => void,
    onComplete?: () => void,
) => {
    return createStreamingConnection(
        '/stream/research-topic',
        {
            topic: params.topic,
            depth: params.depth ?? 'moderate',
            max_sources: params.max_sources ?? 5,
            max_steps: params.max_steps ?? 50,
            headless: params.headless ?? false,
        },
        onEvent,
        onError,
        onComplete,
    );
};

export interface StreamingCompareProductsParams {
    products: string[];
    aspects: string[];
    max_steps?: number;
    headless?: boolean;
}

export const streamCompareProducts = (
    params: StreamingCompareProductsParams,
    onEvent: StreamingEventHandler,
    onError?: (error: Error) => void,
    onComplete?: () => void,
) => {
    return createStreamingConnection(
        '/stream/compare-products',
        {
            products: params.products,
            aspects: params.aspects,
            max_steps: params.max_steps ?? 60,
            headless: params.headless ?? false,
        },
        onEvent,
        onError,
        onComplete,
    );
};

export interface StreamingComparePagesParams {
    urls: string[];
    comparison_criteria: string;
    max_steps?: number;
    headless?: boolean;
}

export const streamComparePages = (
    params: StreamingComparePagesParams,
    onEvent: StreamingEventHandler,
    onError?: (error: Error) => void,
    onComplete?: () => void,
) => {
    return createStreamingConnection(
        '/stream/compare-pages',
        {
            urls: params.urls,
            comparison_criteria: params.comparison_criteria,
            max_steps: params.max_steps ?? 30,
            headless: params.headless ?? false,
        },
        onEvent,
        onError,
        onComplete,
    );
};


// ============== Artifacts API ==============

export interface ArtifactInfo {
    name: string;
    type: string;
    path: string;
    size?: number;
    url: string;
}

export interface SessionArtifacts {
    session_id: string;
    output_directory: string;
    artifacts: ArtifactInfo[];
    html_report?: string;
    json_report?: string;
    playwright_code?: string;
    screenshots: string[];
    video?: string;
}

export interface SessionInfo {
    session_id: string;
    created_at: number;
    has_report: boolean;
    task?: string | null;
    max_steps?: number | null;
}

export interface PlaywrightCode {
    filename: string;
    content: string;
    path: string;
}

export const getSessionArtifacts = async (sessionId: string): Promise<SessionArtifacts> => {
    const response = await fetch(`${API_BASE_URL}/artifacts/${sessionId}`);

    if (!response.ok) {
        throw new Error(`Failed to get artifacts: ${response.statusText}`);
    }

    return response.json();
};

export const getPlaywrightCode = async (sessionId: string): Promise<PlaywrightCode> => {
    const response = await fetch(`${API_BASE_URL}/artifacts/${sessionId}/code`);

    if (!response.ok) {
        throw new Error(`Failed to get code: ${response.statusText}`);
    }

    return response.json();
};

export const listSessions = async (): Promise<{ sessions: SessionInfo[] }> => {
    const response = await fetch(`${API_BASE_URL}/sessions`);

    if (!response.ok) {
        throw new Error(`Failed to list sessions: ${response.statusText}`);
    }

    return response.json();
};


// ============== Replay API ==============

export interface ReplaySessionInfo {
    session_id: string;
    task: string;
    initial_url: string;
    recorded_at: string;
    action_count: number;
    recording_path: string;
}

export interface ReplayResult {
    success: boolean;
    session_id: string;
    actions_total: number;
    actions_succeeded: number;
    actions_failed: number;
    failed_steps: number[];
    errors: string[];
    duration_seconds: number;
}

export interface ReplayRequest {
    headless?: boolean;
    stop_on_failure?: boolean;
    sensitive_data?: Record<string, string>;
}

export interface ReplayInfo {
    session_id: string;
    task: string;
    initial_url: string;
    recorded_at: string;
    browser_use_version: string;
    action_count: number;
    action_summary: Record<string, number>;
    actions: Array<{
        step: number;
        type: string;
        url?: string;
        text?: string;
        element_selector?: string;
    }>;
}

/**
 * List all sessions that have replay recordings available.
 */
export const listReplaySessions = async (): Promise<{ sessions: ReplaySessionInfo[]; total: number }> => {
    const response = await fetch(`${API_BASE_URL}/replay/sessions`);

    if (!response.ok) {
        throw new Error(`Failed to list replay sessions: ${response.statusText}`);
    }

    return response.json();
};

/**
 * Get detailed info about a replay recording.
 */
export const getReplayInfo = async (sessionId: string): Promise<ReplayInfo> => {
    const response = await fetch(`${API_BASE_URL}/replay/${sessionId}/info`);

    if (!response.ok) {
        throw new Error(`Failed to get replay info: ${response.statusText}`);
    }

    return response.json();
};

/**
 * Run a deterministic replay for a session.
 */
export const runReplay = async (sessionId: string, request?: ReplayRequest): Promise<ReplayResult> => {
    const response = await fetch(`${API_BASE_URL}/replay/${sessionId}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request || {}),
    });

    if (!response.ok) {
        throw new Error(`Replay failed: ${response.statusText}`);
    }

    return response.json();
};

/**
 * SSE streaming event types for replay
 */
export interface ReplayStreamEvent {
    type: 'started' | 'step_start' | 'step_complete' | 'complete' | 'error' | 'keepalive';
    session_id?: string;
    total_actions?: number;
    step?: number;
    action_type?: string;
    total?: number;
    success?: boolean;
    error?: string;
    message?: string;
    // Complete event fields
    actions_total?: number;
    actions_succeeded?: number;
    actions_failed?: number;
    failed_steps?: number[];
    errors?: string[];
    duration_seconds?: number;
}

export type ReplayStreamEventHandler = (event: ReplayStreamEvent) => void;

/**
 * Stream replay execution with real-time progress updates.
 * Returns a cleanup function to abort the stream.
 */
export const streamReplay = (
    sessionId: string,
    request: ReplayRequest,
    onEvent: ReplayStreamEventHandler,
    onError?: (error: Error) => void,
    onComplete?: () => void,
): (() => void) => {
    const abortController = new AbortController();

    const startStream = async () => {
        try {
            const response = await fetch(`${API_BASE_URL}/stream/replay/${sessionId}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(request),
                signal: abortController.signal,
            });

            if (!response.ok) {
                throw new Error(`Replay stream failed: ${response.statusText}`);
            }

            const reader = response.body?.getReader();
            if (!reader) {
                throw new Error('No response body');
            }

            const decoder = new TextDecoder();
            let buffer = '';

            while (true) {
                const { done, value } = await reader.read();

                if (done) {
                    onComplete?.();
                    break;
                }

                buffer += decoder.decode(value, { stream: true });

                // Process complete SSE messages
                const lines = buffer.split('\n');
                buffer = lines.pop() || '';

                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        try {
                            const eventData = JSON.parse(line.slice(6));
                            onEvent(eventData as ReplayStreamEvent);

                            if (eventData.type === 'complete' || eventData.type === 'error') {
                                onComplete?.();
                            }
                        } catch (e) {
                            // Skip invalid JSON
                        }
                    }
                }
            }
        } catch (error) {
            if ((error as Error).name !== 'AbortError') {
                onError?.(error as Error);
            }
        }
    };

    startStream();

    return () => {
        abortController.abort();
    };
};
