import { SeasonCarousel } from '../components/SeasonCarousel.js';
import { LoadingState } from '../components/LoadingState.js';
import GLOBAL_STORE from '../services/store.js';

export const HomeView = (onEpisodeClick) => {
    const { episodes, isLoading } = GLOBAL_STORE.getState();
    const container = document.createElement('div');
    container.className = 'netflix-home';

    if (isLoading && episodes.length === 0) {
        container.appendChild(LoadingState());
        container.appendChild(LoadingState());
        return container;
    }

    // Billboard (Featured Episode)
    const featured = episodes[0] || { title: 'Your Story', narrative_text: 'Start documenting your life today.' };
    
    const billboard = document.createElement('section');
    billboard.className = 'billboard';
    billboard.innerHTML = `
        <div class="billboard-content">
            <h1 class="billboard-title">${featured.title}</h1>
            <p class="billboard-synopsis">${featured.narrative_text || 'No narrative yet.'}</p>
            <div class="billboard-actions">
                <button class="btn-netflix primary">▶ Play Narrative</button>
                <button class="btn-netflix secondary">ⓘ More Info</button>
            </div>
        </div>
    `;

    container.appendChild(billboard);

    // Rows
    const recentRow = SeasonCarousel('Continue Watching', episodes.slice(0, 10), onEpisodeClick);
    const popularRow = SeasonCarousel('Trending Now', [...episodes].reverse().slice(0, 10), onEpisodeClick);
    
    container.appendChild(recentRow);
    container.appendChild(popularRow);

    return container;
};
