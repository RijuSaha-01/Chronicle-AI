/**
 * EpisodeCard Component - Netflix Edition
 */

export const EpisodeCard = (episode, onClick) => {
    const title = episode.title || 'Untitled Episode';
    const synopsis = episode.synopsis || episode.narrative_text || 'No synopsis available';
    const duration = episode.audio_duration ? formatDuration(episode.audio_duration) : '12m';
    const mood = episode.mood || 'Neutral';
    
    // Process cover art path for URL
    let coverArt = 'https://images.unsplash.com/photo-1485846234645-a62644f84728?q=80&w=800&auto=format&fit=crop';
    if (episode.cover_art_path) {
        // Convert Windows backslashes to forward slashes and ensure it starts with /
        const path = episode.cover_art_path.replace(/\\/g, '/');
        coverArt = path.startsWith('/') ? path : `/${path}`;
    }
    
    // Mood color mapping
    const moodColors = {
        'Happy': '#46d369',
        'Sad': '#54a0ff',
        'Excited': '#ff9f43',
        'Anxious': '#ee5253',
        'Melancholic': '#5f27cd',
        'Romantic': '#ff9ff3',
        'Tense': '#feca57',
        'Neutral': '#c8d6e5',
        'Dramatic': '#d4af37',
        'Cinematic': '#d4af37'
    };
    const moodColor = moodColors[mood] || '#d4af37';

    const card = document.createElement('div');
    card.className = 'netflix-episode-card';
    card.tabIndex = 0; // Make focusable
    
    const progress = episode.playback_position && episode.audio_duration 
        ? (episode.playback_position / episode.audio_duration) * 100 
        : 0;

    card.innerHTML = `
        <div class="episode-card-thumbnail">
            <img src="${coverArt}" alt="${title}" loading="lazy" class="episode-img">
            <div class="episode-mood-accent" style="background: ${moodColor}"></div>
            <div class="episode-duration">${duration}</div>
            ${progress > 0 ? `
                <div class="episode-progress-container">
                    <div class="episode-progress-fill" style="width: ${progress}%"></div>
                </div>
            ` : ''}
            <div class="episode-overlay-bottom">
                <h3 class="episode-card-title">${title}</h3>
            </div>
        </div>
        <div class="episode-card-hover-content">
            <div class="hover-header">
                <span class="hover-match">98% Match</span>
                <span class="hover-mood" style="color: ${moodColor}">${mood}</span>
            </div>
            <p class="hover-synopsis">${synopsis}</p>
            <div class="hover-actions">
                <button class="hover-play-btn">▶</button>
                <span class="hover-title">${title}</span>
            </div>
        </div>
    `;

    card.addEventListener('click', (e) => {
        onClick(episode.id);
    });

    // Handle Enter key for keyboard navigation
    card.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') onClick(episode.id);
    });

    return card;
};

/**
 * Formats seconds into a human-readable duration (e.g., "12m")
 */
function formatDuration(seconds) {
    if (!seconds) return '12m';
    const mins = Math.max(1, Math.floor(seconds / 60));
    return `${mins}m`;
}
