/**
 * SettingsView - Chronicle AI Settings & Preferences Page
 */
import API from '../services/api.js';

export const SettingsView = () => {
    const container = document.createElement('div');
    container.className = 'settings-view-container';

    // State for local settings before saving
    let localSettings = {
        tone_preference: 'cinematic',
        protagonist_name: 'Protagonist',
        visual_style: 'cinematic',
        voice_profile: 'STORYTELLER',
        playback_speed: 1.0,
        data_location: 'data'
    };

    let storageStats = {
        total_size_mb: 0,
        file_count: 0,
        base_path: 'data/images'
    };

    let serviceStatus = {
        ollama: false,
        stable_diffusion: false,
        tts: false
    };

    // Style presets for the VISUALS section with high-quality descriptions and previews
    const stylePresets = [
        {
            id: 'cinematic',
            name: 'Cinematic Noir',
            desc: 'High contrast, moody lighting, deep shadows, and cinematic framing.',
            colors: ['#000000', '#1F1F1F', '#E50914', '#FFFFFF'],
            camera: 'Tracking low-angle shot',
            lighting: 'Moody noir shadows'
        },
        {
            id: 'gold',
            name: 'Hollywood Gold',
            desc: 'Warm golden hour colors, rich sun-kissed textures, and luxury appeal.',
            colors: ['#141414', '#2B2315', '#C29B38', '#F5F5F7'],
            camera: 'Wide anamorphic shot',
            lighting: 'Golden hour warmth'
        },
        {
            id: 'vibrant',
            name: 'Neon Cyberpunk',
            desc: 'Saturated neon blues and purples, glossy textures, futuristic cyberpunk essence.',
            colors: ['#0A051B', '#1B0933', '#00F0FF', '#FF007A'],
            camera: 'Close-up handheld cam',
            lighting: 'Vibrant neon glow'
        },
        {
            id: 'classic',
            name: 'Warm Documentary',
            desc: 'Soft natural light, quiet tones, nostalgic feel, realistic and reflective.',
            colors: ['#1C1A17', '#322E2B', '#D2B48C', '#EAE0D5'],
            camera: 'Static long shot',
            lighting: 'Soft candlelight and sunshine'
        }
    ];

    const showToast = (msg, type = 'success') => {
        const toastContainer = document.getElementById('toast-container');
        if (toastContainer) {
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            toast.textContent = msg;
            toastContainer.appendChild(toast);
            setTimeout(() => toast.remove(), 4000);
        }
    };

    const render = () => {
        container.innerHTML = `
            <div class="settings-hero">
                <div class="settings-hero-content">
                    <span class="settings-badge">⚙️ PROFILE & UTILITIES</span>
                    <h1 class="settings-title">Settings & Preferences</h1>
                    <p class="settings-subtitle">Customize your cinematic AI generator, visual style layouts, audio narrator voices, and manage system databases.</p>
                </div>
            </div>

            <div class="settings-layout-grid">
                <!-- LEFT PANEL: NAVLINKS -->
                <div class="settings-sidebar">
                    <div class="settings-nav-card">
                        <button class="settings-nav-btn active" data-target="narrative-sec">✍️ Narrative Tone</button>
                        <button class="settings-nav-btn" data-target="visuals-sec">🎬 Visual Presets</button>
                        <button class="settings-nav-btn" data-target="audio-sec">🎙️ Audio & Voice</button>
                        <button class="settings-nav-btn" data-target="system-sec">🖥️ System Services</button>
                        <button class="settings-nav-btn" data-target="storage-sec">💾 Storage Statistics</button>
                        <button class="settings-nav-btn text-danger" data-target="privacy-sec">🔒 Privacy & Reset</button>
                    </div>
                    <button class="btn-netflix primary btn-save-all-floating">💾 Save All Preferences</button>
                </div>

                <!-- RIGHT PANEL: CONTENT SECTIONS -->
                <div class="settings-main-content">
                    
                    <!-- NARRATIVE SECTION -->
                    <section id="narrative-sec" class="settings-card active-section">
                        <div class="settings-card-header">
                            <h3>Narrative Customization</h3>
                            <p>Tweak the personality, tone, and character details of generated life stories.</p>
                        </div>
                        <div class="settings-card-body">
                            <div class="form-group-netflix">
                                <label for="protagonist_name">Protagonist Name</label>
                                <input type="text" id="protagonist_name" value="${localSettings.protagonist_name}" placeholder="e.g. Alex, Jordan">
                                <small>The primary third-person name used for generated narrative chapters.</small>
                            </div>
                            <div class="form-group-netflix">
                                <label for="tone_preference">Tone & Writing Preference</label>
                                <select id="tone_preference">
                                    <option value="cinematic" ${localSettings.tone_preference === 'cinematic' ? 'selected' : ''}>Cinematic Prose (Dramatic & Immersive)</option>
                                    <option value="documentary" ${localSettings.tone_preference === 'documentary' ? 'selected' : ''}>Documentary Logbook (Factual & Objective)</option>
                                    <option value="theatrical" ${localSettings.tone_preference === 'theatrical' ? 'selected' : ''}>Theatrical Screenplay (Heavy Dialogue & Actions)</option>
                                    <option value="creative" ${localSettings.tone_preference === 'creative' ? 'selected' : ''}>Poetic / Creative (Deep Metaphors & Sensory)</option>
                                    <option value="casual" ${localSettings.tone_preference === 'casual' ? 'selected' : ''}>Casual & Intimate (Modern First/Third Diary style)</option>
                                </select>
                                <small>Alters how Ollama translates your daily events into episodic chapters.</small>
                            </div>
                        </div>
                    </section>

                    <!-- VISUALS SECTION -->
                    <section id="visuals-sec" class="settings-card">
                        <div class="settings-card-header">
                            <h3>Visual Style Presets</h3>
                            <p>Select your default artwork style. This drives the Stable Diffusion visual parameters.</p>
                        </div>
                        <div class="settings-card-body">
                            <div class="style-presets-grid">
                                ${stylePresets.map(preset => `
                                    <div class="preset-card ${localSettings.visual_style === preset.id ? 'active' : ''}" data-preset-id="${preset.id}">
                                        <div class="preset-color-row">
                                            ${preset.colors.map(col => `<span class="color-dot" style="background-color: ${col}"></span>`).join('')}
                                        </div>
                                        <h4 class="preset-name">${preset.name}</h4>
                                        <p class="preset-desc">${preset.desc}</p>
                                        <div class="preset-meta">
                                            <span>📷 ${preset.camera}</span><br/>
                                            <span>💡 ${preset.lighting}</span>
                                        </div>
                                    </div>
                                `).join('')}
                            </div>
                        </div>
                    </section>

                    <!-- AUDIO SECTION -->
                    <section id="audio-sec" class="settings-card">
                        <div class="settings-card-header">
                            <h3>Audio & Voice Preferences</h3>
                            <p>Configure narration settings, voice profiles, and speech pacing.</p>
                        </div>
                        <div class="settings-card-body">
                            <div class="form-group-netflix">
                                <label for="voice_profile">Narrator Voice Profile</label>
                                <div class="voice-picker-wrapper">
                                    <select id="voice_profile">
                                        <option value="STORYTELLER" ${localSettings.voice_profile === 'STORYTELLER' ? 'selected' : ''}>Abrahan Mack (Warm, Audiobook Storyteller)</option>
                                        <option value="DRAMATIC" ${localSettings.voice_profile === 'DRAMATIC' ? 'selected' : ''}>Baldur Valur (Intense, Theatrical Drama)</option>
                                        <option value="CALM" ${localSettings.voice_profile === 'CALM' ? 'selected' : ''}>Asya Arafat (Soothing, Nature/Calm Documentary)</option>
                                        <option value="NOIR" ${localSettings.voice_profile === 'NOIR' ? 'selected' : ''}>Noir Sleuth (Deep, Mysterious, Low-pitch)</option>
                                    </select>
                                    <button class="btn-netflix secondary btn-preview-voice">🔊 Play Voice Sample</button>
                                </div>
                                <small>Uses Coqui XTTS cloned/synthetic voice models to narrate episodes.</small>
                            </div>
                            <div class="form-group-netflix">
                                <label for="playback_speed">Narrator Speed Pacing (<span id="speed-val">${localSettings.playback_speed}</span>x)</label>
                                <input type="range" id="playback_speed" min="0.5" max="2.0" step="0.05" value="${localSettings.playback_speed}">
                                <div class="range-labels">
                                    <span>0.5x (Slow)</span>
                                    <span>1.0x (Normal)</span>
                                    <span>2.0x (Fast)</span>
                                </div>
                            </div>
                        </div>
                    </section>

                    <!-- SYSTEM SECTION -->
                    <section id="system-sec" class="settings-card">
                        <div class="settings-card-header">
                            <h3>AI Service Status Indicators</h3>
                            <p>Real-time network and API status of local generative intelligence models.</p>
                        </div>
                        <div class="settings-card-body">
                            <div class="services-status-list">
                                <div class="service-status-row">
                                    <div class="service-info">
                                        <span class="service-icon">🧠</span>
                                        <div>
                                            <h4 class="service-title">Ollama (Llama 3.2 Narrative Engine)</h4>
                                            <p class="service-desc">Generates cinematic narratives, loglines, synopses, conflict, and titles locally.</p>
                                        </div>
                                    </div>
                                    <div class="service-badge-wrapper">
                                        <span class="status-indicator-badge ${serviceStatus.ollama ? 'online' : 'offline'}">
                                            <span class="status-dot"></span>
                                            ${serviceStatus.ollama ? 'ONLINE' : 'OFFLINE'}
                                        </span>
                                    </div>
                                </div>

                                <div class="service-status-row">
                                    <div class="service-info">
                                        <span class="service-icon">🎨</span>
                                        <div>
                                            <h4 class="service-title">Stable Diffusion API (ComfyUI / A1111)</h4>
                                            <p class="service-desc">Renders gorgeous 16:9 cinematic covers and portrait poster artwork variants.</p>
                                        </div>
                                    </div>
                                    <div class="service-badge-wrapper">
                                        <span class="status-indicator-badge ${serviceStatus.stable_diffusion ? 'online' : 'offline'}">
                                            <span class="status-dot"></span>
                                            ${serviceStatus.stable_diffusion ? 'ONLINE' : 'OFFLINE'}
                                        </span>
                                    </div>
                                </div>

                                <div class="service-status-row">
                                    <div class="service-info">
                                        <span class="service-icon">🎙️</span>
                                        <div>
                                            <h4 class="service-title">Coqui XTTS v2 Narration Module</h4>
                                            <p class="service-desc">Transforms text narrative into emotional voice-over audio files.</p>
                                        </div>
                                    </div>
                                    <div class="service-badge-wrapper">
                                        <span class="status-indicator-badge ${serviceStatus.tts ? 'online' : 'offline'}">
                                            <span class="status-dot"></span>
                                            ${serviceStatus.tts ? 'ONLINE' : 'OFFLINE'}
                                        </span>
                                    </div>
                                </div>
                            </div>
                            <button class="btn-netflix secondary btn-refresh-services" style="margin-top: 1rem; width: 100%;">🔄 Refresh System Services</button>
                        </div>
                    </section>

                    <!-- STORAGE SECTION -->
                    <section id="storage-sec" class="settings-card">
                        <div class="settings-card-header">
                            <h3>Storage & Directories</h3>
                            <p>Review disk usage, cached files, and manage offline data directories.</p>
                        </div>
                        <div class="settings-card-body">
                            <div class="storage-metrics-grid">
                                <div class="storage-metric-card">
                                    <span class="metric-label">TOTAL SIZE ON DISK</span>
                                    <span class="metric-value">${storageStats.total_size_mb} MB</span>
                                </div>
                                <div class="storage-metric-card">
                                    <span class="metric-label">GENERATED MEDIA FILES</span>
                                    <span class="metric-value">${storageStats.file_count}</span>
                                </div>
                            </div>
                            <div class="form-group-netflix" style="margin-top: 1.5rem;">
                                <label>Base Data Directory Path</label>
                                <input type="text" value="${localSettings.data_location}" disabled class="disabled-path-input">
                                <small>SQLite database, logs, cover-art, and media exports directory.</small>
                            </div>
                            <div class="storage-actions-row">
                                <button class="btn-netflix secondary btn-export-zip">📦 Backup & Export Zip</button>
                            </div>
                        </div>
                    </section>

                    <!-- PRIVACY SECTION -->
                    <section id="privacy-sec" class="settings-card">
                        <div class="settings-card-header text-danger">
                            <h3>Danger Zone & Privacy</h3>
                            <p>Irreversibly delete database chapters or export raw copies of your entire episodic history.</p>
                        </div>
                        <div class="settings-card-body danger-zone-body">
                            <div class="privacy-row">
                                <div class="privacy-text">
                                    <h4>Export All Memories</h4>
                                    <p>Download a complete zip file containing the chronicle SQLite DB, audio wav files, and artwork.</p>
                                </div>
                                <button class="btn-netflix secondary btn-export-all-privacy">Export All Data</button>
                            </div>

                            <div class="privacy-row border-danger">
                                <div class="privacy-text">
                                    <h4 class="text-danger">Delete All Chronicle Records</h4>
                                    <p>Reset the application by completely erasing all diary entries, generated characters, seasons, and chat logs.</p>
                                </div>
                                <button class="btn-netflix primary btn-delete-all-danger">🚨 Reset Database</button>
                            </div>
                        </div>
                    </section>

                </div>
            </div>
        `;

        setupListeners();
    };

    const setupListeners = () => {
        // Sidebar tab switching
        const tabs = container.querySelectorAll('.settings-nav-btn');
        const sections = container.querySelectorAll('.settings-card');

        tabs.forEach(tab => {
            tab.onclick = () => {
                tabs.forEach(t => t.classList.remove('active'));
                sections.forEach(s => s.classList.remove('active-section'));

                tab.classList.add('active');
                const targetId = tab.dataset.target;
                container.querySelector(`#${targetId}`).classList.add('active-section');
            };
        });

        // Interactive Visual Preset cards selection
        const presetCards = container.querySelectorAll('.preset-card');
        presetCards.forEach(card => {
            card.onclick = () => {
                presetCards.forEach(c => c.classList.remove('active'));
                card.classList.add('active');
                localSettings.visual_style = card.dataset.presetId;
            };
        });

        // Speed pacing live slider text
        const speedSlider = container.querySelector('#playback_speed');
        const speedValSpan = container.querySelector('#speed-val');
        if (speedSlider && speedValSpan) {
            speedSlider.oninput = (e) => {
                localSettings.playback_speed = parseFloat(e.target.value);
                speedValSpan.textContent = e.target.value;
            };
        }

        // Save All Button clicked
        const saveFloatingBtn = container.querySelector('.btn-save-all-floating');
        if (saveFloatingBtn) {
            saveFloatingBtn.onclick = async () => {
                saveFloatingBtn.disabled = true;
                saveFloatingBtn.textContent = '💾 Saving...';

                const protagonistNameInput = container.querySelector('#protagonist_name');
                const tonePrefSelect = container.querySelector('#tone_preference');
                const voiceProfileSelect = container.querySelector('#voice_profile');

                if (protagonistNameInput) localSettings.protagonist_name = protagonistNameInput.value;
                if (tonePrefSelect) localSettings.tone_preference = tonePrefSelect.value;
                if (voiceProfileSelect) localSettings.voice_profile = voiceProfileSelect.value;

                try {
                    await API.updateSettings(localSettings);
                    showToast('Settings & Preferences saved successfully!');
                } catch (e) {
                    showToast(e.message || 'Failed to save settings', 'error');
                } finally {
                    saveFloatingBtn.disabled = false;
                    saveFloatingBtn.textContent = '💾 Save All Preferences';
                }
            };
        }

        // Voice Sample Audio Preview
        const previewVoiceBtn = container.querySelector('.btn-preview-voice');
        if (previewVoiceBtn) {
            previewVoiceBtn.onclick = () => {
                const voiceSelect = container.querySelector('#voice_profile');
                const voice = voiceSelect ? voiceSelect.value : 'STORYTELLER';
                showToast(`Generating & playing voice preview for ${voice}...`);
                
                // Let's speak sample using browser TTS or play an audio beep
                try {
                    const speech = new SpeechSynthesisUtterance();
                    speech.text = `Welcome to Chronicle A.I. This is a voice sample demonstrating the ${voice} profile narration.`;
                    speech.rate = localSettings.playback_speed || 1.0;
                    if (voice === 'CALM') speech.rate *= 0.85;
                    if (voice === 'DRAMATIC') speech.rate *= 1.1;
                    window.speechSynthesis.speak(speech);
                } catch (err) {
                    console.warn('Speech synthesis not fully supported:', err);
                }
            };
        }

        // Refresh Services Status
        const refreshServicesBtn = container.querySelector('.btn-refresh-services');
        if (refreshServicesBtn) {
            refreshServicesBtn.onclick = async () => {
                refreshServicesBtn.disabled = true;
                refreshServicesBtn.textContent = '🔄 Checking...';
                await loadServicesStatus();
                render();
                showToast('AI Service health status updated!');
            };
        }

        // Backup & Export Zip
        const exportZipBtn = container.querySelector('.btn-export-zip');
        const exportAllPrivacyBtn = container.querySelector('.btn-export-all-privacy');
        const handleExport = async (btn) => {
            btn.disabled = true;
            btn.textContent = '📦 Bundling backup...';
            try {
                const res = await API.exportAll();
                showToast(`Success! Backup created: ${res.filepath}`);
            } catch (err) {
                showToast(err.message || 'Export failed', 'error');
            } finally {
                btn.disabled = false;
                btn.textContent = '📦 Backup & Export Zip';
            }
        };

        if (exportZipBtn) exportZipBtn.onclick = () => handleExport(exportZipBtn);
        if (exportAllPrivacyBtn) exportAllPrivacyBtn.onclick = () => handleExport(exportAllPrivacyBtn);

        // Danger Zone DB Reset
        const resetBtn = container.querySelector('.btn-delete-all-danger');
        if (resetBtn) {
            resetBtn.onclick = async () => {
                const confirm1 = confirm('🚨 WARNING: You are about to clear the entire Chronicle database!\nThis deletes all daily memories, generated episode narratives, seasons, characters, and memory chats permanently.\n\nAre you absolutely sure you want to continue?');
                if (confirm1) {
                    const confirm2 = prompt('Type "DELETE ALL" to confirm deletion:');
                    if (confirm2 === 'DELETE ALL') {
                        resetBtn.disabled = true;
                        resetBtn.textContent = '🚨 Erasing Data...';
                        try {
                            await API.deleteAll();
                            showToast('Database reset complete. All entries deleted.', 'error');
                            // Refresh page
                            setTimeout(() => {
                                window.location.reload();
                            }, 2000);
                        } catch (err) {
                            showToast(err.message || 'Reset failed', 'error');
                            resetBtn.disabled = false;
                            resetBtn.textContent = '🚨 Reset Database';
                        }
                    } else {
                        showToast('Confirmation mismatch. Reset aborted.', 'error');
                    }
                }
            };
        }
    };

    const loadData = async () => {
        try {
            // Load Settings
            const setRes = await API.getSettings();
            if (setRes) {
                localSettings = {
                    tone_preference: setRes.tone_preference || 'cinematic',
                    protagonist_name: setRes.protagonist_name || 'Protagonist',
                    visual_style: setRes.visual_style || 'cinematic',
                    voice_profile: setRes.voice_profile || 'STORYTELLER',
                    playback_speed: parseFloat(setRes.playback_speed || 1.0),
                    data_location: setRes.data_location || 'data'
                };
            }
        } catch (e) {
            console.error('Failed to load settings:', e);
        }

        try {
            // Load Storage Stats
            const storRes = await API.getStorageUsage();
            if (storRes) {
                storageStats = {
                    total_size_mb: storRes.total_size_mb || 0,
                    file_count: storRes.file_count || 0,
                    base_path: storRes.base_path || 'data/images'
                };
            }
        } catch (e) {
            console.error('Failed to load storage usage:', e);
        }

        await loadServicesStatus();
        render();
    };

    const loadServicesStatus = async () => {
        try {
            const statRes = await API.getServicesStatus();
            if (statRes) {
                serviceStatus = {
                    ollama: statRes.ollama || false,
                    stable_diffusion: statRes.stable_diffusion || false,
                    tts: statRes.tts || false
                };
            }
        } catch (e) {
            console.error('Failed to check services status:', e);
        }
    };

    // Load initial data
    loadData();

    return container;
};
