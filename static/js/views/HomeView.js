/**
 * HomeView - Netflix-style Homepage
 */
import { SeasonCarousel } from '../components/SeasonCarousel.js';
import { LoadingState } from '../components/LoadingState.js';
import GLOBAL_STORE from '../services/store.js';

export const HomeView = (onEpisodeClick) => {
    const container = document.createElement('div');
    container.className = 'netflix-home';

    // Show initial skeleton loaders
    const renderSkeleton = () => {
        container.innerHTML = '';
        container.appendChild(LoadingState());
        container.appendChild(LoadingState());
    };

    const renderRecommendations = (data) => {
        container.innerHTML = '';

        // 1. Hero: Featured episode
        const featured = data.hero || { title: 'Your Story', narrative_text: 'Start documenting your life today.' };
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
                <span class="billboard-badge">✨ FEATURED STORIES</span>
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

        // 2. Continue Listening
        if (data.continue_listening && data.continue_listening.length > 0) {
            container.appendChild(SeasonCarousel('Continue Listening', data.continue_listening, onEpisodeClick));
        }

        // 3. Because you viewed [X]
        if (data.similar_recommendations && data.similar_recommendations.episodes && data.similar_recommendations.episodes.length > 0) {
            container.appendChild(SeasonCarousel(`Because you viewed: ${data.similar_recommendations.reference_title}`, data.similar_recommendations.episodes, onEpisodeClick));
        }

        // 4. Your [Theme] Journey for top themes
        if (data.theme_journeys && data.theme_journeys.length > 0) {
            data.theme_journeys.forEach(journey => {
                container.appendChild(SeasonCarousel(`Your ${journey.theme} Journey`, journey.episodes, onEpisodeClick, { isThemeJourney: true }));
            });
        }

        // 5. On This Day from previous years
        if (data.on_this_day && data.on_this_day.length > 0) {
            container.appendChild(SeasonCarousel('On This Day (Flashback)', data.on_this_day, onEpisodeClick));
        }

        // 6. Season Highlights (best episodes)
        if (data.season_highlights && data.season_highlights.length > 0) {
            data.season_highlights.forEach(highlight => {
                container.appendChild(SeasonCarousel(`${highlight.season_title} Highlights`, highlight.episodes, onEpisodeClick));
            });
        }

        // 7. Flashback (Random Flashback suggestion)
        if (data.flashback) {
            container.appendChild(SeasonCarousel('Flashback Roulette', [data.flashback], onEpisodeClick));
        }
    };

    // Load recommendations from backend
    renderSkeleton();
    fetch('/recommendations/homepage')
        .then(res => res.json())
        .then(data => {
            renderRecommendations(data);
        })
        .catch(err => {
            console.error('Failed to fetch homepage recommendations, falling back to static store:', err);
            // Fallback rendering
            const { episodes, seasons } = GLOBAL_STORE.getState();
            const fallbackData = {
                hero: episodes[0] || null,
                continue_listening: episodes.filter(e => e.playback_position > 0).slice(0, 10),
                similar_recommendations: { reference_title: episodes[0]?.title || '', episodes: episodes.slice(1, 7) },
                theme_journeys: Object.entries(
                    episodes.reduce((acc, ep) => {
                        if (ep.cluster_label) {
                            if (!acc[ep.cluster_label]) acc[ep.cluster_label] = [];
                            acc[ep.cluster_label].push(ep);
                        }
                        return acc;
                    }, {})
                ).map(([theme, eps]) => ({ theme, episodes: eps })),
                on_this_day: [],
                season_highlights: seasons.map(s => ({ season_title: s.title, episodes: episodes.filter(e => e.season_id === s.id) })),
                flashback: episodes[Math.floor(Math.random() * episodes.length)] || null
            };
            renderRecommendations(fallbackData);
        });

    return container;
};
