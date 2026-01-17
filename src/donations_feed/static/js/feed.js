(function() {
    const donationsList = document.getElementById('donations-list');
    const statusIndicator = document.getElementById('status-indicator');
    const statusText = document.getElementById('status-text');

    let ws = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 10;
    const reconnectDelay = 2000;

    function updateStatus(connected) {
        if (connected) {
            statusIndicator.className = 'connected';
            statusText.textContent = 'Підключено';
        } else {
            statusIndicator.className = 'disconnected';
            statusText.textContent = 'Не підключено';
        }
    }

    function connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/feed/ws`;

        console.log('[Feed] Connecting to', wsUrl);
        ws = new WebSocket(wsUrl);

        ws.onopen = function() {
            console.log('[Feed] WebSocket connected');
            reconnectAttempts = 0;
            updateStatus(true);
        };

        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleMessage(data);
            } catch (e) {
                console.error('[Feed] Failed to parse message:', e);
            }
        };

        ws.onclose = function() {
            console.log('[Feed] WebSocket disconnected');
            updateStatus(false);
            scheduleReconnect();
        };

        ws.onerror = function(error) {
            console.error('[Feed] WebSocket error:', error);
            updateStatus(false);
        };
    }

    function scheduleReconnect() {
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`[Feed] Reconnecting in ${reconnectDelay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
            setTimeout(connect, reconnectDelay);
        }
    }

    function handleMessage(data) {
        console.log('[Feed] Handling message:', data);

        switch (data.type) {
            case 'init':
                initDonations(data.donations);
                break;
            case 'new_donation':
                addDonation(data.donation, true);
                break;
            default:
                console.warn('[Feed] Unknown message type:', data.type);
        }
    }

    function initDonations(donations) {
        donationsList.innerHTML = '';

        if (donations.length === 0) {
            showEmptyState();
            return;
        }

        // Add donations (they come sorted from server)
        donations.forEach(donation => {
            addDonation(donation, false);
        });
    }

    function addDonation(donation, isNew) {
        // Remove empty state if exists
        const emptyState = donationsList.querySelector('.empty-state');
        if (emptyState) {
            emptyState.remove();
        }

        const item = document.createElement('div');
        item.className = `donation-item${isNew ? ' new' : ''}`;

        const amount = parseFloat(donation.amount).toFixed(2);
        const time = new Date(donation.timestamp * 1000).toLocaleTimeString('uk-UA');

        item.innerHTML = `
            <div class="donation-header">
                <div class="donor-name">${escapeHtml(donation.donor_name)}</div>
                <div class="donation-amount">${amount} ₴</div>
            </div>
            ${donation.comment ? `<div class="donation-comment">"${escapeHtml(donation.comment)}"</div>` : ''}
            <div class="donation-time">${time}</div>
        `;

        // Add at the end (newest last)
        donationsList.appendChild(item);

        // Scroll to bottom if new
        if (isNew) {
            setTimeout(() => {
                donationsList.scrollTop = donationsList.scrollHeight;
            }, 100);
        }

        // Remove 'new' class after animation
        if (isNew) {
            setTimeout(() => {
                item.classList.remove('new');
            }, 3000);
        }
    }

    function showEmptyState() {
        donationsList.innerHTML = '<div class="empty-state">Тут буде список донатів...</div>';
    }

    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // Start connection
    updateStatus(false);
    connect();
})();
