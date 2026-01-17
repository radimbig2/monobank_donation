(function() {
    const mediaContainer = document.getElementById('media-container');
    const mediaImage = document.getElementById('media-image');
    const mediaAudio = document.getElementById('media-audio');
    const statusEl = document.getElementById('status');
    const testBtn = document.getElementById('test-btn');

    let hideTimeout = null;
    let ws = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 10;
    const reconnectDelay = 2000;

    function updateStatus(connected) {
        if (statusEl) {
            statusEl.textContent = connected ? 'WebSocket: connected' : 'WebSocket: disconnected';
            statusEl.className = connected ? 'connected' : 'disconnected';
        }
        if (testBtn) {
            testBtn.disabled = !connected;
        }
    }

    function connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        console.log('[Overlay] Connecting to', wsUrl);
        ws = new WebSocket(wsUrl);

        ws.onopen = function() {
            console.log('[Overlay] WebSocket connected');
            reconnectAttempts = 0;
            updateStatus(true);
        };

        ws.onmessage = function(event) {
            console.log('[Overlay] Raw message:', event.data);
            try {
                const data = JSON.parse(event.data);
                handleMessage(data);
            } catch (e) {
                console.error('[Overlay] Failed to parse message:', e);
            }
        };

        ws.onclose = function() {
            console.log('[Overlay] WebSocket disconnected');
            updateStatus(false);
            scheduleReconnect();
        };

        ws.onerror = function(error) {
            console.error('[Overlay] WebSocket error:', error);
            updateStatus(false);
        };
    }

    function scheduleReconnect() {
        if (reconnectAttempts < maxReconnectAttempts) {
            reconnectAttempts++;
            console.log(`[Overlay] Reconnecting in ${reconnectDelay}ms (attempt ${reconnectAttempts}/${maxReconnectAttempts})`);
            setTimeout(connect, reconnectDelay);
        } else {
            console.error('[Overlay] Max reconnect attempts reached');
        }
    }

    function handleMessage(data) {
        console.log('[Overlay] Handling message:', data);

        switch (data.type) {
            case 'show_image':
                showImage(data.image, data.duration);
                break;
            case 'show_media':
                showMedia(data.image, data.audio, data.duration);
                break;
            case 'clear':
                hideMedia();
                break;
            default:
                console.warn('[Overlay] Unknown message type:', data.type);
        }
    }

    function showImage(imageSrc, duration) {
        showMedia(imageSrc, null, duration);
    }

    function showMedia(imageSrc, audioSrc, duration) {
        console.log('[Overlay] showMedia:', { imageSrc, audioSrc, duration });

        // Clear any pending hide
        if (hideTimeout) {
            clearTimeout(hideTimeout);
            hideTimeout = null;
        }

        // Set image source
        mediaImage.src = imageSrc;
        console.log('[Overlay] Image src set to:', imageSrc);

        // Show container with animation
        mediaContainer.classList.remove('hidden', 'animate-out');
        mediaContainer.classList.add('visible', 'animate-in');
        console.log('[Overlay] Container classes:', mediaContainer.className);

        // Play audio if provided
        if (audioSrc) {
            mediaAudio.src = audioSrc;
            mediaAudio.currentTime = 0;
            console.log('[Overlay] Playing audio:', audioSrc);
            mediaAudio.play().then(() => {
                console.log('[Overlay] Audio playing successfully');
            }).catch(e => {
                console.warn('[Overlay] Audio play failed (browser may require user interaction first):', e.message);
            });
        }

        // Schedule hide
        hideTimeout = setTimeout(function() {
            hideMedia();
        }, duration || 5000);
    }

    function hideMedia() {
        console.log('[Overlay] Hiding media');
        if (hideTimeout) {
            clearTimeout(hideTimeout);
            hideTimeout = null;
        }

        mediaContainer.classList.remove('animate-in');
        mediaContainer.classList.add('animate-out');

        // Stop audio
        mediaAudio.pause();
        mediaAudio.currentTime = 0;

        // After animation, hide completely
        setTimeout(function() {
            mediaContainer.classList.remove('visible', 'animate-out');
            mediaContainer.classList.add('hidden');
            mediaImage.src = '';
        }, 300);
    }

    // Test button click - request test donation from server
    if (testBtn) {
        testBtn.addEventListener('click', function() {
            console.log('[Overlay] Test button clicked');
            fetch('/test-donation', { method: 'POST' })
                .then(response => response.json())
                .then(data => console.log('[Overlay] Test response:', data))
                .catch(e => console.error('[Overlay] Test request failed:', e));
        });
    }

    // Start connection
    updateStatus(false);
    connect();
})();
