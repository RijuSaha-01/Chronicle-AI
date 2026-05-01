/**
 * AudioPlayer Component - Spotify/Netflix Style
 * Handles persistent audio playback with cinematic controls.
 */

class AudioPlayerManager {
    constructor() {
        this.audio = new Audio();
        this.currentEpisode = null;
        this.isCollapsed = false;
        this.container = null;
        this.setupListeners();
    }

    setupListeners() {
        this.audio.addEventListener('timeupdate', () => this.updateProgress());
        this.audio.addEventListener('loadedmetadata', () => this.updateDuration());
        this.audio.addEventListener('ended', () => this.handleEnded());
        this.audio.addEventListener('play', () => this.updatePlayPauseIcon(true));
        this.audio.addEventListener('pause', () => this.updatePlayPauseIcon(false));

        // Keyboard Shortcut: Space for play/pause
        document.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && !['INPUT', 'TEXTAREA'].includes(document.activeElement.tagName)) {
                e.preventDefault();
                this.togglePlay();
            }
        });
    }

    render(episode) {
        if (!episode) return null;
        
        // If it's a new episode, load it
        if (!this.currentEpisode || this.currentEpisode.id !== episode.id) {
            this.currentEpisode = episode;
            // In a real app, episode.audio_url would be used. 
            // For demo, we'll use a placeholder if not provided.
            this.audio.src = episode.audio_url || 'https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3';
            this.audio.play();
        }

        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = 'netflix-persistent-player';
            this.container.className = 'netflix-player-bar';
        }

        this.updateUI();
        return this.container;
    }

    updateUI() {
        if (!this.currentEpisode) return;

        const chapters = this.currentEpisode.chapters || [
            { title: 'Act I: The Beginning', time: 0 },
            { title: 'Act II: The Conflict', time: 300 },
            { title: 'Act III: Resolution', time: 600 }
        ];

        this.container.innerHTML = `
            <div class="player-content ${this.isCollapsed ? 'collapsed' : ''}">
                <button class="player-expand-btn" id="player-toggle-collapse">
                    ${this.isCollapsed ? '▲' : '▼'}
                </button>
                
                <div class="player-info">
                    <img src="${this.currentEpisode.cover_url || 'https://images.unsplash.com/photo-1614613535308-eb5fbd3d2c17?q=80&w=200&h=200&fit=crop'}" class="player-thumbnail" alt="Cover">
                    <div class="player-text">
                        <span class="player-episode-title">${this.currentEpisode.title}</span>
                        <span class="player-series">Chronicle AI • Narrating Life</span>
                    </div>
                </div>
                
                <div class="player-controls">
                    <div class="control-buttons">
                        <button class="player-btn" id="player-rewind">↺</button>
                        <button class="player-btn play-pause" id="player-play-pause">▶</button>
                        <button class="player-btn" id="player-forward">↻</button>
                    </div>
                    
                    <div class="player-progress-container">
                        <span class="time" id="current-time">0:00</span>
                        <div class="progress-bar" id="progress-bar-root">
                            <div class="progress-fill" id="progress-fill" style="width: 0%"></div>
                            <div class="progress-knob"></div>
                        </div>
                        <span class="time" id="total-duration">0:00</span>
                    </div>
                </div>

                <div class="player-actions">
                    <div class="chapter-dropdown">
                        <button class="player-btn" id="chapter-btn">≣ Chapters</button>
                        <div class="chapter-menu" id="chapter-menu">
                            ${chapters.map((ch, i) => `
                                <div class="chapter-item" data-time="${ch.time}">
                                    <span class="ch-num">${i + 1}</span>
                                    <span class="ch-title">${ch.title}</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>

                    <div class="volume-control">
                        <button class="player-btn" id="volume-btn">🔊</button>
                        <div class="volume-slider-container">
                            <input type="range" id="volume-slider" min="0" max="1" step="0.01" value="${this.audio.volume}">
                        </div>
                    </div>
                    
                    <button id="close-player" class="player-btn">✕</button>
                </div>
            </div>
        `;

        this.attachEvents();
    }

    attachEvents() {
        const btnPlayPause = this.container.querySelector('#player-play-pause');
        const btnRewind = this.container.querySelector('#player-rewind');
        const btnForward = this.container.querySelector('#player-forward');
        const progressBar = this.container.querySelector('#progress-bar-root');
        const btnToggle = this.container.querySelector('#player-toggle-collapse');
        const btnClose = this.container.querySelector('#close-player');
        const volumeSlider = this.container.querySelector('#volume-slider');
        const chapterBtn = this.container.querySelector('#chapter-btn');
        const chapterMenu = this.container.querySelector('#chapter-menu');

        btnPlayPause.onclick = () => this.togglePlay();
        btnRewind.onclick = () => this.audio.currentTime -= 10;
        btnForward.onclick = () => this.audio.currentTime += 10;
        
        progressBar.onclick = (e) => {
            const rect = progressBar.getBoundingClientRect();
            const pos = (e.clientX - rect.left) / rect.width;
            this.audio.currentTime = pos * this.audio.duration;
        };

        this.container.onclick = (e) => {
            if (this.isCollapsed && !e.target.closest('#close-player')) {
                this.expandPlayer();
            }
        };

        btnToggle.onclick = (e) => {
            e.stopPropagation();
            if (this.isCollapsed) {
                this.expandPlayer();
            } else {
                this.collapsePlayer();
            }
        };

        btnClose.onclick = () => {
            this.audio.pause();
            this.container.classList.add('fade-out');
            setTimeout(() => {
                this.container.remove();
                this.container = null;
                this.currentEpisode = null;
            }, 300);
        };

        volumeSlider.oninput = (e) => {
            this.audio.volume = e.target.value;
            this.container.querySelector('#volume-btn').innerHTML = this.audio.volume === 0 ? '🔇' : '🔊';
        };

        chapterBtn.onclick = (e) => {
            e.stopPropagation();
            chapterMenu.classList.toggle('active');
        };

        document.addEventListener('click', () => {
            if (chapterMenu) chapterMenu.classList.remove('active');
        });

        this.container.querySelectorAll('.chapter-item').forEach(item => {
            item.onclick = () => {
                this.audio.currentTime = parseInt(item.dataset.time);
                chapterMenu.classList.remove('active');
            };
        });
    }

    collapsePlayer() {
        this.isCollapsed = true;
        this.container.querySelector('.player-content').classList.add('collapsed');
        const btnToggle = this.container.querySelector('#player-toggle-collapse');
        if (btnToggle) btnToggle.innerHTML = '▲';
    }

    expandPlayer() {
        this.isCollapsed = false;
        this.container.querySelector('.player-content').classList.remove('collapsed');
        const btnToggle = this.container.querySelector('#player-toggle-collapse');
        if (btnToggle) btnToggle.innerHTML = '▼';
    }

    togglePlay() {
        if (this.audio.paused) {
            this.audio.play();
        } else {
            this.audio.pause();
        }
    }

    updatePlayPauseIcon(isPlaying) {
        const btn = this.container?.querySelector('#player-play-pause');
        if (btn) btn.innerHTML = isPlaying ? '⏸' : '▶';
    }

    updateProgress() {
        if (!this.audio.duration) return;
        const percent = (this.audio.currentTime / this.audio.duration) * 100;
        const fill = this.container?.querySelector('#progress-fill');
        const currentTime = this.container?.querySelector('#current-time');
        
        if (fill) fill.style.width = `${percent}%`;
        if (currentTime) currentTime.innerHTML = this.formatTime(this.audio.currentTime);
    }

    updateDuration() {
        const totalDuration = this.container?.querySelector('#total-duration');
        if (totalDuration) totalDuration.innerHTML = this.formatTime(this.audio.duration);
    }

    handleEnded() {
        this.updatePlayPauseIcon(false);
    }

    formatTime(seconds) {
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
}

const PLAYER_INSTANCE = new AudioPlayerManager();

export const AudioPlayer = (episode) => {
    return PLAYER_INSTANCE.render(episode);
};
