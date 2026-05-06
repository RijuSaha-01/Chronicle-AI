/**
 * ChatView - Conversational Memory Chat (ChatGPT-style)
 */
import API from '../services/api.js';
import GLOBAL_STORE from '../services/store.js';

export const ChatView = (onEpisodeClick) => {
    const container = document.createElement('div');
    container.className = 'netflix-chat-container';

    let activeSessionId = null;
    let chatSessions = [];

    // Main layout
    container.innerHTML = `
        <!-- Sidebar for past sessions -->
        <aside class="chat-sidebar">
            <div class="sidebar-header">
                <button class="btn-new-chat" id="new-chat-btn">
                    <span>➕</span>
                    <span>New Chat</span>
                </button>
            </div>
            <div class="chat-sessions-list" id="sessions-list">
                <!-- Injected dynamically -->
            </div>
        </aside>

        <!-- Main Chat Panel -->
        <main class="chat-main">
            <!-- Header -->
            <header class="chat-header">
                <div class="chat-header-title" id="chat-title">New Chat</div>
            </header>

            <!-- Message List -->
            <div class="chat-messages" id="chat-messages-container">
                <!-- Welcome/Starter state or Message bubbles -->
            </div>

            <!-- Input area -->
            <div class="chat-input-container">
                <div class="chat-input-wrapper">
                    <textarea 
                        class="chat-textarea" 
                        id="chat-textarea" 
                        placeholder="Ask Chronicle AI about your history (e.g. 'How has my mood been lately?')" 
                        rows="1"
                    ></textarea>
                    <button class="btn-send-chat" id="send-chat-btn" disabled>
                        <span>➔</span>
                    </button>
                </div>
            </div>
        </main>
    `;

    const sessionsList = container.querySelector('#sessions-list');
    const chatTitle = container.querySelector('#chat-title');
    const messagesContainer = container.querySelector('#chat-messages-container');
    const textarea = container.querySelector('#chat-textarea');
    const sendBtn = container.querySelector('#send-chat-btn');
    const newChatBtn = container.querySelector('#new-chat-btn');

    // Enable/disable send button based on input
    textarea.addEventListener('input', () => {
        textarea.style.height = 'auto';
        textarea.style.height = `${Math.min(textarea.scrollHeight, 120)}px`;
        sendBtn.disabled = textarea.value.trim().length === 0;
    });

    textarea.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (textarea.value.trim().length > 0) {
                sendMessage();
            }
        }
    });

    sendBtn.onclick = () => sendMessage();
    newChatBtn.onclick = () => startNewChat();

    // Load Chat Sessions list on mount
    async function loadSessions() {
        try {
            chatSessions = await API.getChatSessions();
            renderSessions();
        } catch (error) {
            console.error('Failed to load chat sessions:', error);
        }
    }

    function renderSessions() {
        if (chatSessions.length === 0) {
            sessionsList.innerHTML = `
                <div style="text-align: center; color: var(--text-tertiary); font-size: 0.8rem; margin-top: 2rem;">
                    No past chats
                </div>
            `;
            return;
        }

        sessionsList.innerHTML = chatSessions.map(session => `
            <div class="chat-session-item ${session.id === activeSessionId ? 'active' : ''}" data-id="${session.id}">
                <span class="session-title-text" title="${session.title}">${session.title}</span>
                <button class="btn-delete-session" data-id="${session.id}" title="Delete Chat">
                    🗑️
                </button>
            </div>
        `).join('');

        // Attach click handlers
        sessionsList.querySelectorAll('.chat-session-item').forEach(item => {
            item.onclick = (e) => {
                // If clicked on delete button, do not switch session
                if (e.target.closest('.btn-delete-session')) return;
                
                const sessionId = parseInt(item.dataset.id);
                loadSession(sessionId);
            };
        });

        sessionsList.querySelectorAll('.btn-delete-session').forEach(btn => {
            btn.onclick = async (e) => {
                e.stopPropagation();
                if (confirm('Are you sure you want to delete this chat session?')) {
                    const id = parseInt(btn.dataset.id);
                    await deleteSession(id);
                }
            };
        });
    }

    async function deleteSession(id) {
        try {
            await API.deleteChatSession(id);
            if (activeSessionId === id) {
                startNewChat();
            }
            await loadSessions();
        } catch (error) {
            console.error('Failed to delete chat session:', error);
        }
    }

    async function loadSession(sessionId) {
        activeSessionId = sessionId;
        renderSessions();
        messagesContainer.innerHTML = `
            <div style="display: flex; justify-content: center; align-items: center; height: 100%;">
                <div class="typing-indicator">
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                    <span class="typing-dot"></span>
                </div>
            </div>
        `;

        try {
            const session = await API.getChatSession(sessionId);
            chatTitle.textContent = session.title;
            
            if (!session.messages || session.messages.length === 0) {
                renderWelcomeState();
            } else {
                renderMessages(session.messages);
            }
        } catch (error) {
            console.error('Failed to load session details:', error);
            messagesContainer.innerHTML = `
                <div style="text-align: center; color: var(--netflix-red); padding: 2rem;">
                    Failed to load conversation history.
                </div>
            `;
        }
    }

    function startNewChat() {
        activeSessionId = null;
        chatTitle.textContent = 'New Chat';
        renderSessions();
        renderWelcomeState();
        textarea.value = '';
        textarea.style.height = 'auto';
        sendBtn.disabled = true;
        textarea.focus();
    }

    function renderWelcomeState() {
        messagesContainer.innerHTML = `
            <div class="chat-welcome">
                <div class="welcome-logo">🎬</div>
                <h1 class="welcome-title">Chronicle AI Companion</h1>
                <p class="welcome-subtitle">
                    I am your conversational memory engine. Ask me anything about your recorded history, emotional patterns, milestones, or previous adventures.
                </p>
                <div class="starters-grid">
                    <div class="starter-card" data-query="What was my most creative day this season?">
                        <div class="starter-card-title">💡 Highlights & Creativity</div>
                        <div class="starter-card-desc">"What was my most creative day this season?"</div>
                    </div>
                    <div class="starter-card" data-query="How has my fitness routine evolved?">
                        <div class="starter-card-title">🏃 Habits & Health</div>
                        <div class="starter-card-desc">"How has my fitness routine evolved?"</div>
                    </div>
                    <div class="starter-card" data-query="Summarize my career highlights from the past few months.">
                        <div class="starter-card-title">💼 Career & Growth</div>
                        <div class="starter-card-desc">"Summarize my career highlights from the past few months."</div>
                    </div>
                    <div class="starter-card" data-query="Tell me about a major conflict I overcame.">
                        <div class="starter-card-title">🔥 Overcoming Obstacles</div>
                        <div class="starter-card-desc">"Tell me about a major conflict I overcame."</div>
                    </div>
                </div>
            </div>
        `;

        // Attach starter questions click handlers
        messagesContainer.querySelectorAll('.starter-card').forEach(card => {
            card.onclick = () => {
                textarea.value = card.dataset.query;
                sendBtn.disabled = false;
                sendMessage();
            };
        });
    }

    function renderMessages(messages) {
        messagesContainer.innerHTML = '';
        messages.forEach(msg => {
            appendMessageBubble(msg.role, msg.content, []);
        });
        scrollToBottom();
    }

    function scrollToBottom() {
        setTimeout(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        }, 50);
    }

    // Markdown Parser
    function parseMarkdown(text) {
        if (!text) return '';
        
        let html = text
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;');

        // Code blocks: ```code```
        html = html.replace(/```([\s\S]+?)```/g, '<pre><code>$1</code></pre>');
        
        // Inline code: `code`
        html = html.replace(/`([^`]+?)`/g, '<code>$1</code>');

        // Bold: **text**
        html = html.replace(/\*\*([\s\S]+?)\*\*/g, '<strong>$1</strong>');

        // Italic: *text*
        html = html.replace(/\*([\s\S]+?)\*/g, '<em>$1</em>');

        // Blockquotes starting with >
        html = html.replace(/^\s*&gt;\s*([\s\S]+?)$/gm, '<blockquote>$1</blockquote>');

        // Newlines to <br> (but not inside pre or blockquote blocks)
        html = html.replace(/\n/g, '<br>');

        // Inline episode citations [Episode X: 'Title'] -> clickable link
        html = html.replace(/\[Episode\s+(\d+)(?::\s*['"]?([^'"]+?)['"]?)?\]/gi, (match, id, title) => {
            const displayTitle = title ? `Episode ${id}: '${title}'` : `Episode ${id}`;
            return `<a href="#" class="inline-citation" data-id="${id}" style="color: var(--gold-bright); font-weight: 600; text-decoration: underline;">${displayTitle}</a>`;
        });

        return html;
    }

    function appendMessageBubble(role, content, sources = []) {
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${role === 'user' ? 'user' : 'assistant'}`;

        const bubble = document.createElement('div');
        bubble.className = 'chat-bubble';
        
        // Parse markdown for assistant, plain text with simple formatting for user
        if (role === 'assistant') {
            bubble.innerHTML = parseMarkdown(content);
            
            // Render citation mini cards if sources exist
            if (sources && sources.length > 0) {
                const citationsWrapper = document.createElement('div');
                citationsWrapper.className = 'citations-wrapper';
                citationsWrapper.innerHTML = `<span class="citations-label">References</span>`;
                
                const containerEl = document.createElement('div');
                containerEl.className = 'citations-container';
                
                sources.forEach(src => {
                    const card = document.createElement('div');
                    card.className = 'citation-mini-card';
                    card.dataset.id = src.episode_id;
                    card.title = `Click to view Episode ${src.episode_id}: ${src.title || 'Details'}`;
                    card.innerHTML = `
                        <span class="citation-card-icon">🎬</span>
                        <span class="citation-card-title">Ep ${src.episode_id}: ${src.title || 'Untitled'}</span>
                    `;
                    containerEl.appendChild(card);
                });
                
                citationsWrapper.appendChild(containerEl);
                bubble.appendChild(citationsWrapper);
            }
        } else {
            bubble.textContent = content;
        }

        wrapper.appendChild(bubble);
        messagesContainer.appendChild(wrapper);

        // Attach click handlers for citations
        wrapper.querySelectorAll('.inline-citation, .citation-mini-card').forEach(el => {
            el.onclick = (e) => {
                e.preventDefault();
                const id = parseInt(el.dataset.id);
                if (id) onEpisodeClick(id);
            };
        });
    }

    async function sendMessage() {
        const text = textarea.value.trim();
        if (!text) return;

        // Clear input immediately
        textarea.value = '';
        textarea.style.height = 'auto';
        sendBtn.disabled = true;

        // If it was the welcome screen, clear it
        if (messagesContainer.querySelector('.chat-welcome')) {
            messagesContainer.innerHTML = '';
        }

        // 1. Append User Message Bubble
        appendMessageBubble('user', text);
        scrollToBottom();

        // 2. Show Typing Indicator
        const typingIndicator = document.createElement('div');
        typingIndicator.className = 'message-wrapper assistant';
        typingIndicator.id = 'typing-indicator-wrapper';
        typingIndicator.innerHTML = `
            <div class="typing-indicator">
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
                <span class="typing-dot"></span>
            </div>
        `;
        messagesContainer.appendChild(typingIndicator);
        scrollToBottom();

        try {
            // 3. Make API Call
            const response = await API.ask(text, activeSessionId);
            
            // Remove typing indicator
            const indicatorEl = messagesContainer.querySelector('#typing-indicator-wrapper');
            if (indicatorEl) indicatorEl.remove();

            // 4. Append AI Message Bubble with citations/sources
            appendMessageBubble('assistant', response.answer, response.sources);
            scrollToBottom();

            // Update active session ID if this was a new session
            if (!activeSessionId && response.session_id) {
                activeSessionId = response.session_id;
                // Reload session list to show updated title
                await loadSessions();
            } else {
                // Just reload sessions in case the title changed
                await loadSessions();
            }

            // Update active session header title
            const activeSession = chatSessions.find(s => s.id === activeSessionId);
            if (activeSession) {
                chatTitle.textContent = activeSession.title;
            }

        } catch (error) {
            console.error('Failed to get answer:', error);
            // Remove typing indicator
            const indicatorEl = messagesContainer.querySelector('#typing-indicator-wrapper');
            if (indicatorEl) indicatorEl.remove();

            appendMessageBubble('assistant', 'Sorry, I encountered an error while searching your memories. Please check your AI model availability and try again.');
            scrollToBottom();
        }
    }

    // Initialize View
    loadSessions();
    startNewChat();

    return container;
};
