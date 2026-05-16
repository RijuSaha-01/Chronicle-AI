/**
 * Performance Utilities - Debounce, Throttle, Lazy Loading
 */

/**
 * Debounce function to limit the rate at which a function can fire.
 */
export const debounce = (func, wait) => {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
};

/**
 * Lazy Load Images using IntersectionObserver
 */
export const initLazyLoading = () => {
    const imageObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                if (img.dataset.src) {
                    img.src = img.dataset.src;
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            }
        });
    }, {
        rootMargin: '50px 0px',
        threshold: 0.01
    });

    return {
        observe: (element) => imageObserver.observe(element),
        refresh: () => {
            const imgs = document.querySelectorAll('img[data-src]:not(.loaded)');
            imgs.forEach(img => imageObserver.observe(img));
        }
    };
};

export const LazyLoader = initLazyLoading();
