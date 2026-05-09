/**
 * Chronicle AI - Theme & Appearance Manager
 */
import API from './api.js';

const DEFAULT_THEME_SETTINGS = {
    theme_mode: 'dark',
    accent_color: '#d4af37',
    font_size: 'medium',
    episode_card_size: 'comfortable',
    custom_css: ''
};

const ThemeManager = {
    getSettings() {
        try {
            const local = localStorage.getItem('theme_settings');
            if (local) {
                return { ...DEFAULT_THEME_SETTINGS, ...JSON.parse(local) };
            }
        } catch (e) {
            console.error('Failed to parse local theme settings:', e);
        }
        return { ...DEFAULT_THEME_SETTINGS };
    },

    apply(settings) {
        const body = document.body;
        const html = document.documentElement;

        // 1. Dark/Light Mode
        if (settings.theme_mode === 'light') {
            body.classList.add('theme-light');
        } else {
            body.classList.remove('theme-light');
        }

        // 2. Accent Color
        if (settings.accent_color) {
            html.style.setProperty('--gold-primary', settings.accent_color);
            // Derive subtle/bright variants
            html.style.setProperty('--gold-bright', settings.accent_color);
            html.style.setProperty('--gold-dark', settings.accent_color);
            html.style.setProperty('--border-subtle', `${settings.accent_color}25`);
            html.style.setProperty('--border-medium', `${settings.accent_color}50`);
            html.style.setProperty('--border-bright', `${settings.accent_color}90`);
            html.style.setProperty('--gradient-gold', `linear-gradient(135deg, ${settings.accent_color} 0%, ${settings.accent_color}dd 100%)`);
        }

        // 3. Font Size
        html.classList.remove('font-size-small', 'font-size-medium', 'font-size-large');
        html.classList.add(`font-size-${settings.font_size || 'medium'}`);

        // 4. Episode Card Size
        body.classList.remove('card-size-compact', 'card-size-comfortable');
        body.classList.add(`card-size-${settings.episode_card_size || 'comfortable'}`);

        // 5. Custom CSS Override
        let styleTag = document.getElementById('theme-custom-css-override');
        if (!styleTag) {
            styleTag = document.createElement('style');
            styleTag.id = 'theme-custom-css-override';
            document.head.appendChild(styleTag);
        }
        styleTag.textContent = settings.custom_css || '';
    },

    async init() {
        // Apply local settings first for instant/flicker-free load
        const localSettings = this.getSettings();
        this.apply(localSettings);

        // Fetch and sync with backend in the background
        try {
            const backendSettings = await API.getSettings();
            if (backendSettings) {
                const mergedSettings = {
                    theme_mode: backendSettings.theme_mode || localSettings.theme_mode,
                    accent_color: backendSettings.accent_color || localSettings.accent_color,
                    font_size: backendSettings.font_size || localSettings.font_size,
                    episode_card_size: backendSettings.episode_card_size || localSettings.episode_card_size,
                    custom_css: backendSettings.custom_css !== undefined ? backendSettings.custom_css : localSettings.custom_css
                };
                
                localStorage.setItem('theme_settings', JSON.stringify(mergedSettings));
                this.apply(mergedSettings);
                return mergedSettings;
            }
        } catch (err) {
            console.warn('Could not sync theme with backend on init:', err);
        }
        return localSettings;
    },

    async update(newSettings) {
        const current = this.getSettings();
        const merged = { ...current, ...newSettings };
        
        // Apply instantly
        this.apply(merged);

        // Save locally
        localStorage.setItem('theme_settings', JSON.stringify(merged));

        // Sync with backend
        try {
            await API.updateSettings(merged);
        } catch (err) {
            console.error('Failed to sync theme settings with backend:', err);
        }
    }
};

export default ThemeManager;
