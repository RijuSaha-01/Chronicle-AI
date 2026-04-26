/**
 * CreateView - Entry Creation
 */
import GLOBAL_STORE from '../services/store.js';

export const CreateView = (onSubmit) => {
    const container = document.createElement('div');
    container.className = 'view-container';
    
    // Using the same structure but as a dynamic component
    container.innerHTML = `
        <div class="view-header">
            <h1 class="view-title">Create Episode</h1>
            <p class="view-subtitle">Transform your day into a masterpiece</p>
        </div>

        <div class="mode-selector">
            <button class="mode-btn active" data-mode="quick">
                <span class="mode-icon">⚡</span>
                <span class="mode-label">Quick Entry</span>
                <span class="mode-desc">Fast capture for busy days</span>
            </button>
            <button class="mode-btn" data-mode="guided">
                <span class="mode-icon">🧭</span>
                <span class="mode-label">Guided Reflection</span>
                <span class="mode-desc">Structured daily review</span>
            </button>
        </div>

        <div id="create-form-container">
            <!-- Form will be injected here -->
        </div>
    `;

    const formContainer = container.querySelector('#create-form-container');
    
    const renderForm = (mode) => {
        if (mode === 'quick') {
            formContainer.innerHTML = `
                <div class="entry-form active">
                    <form class="form-card">
                        <div class="form-body">
                            <div class="form-group">
                                <label>What happened today?</label>
                                <textarea id="input-quick-text" rows="8" placeholder="Today was..." required></textarea>
                            </div>
                            <div class="form-row">
                                <div class="form-group">
                                    <label>Date</label>
                                    <input type="date" id="input-quick-date" value="${new Date().toISOString().split('T')[0]}">
                                </div>
                                <div class="form-group">
                                    <label class="checkbox-wrapper">
                                        <input type="checkbox" id="input-skip-ai">
                                        <span>Skip AI processing</span>
                                    </label>
                                </div>
                            </div>
                        </div>
                        <div class="form-footer">
                            <button type="submit" class="btn-primary">Generate Episode</button>
                        </div>
                    </form>
                </div>
            `;
        } else {
            formContainer.innerHTML = `
                <div class="entry-form active">
                    <form class="form-card">
                        <div class="form-body">
                            <div class="guided-sections">
                                <div class="guided-section"><label>🌅 Morning</label><textarea id="input-morning" rows="3"></textarea></div>
                                <div class="guided-section"><label>☀️ Afternoon</label><textarea id="input-afternoon" rows="3"></textarea></div>
                                <div class="guided-section"><label>🌙 Evening</label><textarea id="input-evening" rows="3"></textarea></div>
                                <div class="guided-section"><label>💭 Reflections</label><textarea id="input-thoughts" rows="3"></textarea></div>
                                <div class="guided-section compact"><label>😊 Mood</label><input type="text" id="input-mood"></div>
                                <div class="guided-section compact"><label>Date</label><input type="date" id="input-guided-date" value="${new Date().toISOString().split('T')[0]}"></div>
                            </div>
                        </div>
                        <div class="form-footer">
                            <button type="submit" class="btn-primary">Generate Episode</button>
                        </div>
                    </form>
                </div>
            `;
        }

        const form = formContainer.querySelector('form');
        form.onsubmit = (e) => {
            e.preventDefault();
            const formData = mode === 'quick' ? {
                mode: 'quick',
                raw_text: form.querySelector('#input-quick-text').value,
                date: form.querySelector('#input-quick-date').value,
                skip_ai: form.querySelector('#input-skip-ai').checked
            } : {
                mode: 'guided',
                morning: form.querySelector('#input-morning').value,
                afternoon: form.querySelector('#input-afternoon').value,
                evening: form.querySelector('#input-evening').value,
                thoughts: form.querySelector('#input-thoughts').value,
                mood: form.querySelector('#input-mood').value,
                date: form.querySelector('#input-guided-date').value
            };
            onSubmit(formData);
        };
    };

    renderForm('quick');

    container.querySelectorAll('.mode-btn').forEach(btn => {
        btn.onclick = () => {
            container.querySelectorAll('.mode-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            renderForm(btn.dataset.mode);
        };
    });

    return container;
};
