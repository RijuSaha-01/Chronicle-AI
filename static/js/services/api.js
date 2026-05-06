/**
 * Chronicle AI - API Service
 */

const API = {
    async call(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                const error = await response.json().catch(() => ({}));
                throw new Error(error.detail || `Request failed: ${response.status}`);
            }

            if (response.status === 204) return null;
            return await response.json();
        } catch (error) {
            console.error('API Error:', error);
            throw error;
        }
    },

    async getEpisodes(limit = 50) {
        return await this.call(`/entries?limit=${limit}`);
    },

    async getSeasons() {
        return await this.call('/seasons');
    },

    async getEpisode(id) {
        return await this.call(`/entries/${id}`);
    },

    async createQuickEntry(data) {
        return await this.call('/entries', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async createGuidedEntry(data) {
        return await this.call('/entries/guided', {
            method: 'POST',
            body: JSON.stringify(data)
        });
    },

    async regenerateEpisode(id) {
        return await this.call(`/entries/${id}/regenerate`, {
            method: 'POST'
        });
    },

    async exportEpisode(id) {
        return await this.call(`/export/${id}`, {
            method: 'POST'
        });
    },

    async checkAIStatus() {
        try {
            const health = await this.call('/health');
            return health?.ollama_available || false;
        } catch {
            return false;
        }
    },

    async search(query, filters = {}, limit = 20) {
        let url = `/search?q=${encodeURIComponent(query)}&limit=${limit}`;
        if (filters.start_date) url += `&start_date=${filters.start_date}`;
        if (filters.end_date) url += `&end_date=${filters.end_date}`;
        if (filters.season) url += `&season=${filters.season}`;
        if (filters.mood) url += `&mood=${filters.mood}`;
        if (filters.themes) url += `&themes=${filters.themes}`;
        return await this.call(url);
    },

    async ask(question, sessionId = null) {
        return await this.call('/ask', {
            method: 'POST',
            body: JSON.stringify({ question, session_id: sessionId })
        });
    },

    async getChatSessions() {
        return await this.call('/chat/sessions');
    },

    async getChatSession(sessionId) {
        return await this.call(`/chat/sessions/${sessionId}`);
    },

    async deleteChatSession(sessionId) {
        return await this.call(`/chat/sessions/${sessionId}`, {
            method: 'DELETE'
        });
    }
};

export default API;
