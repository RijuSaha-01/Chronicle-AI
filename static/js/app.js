/**
 * Chronicle AI - Modular App Entry
 */
import API from './services/api.js';
import GLOBAL_STORE from './services/store.js';
import ThemeManager from './services/theme.js';
import { HomeView } from './views/HomeView.js';
import { CreateView } from './views/CreateView.js';
import { EpisodeDetailView } from './views/EpisodeDetailView.js';
import { ReadingModeView } from './views/ReadingModeView.js';
import { SearchView } from './views/SearchView.js';
import { ChatView } from './views/ChatView.js';
import { SettingsView } from './views/SettingsView.js';
import { AudioPlayer } from './components/AudioPlayer.js';
import { KeyboardManager } from './services/keyboard.js';

const APP = {
    async init() {
        console.log('🎬 Chronicle AI: Netflix Edition Initializing...');
        
        // Initialize Theme customization instantly
        ThemeManager.init();
        
        // Initialize Keyboard Shortcuts
        KeyboardManager.init();

        this.root = document.getElementById('app-root');
        this.navLinks = document.querySelectorAll('.nav-link');
        this.playerContainer = document.getElementById('audio-player-root');
        this.searchBar = document.getElementById('header-search');
        this.searchDropdown = document.getElementById('search-live-results');
        
        // Initial state load
        await this.refreshData();
        
        // Listen to state changes
        GLOBAL_STORE.subscribe((state) => this.render(state));
        
        // Setup Nav
        this.navLinks.forEach(link => {
            link.onclick = () => {
                const view = link.dataset.view;
                GLOBAL_STORE.setState({ currentView: view });
            };
        });

        // Search Bar Logic
        let debounceTimer;
        this.searchBar.oninput = (e) => {
            const query = e.target.value;
            clearTimeout(debounceTimer);
            if (query.length > 2) {
                debounceTimer = setTimeout(() => this.performLiveSearch(query), 300);
            } else {
                this.searchDropdown.classList.remove('active');
            }
        };

        this.searchBar.onkeydown = (e) => {
            if (e.key === 'Enter') {
                this.triggerFullSearch(this.searchBar.value);
            }
        };

        // Close dropdown when clicking outside
        document.addEventListener('click', (e) => {
            if (!this.searchBar.contains(e.target) && !this.searchDropdown.contains(e.target)) {
                this.searchDropdown.classList.remove('active');
            }
        });

        // AI Status Check
        this.checkStatus();
        setInterval(() => this.checkStatus(), 30000);

        // Initial render
        this.render(GLOBAL_STORE.getState());
        
        // Handled by KeyboardManager now
    },

    async performLiveSearch(query) {
        try {
            const results = await API.search(query, {}, 5);
            this.renderLiveResults(results.results || []);
        } catch (error) {
            console.error('Live search failed:', error);
        }
    },

    renderLiveResults(results) {
        if (results.length === 0) {
            this.searchDropdown.classList.remove('active');
            return;
        }

        this.searchDropdown.innerHTML = results.map(res => `
            <div class="search-item" data-id="${res.episode_id}">
                <img src="${res.metadata?.cover_art_path || '/static/img/placeholder.jpg'}" class="search-item-thumb">
                <div class="search-item-info">
                    <div class="search-item-title">${res.title}</div>
                    <div class="search-item-snippet">${res.highlighted_text}</div>
                </div>
            </div>
        `).join('') + `
            <div class="search-item search-see-all">
                <div style="text-align: center; width: 100%; color: var(--netflix-gold); font-size: 0.8rem; font-weight: 600;">
                    See all results for "${this.searchBar.value}"
                </div>
            </div>
        `;

        this.searchDropdown.classList.add('active');

        this.searchDropdown.querySelectorAll('.search-item').forEach(item => {
            item.onclick = () => {
                if (item.classList.contains('search-see-all')) {
                    this.triggerFullSearch(this.searchBar.value);
                } else {
                    this.handleEpisodeClick(item.dataset.id);
                }
                this.searchDropdown.classList.remove('active');
            };
        });
    },

    async triggerFullSearch(query) {
        if (!query) return;
        this.searchDropdown.classList.remove('active');
        this.searchBar.blur();
        
        GLOBAL_STORE.setState({ 
            isSearching: true, 
            searchQuery: query,
            currentView: 'search'
        });

        try {
            const results = await API.search(query, GLOBAL_STORE.getState().searchFilters);
            
            // Update recent searches
            let recent = GLOBAL_STORE.getState().recentSearches;
            recent = [query, ...recent.filter(s => s !== query)].slice(0, 5);
            localStorage.setItem('recentSearches', JSON.stringify(recent));

            GLOBAL_STORE.setState({ 
                searchResults: results.results || [], 
                isSearching: false,
                recentSearches: recent
            });
        } catch (error) {
            this.showToast('Search failed', 'error');
            GLOBAL_STORE.setState({ isSearching: false });
        }
    },

    async refreshData() {
        GLOBAL_STORE.setState({ isLoading: true });
        try {
            const [episodesData, seasonsData] = await Promise.all([
                API.getEpisodes(100),
                API.getSeasons()
            ]);
            GLOBAL_STORE.setState({ 
                episodes: episodesData.entries || [], 
                seasons: seasonsData.seasons || [],
                isLoading: false 
            });
        } catch (error) {
            this.showToast(error.message, 'error');
            GLOBAL_STORE.setState({ isLoading: false });
        }
    },

    async checkStatus() {
        const online = await API.checkAIStatus();
        GLOBAL_STORE.setState({ aiOnline: online });
        const indicator = document.getElementById('ai-status');
        if (indicator) {
            indicator.className = `status-indicator ${online ? 'online' : 'offline'}`;
        }
    },

    render(state) {
        // Update Nav Active State
        this.navLinks.forEach(link => {
            link.classList.toggle('active', link.dataset.view === state.currentView);
        });

        // Clear root
        this.root.innerHTML = '';

        // View Routing
        if (state.currentView === 'episodes') {
            this.root.appendChild(HomeView((id) => this.handleEpisodeClick(id)));
        } else if (state.currentView === 'create') {
            this.root.appendChild(CreateView((data) => this.handleCreate(data)));
        } else if (state.currentView === 'episodeDetail') {
            this.root.appendChild(EpisodeDetailView(state.selectedEpisodeId, (id) => this.handleEpisodeClick(id)));
        } else if (state.currentView === 'readingMode') {
            this.root.appendChild(ReadingModeView(state.selectedEpisodeId));
        } else if (state.currentView === 'search') {
            this.root.appendChild(SearchView((id) => this.handleEpisodeClick(id)));
        } else if (state.currentView === 'chat') {
            this.root.appendChild(ChatView((id) => this.handleEpisodeClick(id)));
        } else if (state.currentView === 'settings') {
            this.root.appendChild(SettingsView());
        }

        // Handle Audio Player
        if (state.currentEpisode) {
            const playerEl = AudioPlayer(state.currentEpisode);
            if (playerEl && !this.playerContainer.contains(playerEl)) {
                this.playerContainer.innerHTML = '';
                this.playerContainer.appendChild(playerEl);
            }
        }
    },

    async handleEpisodeClick(id) {
        GLOBAL_STORE.setState({ 
            selectedEpisodeId: id,
            currentView: 'episodeDetail'
        });
        window.scrollTo(0, 0);
    },

    async handleCreate(data) {
        GLOBAL_STORE.setState({ isLoading: true });
        try {
            if (data.mode === 'quick') {
                await API.createQuickEntry(data);
            } else {
                await API.createGuidedEntry(data);
            }
            this.showToast('Episode Created Successfully!', 'success');
            await this.refreshData();
            GLOBAL_STORE.setState({ currentView: 'episodes' });
        } catch (error) {
            this.showToast(error.message, 'error');
        } finally {
            GLOBAL_STORE.setState({ isLoading: false });
        }
    },

    openModal(episode) {
        const modal = document.getElementById('modal-episode');
        const body = document.getElementById('modal-body');
        if (!modal || !body) return;

        body.innerHTML = `
            <div class="modal-episode-meta">📅 ${new Date(episode.date).toLocaleDateString()} • ID: ${episode.id}</div>
            <h2 class="modal-episode-title">${episode.title || 'Untitled'}</h2>
            <p class="modal-narrative">"${episode.narrative_text || 'Narrative in progress...'}"</p>
            
            <div class="modal-section">
                <h4>Original Entry</h4>
                <div class="modal-raw-text">${episode.raw_text}</div>
            </div>

            <div class="modal-actions">
                <button class="btn-netflix primary play-trigger" style="width:100%">▶ Play Narrative</button>
            </div>
        `;

        modal.classList.add('active');

        body.querySelector('.play-trigger').onclick = () => {
            GLOBAL_STORE.setState({ currentEpisode: episode });
            modal.classList.remove('active');
        };

        const closeBtn = modal.querySelector('.modal-close');
        const overlay = modal.querySelector('.modal-overlay');
        
        const close = () => modal.classList.remove('active');
        closeBtn.onclick = close;
        overlay.onclick = close;
    },

    showToast(message, type = 'success') {
        const container = document.getElementById('toast-container');
        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.textContent = message;
        container.appendChild(toast);
        setTimeout(() => toast.remove(), 3000);
    }
};

document.addEventListener('DOMContentLoaded', () => APP.init());
