/**
 * Chronicle AI - Search View
 */
import GLOBAL_STORE from '../services/store.js';
import API from '../services/api.js';
import { EpisodeCard } from '../components/EpisodeCard.js';
import { VirtualList } from '../components/VirtualList.js';

export const SearchView = (onEpisodeClick) => {
    const state = GLOBAL_STORE.getState();
    const container = document.createElement('div');
    container.className = 'search-view';

    // Sidebar with Filters
    const sidebar = document.createElement('aside');
    sidebar.className = 'search-sidebar';
    sidebar.innerHTML = `
        <div class="search-filters-card">
            <h3>Filters</h3>
            
            <div class="filter-group">
                <label>Date Range</label>
                <div style="display: flex; gap: 0.5rem; align-items: center;">
                    <input type="date" id="filter-start-date" class="filter-input" value="${state.searchFilters.start_date}">
                    <span>-</span>
                    <input type="date" id="filter-end-date" class="filter-input" value="${state.searchFilters.end_date}">
                </div>
            </div>

            <div class="filter-group">
                <label>Season</label>
                <select id="filter-season" class="filter-input">
                    <option value="">All Seasons</option>
                    ${state.seasons.map(s => `<option value="${s.id}" ${state.searchFilters.season == s.id ? 'selected' : ''}>Season ${s.id}: ${s.title}</option>`).join('')}
                </select>
            </div>

            <div class="filter-group">
                <label>Mood</label>
                <select id="filter-mood" class="filter-input">
                    <option value="">All Moods</option>
                    <option value="Productive" ${state.searchFilters.mood === 'Productive' ? 'selected' : ''}>Productive</option>
                    <option value="Anxious" ${state.searchFilters.mood === 'Anxious' ? 'selected' : ''}>Anxious</option>
                    <option value="Excited" ${state.searchFilters.mood === 'Excited' ? 'selected' : ''}>Excited</option>
                    <option value="Reflective" ${state.searchFilters.mood === 'Reflective' ? 'selected' : ''}>Reflective</option>
                    <option value="Tired" ${state.searchFilters.mood === 'Tired' ? 'selected' : ''}>Tired</option>
                </select>
            </div>

            <div class="filter-group">
                <label>Themes</label>
                <input type="text" id="filter-themes" class="filter-input" placeholder="e.g. work, health" value="${state.searchFilters.themes}">
            </div>

            <button id="apply-filters" class="btn-netflix primary" style="width: 100%; margin-top: 1rem;">Apply Filters</button>

            <div class="recent-searches">
                <label>Recent Searches</label>
                <div class="recent-tags">
                    ${state.recentSearches.map(s => `<span class="recent-search-tag">${s}</span>`).join('')}
                </div>
            </div>
        </div>
    `;

    // Main Results Area
    const main = document.createElement('section');
    main.className = 'search-results-main';

    const resultsHeader = document.createElement('div');
    resultsHeader.className = 'search-results-header';
    resultsHeader.innerHTML = `
        <div class="results-info">
            <h2>Results for "${state.searchQuery}"</h2>
            <p>${state.searchResults.length} matches found</p>
        </div>
        <div class="view-toggle">
            <button class="toggle-btn ${state.searchViewMode === 'grid' ? 'active' : ''}" data-mode="grid">Grid</button>
            <button class="toggle-btn ${state.searchViewMode === 'list' ? 'active' : ''}" data-mode="list">List</button>
        </div>
    `;


    const resultsList = document.createElement('div');
    resultsList.className = state.searchViewMode === 'grid' ? 'results-grid' : 'results-list';

    if (state.isSearching) {
        resultsList.innerHTML = '<div class="loading-spinner">Searching deep into your memories...</div>';
    } else if (state.searchResults.length === 0) {
        resultsList.innerHTML = `
            <div class="no-results">
                <h2>∅</h2>
                <h3>No memories found matching that query.</h3>
                <p>Try searching for specific emotions, locations, or people.</p>
                <div class="suggestion-chips">
                    <span class="recent-search-tag">Productive morning</span>
                    <span class="recent-search-tag">Late night thoughts</span>
                    <span class="recent-search-tag">Meetings with team</span>
                </div>
            </div>
        `;
    } else {
        if (state.searchViewMode === 'grid') {
            state.searchResults.forEach(res => {
                const ep = state.episodes.find(e => e.id == res.episode_id) || {
                    id: res.episode_id,
                    title: res.title,
                    date: res.date,
                    mood: res.mood,
                    cover_art_path: res.metadata?.cover_art_path || '/static/img/placeholder.jpg'
                };
                const card = EpisodeCard(ep, () => onEpisodeClick(ep.id));
                resultsList.appendChild(card);
            });
        } else {
            const renderItem = (res) => {
                const card = document.createElement('div');
                card.className = 'result-card-list';
                card.onclick = () => onEpisodeClick(res.episode_id);
                
                const cover = res.metadata?.cover_art_path || '/static/img/placeholder.jpg';
                
                card.innerHTML = `
                    <img data-src="${cover}" src="data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII=" class="result-list-cover lazy" alt="Cover">
                    <div class="result-list-content">
                        <div class="result-list-meta">${new Date(res.date).toLocaleDateString()} • ${res.mood || 'Reflective'}</div>
                        <h3 class="result-list-title">${res.title}</h3>
                        <div class="result-list-snippet">${res.highlighted_text}</div>
                    </div>
                `;
                // Lazy load the list image
                const img = card.querySelector('.lazy');
                import('../utils/performance.js').then(({ LazyLoader }) => LazyLoader.observe(img));
                
                return card;
            };

            const virtualList = VirtualList(state.searchResults, renderItem, {
                itemHeight: 120,
                containerHeight: window.innerHeight - 250
            });
            resultsList.appendChild(virtualList);
        }
    }

    main.appendChild(resultsHeader);
    main.appendChild(resultsList);

    container.appendChild(sidebar);
    container.appendChild(main);

    // Event Listeners
    container.querySelectorAll('.toggle-btn').forEach(btn => {
        btn.onclick = () => {
            GLOBAL_STORE.setState({ searchViewMode: btn.dataset.mode });
        };
    });

    container.querySelectorAll('.recent-search-tag').forEach(tag => {
        tag.onclick = () => {
            const query = tag.textContent;
            document.getElementById('header-search').value = query;
            triggerSearch(query);
        };
    });

    container.querySelector('#apply-filters').onclick = () => {
        const filters = {
            start_date: container.querySelector('#filter-start-date').value,
            end_date: container.querySelector('#filter-end-date').value,
            season: container.querySelector('#filter-season').value,
            mood: container.querySelector('#filter-mood').value,
            themes: container.querySelector('#filter-themes').value
        };
        GLOBAL_STORE.setState({ searchFilters: filters });
        triggerSearch(state.searchQuery, filters);
    };

    return container;
};

async function triggerSearch(query, filters = null) {
    if (!query) return;
    
    GLOBAL_STORE.setState({ 
        isSearching: true, 
        searchQuery: query,
        currentView: 'search'
    });

    try {
        const activeFilters = filters || GLOBAL_STORE.getState().searchFilters;
        const results = await API.search(query, activeFilters);
        
        // Update recent searches
        let recent = GLOBAL_STORE.getState().recentSearches;
        recent = [query, ...recent.filter(s => s !== query)].slice(0, 5);
        localStorage.setItem('recentSearches', JSON.stringify(recent));

        GLOBAL_STORE.setState({ 
            searchResults: results.results || [], 
            isSearching: false,
            recentSearches: recent
        });
    } catch (error) {
        console.error('Search failed:', error);
        GLOBAL_STORE.setState({ isSearching: false });
    }
}
