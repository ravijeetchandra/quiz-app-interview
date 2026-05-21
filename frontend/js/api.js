const API_BASE = (window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1'))
    ? 'http://localhost:8000'
    : 'https://quiz-prep-api.onrender.com';

const BASE_PATH = (window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1'))
    ? ''
    : '/quiz-app-interview';

// SAFETY: No API keys are stored or sent from the frontend.
// All secret keys (Gemini, JWT secret, database) live ONLY in
// backend environment variables on the server. The frontend
// never sees or handles any secret key.

const API = {
    async request(endpoint, options = {}) {
        const token = localStorage.getItem('access_token');
        const headers = {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...options.headers,
        };

        const config = {
            ...options,
            headers,
        };

        if (options.body instanceof FormData) {
            delete headers['Content-Type'];
            config.body = options.body;
        }

        const response = await fetch(`${API_BASE}${endpoint}`, config);

        if (response.status === 401 && token) {
            const refreshed = await this.refreshToken();
            if (refreshed) {
                headers['Authorization'] = `Bearer ${localStorage.getItem('access_token')}`;
                config.headers = headers;
                const retry = await fetch(`${API_BASE}${endpoint}`, config);
                if (!retry.ok) {
                    const err = await retry.json().catch(() => ({ detail: `HTTP ${retry.status}` }));
                    throw new Error(err.detail || 'Request failed');
                }
                return retry.json();
            }
            this._clearTokens();
            window.location.href = BASE_PATH + '/pages/login.html';
            return;
        }

        if (!response.ok) {
            const err = await response.json().catch(() => ({ detail: `HTTP ${response.status}` }));
            throw new Error(err.detail || 'Request failed');
        }

        return response.json();
    },

    _getRefreshToken() {
        return localStorage.getItem('refresh_token') || sessionStorage.getItem('refresh_token');
    },

    _setRefreshToken(token) {
        if (localStorage.getItem('refresh_token')) {
            localStorage.setItem('refresh_token', token);
        } else {
            sessionStorage.setItem('refresh_token', token);
        }
    },

    _clearTokens() {
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        localStorage.removeItem('user');
        sessionStorage.removeItem('refresh_token');
    },

    async refreshToken() {
        const refresh = this._getRefreshToken();
        if (!refresh) return false;
        try {
            const res = await fetch(`${API_BASE}/api/auth/refresh`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ refresh_token: refresh }),
            });
            if (res.ok) {
                const data = await res.json();
                localStorage.setItem('access_token', data.access_token);
                this._setRefreshToken(data.refresh_token);
                return true;
            }
        } catch {}
        return false;
    },

    // Auth
    async register(data) {
        const res = await this.request('/api/auth/register', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        localStorage.setItem('access_token', res.access_token);
        localStorage.setItem('refresh_token', res.refresh_token);
        localStorage.setItem('user', JSON.stringify(res.user));
        return res;
    },

    async login(data) {
        const res = await this.request('/api/auth/login', {
            method: 'POST',
            body: JSON.stringify(data),
        });
        localStorage.setItem('access_token', res.access_token);
        localStorage.setItem('user', JSON.stringify(res.user));
        if (data.remember_me) {
            localStorage.setItem('refresh_token', res.refresh_token);
        } else {
            sessionStorage.setItem('refresh_token', res.refresh_token);
        }
        return res;
    },

    async logout() {
        try { await this.request('/api/auth/logout', { method: 'POST' }); } catch {}
        this._clearTokens();
    },

    async getMe() {
        return this.request('/api/auth/me');
    },

    async getDomains() {
        return this.request('/api/domains');
    },

    // Quiz
    async uploadFile(file, domain) {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('domain', domain);
        return this.request('/api/quiz/upload', {
            method: 'POST',
            body: formData,
        });
    },

    async generateQuiz(config, fileText, filename) {
        const formData = new FormData();
        formData.append('config', JSON.stringify(config));
        formData.append('file_text', fileText);
        formData.append('filename', filename);
        return this.request('/api/quiz/generate', {
            method: 'POST',
            body: formData,
        });
    },

    async submitQuiz(sessionId, answers) {
        return this.request(`/api/quiz/${sessionId}/submit`, {
            method: 'POST',
            body: JSON.stringify({ answers }),
        });
    },

    async getQuizResult(sessionId) {
        return this.request(`/api/quiz/${sessionId}/result`);
    },

    async getQuizHistory() {
        return this.request('/api/quiz/history');
    },

    async getDashboard() {
        return this.request('/api/quiz/dashboard');
    },
};
