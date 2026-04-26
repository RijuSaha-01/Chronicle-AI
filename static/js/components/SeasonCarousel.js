/**
 * SeasonCarousel Component
 */
import { EpisodeCard } from './EpisodeCard.js';

export const SeasonCarousel = (title, episodes, onEpisodeClick) => {
    const container = document.createElement('section');
    container.className = 'netflix-row';
    
    container.innerHTML = `
        <h2 class="row-title">${title}</h2>
        <div class="carousel-container">
            <button class="carousel-nav prev" aria-label="Previous">❮</button>
            <div class="carousel-viewport">
                <div class="carousel-track"></div>
            </div>
            <button class="carousel-nav next" aria-label="Next">❯</button>
        </div>
    `;

    const track = container.querySelector('.carousel-track');
    
    if (episodes.length === 0) {
        track.innerHTML = '<div class="empty-state">No episodes in this season</div>';
    } else {
        episodes.forEach(episode => {
            track.appendChild(EpisodeCard(episode, onEpisodeClick));
        });
    }

    // Scroll Logic
    const viewport = container.querySelector('.carousel-viewport');
    container.querySelector('.next').onclick = () => {
        viewport.scrollBy({ left: 600, behavior: 'smooth' });
    };
    container.querySelector('.prev').onclick = () => {
        viewport.scrollBy({ left: -600, behavior: 'smooth' });
    };

    return container;
};
