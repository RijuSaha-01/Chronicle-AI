/**
 * Chronicle AI - Simple Reactive Store
 */

class Store {
    constructor(initialState) {
        this.state = initialState;
        this.listeners = [];
    }

    getState() {
        return this.state;
    }

    setState(newState) {
        this.state = { ...this.state, ...newState };
        this.notify();
    }

    subscribe(listener) {
        this.listeners.push(listener);
        return () => {
            this.listeners = this.listeners.filter(l => l !== listener);
        };
    }

    notify() {
        this.listeners.forEach(listener => listener(this.state));
    }
}

const GLOBAL_STORE = new Store({
    currentView: 'episodes',
    episodes: [],
    seasons: [],
    isLoading: false,
    aiOnline: false,
    currentEpisode: null, 
    selectedEpisodeId: null,
    toast: null,
    // Search State
    searchQuery: '',
    searchResults: [],
    searchFilters: {
        start_date: '',
        end_date: '',
        season: '',
        mood: '',
        themes: ''
    },
    isSearching: false,
    searchViewMode: 'grid', // 'grid' or 'list'
    recentSearches: JSON.parse(localStorage.getItem('recentSearches') || '[]')
});

export default GLOBAL_STORE;
