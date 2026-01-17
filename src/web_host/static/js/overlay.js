(function() {
    const mediaContainer = document.getElementById('media-container');
    const mediaImage = document.getElementById('media-image');
    const mediaAudio = document.getElementById('media-audio');

    let hideTimeout = null;
    let ws = null;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 10;
    const reconnectDelay = 2000;

    function connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;

        ws = new WebSocket(wsUrl);

        ws.onopen = function() {
            console.log('[Overlay] WebSocket connected');
            reconnectAttempts = 0;
        };

        ws.onmessage = function(event) {
            try {
                const data = JSON.parse(event.data);
                handleMessage(data);
            } catch (e) {
                console.error('[Overlay] Failed to parse message:', e);
            }
        };

        ws.onclose = function() {
            console.log('[Overlay] WebSocket disconnected');
            scheduleReconnect();
        };

        ws.onerror = function(error) {
            console.error('[Overlay] WebSocket error:', error);
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
        console.log('[Overlay] Received:', data);

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
        // Clear any pending hide
        if (hideTimeout) {
            clearTimeout(hideTimeout);
            hideTimeout = null;
        }

        // Set image source
        mediaImage.src = imageSrc;

        // Show container with animation
        mediaContainer.classList.remove('hidden', 'animate-out');
        mediaContainer.classList.add('visible', 'animate-in');

        // Play audio if provided
        if (audioSrc) {
            mediaAudio.src = audioSrc;
            mediaAudio.currentTime = 0;
            mediaAudio.play().catch(e => {
                console.warn('[Overlay] Audio play failed:', e);
            });
        }

        // Schedule hide
        hideTimeout = setTimeout(function() {
            hideMedia();
        }, duration || 5000);
    }

    function hideMedia() {
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

    // Start connection
    connect();
})();
