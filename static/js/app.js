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
        
        // Setup Global Progress Bar
        this.progress = document.createElement('div');
        this.progress.className = 'global-progress-bar';
        this.progress.innerHTML = '<div class="global-progress-fill"></div>';
        document.body.appendChild(this.progress);
        this.progressFill = this.progress.querySelector('.global-progress-fill');
        
        
        // Initial state load
        await this.refreshData();
        
        // Listen to state changes
        GLOBAL_STORE.subscribe((state) => this.render(state));
        
        // Setup Nav (Desktop, Drawer, Bottom)
        const allNavLinks = document.querySelectorAll('.nav-link, .drawer-link, .bottom-nav-link');
        allNavLinks.forEach(link => {
            link.onclick = () => {
                const view = link.dataset.view;
                GLOBAL_STORE.setState({ currentView: view });
                this.closeDrawer();
            };
        });

        // Mobile Menu Toggles
        this.menuToggle = document.getElementById('mobile-menu-toggle');
        this.drawer = document.getElementById('mobile-drawer');
        this.drawerClose = document.getElementById('drawer-close');
        this.drawerOverlay = document.getElementById('drawer-overlay');

        if (this.menuToggle) this.menuToggle.onclick = () => this.toggleDrawer();
        if (this.drawerClose) this.drawerClose.onclick = () => this.closeDrawer();
        if (this.drawerOverlay) this.drawerOverlay.onclick = () => this.closeDrawer();

        // Swipe Gestures for Episode Navigation
        this.setupSwipeGestures();

        // Pull to Refresh
        this.setupPullToRefresh();

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
        
        this.setProgress(30);
        GLOBAL_STORE.setState({ 
            isSearching: true, 
            searchQuery: query,
            currentView: 'search'
        });

        try {
            const results = await API.search(query, GLOBAL_STORE.getState().searchFilters);
            this.setProgress(80);
            
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
        } finally {
            this.setProgress(100);
            setTimeout(() => this.setProgress(null), 500);
        }
    },

    async refreshData() {
        GLOBAL_STORE.setState({ isLoading: true });
        this.setProgress(20);
        try {
            const [episodesData, seasonsData] = await Promise.all([
                API.getEpisodes(100),
                API.getSeasons()
            ]);
            this.setProgress(80);
            GLOBAL_STORE.setState({ 
                episodes: episodesData.entries || [], 
                seasons: seasonsData.seasons || [],
                isLoading: false 
            });
        } catch (error) {
            this.showToast(error.message, 'error');
            GLOBAL_STORE.setState({ isLoading: false });
        } finally {
            this.setProgress(100);
            setTimeout(() => this.setProgress(null), 500);
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
        // Update Nav Active State (Desktop, Drawer, Bottom)
        const allNavLinks = document.querySelectorAll('.nav-link, .drawer-link, .bottom-nav-link');
        allNavLinks.forEach(link => {
            link.classList.toggle('active', link.dataset.view === state.currentView);
        });

        // Clear and add fade-in
        this.root.innerHTML = '';
        this.root.classList.remove('fade-in');
        // Trigger reflow
        void this.root.offsetWidth;
        this.root.classList.add('fade-in');

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
        this.setProgress(10);
        try {
            this.setProgress(30);
            if (data.mode === 'quick') {
                await API.createQuickEntry(data);
            } else {
                await API.createGuidedEntry(data);
            }
            this.setProgress(80);
            this.showToast('Episode Created Successfully!', 'success');
            await this.refreshData();
            this.setProgress(100);
            GLOBAL_STORE.setState({ currentView: 'episodes' });
        } catch (error) {
            this.showToast(error.message, 'error');
        } finally {
            GLOBAL_STORE.setState({ isLoading: false });
            setTimeout(() => this.setProgress(null), 500);
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
        
        // Trigger animation
        setTimeout(() => toast.classList.add('show'), 10);
        
        // Remove after 3s
        setTimeout(() => {
            toast.classList.remove('show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    },

    setProgress(percent) {
        if (percent === null || percent === undefined) {
            this.progress.classList.remove('active');
            this.progressFill.style.width = '0%';
        } else {
            this.progress.classList.add('active');
            this.progressFill.style.width = `${percent}%`;
        }
    },

    // MOBILE HELPERS
    toggleDrawer() {
        this.drawer.classList.add('open');
        this.drawerOverlay.classList.add('open');
    },

    closeDrawer() {
        if (this.drawer) this.drawer.classList.remove('open');
        if (this.drawerOverlay) this.drawerOverlay.classList.remove('open');
    },

    setupSwipeGestures() {
        let touchstartX = 0;
        let touchendX = 0;
        
        document.addEventListener('touchstart', e => {
            touchstartX = e.changedTouches[0].screenX;
        }, false);

        document.addEventListener('touchend', e => {
            touchendX = e.changedTouches[0].screenX;
            this.handleSwipe(touchstartX, touchendX);
        }, false);
    },

    handleSwipe(start, end) {
        const threshold = 100;
        const state = GLOBAL_STORE.getState();
        
        // Navigation logic
        if (state.currentView === 'episodes') {
            if (end - start > threshold) {
                // Swiped Right -> Open drawer
                this.toggleDrawer();
            }
        } else if (state.currentView === 'episodeDetail') {
            const episodes = state.episodes || [];
            const currentIndex = episodes.findIndex(ep => ep.id === state.selectedEpisodeId);
            
            if (start - end > threshold) {
                // Swiped Left -> Next Episode
                if (currentIndex < episodes.length - 1) {
                    this.handleEpisodeClick(episodes[currentIndex + 1].id);
                }
            } else if (end - start > threshold) {
                // Swiped Right -> Previous Episode or Back
                if (currentIndex > 0) {
                    this.handleEpisodeClick(episodes[currentIndex - 1].id);
                } else {
                    GLOBAL_STORE.setState({ currentView: 'episodes' });
                }
            }
        }
    },

    setupPullToRefresh() {
        let touchstart = 0;
        const main = document.querySelector('.app-main');
        
        // Add PTR element if not exists
        if (!document.querySelector('.pull-to-refresh')) {
            const ptr = document.createElement('div');
            ptr.className = 'pull-to-refresh';
            ptr.innerHTML = '<div class="ptr-indicator"></div>';
            main.prepend(ptr);
        }

        const ptr = document.querySelector('.pull-to-refresh');

        window.addEventListener('touchstart', (e) => {
            if (window.scrollY === 0) {
                touchstart = e.touches[0].pageY;
            }
        });

        window.addEventListener('touchmove', (e) => {
            const touch = e.touches[0].pageY;
            if (window.scrollY === 0 && touch > touchstart) {
                const diff = touch - touchstart;
                if (diff > 50) {
                    ptr.classList.add('active');
                }
            }
        });

        window.addEventListener('touchend', async () => {
            if (ptr.classList.contains('active')) {
                await this.refreshData();
                ptr.classList.remove('active');
                this.showToast('Data refreshed', 'success');
            }
        });
    }
};

document.addEventListener('DOMContentLoaded', () => APP.init());
