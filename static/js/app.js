/**
 * Chronicle AI - Modular App Entry
 */
import API from './services/api.js';
import GLOBAL_STORE from './services/store.js';
import { HomeView } from './views/HomeView.js';
import { CreateView } from './views/CreateView.js';
import { AudioPlayer } from './components/AudioPlayer.js';

const APP = {
    async init() {
        console.log('🎬 Chronicle AI: Netflix Edition Initializing...');
        
        this.root = document.getElementById('app-root');
        this.navLinks = document.querySelectorAll('.nav-link');
        this.playerContainer = document.getElementById('audio-player-root');
        
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

        // AI Status Check
        this.checkStatus();
        setInterval(() => this.checkStatus(), 30000);

        // Initial render
        this.render(GLOBAL_STORE.getState());
    },

    async refreshData() {
        GLOBAL_STORE.setState({ isLoading: true });
        try {
            const data = await API.getEpisodes();
            GLOBAL_STORE.setState({ episodes: data.entries || [], isLoading: false });
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
        }

        // Handle Audio Player
        if (state.currentEpisode && !document.querySelector('.netflix-player-bar')) {
            this.playerContainer.innerHTML = '';
            this.playerContainer.appendChild(AudioPlayer(state.currentEpisode));
        }
    },

    async handleEpisodeClick(id) {
        try {
            const episode = await API.getEpisode(id);
            GLOBAL_STORE.setState({ currentEpisode: episode });
            // For now, opening detailed info could still be the modal
            this.openModal(episode);
        } catch (error) {
            this.showToast('Failed to load episode details', 'error');
        }
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
