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

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
});

async function initializeApp() {
    await checkServerHealth();
    await loadSchemas();
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


    // Sidebar toggle
    const sidebar = document.getElementById('sidebar');
    const sidebarToggle = document.getElementById('sidebar-toggle');

    // Load sidebar state (default to collapsed)
    const sidebarState = localStorage.getItem('sidebar-collapsed-v2');
    if (sidebarState === 'false') {
        sidebar.classList.remove('collapsed');
    }

    sidebarToggle.addEventListener('click', () => {
        sidebar.classList.toggle('collapsed');
        localStorage.setItem('sidebar-collapsed-v2', sidebar.classList.contains('collapsed'));
    });

    // Schema generation modal
    setupSchemaModal();

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
        const resultsHeader = document.createElement('div');
        resultsHeader.className = 'results-header';
        resultsHeader.innerHTML = `
            <span class="results-count">Found <strong>${results.count}</strong> result(s)</span>
            <div class="results-view-toggle">
                <button class="view-toggle-btn active" data-view="table">Table</button>
                <button class="view-toggle-btn" data-view="json">JSON</button>
            </div>
        `;

        const tableContainer = document.createElement('div');
        tableContainer.className = 'results-table-container view-section';
        tableContainer.innerHTML = createResultsTable(results.results);

        const jsonContainer = document.createElement('div');
        jsonContainer.className = 'results-json view-section hidden';
        jsonContainer.textContent = JSON.stringify(results.results, null, 2);

        resultsDisplay.appendChild(resultsHeader);
        resultsDisplay.appendChild(tableContainer);
        resultsDisplay.appendChild(jsonContainer);

        // Setup toggle listeners
        const buttons = resultsHeader.querySelectorAll('.view-toggle-btn');
        buttons.forEach(btn => {
            btn.addEventListener('click', () => {
                buttons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');

                const view = btn.dataset.view;
                if (view === 'table') {
                    tableContainer.classList.remove('hidden');
                    jsonContainer.classList.add('hidden');
                } else {
                    tableContainer.classList.add('hidden');
                    jsonContainer.classList.remove('hidden');
                }
            });
        });

        // Decide initial view based on "tabular-ability"
        const isTabular = results.results.every(item => {
            return Object.values(item).every(val => typeof val !== 'object' || val === null);
        });

        if (!isTabular) {
            // Default to JSON if data is nested
            buttons[1].click();
        }

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

/**
 * Helper to create a table from query results
 */
function createResultsTable(data) {
    if (!data || data.length === 0) return '';

    // Extract all unique headers from all rows
    const headers = [...new Set(data.flatMap(obj => Object.keys(obj)))];

    let html = '<table class="results-table"><thead><tr>';
    headers.forEach(header => {
        html += `<th>${header}</th>`;
    });
    html += '</tr></thead><tbody>';

    data.forEach(row => {
        html += '<tr>';
        headers.forEach(header => {
            let val = row[header];
            let displayVal = '';
            let valClass = '';

            if (val === undefined || val === null) {
                displayVal = '<span class="null-val">null</span>';
            } else if (typeof val === 'object') {
                displayVal = `<span class="obj-val" title='${JSON.stringify(val).replace(/'/g, "&apos;")}'>{ ... }</span>`;
            } else if (typeof val === 'number') {
                displayVal = val.toLocaleString();
                valClass = 'val-number';
            } else if (typeof val === 'boolean') {
                displayVal = val ? 'TRUE' : 'FALSE';
                valClass = 'val-boolean';
            } else if (typeof val === 'string' && val.includes('T') && !isNaN(Date.parse(val))) {
                // If it looks like an ISO date
                const date = new Date(val);
                displayVal = date.toLocaleString();
                valClass = 'val-date';
            } else {
                displayVal = val.toString();
                valClass = 'val-string';
            }

            html += `<td><span class="${valClass}" title="${typeof val === 'string' ? val.replace(/"/g, '&quot;') : ''}">${displayVal}</span></td>`;
        });
        html += '</tr>';
    });

    html += '</tbody></table>';
    return html;
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

// ========================================
// Schema Generation Modal
// ========================================

let selectedCollections = new Set();

function setupSchemaModal() {
    const modal = document.getElementById('schema-modal');
    const openBtn = document.getElementById('generate-schema-btn');
    const closeBtn = document.getElementById('modal-close-btn');
    const cancelBtn = document.getElementById('cancel-btn');
    const generateBtn = document.getElementById('generate-btn');
    const selectAllBtn = document.getElementById('select-all-collections');
    const sampleSizeInput = document.getElementById('sample-size');
    const sampleSizeValue = document.getElementById('sample-size-value');

    // Open modal
    openBtn.addEventListener('click', async () => {
        modal.style.display = 'flex';
        selectedCollections.clear();
        await loadCollectionsList();
    });

    // Close modal
    const closeModal = () => {
        modal.style.display = 'none';
        document.getElementById('relationship-preview').style.display = 'none';
        document.getElementById('relationship-preview').innerHTML = '';
    };

    closeBtn.addEventListener('click', closeModal);
    cancelBtn.addEventListener('click', closeModal);

    // Close on outside click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            closeModal();
        }
    });

    // Sample size slider
    sampleSizeInput.addEventListener('input', (e) => {
        sampleSizeValue.textContent = e.target.value;
    });

    // Select all collections
    selectAllBtn.addEventListener('click', () => {
        const checkboxes = document.querySelectorAll('.collection-checkbox');
        const allSelected = selectedCollections.size === checkboxes.length;

        if (allSelected) {
            // Deselect all
            checkboxes.forEach(cb => cb.checked = false);
            selectedCollections.clear();
            selectAllBtn.textContent = 'Select All';
        } else {
            // Select all
            checkboxes.forEach(cb => {
                cb.checked = true;
                selectedCollections.add(cb.value);
            });
            selectAllBtn.textContent = 'Deselect All';
        }

        updateGenerateButton();
    });

    // Generate schema
    generateBtn.addEventListener('click', async () => {
        await generateSchemas();
    });
}

async function loadCollectionsList() {
    const listContainer = document.getElementById('collection-list');
    listContainer.innerHTML = '<div class="loading-spinner">Loading collections...</div>';

    try {
        const response = await fetch(`${API_BASE_URL}/api/collections`);
        const data = await response.json();

        if (data.success && data.collections.length > 0) {
            listContainer.innerHTML = '';

            data.collections.forEach(collectionName => {
                const item = document.createElement('label');
                item.className = 'collection-item';
                item.innerHTML = `
                    <input type="checkbox" class="collection-checkbox" value="${collectionName}">
                    <span class="collection-name">${collectionName}</span>
                `;

                const checkbox = item.querySelector('input');
                checkbox.addEventListener('change', (e) => {
                    if (e.target.checked) {
                        selectedCollections.add(collectionName);
                    } else {
                        selectedCollections.delete(collectionName);
                    }
                    updateGenerateButton();
                    updateSelectAllButton();
                });

                listContainer.appendChild(item);
            });
        } else {
            listContainer.innerHTML = '<div class="no-collections">No collections found in database</div>';
        }
    } catch (error) {
        listContainer.innerHTML = `<div class="error-message">Failed to load collections: ${error.message}</div>`;
    }
}

function updateGenerateButton() {
    const generateBtn = document.getElementById('generate-btn');
    generateBtn.disabled = selectedCollections.size === 0;
}

function updateSelectAllButton() {
    const selectAllBtn = document.getElementById('select-all-collections');
    const checkboxes = document.querySelectorAll('.collection-checkbox');
    const allSelected = selectedCollections.size === checkboxes.length && checkboxes.length > 0;
    selectAllBtn.textContent = allSelected ? 'Deselect All' : 'Select All';
}

async function generateSchemas() {
    const generateBtn = document.getElementById('generate-btn');
    const sampleSize = parseInt(document.getElementById('sample-size').value);
    const detectRelationships = document.getElementById('detect-relationships').checked;
    const previewSection = document.getElementById('relationship-preview');

    // Disable button and show loading
    generateBtn.disabled = true;
    generateBtn.innerHTML = '<span class="spinner"></span> Generating...';

    try {
        const response = await fetch(`${API_BASE_URL}/api/generate-schema`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                collections: Array.from(selectedCollections),
                sample_size: sampleSize,
                detect_relationships: detectRelationships,
                merge_strategy: 'merge'
            })
        });

        const result = await response.json();

        if (result.success) {
            // Show success message
            displayGenerationResults(result);

            // Refresh schema status
            await checkServerHealth();

            // Show preview
            previewSection.style.display = 'block';
        } else {
            throw new Error(result.error || 'Schema generation failed');
        }
    } catch (error) {
        alert(`Schema generation failed: ${error.message}`);
    } finally {
        generateBtn.disabled = false;
        generateBtn.textContent = 'Generate Schema';
    }
}

function displayGenerationResults(result) {
    const previewSection = document.getElementById('relationship-preview');

    let html = '<div class="generation-results">';
    html += '<h3>✓ Schema Generation Complete</h3>';

    // Stats
    html += '<div class="stats-grid">';
    html += `<div class="stat-item">
        <span class="stat-label">Collections Analyzed</span>
        <span class="stat-value">${result.stats.collections_analyzed}</span>
    </div>`;
    html += `<div class="stat-item">
        <span class="stat-label">Total Fields</span>
        <span class="stat-value">${result.stats.total_fields}</span>
    </div>`;
    html += `<div class="stat-item">
        <span class="stat-label">Relationships Found</span>
        <span class="stat-value">${result.stats.relationships_found}</span>
    </div>`;
    html += '</div>';

    // Relationships
    if (result.relationships && result.relationships.links && result.relationships.links.length > 0) {
        html += '<div class="relationships-section">';
        html += '<h4>Detected Relationships</h4>';
        html += '<div class="relationships-list">';

        result.relationships.links.forEach(link => {
            html += `<div class="relationship-item">
                <div class="relationship-arrow">
                    <span class="from-collection">${link.from}</span>
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" width="20" height="20">
                        <path d="M5 12h14M12 5l7 7-7 7" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                    </svg>
                    <span class="to-collection">${link.to}</span>
                </div>
                <div class="relationship-details">
                    <span class="relationship-type">${link.type}</span>
                    <span class="relationship-field">via ${link.field}</span>
                    <span class="relationship-confidence">confidence: ${(link.confidence * 100).toFixed(0)}%</span>
                </div>
            </div>`;
        });

        html += '</div></div>';
    }

    html += '<div class="success-actions">';
    html += '<button class="primary-btn" onclick="document.getElementById(\'schema-modal\').style.display=\'none\'">Done</button>';
    html += '</div>';
    html += '</div>';

    previewSection.innerHTML = html;
}

