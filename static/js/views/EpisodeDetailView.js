/**
 * EpisodeDetailView - Detailed view for a single episode
 */
import API from '../services/api.js';
import GLOBAL_STORE from '../services/store.js';
import { SeasonCarousel } from '../components/SeasonCarousel.js';
import { LoadingState } from '../components/LoadingState.js';

export const EpisodeDetailView = (episodeId, onEpisodeClick) => {
    const container = document.createElement('div');
    container.className = 'episode-detail-view';
    
    // Initial loading state
    container.appendChild(LoadingState());

    // Fetch full data
    loadEpisodeData(container, episodeId, onEpisodeClick);

    return container;
};

async function loadEpisodeData(container, episodeId, onEpisodeClick) {
    try {
        const [episode, similarData] = await Promise.all([
            API.getEpisode(episodeId),
            API.call(`/episodes/${episodeId}/similar?limit=6`)
        ]);

        container.innerHTML = '';
        
        // Hero Section
        const hero = createHero(episode);
        container.appendChild(hero);

        // Metadata Bar
        const metaBar = createMetaBar(episode);
        container.appendChild(metaBar);

        // Content Section with Tabs
        const contentSection = createContentSection(episode, similarData, onEpisodeClick);
        container.appendChild(contentSection);

        // Episode Navigation (Prev/Next)
        const navigation = createNavigation(episode, onEpisodeClick);
        container.appendChild(navigation);

    } catch (error) {
        container.innerHTML = `<div class="error-state">
            <h2>Failed to load episode details</h2>
            <p>${error.message}</p>
            <button class="btn-netflix primary" onclick="location.reload()">Retry</button>
        </div>`;
    }
}

function createHero(episode) {
    const hero = document.createElement('section');
    hero.className = 'episode-hero';
    
    let bgUrl = 'https://images.unsplash.com/photo-1485846234645-a62644f84728?q=80&w=1200&auto=format&fit=crop';
    if (episode.cover_art_path) {
        bgUrl = episode.cover_art_path.replace(/\\/g, '/');
        if (!bgUrl.startsWith('/')) bgUrl = '/' + bgUrl;
    }

    hero.style.backgroundImage = `linear-gradient(to bottom, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.9) 100%), url(${bgUrl})`;
    
    hero.innerHTML = `
        <div class="hero-content">
            <h1 class="hero-title">${episode.title || 'Untitled Episode'}</h1>
            <div class="hero-actions">
                <button class="btn-netflix primary play-trigger">▶ Play Episode</button>
                <button class="btn-netflix secondary reading-trigger">📖 Reading Mode</button>
                <button class="btn-netflix secondary regenerate-trigger">↻ Regenerate</button>
            </div>
        </div>
    `;

    hero.querySelector('.play-trigger').onclick = () => {
        GLOBAL_STORE.setState({ currentEpisode: episode });
    };

    hero.querySelector('.reading-trigger').onclick = () => {
        GLOBAL_STORE.setState({ currentView: 'readingMode' });
    };

    hero.querySelector('.regenerate-trigger').onclick = async () => {
        hero.querySelector('.regenerate-trigger').disabled = true;
        hero.querySelector('.regenerate-trigger').textContent = 'Regenerating...';
        try {
            await API.regenerateEpisode(episode.id);
            location.reload(); // Refresh to show new data
        } catch (err) {
            alert('Regeneration failed: ' + err.message);
            hero.querySelector('.regenerate-trigger').disabled = false;
            hero.querySelector('.regenerate-trigger').textContent = '↻ Regenerate';
        }
    };

    return hero;
}

function createMetaBar(episode) {
    const bar = document.createElement('div');
    bar.className = 'metadata-bar';
    
    const date = new Date(episode.date).toLocaleDateString(undefined, { 
        year: 'numeric', month: 'long', day: 'numeric' 
    });
    
    const duration = episode.audio_duration 
        ? `${Math.floor(episode.audio_duration / 60)}m ${Math.floor(episode.audio_duration % 60)}s`
        : '2m 30s'; // Fallback

    const moodColor = getMoodColor(episode.mood);

    bar.innerHTML = `
        <div class="meta-item">📅 ${date}</div>
        <div class="meta-item">🎬 Season ${episode.season_id || 1} • Episode ${episode.id}</div>
        <div class="meta-item">⏱ ${duration}</div>
        <div class="meta-badge" style="background: ${moodColor}33; color: ${moodColor}; border: 1px solid ${moodColor}66">
            ${episode.mood || 'Neutral'}
        </div>
    `;
    
    return bar;
}

function createContentSection(episode, similarData, onEpisodeClick) {
    const section = document.createElement('section');
    section.className = 'detail-content-section';
    
    section.innerHTML = `
        <div class="tab-nav">
            <button class="tab-btn active" data-tab="narrative">Narrative</button>
            <button class="tab-btn" data-tab="scenes">Scenes</button>
            <button class="tab-btn" data-tab="similar">Similar</button>
        </div>
        <div class="tab-content active" id="tab-narrative">
            <div class="narrative-container"></div>
        </div>
        <div class="tab-content" id="tab-scenes">
            <div class="scenes-grid"></div>
        </div>
        <div class="tab-content" id="tab-similar">
            <div class="similar-container"></div>
        </div>
    `;

    // Narrative Tab
    const narrativeContainer = section.querySelector('.narrative-container');
    const narrativeText = episode.narrative_text || 'No narrative generated yet.';
    
    // Split into acts if possible
    const acts = splitIntoActs(narrativeText);
    acts.forEach((act, index) => {
        const actEl = document.createElement('div');
        actEl.className = 'act-block';
        actEl.innerHTML = `
            <div class="act-header">
                <h3>Act ${index + 1}: ${act.title}</h3>
                <span class="act-toggle">▼</span>
            </div>
            <div class="act-body">${act.content}</div>
        `;
        actEl.querySelector('.act-header').onclick = () => {
            actEl.classList.toggle('collapsed');
            actEl.querySelector('.act-toggle').textContent = actEl.classList.contains('collapsed') ? '▶' : '▼';
        };
        narrativeContainer.appendChild(actEl);
    });

    // Original entry as well
    const rawEl = document.createElement('div');
    rawEl.className = 'raw-entry-block';
    rawEl.innerHTML = `
        <h4>Original Entry</h4>
        <div class="raw-text">${episode.raw_text}</div>
    `;
    narrativeContainer.appendChild(rawEl);

    // Scenes Tab
    const scenesGrid = section.querySelector('.scenes-grid');
    const variants = episode.image_variants || {};
    const variantKeys = Object.keys(variants);
    
    if (variantKeys.length > 0) {
        variantKeys.forEach(key => {
            const path = variants[key].replace(/\\/g, '/');
            const imgPath = path.startsWith('/') ? path : '/' + path;
            
            const sceneCard = document.createElement('div');
            sceneCard.className = 'scene-card';
            sceneCard.innerHTML = `
                <img src="${imgPath}" alt="${key}" loading="lazy">
                <div class="scene-label">${key}</div>
            `;
            scenesGrid.appendChild(sceneCard);
        });
    } else {
        scenesGrid.innerHTML = `<div class="empty-state">No storyboard scenes generated for this episode yet.</div>`;
    }

    // Similar Tab
    const similarContainer = section.querySelector('.similar-container');
    if (similarData && similarData.results && similarData.results.length > 0) {
        // Map similar results to episode objects (minimal)
        const similarEpisodes = similarData.results.map(res => ({
            id: res.episode_id,
            title: res.title,
            date: res.date,
            synopsis: res.explanation || res.themes
        }));
        similarContainer.appendChild(SeasonCarousel('Episodes with similar narrative echoes', similarEpisodes, onEpisodeClick));
    } else {
        similarContainer.innerHTML = `<div class="empty-state">No similar episodes found in the archives.</div>`;
    }

    // Tab Switching Logic
    const tabs = section.querySelectorAll('.tab-btn');
    const contents = section.querySelectorAll('.tab-content');
    
    tabs.forEach(tab => {
        tab.onclick = () => {
            tabs.forEach(t => t.classList.remove('active'));
            contents.forEach(c => c.classList.remove('active'));
            
            tab.classList.add('active');
            section.querySelector(`#tab-${tab.dataset.tab}`).classList.add('active');
        };
    });

    return section;
}

function createNavigation(episode, onEpisodeClick) {
    const nav = document.createElement('div');
    nav.className = 'episode-nav-footer';
    
    const { episodes } = GLOBAL_STORE.getState();
    const currentIndex = episodes.findIndex(e => e.id === episode.id);
    
    const prevEp = currentIndex < episodes.length - 1 ? episodes[currentIndex + 1] : null;
    const nextEp = currentIndex > 0 ? episodes[currentIndex - 1] : null;

    nav.innerHTML = `
        <div class="nav-prev">
            ${prevEp ? `
                <div class="nav-label">Previous</div>
                <div class="nav-link-item" data-id="${prevEp.id}">
                    <span class="arrow">←</span>
                    <span class="title">${prevEp.title || 'Previous Episode'}</span>
                </div>
            ` : ''}
        </div>
        <div class="nav-next">
            ${nextEp ? `
                <div class="nav-label">Next</div>
                <div class="nav-link-item" data-id="${nextEp.id}">
                    <span class="title">${nextEp.title || 'Next Episode'}</span>
                    <span class="arrow">→</span>
                </div>
            ` : ''}
        </div>
    `;

    nav.querySelectorAll('.nav-link-item').forEach(link => {
        link.onclick = () => onEpisodeClick(parseInt(link.dataset.id));
    });

    return nav;
}

function splitIntoActs(text) {
    // Simple heuristic: Split by sentences and group into 3 acts
    const sentences = text.split(/[.!?]+/).filter(s => s.trim().length > 5);
    
    if (sentences.length < 3) {
        return [{ title: 'The Encounter', content: text }];
    }

    const size = Math.ceil(sentences.length / 3);
    const act1 = sentences.slice(0, size).join('. ') + '.';
    const act2 = sentences.slice(size, size * 2).join('. ') + '.';
    const act3 = sentences.slice(size * 2).join('. ') + '.';

    return [
        { title: 'The Setup', content: act1 },
        { title: 'The Confrontation', content: act2 },
        { title: 'The Resolution', content: act3 }
    ];
}

function getMoodColor(mood) {
    const colors = {
        'anxious': '#1e3c72',
        'triumphant': '#f8b500',
        'melancholic': '#606c88',
        'peaceful': '#acb6e5',
        'adventurous': '#34e89e',
        'lonely': '#434343',
        'energetic': '#ff00cc',
        'frustrated': '#cb3066',
        'hopeful': '#ffd194',
        'nostalgic': '#e6dada',
        'mysterious': '#4b6cb7',
        'determined': '#232526',
        'exhausted': '#bdc3c7',
        'joyful': '#fffbd5',
        'productive': '#46d369',
        'reflective': '#606c88',
        'stressful': '#cb3066',
        'relaxed': '#acb6e5',
        'neutral': '#ffffff'
    };
    return colors[mood?.toLowerCase()] || '#ffffff';
}
