const API_BASE_URL = 'http://localhost:8001';

export const runUIAutomator = async (instruction: string) => {
    const response = await fetch(`${API_BASE_URL}/run-ui-automator`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ instruction })
    });

    if (!response.ok) {
        throw new Error(`Backend error: ${response.statusText}`);
    }

    return response.json();
};

export const profileData = async (fileName: string, sampleData: string) => {
    const response = await fetch(`${API_BASE_URL}/profile-data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ fileName, sampleData })
    });

    if (!response.ok) {
        throw new Error(`Backend error: ${response.statusText}`);
    }

    return response.json();
};

export const checkDataQuality = async (data: string, rules: string) => {
    const response = await fetch(`${API_BASE_URL}/check-data-quality`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ data, rules })
    });

    if (!response.ok) {
        throw new Error(`Backend error: ${response.statusText}`);
    }

    return response.json();
};


// ============== Advanced Browser Services ==============

export interface TaskResult {
    success: boolean;
    task_type: string;
    summary: string;
    data: Record<string, unknown>;
    steps: Array<{ action: string; status: string }>;
    error?: string | null;
}

export interface ExtractDataParams {
    url: string;
    data_schema: Record<string, string>;
    max_items?: number;
    max_steps?: number;
}

export const extractData = async (params: ExtractDataParams): Promise<TaskResult> => {
    const response = await fetch(`${API_BASE_URL}/extract-data`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            url: params.url,
            data_schema: params.data_schema,
            max_items: params.max_items,
            max_steps: params.max_steps ?? 40,
        })
    });

    if (!response.ok) {
        throw new Error(`Backend error: ${response.statusText}`);
    }

    return response.json();
};

export interface ResearchTopicParams {
    topic: string;
    depth?: 'shallow' | 'moderate' | 'deep';
    max_sources?: number;
    max_steps?: number;
}

export const researchTopic = async (params: ResearchTopicParams): Promise<TaskResult> => {
    const response = await fetch(`${API_BASE_URL}/research-topic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            topic: params.topic,
            depth: params.depth ?? 'moderate',
            max_sources: params.max_sources ?? 5,
            max_steps: params.max_steps ?? 50,
        })
    });

    if (!response.ok) {
        throw new Error(`Backend error: ${response.statusText}`);
    }

    return response.json();
};

export interface CompareProductsParams {
    products: string[];
    aspects: string[];
    max_steps?: number;
}

export const compareProducts = async (params: CompareProductsParams): Promise<TaskResult> => {
    const response = await fetch(`${API_BASE_URL}/compare-products`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            products: params.products,
            aspects: params.aspects,
            max_steps: params.max_steps ?? 60,
        })
    });

    if (!response.ok) {
        throw new Error(`Backend error: ${response.statusText}`);
    }

    return response.json();
};

export interface ParallelTask {
    id: string;
    description: string;
    max_steps?: number;
}

export interface RunParallelTasksParams {
    tasks: ParallelTask[];
    max_concurrent?: number;
}

export const runParallelTasks = async (params: RunParallelTasksParams): Promise<TaskResult[]> => {
    const response = await fetch(`${API_BASE_URL}/run-parallel-tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            tasks: params.tasks.map(t => ({
                id: t.id,
                description: t.description,
                max_steps: t.max_steps ?? 25,
            })),
            max_concurrent: params.max_concurrent ?? 3,
        })
    });

    if (!response.ok) {
        throw new Error(`Backend error: ${response.statusText}`);
    }

    return response.json();
};

export interface ComparePagesParams {
    urls: string[];
    comparison_criteria: string;
    max_steps?: number;
}

export const comparePages = async (params: ComparePagesParams): Promise<TaskResult> => {
    const response = await fetch(`${API_BASE_URL}/compare-pages`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            urls: params.urls,
            comparison_criteria: params.comparison_criteria,
            max_steps: params.max_steps ?? 30,
        })
    });

    if (!response.ok) {
        throw new Error(`Backend error: ${response.statusText}`);
    }

    return response.json();
};


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
