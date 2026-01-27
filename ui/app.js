// Configuration
const API_BASE_URL = 'http://localhost:5000';

// State
let isProcessing = false;
let conversationHistory = [];

// DOM Elements
const chatMessages = document.getElementById('chat-messages');
const userInput = document.getElementById('user-input');
const sendBtn = document.getElementById('send-btn');
const autoExecuteCheckbox = document.getElementById('auto-execute');
const serverStatus = document.getElementById('server-status');
const mongoStatus = document.getElementById('mongo-status');
const schemasStatus = document.getElementById('schemas-status');
const collectionsList = document.getElementById('collections-list');

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
});

async function initializeApp() {
    await checkServerHealth();
    await loadSchemas();
    await loadCollections();
}

function setupEventListeners() {
    // Send button click
    sendBtn.addEventListener('click', handleSendMessage);

    // Enter key to send (Shift+Enter for new line)
    userInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSendMessage();
        }
    });

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = userInput.scrollHeight + 'px';
        updateSendButton();
    });

    // Example query buttons
    document.querySelectorAll('.example-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            userInput.value = btn.dataset.query;
            userInput.focus();
            updateSendButton();
        });
    });

    // Sidebar toggle
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');

    // Load sidebar state
    const sidebarState = localStorage.getItem('sidebar-collapsed');
    if (sidebarState === 'true') {
        sidebar.classList.add('collapsed');
    }

    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebar-collapsed', sidebar.classList.contains('collapsed'));
    });

    updateSendButton();
}

function updateSendButton() {
    const hasText = userInput.value.trim().length > 0;
    sendBtn.disabled = !hasText || isProcessing;
}

async function checkServerHealth() {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();

        // Update server status
        updateStatus(serverStatus, 'connected', 'Connected');

        // Update MongoDB status
        if (data.mongodb === 'connected') {
            updateStatus(mongoStatus, 'connected', 'Connected');
        } else {
            updateStatus(mongoStatus, 'disconnected', 'Disconnected');
        }

        // Update schemas status
        if (data.schemas_loaded > 0) {
            updateStatus(schemasStatus, 'connected', `${data.schemas_loaded} loaded`);
        } else {
            updateStatus(schemasStatus, 'disconnected', 'None loaded');
        }
    } catch (error) {
        updateStatus(serverStatus, 'disconnected', 'Offline');
        updateStatus(mongoStatus, 'disconnected', 'Unknown');
        updateStatus(schemasStatus, 'disconnected', 'Unknown');
        console.error('Health check failed:', error);
    }
}

function updateStatus(element, status, text) {
    element.className = `status-indicator ${status}`;
    element.querySelector('.status-text').textContent = text;
}

async function loadSchemas() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/schemas`);
        const data = await response.json();

        if (data.success) {
            console.log('Schemas loaded:', Object.keys(data.schemas).length);
        }
    } catch (error) {
        console.error('Failed to load schemas:', error);
    }
}

async function loadCollections() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/schemas`);
        const data = await response.json();

        if (data.success && data.schemas) {
            displayCollections(data.schemas);
        }
    } catch (error) {
        console.error('Failed to load collections:', error);
        collectionsList.innerHTML = '<p style="color: var(--text-muted); font-size: 0.875rem;">Failed to load collections</p>';
    }
}

function displayCollections(schemas) {
    collectionsList.innerHTML = '';

    Object.values(schemas).forEach(schema => {
        const item = document.createElement('div');
        item.className = 'collection-item';
        item.innerHTML = `
            <div class="collection-name">${schema.collection}</div>
            <div class="collection-desc">${schema.description || 'No description'}</div>
        `;
        collectionsList.appendChild(item);
    });
}

async function handleSendMessage() {
    const text = userInput.value.trim();
    if (!text || isProcessing) return;

    // Clear input
    userInput.value = '';
    userInput.style.height = 'auto';
    updateSendButton();

    // Add user message
    addMessage('user', text);

    // Remove welcome message if present
    const welcomeMsg = document.querySelector('.welcome-message');
    if (welcomeMsg) {
        welcomeMsg.remove();
    }

    // Show typing indicator
    const typingId = addTypingIndicator();

    isProcessing = true;

    try {
        // Convert text to query
        const queryResult = await convertTextToQuery(text);

        // Remove typing indicator
        removeTypingIndicator(typingId);

        // Add assistant message with query
        addQueryMessage(queryResult);

        // Auto-execute if enabled
        if (autoExecuteCheckbox.checked) {
            await executeQuery(queryResult);
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        addErrorMessage(error.message);
    } finally {
        isProcessing = false;
        updateSendButton();
    }
}

async function convertTextToQuery(text) {
    const response = await fetch(`${API_BASE_URL}/api/convert`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({ text })
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to convert query');
    }

    return await response.json();
}

async function executeQuery(queryResult) {
    try {
        const response = await fetch(`${API_BASE_URL}/api/execute`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                collection: queryResult.collection,
                query: queryResult.query,
                query_type: queryResult.query_type
            })
        });

        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.error || 'Failed to execute query');
        }

        const results = await response.json();
        addResultsMessage(results);
    } catch (error) {
        addErrorMessage(`Execution failed: ${error.message}`);
    }
}

function addMessage(role, content) {
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = role === 'user'
        ? '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>'
        : '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = content;

    messageContent.appendChild(bubble);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addQueryMessage(queryResult) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = "I've generated a MongoDB query for you:";

    const queryDisplay = document.createElement('div');
    queryDisplay.className = 'query-display';
    queryDisplay.innerHTML = `
        <div class="query-header">
            <span class="query-label">Collection: ${queryResult.collection}</span>
            <span class="query-type">${queryResult.query_type.toUpperCase()}</span>
        </div>
        <div class="query-code">${JSON.stringify(queryResult.query, null, 2)}</div>
        <div class="query-explanation">${queryResult.explanation}</div>
        ${!autoExecuteCheckbox.checked ? `
            <div class="query-actions">
                <button class="action-btn" onclick="executeQueryFromButton(${JSON.stringify(queryResult).replace(/"/g, '&quot;')})">
                    Execute Query
                </button>
            </div>
        ` : ''}
    `;

    messageContent.appendChild(bubble);
    messageContent.appendChild(queryDisplay);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

// Make executeQueryFromButton available globally
window.executeQueryFromButton = async function (queryResult) {
    await executeQuery(queryResult);
};

function addResultsMessage(results) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.textContent = "Query executed successfully!";

    const resultsDisplay = document.createElement('div');
    resultsDisplay.className = 'results-display';

    if (results.query_type === 'count') {
        resultsDisplay.innerHTML = `
            <div class="results-header">
                <span class="results-count">Count: <strong>${results.count}</strong></span>
            </div>
        `;
    } else if (results.results && results.results.length > 0) {
        resultsDisplay.innerHTML = `
            <div class="results-header">
                <span class="results-count">Found <strong>${results.count}</strong> result(s)</span>
            </div>
            <div class="results-json">${JSON.stringify(results.results, null, 2)}</div>
        `;
    } else {
        resultsDisplay.innerHTML = `
            <div class="results-header">
                <span class="results-count">No results found</span>
            </div>
        `;
    }

    messageContent.appendChild(bubble);
    messageContent.appendChild(resultsDisplay);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addErrorMessage(errorText) {
    const messageDiv = document.createElement('div');
    messageDiv.className = 'message assistant';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = `<div class="error-message">❌ ${errorText}</div>`;

    messageContent.appendChild(bubble);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    chatMessages.appendChild(messageDiv);
    scrollToBottom();
}

function addTypingIndicator() {
    const id = 'typing-' + Date.now();
    const messageDiv = document.createElement('div');
    messageDiv.id = id;
    messageDiv.className = 'message assistant';

    const avatar = document.createElement('div');
    avatar.className = 'message-avatar';
    avatar.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor"><path d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/></svg>';

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';

    const bubble = document.createElement('div');
    bubble.className = 'message-bubble';
    bubble.innerHTML = '<div class="typing-indicator"><div class="typing-dot"></div><div class="typing-dot"></div><div class="typing-dot"></div></div>';

    messageContent.appendChild(bubble);
    messageDiv.appendChild(avatar);
    messageDiv.appendChild(messageContent);

    chatMessages.appendChild(messageDiv);
    scrollToBottom();

    return id;
}

function removeTypingIndicator(id) {
    const element = document.getElementById(id);
    if (element) {
        element.remove();
    }
}

function scrollToBottom() {
    chatMessages.scrollTop = chatMessages.scrollHeight;
}
