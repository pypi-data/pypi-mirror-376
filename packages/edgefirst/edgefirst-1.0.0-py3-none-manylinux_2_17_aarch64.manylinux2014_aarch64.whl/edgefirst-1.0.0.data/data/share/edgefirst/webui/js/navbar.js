function createNavbar(pageTitle) {
    const navbar = document.createElement('header');
    navbar.className = 'bg-[#24088E]'; // Purple background
    navbar.innerHTML = `
        <nav class="navbar" style="background: #24088E;">
            <div class="navbar-start">
                <a href="/" class="flex items-center gap-2">
                    <img src="../assets/auzoneLogo.svg" alt="AuZone Logo" class="h-12 w-auto">
                </a>
            </div>
            <div class="navbar-center">
                <h1 class="text-xl font-semibold text-white">${pageTitle}</h1>
            </div>
            <div class="navbar-end">
                <div class="flex items-center gap-4">
                    <!-- Minimalist recording button with tooltip -->
                    <button id="recordingButton" class="rec-btn flex items-center gap-2 px-4 py-1 rounded-full bg-gray-200 text-red-600 font-semibold transition-colors duration-200 focus:outline-none" aria-pressed="false" aria-label="Start Recording">
                        <span class="rec-dot inline-block w-3 h-3 rounded-full bg-red-600"></span>
                        <span class="rec-text">REC</span>
                        <span class="rec-tooltip absolute left-1/2 -translate-x-1/2 top-110% mt-2 px-2 py-1 rounded bg-gray-900 text-white text-xs opacity-0 pointer-events-none transition-opacity">Start Recording</span>
                    </button>
                    <!-- Add MCAP Files button -->
                    <div class="relative">
                        <button class="btn btn-ghost btn-circle group" onclick="showMcapDialog()" id="mcapDialogBtn" aria-label="Show MCAP Details">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.5"
                                stroke="currentColor" class="w-6 h-6">
                                <path stroke-linecap="round" stroke-linejoin="round"
                                    d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
                            </svg>
                            <span class="mcap-tooltip absolute left-1/2 -translate-x-1/2 top-110% mt-2 px-2 py-1 rounded bg-gray-900 text-white text-xs opacity-0 pointer-events-none transition-opacity group-hover:opacity-100 group-focus:opacity-100" style="white-space:nowrap;z-index:20;">MCAP Details</span>
                        </button>
                    </div>
                </div>
            </div>
        </nav>
    `;

    // Add styles for recording button
    const style = document.createElement('style');
    style.textContent = `
        .rec-btn {
            display: flex;
            align-items: center;
            gap: 8px;
            font-size: 15px;
            font-weight: 600;
            background: #e5e7eb;
            color: #111;
            border: none;
            border-radius: 9999px;
            padding: 0.25rem 1.1rem;
            cursor: pointer;
            transition: background 0.2s, color 0.2s;
            position: relative;
            outline: none;
            box-shadow: none;
        }
        .rec-btn.recording {
            background: #dc2626;
            color: white;
        }
        .rec-btn .rec-dot {
            background: #111;
            width: 0.75rem;
            height: 0.75rem;
            border-radius: 9999px;
            transition: background 0.2s;
        }
        .rec-btn.recording .rec-dot {
            background: white;
            animation: rec-pulse-minimal 1s infinite;
        }
        @keyframes rec-pulse-minimal {
            0% { transform: scale(1); opacity: 1; }
            50% { transform: scale(1.3); opacity: 0.7; }
            100% { transform: scale(1); opacity: 1; }
        }
        .rec-btn .rec-tooltip {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            top: 110%;
            margin-top: 0.5rem;
            background: #111827;
            color: #fff;
            padding: 0.25rem 0.75rem;
            border-radius: 0.375rem;
            font-size: 0.75rem;
            opacity: 0;
            pointer-events: none;
            white-space: nowrap;
            z-index: 10;
            transition: opacity 0.2s;
        }
        .rec-btn:hover .rec-tooltip,
        .rec-btn:focus .rec-tooltip {
            opacity: 1;
        }
        .rec-btn .rec-text {
            font-size: 1.1rem;
            font-weight: bold;
            transition: opacity 0.3s;
        }
        .rec-btn .rec-icon {
            color: inherit;
        }

        #modeIndicator {
            transition: all 0.3s ease;
            white-space: nowrap;
            cursor: pointer;
            position: relative;
        }
        #modeIndicator .mode-tooltip {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            top: 110%;
            margin-top: 0.5rem;
            background: #111827;
            color: #fff;
            padding: 0.25rem 0.75rem;
            border-radius: 0.375rem;
            font-size: 0.75rem;
            opacity: 0;
            pointer-events: none;
            white-space: nowrap;
            z-index: 10;
            transition: opacity 0.2s;
        }
        #modeIndicator:hover .mode-tooltip,
        #modeIndicator:focus .mode-tooltip {
            opacity: 1;
        }

        .navbar-end .btn-circle svg {
            width: 24px;
            height: 24px;
            color: white;
        }

        .navbar-end .btn-circle:hover svg {
            color: #e2e8f0;
        }

        .navbar-end .menu {
            display: flex;
            align-items: center;
        }

        .navbar-end .btn-circle.btn-lg {
            width: 3rem;
            height: 3rem;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .navbar-end .btn-circle.btn-lg svg {
            margin-top: -5px;
            width: 25px;
            height: 25px;
            color: white;
        }

        .navbar-end .btn-circle.btn-lg:hover svg {
            color: #e2e8f0;
        }

        #serviceStatusTooltip {
            position: absolute;
            top: 100%;
            right: 0;
            left: auto;
            transform: none;
            margin-top: 0.75rem;
            width: 16rem;
            max-width: 90vw;
            background: white;
            border-radius: 0.5rem;
            box-shadow: 0 10px 15px -3px rgba(0,0,0,0.1), 0 4px 6px -2px rgba(0,0,0,0.05);
            padding: 1rem;
            z-index: 50;
            display: none;
            transition: all 0.2s ease;
            pointer-events: none;
        }
        #serviceStatusTooltip * {
            pointer-events: auto;
        }
        .service-info-btn:hover + #serviceStatusTooltip,
        .service-info-btn:focus + #serviceStatusTooltip {
            display: block;
        }

        .mcap-btn {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            width: 2.25rem;
            height: 2.25rem;
            border-radius: 9999px;
            border: none;
            outline: none;
            cursor: pointer;
            transition: background 0.15s;
            font-size: 1rem;
            padding: 0;
        }
        .mcap-btn-blue {
            background: #4285f4;
            color: #fff;
        }
        .mcap-btn-blue:hover {
            background: #1a73e8;
        }
        .mcap-tooltip {
            position: absolute;
            left: 50%;
            transform: translateX(-50%);
            top: 110%;
            margin-top: 0.5rem;
            background: #111827;
            color: #fff;
            padding: 0.25rem 0.75rem;
            border-radius: 0.375rem;
            font-size: 0.75rem;
            opacity: 0;
            pointer-events: none;
            white-space: nowrap;
            z-index: 20;
            transition: opacity 0.2s;
        }
        .group:hover .mcap-tooltip,
        .group:focus .mcap-tooltip {
            opacity: 1;
        }
    `;
    document.head.appendChild(style);

    return navbar;
}

// Function to initialize the navbar
function initNavbar(pageTitle) {
    // Create the navbar
    const navbar = createNavbar(pageTitle);

    // Insert the navbar at the beginning of the body
    document.body.insertBefore(navbar, document.body.firstChild);

    // Add recording button logic
    setTimeout(() => {
        const recordingButton = document.getElementById('recordingButton');
        if (recordingButton) {
            // Tooltip logic
            recordingButton.addEventListener('mouseenter', function () {
                const tooltip = recordingButton.querySelector('.rec-tooltip');
                if (tooltip) tooltip.style.opacity = 1;
            });
            recordingButton.addEventListener('mouseleave', function () {
                const tooltip = recordingButton.querySelector('.rec-tooltip');
                if (tooltip) tooltip.style.opacity = 0;
            });
            // Click event
            recordingButton.addEventListener('click', function () {
                if (recordingButton.classList.contains('recording')) {
                    stopRecording();
                } else {
                    startRecording();
                }
            });
        }

        // --- NEW: Set UI from localStorage cache immediately ---
        const cachedStatus = localStorage.getItem('recordingStatus');
        if (cachedStatus === 'recording') {
            updateRecordingUI(true);
        } else if (cachedStatus === 'not-recording') {
            updateRecordingUI(false);
        }

        // Listen for storage events to sync across tabs
        window.addEventListener('storage', (event) => {
            if (event.key === 'recordingStatus') {
                if (event.newValue === 'recording') {
                    updateRecordingUI(true);
                } else if (event.newValue === 'not-recording') {
                    updateRecordingUI(false);
                }
            }
        });

        if (window.serviceCache && !window.serviceCache.isInitialized) {
            window.serviceCache.startBackgroundUpdates();
        } else if (!window.serviceCache) {
            console.warn('Service cache not initialized yet');
            // Try to initialize when service cache becomes available
            const checkServiceCache = setInterval(() => {
                if (window.serviceCache) {
                    window.serviceCache.startBackgroundUpdates();
                    clearInterval(checkServiceCache);
                }
            }, 100);
        }

        const updateUIFromCache = () => {
            if (!window.serviceCache) return;

            const serviceStatuses = window.serviceCache.serviceStatuses;
            const replayStatus = window.serviceCache.replayStatus;


            if (serviceStatuses) {
                updateQuickStatus();
            }
            if (replayStatus !== null) {
                checkReplayStatus();
            }
            checkRecordingStatus();
        };

        updateUIFromCache();

        if (window.serviceCache) {
            window.serviceCache.registerUpdateCallback(updateUIFromCache);
        }
        const modeIndicator = document.getElementById('modeIndicator');
        if (modeIndicator) {
            const tooltip = modeIndicator.querySelector('.mode-tooltip-custom');
            let tooltipHover = false;
            let indicatorHover = false;

            function showTooltip() {
                updateModeTooltipCustom();
                tooltip.style.opacity = '1';
                tooltip.style.pointerEvents = 'auto';
            }
            function hideTooltip() {
                tooltip.style.opacity = '0';
                tooltip.style.pointerEvents = 'none';
            }

            modeIndicator.addEventListener('mouseenter', function () {
                indicatorHover = true;
                showTooltip();
            });
            modeIndicator.addEventListener('mouseleave', function () {
                indicatorHover = false;
                setTimeout(() => {
                    if (!tooltipHover && !indicatorHover) hideTooltip();
                }, 50);
            });
            tooltip.addEventListener('mouseenter', function () {
                tooltipHover = true;
                showTooltip();
            });
            tooltip.addEventListener('mouseleave', function () {
                tooltipHover = false;
                setTimeout(() => {
                    if (!tooltipHover && !indicatorHover) hideTooltip();
                }, 50);
            });
            if (window.serviceCache) {
                window.serviceCache.registerUpdateCallback(() => {
                    if (indicatorHover || tooltipHover) {
                        updateModeTooltipCustom();
                    }
                });
            }
            modeIndicator.addEventListener('click', function (e) {
                // Prevent click on the link from firing twice
                if (e.target.closest('#modeTooltipDetailsLink')) return;
                if (typeof showServiceStatus === 'function') {
                    showServiceStatus();
                }
            });
            const detailsLink = tooltip.querySelector('#modeTooltipDetailsLink');
            if (detailsLink) {
                detailsLink.addEventListener('click', function (e) {
                    e.preventDefault();
                    if (typeof showServiceStatus === 'function') {
                        showServiceStatus();
                    }
                });
            }
        }
    }, 0);

    updateRecordingButtonForStorage();
}

let navbarRecordingFile = null;

window.wasRecording = false;
window.lowDiskDialogShown = false;

function checkRecordingStatus() {
    fetch('/recorder-status')
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.text();
        })
        .then(statusText => {
            const isRecording = statusText.trim() === "Recorder is running";
            if (isRecording) {
                window.lowDiskDialogShown = false;
                return fetch('/current-recording')
                    .then(response => response.json())
                    .then(data => {
                        navbarRecordingFile = data.status === "recording" ? data.filename : null;
                        updateRecordingUI(true);
                        window.wasRecording = true;
                    });
            } else {
                navbarRecordingFile = null;
                fetch('/check-storage')
                    .then(resp => resp.ok ? resp.json() : null)
                    .then(info => {
                        let availValue = 0;
                        if (info && info.available_space && typeof info.available_space === 'object') {
                            const availObj = info.available_space;
                            const unit = (availObj.unit || '').toUpperCase();
                            if (unit === 'GB') availValue = availObj.value;
                            else if (unit === 'MB') availValue = availObj.value / 1024;
                            else if (unit === 'TB') availValue = availObj.value * 1024;
                            else availValue = availObj.value; // fallback
                        }
                        updateRecordingUI(false);
                        if (window.wasRecording && availValue < 0.1 && !window.lowDiskDialogShown) {
                            showLowDiskDialog('Recording stopped because there is less than 500MB free disk space.');
                            window.lowDiskDialogShown = true;
                            console.log("Stopping recording because there is less than 500MB free disk space.");
                            stopRecording();
                            updateRecordingButtonForStorage();
                        }
                        window.wasRecording = false;
                    })
                    .catch(() => {
                        updateRecordingUI(false);
                        window.wasRecording = false;
                    });
            }
        })
        .catch(error => {
            console.error('Error checking recording status:', error);
            navbarRecordingFile = null;
            updateRecordingUI(false);
            window.wasRecording = false;
        });
}

function updateRecordingUI(isRecording) {
    const recordingButton = document.getElementById('recordingButton');
    if (recordingButton) {
        const recText = recordingButton.querySelector('.rec-text');
        const recDot = recordingButton.querySelector('.rec-dot');
        const tooltip = recordingButton.querySelector('.rec-tooltip');
        if (isRecording) {
            recordingButton.classList.add('recording');
            recordingButton.setAttribute('aria-pressed', 'true');
            recordingButton.setAttribute('aria-label', 'Stop Recording');
            if (recText) recText.textContent = 'REC';
            if (tooltip) tooltip.textContent = 'Stop Recording';
            if (recDot) recDot.style.background = 'white';
            localStorage.setItem('recordingStatus', 'recording');
        } else {
            recordingButton.classList.remove('recording');
            recordingButton.setAttribute('aria-pressed', 'false');
            recordingButton.setAttribute('aria-label', 'Start Recording');
            if (recText) recText.textContent = 'REC';
            if (tooltip) tooltip.textContent = 'Start Recording';
            if (recDot) recDot.style.background = '#111';
            localStorage.setItem('recordingStatus', 'not-recording');
        }
    }
}

function showRecCheckmark() {
    const recordingButton = document.getElementById('recordingButton');
    if (recordingButton) {
        const recCheck = recordingButton.querySelector('.rec-check');
        if (recCheck) {
            recCheck.classList.remove('hidden');
            setTimeout(() => {
                recCheck.classList.add('hidden');
            }, 900);
        }
    }
}

function startRecording() {
    console.log("startRecording called");
    fetch('/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
    })
        .then(response => {
            console.log("/start response status:", response.status);
            if (!response.ok) {
                throw new Error(`HTTP error ${response.status}`);
            }
            return response.text();
        })
        .then(text => {
            console.log('Recording started:', text);
            navbarRecordingFile = null;
            updateRecordingUI(true);
            showRecCheckmark();
        })
        .catch(error => {
            console.error('Error starting recording:', error);
            alert(`Error starting recording: ${error.message}`);
            updateRecordingUI(false);
        });
}

function stopRecording() {
    console.log("stopRecording called");
    fetch('/stop', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({})
    })
        .then(response => {
            console.log("/stop response status:", response.status);
            if (!response.ok) throw new Error(`HTTP error ${response.status}`);
            return response.text();
        })
        .then(text => {
            console.log('Recording stopped:', text);
            navbarRecordingFile = null;
            updateRecordingUI(false);
            showRecCheckmark();
        })
        .catch(error => {
            console.error('Error stopping recording:', error);
            alert(`Error stopping recording: ${error.message}`);
            updateRecordingUI(true);
        });
}

function ensureFileDetailsModal() {
    if (!document.getElementById('myModal')) {
        const dialog = document.createElement('dialog');
        dialog.id = 'myModal';
        dialog.className = 'bg-white rounded-lg shadow-lg p-6 w-[600px]';
        dialog.innerHTML = '<div id="modalDetails"></div>';
        document.body.appendChild(dialog);
    }
}

function updateModeTooltipCustom() {
    if (!window.serviceCache) return;
    const tooltipContent = document.getElementById('modeTooltipContent');
    if (!tooltipContent) return;
    const serviceStatuses = window.serviceCache.serviceStatuses;
    if (!serviceStatuses) {
        tooltipContent.innerHTML = '<span>Loading services...</span>';
        return;
    }
    if (Array.isArray(serviceStatuses)) {
        const allRunning = serviceStatuses.every(s => (typeof s.status === 'string' ? s.status : s.status?.status) === 'running');
        if (allRunning) {
            tooltipContent.innerHTML = '<div class="flex items-center gap-2"><span style="color:#22c55e;font-size:1.2em;">●</span> <span class="text-green-700">All Services Running</span></div>';
        } else {
            let html = '';
            serviceStatuses.filter(s => (typeof s.status === 'string' ? s.status : s.status?.status) !== 'running').forEach(s => {
                const serviceName = (s.service || s.name || 'Unknown')
                    .replace('.service', '')
                    .split('-')
                    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
                    .join(' ');
                let statusStr = typeof s.status === 'string' ? s.status : (s.status?.status || JSON.stringify(s.status));
                statusStr = statusStr.charAt(0).toUpperCase() + statusStr.slice(1);
                html += `<div class="flex items-center gap-2"><span style=\"color:#ef4444;font-size:1.2em;\">●</span> <span class=\"text-red-700\">${serviceName}: ${statusStr}</span></div>`;
            });
            tooltipContent.innerHTML = html || '<span>Unknown status</span>';
        }
    } else {
        const allRunning = Object.values(serviceStatuses).every(s => s === 'running');
        if (allRunning) {
            tooltipContent.innerHTML = '<div class="flex items-center gap-2"><span style="color:#22c55e;font-size:1.2em;">●</span> <span class="text-green-700">All Services Running</span></div>';
        } else {
            let html = '';
            for (const [service, status] of Object.entries(serviceStatuses)) {
                if (status !== 'running') {
                    html += `<div class=\"flex items-center gap-2\"><span style=\"color:#ef4444;font-size:1.2em;\">●</span> <span class=\"text-red-700\">${service}: ${status}</span></div>`;
                }
            }
            tooltipContent.innerHTML = html || '<span>Unknown status</span>';
        }
    }
}

// Function to check storage and update the recording button
async function updateRecordingButtonForStorage() {
    try {
        const response = await fetch('/check-storage');
        if (!response.ok) return;
        const info = await response.json();
        const availObj = info.available_space;
        let availValueGB = 0;
        if (availObj && typeof availObj === 'object') {
            const unit = (availObj.unit || '').toUpperCase();
            if (unit === 'GB') availValueGB = availObj.value;
            else if (unit === 'MB') availValueGB = availObj.value / 1024;
            else if (unit === 'TB') availValueGB = availObj.value * 1024;
            else availValueGB = availObj.value; // fallback
        }
        const recordingButton = document.getElementById('recordingButton');
        if (recordingButton) {
            if (availValueGB < 0.1) {
                recordingButton.classList.add('opacity-50');
                recordingButton.setAttribute('disabled', 'disabled');
                recordingButton.title = 'Not enough space to record (less than 500MB free)';
            } else {
                recordingButton.classList.remove('opacity-50');
                recordingButton.removeAttribute('disabled');
                recordingButton.title = '';
            }
        }
    } catch (e) { }
}

setTimeout(updateRecordingButtonForStorage, 0);
setInterval(updateRecordingButtonForStorage, 30000);

function showLowDiskDialog(message) {
    let dialog = document.getElementById('lowDiskDialog');
    if (!dialog) {
        dialog = document.createElement('dialog');
        dialog.id = 'lowDiskDialog';
        dialog.style.padding = '0';
        dialog.innerHTML = `
            <form method="dialog" style="margin:0;">
                <div style="padding: 2rem 2.5rem; background: #181a2a; color: #fff; border-radius: 1rem; min-width: 320px; max-width: 90vw; box-shadow: 0 8px 32px rgba(0,0,0,0.18); display: flex; flex-direction: column; align-items: center;">
                    <div style="font-size: 1.25rem; font-weight: 600; margin-bottom: 1rem; color: #facc15; display: flex; align-items: center; gap: 0.5rem;">
                        <svg style='width:1.5em;height:1.5em;vertical-align:-0.2em;' fill='none' stroke='currentColor' stroke-width='2' viewBox='0 0 24 24'><circle cx='12' cy='12' r='10' stroke='#facc15' stroke-width='2' fill='none'/><path d='M12 8v4m0 4h.01' stroke='#facc15' stroke-width='2' stroke-linecap='round'/></svg>
                        Low Disk Space
                    </div>
                    <div style="margin-bottom: 1.5rem; text-align: center; font-size: 1.08rem; color: #fff;">${message}</div>
                    <button type="submit" style="background: #fab010; color: #222; font-weight: 600; border: none; border-radius: 0.5rem; padding: 0.6rem 2.2rem; font-size: 1.08rem; cursor: pointer; box-shadow: 0 2px 8px rgba(0,0,0,0.08);">OK</button>
                </div>
            </form>
        `;
        document.body.appendChild(dialog);
    } else {
        dialog.querySelector('div[style*="margin-bottom: 1.5rem;"]').textContent = message;
    }
    dialog.showModal();
}

setInterval(checkRecordingStatus, 10000);