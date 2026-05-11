/**
 * Keyboard Shortcuts Manager
 */
import GLOBAL_STORE from './store.js';
import { getPlayerInstance } from '../components/AudioPlayer.js';

export const KeyboardManager = {
    init() {
        document.addEventListener('keydown', (e) => this.handleKeydown(e));
        this.injectHelpModal();
    },

    handleKeydown(e) {
        // Disable shortcuts when typing in inputs/textareas
        const isTyping = ['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName) || document.activeElement.isContentEditable;
        
        if (isTyping && e.key !== 'Escape' && e.key !== 'Enter') return;

        const player = getPlayerInstance();

        switch (e.key) {
            // Global Navigation
            case '/':
                if (!isTyping) {
                    e.preventDefault();
                    const searchBar = document.getElementById('header-search');
                    if (searchBar) {
                        searchBar.focus();
                        searchBar.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    }
                }
                break;
            
            case 'h':
            case 'H':
                if (!isTyping) {
                    e.preventDefault();
                    GLOBAL_STORE.setState({ currentView: 'episodes' });
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
                break;

            case '?':
                if (!isTyping) {
                    e.preventDefault();
                    this.toggleHelpModal();
                }
                break;

            case 'Escape':
                this.handleEscape();
                break;

            // List Navigation (j/k / arrows)
            case 'j':
            case 'ArrowDown':
                if (!isTyping) {
                    e.preventDefault();
                    this.navigateFocus(1);
                }
                break;
            case 'k':
            case 'ArrowUp':
                if (!isTyping) {
                    e.preventDefault();
                    this.navigateFocus(-1);
                }
                break;
            case 'ArrowRight':
                if (!isTyping) {
                    e.preventDefault();
                    // Check if we should seek audio instead, but request says Left/Right -> seek
                    // Let's separate: if currently focusing a card, Arrow keys navigate cards.
                    // User spec says Left/Right -> seek audio, and j/k for list nav. 
                    // So let's strictly use Left/Right for seek.
                    player.seekSeconds(10);
                }
                break;
            case 'ArrowLeft':
                if (!isTyping) {
                    e.preventDefault();
                    player.seekSeconds(-10);
                }
                break;

            case 'Enter':
                if (!isTyping) {
                    const focused = document.activeElement;
                    if (focused && focused.classList.contains('netflix-episode-card')) {
                        focused.click();
                    }
                }
                break;

            // Audio Controls
            case ' ':
                if (!isTyping) {
                    e.preventDefault();
                    player.togglePlay();
                }
                break;
            
            case 'm':
            case 'M':
                if (!isTyping) {
                    e.preventDefault();
                    player.toggleMute();
                }
                break;

            // Chapters
            case '1': case '2': case '3': case '4': case '5':
                if (!isTyping) {
                    e.preventDefault();
                    const num = parseInt(e.key) - 1;
                    player.jumpToChapter(num);
                }
                break;
        }
    },

    handleEscape() {
        // Close modals
        const episodeModal = document.getElementById('modal-episode');
        const helpModal = document.getElementById('keyboard-shortcuts-modal');
        const searchDropdown = document.getElementById('search-live-results');
        
        let closedSomething = false;

        if (helpModal && helpModal.classList.contains('active')) {
            helpModal.classList.remove('active');
            closedSomething = true;
        }

        if (episodeModal && episodeModal.classList.contains('active')) {
            episodeModal.classList.remove('active');
            closedSomething = true;
        }

        if (searchDropdown && searchDropdown.classList.contains('active')) {
            searchDropdown.classList.remove('active');
            closedSomething = true;
        }

        const searchBar = document.getElementById('header-search');
        if (searchBar && document.activeElement === searchBar) {
            searchBar.blur();
            closedSomething = true;
        }

        // If nothing to close, and in subview, go back to browse
        if (!closedSomething) {
            const state = GLOBAL_STORE.getState();
            if (state.currentView !== 'episodes') {
                GLOBAL_STORE.setState({ currentView: 'episodes' });
            }
        }
    },

    navigateFocus(direction) {
        const cards = Array.from(document.querySelectorAll('.netflix-episode-card, .nav-link, .result-card-list'));
        if (cards.length === 0) return;

        const currentIndex = cards.indexOf(document.activeElement);
        let nextIndex = 0;

        if (currentIndex === -1) {
            nextIndex = 0;
        } else {
            nextIndex = (currentIndex + direction + cards.length) % cards.length;
        }

        cards[nextIndex].focus();
        cards[nextIndex].scrollIntoView({ behavior: 'smooth', block: 'center', inline: 'center' });
    },

    injectHelpModal() {
        if (document.getElementById('keyboard-shortcuts-modal')) return;

        const modal = document.createElement('div');
        modal.id = 'keyboard-shortcuts-modal';
        modal.className = 'modal keyboard-modal';
        modal.innerHTML = `
            <div class="modal-overlay"></div>
            <div class="modal-content shortcut-dialog">
                <button class="modal-close" id="close-shortcut-modal">×</button>
                <h2 class="modal-title">⌨️ Keyboard Shortcuts</h2>
                
                <div class="shortcut-grid">
                    <div class="shortcut-section">
                        <h3>Navigation</h3>
                        <div class="shortcut-row"><kbd>/</kbd> <span>Focus Search</span></div>
                        <div class="shortcut-row"><kbd>j</kbd> / <kbd>k</kbd> <span>Next/Prev Episode</span></div>
                        <div class="shortcut-row"><kbd>Enter</kbd> <span>Open Selected</span></div>
                        <div class="shortcut-row"><kbd>Esc</kbd> <span>Close / Back</span></div>
                        <div class="shortcut-row"><kbd>h</kbd> <span>Go Home</span></div>
                    </div>
                    <div class="shortcut-section">
                        <h3>Playback</h3>
                        <div class="shortcut-row"><kbd>Space</kbd> <span>Play/Pause</span></div>
                        <div class="shortcut-row"><kbd>←</kbd> / <kbd>→</kbd> <span>Rewind/Forward</span></div>
                        <div class="shortcut-row"><kbd>m</kbd> <span>Mute Toggle</span></div>
                        <div class="shortcut-row"><kbd>1</kbd>-<kbd>5</kbd> <span>Jump to Chapter</span></div>
                        <div class="shortcut-row"><kbd>?</kbd> <span>Show this help</span></div>
                    </div>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        modal.querySelector('.modal-overlay').onclick = () => modal.classList.remove('active');
        modal.querySelector('#close-shortcut-modal').onclick = () => modal.classList.remove('active');
    },

    toggleHelpModal() {
        const modal = document.getElementById('keyboard-shortcuts-modal');
        if (modal) {
            modal.classList.toggle('active');
        }
    }
};
