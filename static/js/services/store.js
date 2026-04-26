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
    isLoading: false,
    aiOnline: false,
    currentEpisode: null, // For modal or detail view
    toast: null
});

export default GLOBAL_STORE;
