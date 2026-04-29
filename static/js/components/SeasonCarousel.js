/**
 * SeasonCarousel Component - Netflix Style
 * Features: Horizontal scrolling, Arrow buttons, Season poster support
 */
import { EpisodeCard } from './EpisodeCard.js';

export const SeasonCarousel = (title, episodes, onEpisodeClick, options = {}) => {
    const { posterPath, isThemeJourney = false } = options;
    
    const container = document.createElement('section');
    container.className = `netflix-row ${posterPath ? 'has-poster' : ''} ${isThemeJourney ? 'theme-journey' : ''}`;
    
    container.innerHTML = `
        <div class="row-header">
            <h2 class="row-title">${title}</h2>
        </div>
        <div class="row-content">
            ${posterPath ? `
                <div class="season-poster-container">
                    <img src="${posterPath}" alt="${title} Poster" class="season-poster">
                </div>
            ` : ''}
            <div class="carousel-container">
                <button class="carousel-nav prev" aria-label="Previous">❮</button>
                <div class="carousel-viewport">
                    <div class="carousel-track"></div>
                </div>
                <button class="carousel-nav next" aria-label="Next">❯</button>
            </div>
        </div>
    `;

    const track = container.querySelector('.carousel-track');
    
    if (episodes.length === 0) {
        track.innerHTML = '<div class="empty-state">No episodes found</div>';
    } else {
        episodes.forEach(episode => {
            const card = EpisodeCard(episode, onEpisodeClick);
            track.appendChild(card);
        });
    }

    // Scroll Logic
    const viewport = container.querySelector('.carousel-viewport');
    const nextBtn = container.querySelector('.next');
    const prevBtn = container.querySelector('.prev');

    const updateNavVisibility = () => {
        prevBtn.style.opacity = viewport.scrollLeft <= 0 ? '0' : '1';
        prevBtn.style.pointerEvents = viewport.scrollLeft <= 0 ? 'none' : 'auto';
        
        const isAtEnd = viewport.scrollLeft + viewport.clientWidth >= viewport.scrollWidth - 10;
        nextBtn.style.opacity = isAtEnd ? '0' : '1';
        nextBtn.style.pointerEvents = isAtEnd ? 'none' : 'auto';
    };

    nextBtn.onclick = () => {
        viewport.scrollBy({ left: viewport.clientWidth * 0.8, behavior: 'smooth' });
    };
    
    prevBtn.onclick = () => {
        viewport.scrollBy({ left: -viewport.clientWidth * 0.8, behavior: 'smooth' });
    };

    viewport.addEventListener('scroll', updateNavVisibility);
    
    // Initial check after a small delay to ensure rendering
    setTimeout(updateNavVisibility, 100);

    return container;
};
