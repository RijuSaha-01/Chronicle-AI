/**
 * LoadingState Component - Skeleton Shimmers
 */

export const LoadingState = () => {
    const container = document.createElement('div');
    container.className = 'netflix-row';
    
    container.innerHTML = `
        <h2 class="row-title shimmer" style="width: 200px; height: 30px; margin-bottom: 2rem;"></h2>
        <div class="carousel-track">
            ${Array(6).fill(0).map(() => `
                <div class="skeleton-card">
                    <div class="skeleton-img shimmer"></div>
                    <div class="skeleton-title shimmer"></div>
                </div>
            `).join('')}
        </div>
    `;

    return container;
};
