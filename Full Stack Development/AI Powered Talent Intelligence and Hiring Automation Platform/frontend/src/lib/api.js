/**
 * API client for HireForge Pro
 * Handles all HTTP requests to the backend
 */

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');

function apiUrl(path) {
    const normalizedPath = path.startsWith('/') ? path : `/${path}`;
    return `${API_BASE_URL}${normalizedPath}`;
}

// Google OAuth configuration
export const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

/**
 * Initialize the API client
 * Sets up default headers if user is authenticated
 */
export function initApiClient(token = null) {
    if (token) {
        setAuthToken(token);
    }
}

/**
 * Set authentication token
 */
export function setAuthToken(token) {
    localStorage.setItem('auth_token', token);
}

/**
 * Get current auth token
 */
export function getAuthToken() {
    return localStorage.getItem('auth_token');
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated() {
    return !!getAuthToken();
}

/**
 * Make authenticated API request
 */
async function authenticatedRequest(path, options = {}) {
    const token = getAuthToken();
    if (!token) {
        throw new Error('Not authenticated');
    }

    const headers = {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
        ...options.headers
    };

    return fetch(apiUrl(path), { ...options, headers });
}

/**
 * Google Login / Register
 */
export async function googleLogin(idToken) {
    try {
        const response = await fetch(apiUrl('/auth/google/verify'), {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ id_token: idToken })
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || 'Authentication failed');
        }

        // Store user data
        localStorage.setItem('user', JSON.stringify(data));
        localStorage.setItem('auth_token', idToken);

        return data;
    } catch (error) {
        console.error('Google login error:', error);

        if (error instanceof TypeError && error.message === 'Failed to fetch') {
            throw new Error('Unable to reach the backend. Make sure the FastAPI server is running on port 8000.');
        }

        throw error;
    }
}

/**
 * Logout - clears local storage
 */
export function logout() {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user');
}

/**
 * Get current user
 */
export async function getCurrentUser() {
    try {
        const token = getAuthToken();
        if (!token) {
            return null;
        }

        const response = await fetch(apiUrl('/auth/me'), {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            throw new Error('Failed to get user');
        }

        const data = await response.json();
        localStorage.setItem('user', JSON.stringify(data));
        return data;
    } catch (error) {
        console.error('Get current user error:', error);
        return null;
    }
}

/**
 * Job endpoints
 */

export async function createJob(jobData) {
    const response = await authenticatedRequest('/jobs/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jobData)
    });
    return response.json();
}

export async function getJobs() {
    const response = await authenticatedRequest('/jobs/');
    return response.json();
}

export async function getJobById(jobId) {
    const response = await authenticatedRequest(`/jobs/${jobId}`);
    return response.json();
}

export async function updateJob(jobId, jobData) {
    const response = await authenticatedRequest(`/jobs/${jobId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(jobData)
    });
    return response.json();
}

export async function deleteJob(jobId) {
    const response = await authenticatedRequest(`/jobs/${jobId}`, {
        method: 'DELETE'
    });
    return response.json();
}

export async function getCandidates() {
    const response = await authenticatedRequest('/jobs/candidates');
    return response.json();
}

export async function createCandidate(jobId, candidateData) {
    const response = await authenticatedRequest(`/jobs/${jobId}/candidates`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(candidateData)
    });
    return response.json();
}

/**
 * Candidate status endpoints
 */

export async function updateCandidateStatus(jobId, candidateId, status, notes = '') {
    const response = await authenticatedRequest(`/jobs/${jobId}/candidates/${candidateId}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ status, notes })
    });
    return response.json();
}

/**
 * Original AI endpoints (for resume screening)
 */

export async function extractSkills(jobDescription) {
    const formData = new FormData();
    formData.append('job_description', jobDescription);

    const response = await fetch(apiUrl('/extract-skills'), {
        method: 'POST',
        body: formData
    });

    return response.json();
}

export async function processMultiple(jobDescription, files) {
    const formData = new FormData();
    formData.append('job_description', jobDescription);

    files.forEach(file => {
        formData.append('files', file);
    });

    const response = await fetch(apiUrl('/process-multiple'), {
        method: 'POST',
        body: formData
    });

    return response.json();
}
