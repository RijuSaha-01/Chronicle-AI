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
    }
};

export default API;
