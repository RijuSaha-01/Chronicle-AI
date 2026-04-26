/**
 * LoadingState Component - Skeleton Shimmers
 */

export const LoadingState = () => {
    const container = document.createElement('div');
    container.className = 'netflix-row';
    
    container.innerHTML = `
        <h2 class="row-title shimmer" style="width: 200px; height: 30px; margin-bottom: 2rem;"></h2>
        <div class="carousel-track">
            ${Array(5).fill(0).map(() => `
                <div class="netflix-card shimmer" style="min-width: 280px; height: 160px;"></div>
            `).join('')}
        </div>
    `;

    return container;
};
