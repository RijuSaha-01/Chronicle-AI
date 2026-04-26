/**
 * AudioPlayer Component - Netflix Style
 */

export const AudioPlayer = (episode) => {
    const container = document.createElement('div');
    container.className = 'netflix-player-bar';
    
    if (!episode) {
        container.style.display = 'none';
        return container;
    }

    container.innerHTML = `
        <div class="player-content">
            <div class="player-info">
                <div class="player-thumbnail"></div>
                <div class="player-text">
                    <span class="player-episode-title">${episode.title}</span>
                    <span class="player-series">Chronicle AI • Narrating Life</span>
                </div>
            </div>
            
            <div class="player-controls">
                <button class="player-btn reverse">↺</button>
                <button class="player-btn play-pause">▶</button>
                <button class="player-btn forward">↻</button>
                <div class="player-progress-container">
                    <span class="time">0:00</span>
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: 30%"></div>
                    </div>
                    <span class="time">12:45</span>
                </div>
            </div>

            <div class="player-actions">
                <button class="player-btn">🔇</button>
                <button class="player-btn">≣</button>
                <button id="close-player" class="player-btn">✕</button>
            </div>
        </div>
    `;

    container.querySelector('#close-player').onclick = () => {
        container.classList.add('fade-out');
        setTimeout(() => container.remove(), 300);
    };

    return container;
};
