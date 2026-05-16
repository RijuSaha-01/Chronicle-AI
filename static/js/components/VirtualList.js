/**
 * VirtualList Component - Performance for long lists
 */
export const VirtualList = (items, renderItem, options = {}) => {
    const { itemHeight = 120, containerHeight = 600 } = options;
    
    const container = document.createElement('div');
    container.className = 'virtual-list-container';
    container.style.height = `${containerHeight}px`;
    container.style.overflowY = 'auto';
    container.style.position = 'relative';

    const totalHeight = items.length * itemHeight;
    const spacer = document.createElement('div');
    spacer.style.height = `${totalHeight}px`;
    spacer.style.width = '100%';
    container.appendChild(spacer);

    const visibleItemsContainer = document.createElement('div');
    visibleItemsContainer.style.position = 'absolute';
    visibleItemsContainer.style.top = '0';
    visibleItemsContainer.style.left = '0';
    visibleItemsContainer.style.width = '100%';
    container.appendChild(visibleItemsContainer);

    let lastScrollTop = -1;

    const updateVisibleItems = () => {
        const scrollTop = container.scrollTop;
        if (Math.abs(scrollTop - lastScrollTop) < itemHeight / 2) return;
        lastScrollTop = scrollTop;

        const startIndex = Math.floor(scrollTop / itemHeight);
        const endIndex = Math.min(items.length - 1, Math.ceil((scrollTop + containerHeight) / itemHeight));

        // Buffer
        const buffer = 2;
        const bufferedStart = Math.max(0, startIndex - buffer);
        const bufferedEnd = Math.min(items.length - 1, endIndex + buffer);

        visibleItemsContainer.innerHTML = '';
        visibleItemsContainer.style.transform = `translateY(${bufferedStart * itemHeight}px)`;

        for (let i = bufferedStart; i <= bufferedEnd; i++) {
            const itemEl = renderItem(items[i]);
            itemEl.style.height = `${itemHeight}px`;
            itemEl.style.boxSizing = 'border-box';
            visibleItemsContainer.appendChild(itemEl);
        }
    };

    container.addEventListener('scroll', updateVisibleItems);
    
    // Initial render
    setTimeout(updateVisibleItems, 0);

    return container;
};
