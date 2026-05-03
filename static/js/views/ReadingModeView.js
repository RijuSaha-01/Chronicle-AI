/**
 * ReadingModeView - Clean reading experience with audio sync
 */
import API from '../services/api.js';
import GLOBAL_STORE from '../services/store.js';
import { LoadingState } from '../components/LoadingState.js';

export const ReadingModeView = (episodeId) => {
    const container = document.createElement('div');
    container.className = 'reading-mode-view';
    
    // Initial loading state
    container.appendChild(LoadingState());

    loadReadingData(container, episodeId);

    return container;
};

async function loadReadingData(container, episodeId) {
    try {
        const episode = await API.getEpisode(episodeId);
        container.innerHTML = '';
        
        // Navigation Header
        const header = document.createElement('header');
        header.className = 'reading-header';
        header.innerHTML = `
            <div class="header-left">
                <button class="btn-back" id="reading-back">← Back</button>
                <div class="reading-meta">
                    <span class="reading-title">${episode.title}</span>
                    <span class="reading-subtitle">Episode ${episode.id}</span>
                </div>
            </div>
            <div class="header-right">
                <button class="btn-sync active" id="sync-toggle">Sync: ON</button>
                <button class="btn-theme" id="theme-toggle">🌙 Night</button>
            </div>
        `;
        container.appendChild(header);

        // Content Area
        const content = document.createElement('main');
        content.className = 'reading-content-area';
        
        const narrativeText = episode.narrative_text || 'No narrative text available.';
        const paragraphs = narrativeText.split('\n\n').filter(p => p.trim() !== '');
        
        const textContainer = document.createElement('div');
        textContainer.className = 'reading-text-container';
        
        paragraphs.forEach((p, index) => {
            const pEl = document.createElement('p');
            pEl.className = 'reading-paragraph';
            pEl.dataset.index = index;
            pEl.innerHTML = p;
            
            pEl.onclick = () => {
                const audio = document.querySelector('audio');
                if (audio && audio.duration) {
                    const totalChars = paragraphs.join('').length;
                    let charsBefore = 0;
                    for (let i = 0; i < index; i++) {
                        charsBefore += paragraphs[i].length;
                    }
                    const percent = charsBefore / totalChars;
                    audio.currentTime = percent * audio.duration;
                    if (audio.paused) audio.play();
                }
            };
            
            textContainer.appendChild(pEl);
        });
        
        content.appendChild(textContainer);
        container.appendChild(content);

        // Logic
        setupReadingLogic(container, paragraphs);

    } catch (error) {
        container.innerHTML = `<div class="error-state">
            <h2>Failed to load reading mode</h2>
            <p>${error.message}</p>
            <button class="btn-netflix primary" onclick="location.reload()">Retry</button>
        </div>`;
    }
}

function setupReadingLogic(container, paragraphs) {
    const backBtn = container.querySelector('#reading-back');
    const syncToggle = container.querySelector('#sync-toggle');
    const themeToggle = container.querySelector('#theme-toggle');
    const textContainer = container.querySelector('.reading-text-container');
    
    let isSyncEnabled = true;

    backBtn.onclick = () => {
        GLOBAL_STORE.setState({ currentView: 'episodeDetail' });
    };

    syncToggle.onclick = () => {
        isSyncEnabled = !isSyncEnabled;
        syncToggle.classList.toggle('active', isSyncEnabled);
        syncToggle.textContent = `Sync: ${isSyncEnabled ? 'ON' : 'OFF'}`;
    };

    themeToggle.onclick = () => {
        document.body.classList.toggle('light-reading-mode');
        themeToggle.textContent = document.body.classList.contains('light-reading-mode') ? '☀️ Day' : '🌙 Night';
    };

    // Audio Sync Listener
    const audio = document.querySelector('audio');
    if (audio) {
        const onTimeUpdate = () => {
            if (!isSyncEnabled || !audio.duration) return;

            const percent = audio.currentTime / audio.duration;
            const totalChars = paragraphs.join('').length;
            const targetCharCount = totalChars * percent;

            let currentCharCount = 0;
            let activeIndex = 0;

            for (let i = 0; i < paragraphs.length; i++) {
                currentCharCount += paragraphs[i].length;
                if (currentCharCount >= targetCharCount) {
                    activeIndex = i;
                    break;
                }
            }

            // Update highlighting
            const allP = textContainer.querySelectorAll('.reading-paragraph');
            allP.forEach((p, idx) => {
                p.classList.toggle('active', idx === activeIndex);
            });

            // Auto-scroll
            const activeP = textContainer.querySelector(`.reading-paragraph[data-index="${activeIndex}"]`);
            if (activeP) {
                const rect = activeP.getBoundingClientRect();
                const containerRect = container.getBoundingClientRect();
                
                // If not clearly in view, scroll
                if (rect.top < containerRect.top + 100 || rect.bottom > containerRect.bottom - 100) {
                    activeP.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        };

        audio.addEventListener('timeupdate', onTimeUpdate);
        
        // Clean up listener if view changes? 
        // In this SPA, we might need a way to unsubscribe. 
        // For now, we'll just check if the container is still in DOM.
        const observer = new MutationObserver(() => {
            if (!document.body.contains(container)) {
                audio.removeEventListener('timeupdate', onTimeUpdate);
                observer.disconnect();
            }
        });
        observer.observe(document.body, { childList: true, subtree: true });
    }
}
