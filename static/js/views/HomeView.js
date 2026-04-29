/**
 * HomeView - Netflix-style Homepage
 */
import { SeasonCarousel } from '../components/SeasonCarousel.js';
import { LoadingState } from '../components/LoadingState.js';
import GLOBAL_STORE from '../services/store.js';

export const HomeView = (onEpisodeClick) => {
    const { episodes, seasons, isLoading } = GLOBAL_STORE.getState();
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
    
    let billboardBg = 'https://images.unsplash.com/photo-1485846234645-a62644f84728?q=80&w=1200&auto=format&fit=crop';
    if (featured.cover_art_path) {
        billboardBg = featured.cover_art_path.replace(/\\/g, '/');
        if (!billboardBg.startsWith('/')) billboardBg = '/' + billboardBg;
    }

    billboard.style.backgroundImage = `linear-gradient(to bottom, rgba(20,20,20,0) 0%, rgba(20,20,20,0.8) 70%, rgba(20,20,20,1) 100%), url(${billboardBg})`;
    
    billboard.innerHTML = `
        <div class="billboard-content">
            <h1 class="billboard-title">${featured.title || 'Welcome Home'}</h1>
            <p class="billboard-synopsis">${featured.synopsis || featured.narrative_text || 'Continue your journey by documenting today.'}</p>
            <div class="billboard-actions">
                <button class="btn-netflix primary play-billboard">▶ Play Narrative</button>
                <button class="btn-netflix secondary info-billboard">ⓘ More Info</button>
            </div>
        </div>
    `;

    billboard.querySelector('.play-billboard').onclick = () => onEpisodeClick(featured.id);
    billboard.querySelector('.info-billboard').onclick = () => onEpisodeClick(featured.id);

    container.appendChild(billboard);

    // 1. Continue Listening (Episodes with progress or just the most recent ones)
    const continueListening = episodes.filter(e => e.playback_position > 0).slice(0, 10);
    if (continueListening.length > 0) {
        container.appendChild(SeasonCarousel('Continue Watching', continueListening, onEpisodeClick));
    }

    // 2. Season Rows
    if (seasons && seasons.length > 0) {
        seasons.forEach(season => {
            const seasonEpisodes = episodes.filter(e => e.season_id === season.id);
            if (seasonEpisodes.length > 0) {
                container.appendChild(SeasonCarousel(season.title, seasonEpisodes, onEpisodeClick, {
                    posterPath: season.poster_path ? (season.poster_path.startsWith('/') ? season.poster_path : '/' + season.poster_path.replace(/\\/g, '/')) : null
                }));
            }
        });
    }

    // 3. Recently Added
    const recentlyAdded = [...episodes].sort((a, b) => b.id - a.id).slice(0, 12);
    container.appendChild(SeasonCarousel('Recently Added', recentlyAdded, onEpisodeClick));

    // 4. Theme Journeys (Grouped by clusters or themes)
    const themeGroups = {};
    episodes.forEach(e => {
        if (e.cluster_label) {
            if (!themeGroups[e.cluster_label]) themeGroups[e.cluster_label] = [];
            themeGroups[e.cluster_label].push(e);
        }
    });

    Object.entries(themeGroups).slice(0, 3).forEach(([theme, group]) => {
        container.appendChild(SeasonCarousel(`Your ${theme} Journey`, group, onEpisodeClick, { isThemeJourney: true }));
    });

    // Fallback if no seasons/themes yet
    if (container.children.length < 3 && episodes.length > 10) {
        container.appendChild(SeasonCarousel('More Episodes', episodes.slice(10, 20), onEpisodeClick));
    }

    return container;
};
