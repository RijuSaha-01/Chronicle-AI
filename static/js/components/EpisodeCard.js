/**
 * EpisodeCard Component
 */

export const EpisodeCard = (episode, onClick) => {
    const title = episode.title || 'Untitled Episode';
    const preview = episode.narrative_text || episode.raw_text || 'No content available';
    const date = new Date(episode.date).toLocaleDateString('en-US', {
        month: 'short',
        day: 'numeric'
    });

    const card = document.createElement('div');
    card.className = 'netflix-card';
    card.innerHTML = `
        <div class="card-inner">
            <div class="card-media">
                <div class="card-overlay">
                    <button class="play-btn">▶</button>
                </div>
                <div class="card-date">${date}</div>
            </div>
            <div class="card-info">
                <div class="card-meta">
                    <span class="match-score">98% Match</span>
                    <span class="content-rating">HD</span>
                    <span class="duration">12m</span>
                </div>
                <h3 class="card-title">${title}</h3>
                <p class="card-description">${preview}</p>
                <div class="card-tags">
                    <span>Authentic</span>
                    <span>•</span>
                    <span>Cinematic</span>
                </div>
            </div>
        </div>
    `;

    card.addEventListener('click', () => onClick(episode.id));

    return card;
};
