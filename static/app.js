/**
 * Chronicle AI - Frontend Controller
 * Version 3.0 - Production Ready
 */

// =============================================================================
// STATE & CONFIGURATION
// =============================================================================

const APP_STATE = {
    currentView: 'episodes',
    currentMode: 'quick',
    isLoading: false
};

// =============================================================================
// DOM REFERENCES (Safely acquired)
// =============================================================================

const DOM = {
    // Navigation
    navLinks: document.querySelectorAll('.nav-link'),
    aiStatus: document.getElementById('ai-status'),

    // Views
    viewEpisodes: document.getElementById('view-episodes'),
    viewCreate: document.getElementById('view-create'),

    // Episodes
    episodesContainer: document.getElementById('episodes-container'),
    btnRefresh: document.getElementById('btn-refresh'),

    // Mode selector
    modeBtns: document.querySelectorAll('.mode-btn'),
    formQuick: document.getElementById('form-quick'),
    formGuided: document.getElementById('form-guided'),

    // Quick form
    inputQuickText: document.getElementById('input-quick-text'),
    inputQuickDate: document.getElementById('input-quick-date'),
    inputSkipAI: document.getElementById('input-skip-ai'),
    btnSubmitQuick: document.getElementById('btn-submit-quick'),

    // Guided form
    inputMorning: document.getElementById('input-morning'),
    inputAfternoon: document.getElementById('input-afternoon'),
    inputEvening: document.getElementById('input-evening'),
    inputThoughts: document.getElementById('input-thoughts'),
    inputMood: document.getElementById('input-mood'),
    inputGuidedDate: document.getElementById('input-guided-date'),
    btnSubmitGuided: document.getElementById('btn-submit-guided'),

    // Modal
    modal: document.getElementById('modal-episode'),
    modalBody: document.getElementById('modal-body'),
    modalClose: document.querySelector('.modal-close'),
    modalOverlay: document.querySelector('.modal-overlay'),

    // Toast
    toastContainer: document.getElementById('toast-container')
};

// =============================================================================
// API LAYER
// =============================================================================

async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(endpoint, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({}));
            throw new Error(error.detail || `Request failed: ${response.status}`);
        }

        if (response.status === 204) {
            return null;
        }

        return await response.json();
    } catch (error) {
        console.error('API Error:', error);
        showToast(error.message || 'Network error', 'error');
        throw error;
    }
}

async function loadEpisodes(limit = 50) {
    return await apiCall(`/entries?limit=${limit}`);
}

async function getEpisode(id) {
    return await apiCall(`/entries/${id}`);
}

async function createQuickEntry(data) {
    return await apiCall('/entries', {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function createGuidedEntry(data) {
    return await apiCall('/entries/guided', {
        method: 'POST',
        body: JSON.stringify(data)
    });
}

async function regenerateEpisode(id) {
    return await apiCall(`/entries/${id}/regenerate`, {
        method: 'POST'
    });
}

async function exportEpisode(id) {
    return await apiCall(`/export/${id}`, {
        method: 'POST'
    });
}

async function checkAIStatus() {
    try {
        const health = await apiCall('/health');
        return health?.ollama_available || false;
    } catch {
        return false;
    }
}

// =============================================================================
// VIEW MANAGEMENT
// =============================================================================

function switchView(viewName) {
    if (APP_STATE.isLoading) return;

    APP_STATE.currentView = viewName;

    // Update nav active state
    DOM.navLinks.forEach(link => {
        const isActive = link.dataset.view === viewName;
        link.classList.toggle('active', isActive);
    });

    // Show/hide views
    if (DOM.viewEpisodes) {
        DOM.viewEpisodes.classList.toggle('active', viewName === 'episodes');
    }
    if (DOM.viewCreate) {
        DOM.viewCreate.classList.toggle('active', viewName === 'create');
    }

    // Load data if needed
    if (viewName === 'episodes') {
        loadAndRenderEpisodes();
    }
}

function switchMode(modeName) {
    APP_STATE.currentMode = modeName;

    DOM.modeBtns.forEach(btn => {
        const isActive = btn.dataset.mode === modeName;
        btn.classList.toggle('active', isActive);
    });

    if (DOM.formQuick) {
        DOM.formQuick.classList.toggle('active', modeName === 'quick');
    }
    if (DOM.formGuided) {
        DOM.formGuided.classList.toggle('active', modeName === 'guided');
    }
}

// =============================================================================
// EPISODES RENDERING
// =============================================================================

async function loadAndRenderEpisodes() {
    if (!DOM.episodesContainer) return;

    // Show loading
    DOM.episodesContainer.innerHTML = `
        <div class="empty-state">
            <h3>Loading episodes...</h3>
        </div>
    `;

    try {
        const data = await loadEpisodes();
        renderEpisodes(data.entries || []);
    } catch (error) {
        DOM.episodesContainer.innerHTML = `
            <div class="empty-state">
                <h3>Failed to load episodes</h3>
                <p>${escapeHtml(error.message)}</p>
            </div>
        `;
    }
}

function renderEpisodes(episodes) {
    if (!DOM.episodesContainer) return;

    if (!episodes || episodes.length === 0) {
        DOM.episodesContainer.innerHTML = `
            <div class="empty-state">
                <h3>✨ Your story starts here</h3>
                <p>Create your first episode to begin your Chronicle</p>
            </div>
        `;
        return;
    }

    const html = episodes.map(episode => {
        const title = escapeHtml(episode.title || 'Untitled Episode');
        const preview = escapeHtml(episode.narrative_text || episode.raw_text || 'No content');
        const date = formatDate(episode.date);

        return `
            <article class="episode-card" onclick="handleEpisodeClick(${episode.id})">
                <div class="episode-meta">
                    <span>📅 ${date}</span>
                </div>
                <h3 class="episode-title">${title}</h3>
                <p class="episode-preview">${preview}</p>
            </article>
        `;
    }).join('');

    DOM.episodesContainer.innerHTML = html;
}

// =============================================================================
// MODAL MANAGEMENT
// =============================================================================

async function openEpisodeModal(episodeId) {
    if (!DOM.modal || !DOM.modalBody) return;

    DOM.modal.classList.add('active');
    DOM.modalBody.innerHTML = '<p style="text-align:center;padding:3rem;">Loading...</p>';

    try {
        const episode = await getEpisode(episodeId);
        renderEpisodeModal(episode);
    } catch (error) {
        DOM.modalBody.innerHTML = `
            <div style="text-align:center;padding:3rem;">
                <h3>Failed to load episode</h3>
                <p style="color:var(--text-secondary);margin-top:1rem;">${escapeHtml(error.message)}</p>
            </div>
        `;
    }
}

function renderEpisodeModal(episode) {
    if (!DOM.modalBody) return;

    const title = escapeHtml(episode.title || 'Untitled Episode');
    const narrative = escapeHtml(episode.narrative_text || 'No AI-generated narrative yet.');
    const rawText = escapeHtml(episode.raw_text || '');
    const date = formatDate(episode.date);

    DOM.modalBody.innerHTML = `
        <div class="modal-episode-meta">📅 ${date} • ID: ${episode.id}</div>
        <h2 class="modal-episode-title">${title}</h2>
        <p class="modal-narrative">"${narrative}"</p>
        
        <div class="modal-section">
            <h4>Original Entry</h4>
            <div class="modal-raw-text">${rawText}</div>
        </div>
        
        <div class="modal-actions">
            <button class="btn-secondary" onclick="handleRegenerate(${episode.id})">
                🔄 Regenerate Narrative
            </button>
            <button class="btn-secondary" onclick="handleExport(${episode.id})">
                📥 Export Markdown
            </button>
        </div>
    `;
}

function closeModal() {
    if (DOM.modal) {
        DOM.modal.classList.remove('active');
    }
}

// =============================================================================
// FORM HANDLERS
// =============================================================================

async function handleQuickSubmit(event) {
    event.preventDefault();

    if (APP_STATE.isLoading || !DOM.inputQuickText || !DOM.btnSubmitQuick) return;

    const rawText = DOM.inputQuickText.value.trim();
    if (!rawText) {
        showToast('Please write something first', 'error');
        return;
    }

    const data = {
        raw_text: rawText,
        date: DOM.inputQuickDate?.value || null,
        skip_ai: DOM.inputSkipAI?.checked || false
    };

    setButtonLoading(DOM.btnSubmitQuick, true);
    APP_STATE.isLoading = true;

    try {
        await createQuickEntry(data);
        showToast('Episode created successfully!', 'success');

        // Reset form
        if (DOM.inputQuickText) DOM.inputQuickText.value = '';
        if (DOM.inputSkipAI) DOM.inputSkipAI.checked = false;

        // Switch to episodes view
        setTimeout(() => switchView('episodes'), 500);
    } catch (error) {
        // Error already shown by apiCall
    } finally {
        setButtonLoading(DOM.btnSubmitQuick, false);
        APP_STATE.isLoading = false;
    }
}

async function handleGuidedSubmit(event) {
    event.preventDefault();

    if (APP_STATE.isLoading || !DOM.btnSubmitGuided) return;

    const data = {
        morning: DOM.inputMorning?.value || null,
        afternoon: DOM.inputAfternoon?.value || null,
        evening: DOM.inputEvening?.value || null,
        thoughts: DOM.inputThoughts?.value || null,
        mood: DOM.inputMood?.value || null,
        date: DOM.inputGuidedDate?.value || null
    };

    // Check if at least one field is filled
    const hasContent = Object.values(data).some(val => val && val.trim());
    if (!hasContent) {
        showToast('Please fill in at least one field', 'error');
        return;
    }

    setButtonLoading(DOM.btnSubmitGuided, true);
    APP_STATE.isLoading = true;

    try {
        await createGuidedEntry(data);
        showToast('Guided entry created!', 'success');

        // Reset form
        if (DOM.inputMorning) DOM.inputMorning.value = '';
        if (DOM.inputAfternoon) DOM.inputAfternoon.value = '';
        if (DOM.inputEvening) DOM.inputEvening.value = '';
        if (DOM.inputThoughts) DOM.inputThoughts.value = '';
        if (DOM.inputMood) DOM.inputMood.value = '';

        // Switch to episodes view
        setTimeout(() => switchView('episodes'), 500);
    } catch (error) {
        // Error already shown by apiCall
    } finally {
        setButtonLoading(DOM.btnSubmitGuided, false);
        APP_STATE.isLoading = false;
    }
}

// =============================================================================
// ACTION HANDLERS (Called from HTML)
// =============================================================================

window.handleEpisodeClick = function (episodeId) {
    openEpisodeModal(episodeId);
};

window.handleRegenerate = async function (episodeId) {
    showToast('Regenerating narrative...', 'success');
    try {
        await regenerateEpisode(episodeId);
        showToast('Narrative regenerated!', 'success');
        // Refresh modal and list
        await openEpisodeModal(episodeId);
        if (APP_STATE.currentView === 'episodes') {
            loadAndRenderEpisodes();
        }
    } catch (error) {
        // Error already shown
    }
};

window.handleExport = async function (episodeId) {
    try {
        const result = await exportEpisode(episodeId);
        showToast(`Exported to ${result.filepath || 'exports/'}`, 'success');
    } catch (error) {
        // Error already shown
    }
};

// =============================================================================
// UI UTILITIES
// =============================================================================

function setButtonLoading(button, isLoading) {
    if (!button) return;

    const content = button.querySelector('.btn-content');
    const loader = button.querySelector('.btn-loader');

    button.disabled = isLoading;

    if (content) content.hidden = isLoading;
    if (loader) loader.hidden = !isLoading;
}

function showToast(message, type = 'success') {
    if (!DOM.toastContainer) return;

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.textContent = message;

    DOM.toastContainer.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

function updateAIStatus(isOnline) {
    if (!DOM.aiStatus) return;

    DOM.aiStatus.classList.remove('online', 'offline', 'checking');
    DOM.aiStatus.classList.add(isOnline ? 'online' : 'offline');
}

// =============================================================================
// UTILITIES
// =============================================================================

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatDate(dateString) {
    if (!dateString) return 'Unknown Date';

    try {
        const date = new Date(dateString);
        return date.toLocaleDateString('en-US', {
            month: 'short',
            day: 'numeric',
            year: 'numeric'
        });
    } catch {
        return dateString;
    }
}

function setDefaultDates() {
    const today = new Date().toISOString().split('T')[0];

    if (DOM.inputQuickDate) {
        DOM.inputQuickDate.value = today;
    }
    if (DOM.inputGuidedDate) {
        DOM.inputGuidedDate.value = today;
    }
}

// =============================================================================
// EVENT LISTENERS SETUP
// =============================================================================

function setupEventListeners() {
    // Navigation
    DOM.navLinks.forEach(link => {
        link.addEventListener('click', () => {
            const view = link.dataset.view;
            if (view) switchView(view);
        });
    });

    // Mode selector
    DOM.modeBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const mode = btn.dataset.mode;
            if (mode) switchMode(mode);
        });
    });

    // Refresh button
    if (DOM.btnRefresh) {
        DOM.btnRefresh.addEventListener('click', loadAndRenderEpisodes);
    }

    // Form submissions
    if (DOM.formQuick) {
        const form = DOM.formQuick.querySelector('form');
        if (form) form.addEventListener('submit', handleQuickSubmit);
    }

    if (DOM.formGuided) {
        const form = DOM.formGuided.querySelector('form');
        if (form) form.addEventListener('submit', handleGuidedSubmit);
    }

    // Modal close
    if (DOM.modalClose) {
        DOM.modalClose.addEventListener('click', closeModal);
    }
    if (DOM.modalOverlay) {
        DOM.modalOverlay.addEventListener('click', closeModal);
    }

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
            closeModal();
        }
    });
}

// =============================================================================
// INITIALIZATION
// =============================================================================

async function initialize() {
    console.log('Chronicle AI - Initializing...');

    // Set default dates
    setDefaultDates();

    // Setup all event listeners
    setupEventListeners();

    // Check AI status
    const isAIOnline = await checkAIStatus();
    updateAIStatus(isAIOnline);

    // Set up periodic AI status check
    setInterval(async () => {
        const status = await checkAIStatus();
        updateAIStatus(status);
    }, 30000); // Check every 30 seconds

    // Load initial view
    switchView('episodes');

    console.log('Chronicle AI - Ready!');
}

// Start the application when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initialize);
} else {
    initialize();
}
