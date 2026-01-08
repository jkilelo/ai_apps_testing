const API_BASE_URL = 'http://localhost:8000';

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
