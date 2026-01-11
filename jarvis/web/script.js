// Initial System Check
console.log("JARVIS WEB UI INITIALIZED");

// --- Voice & Sound Configuration ---
const syn = window.speechSynthesis;
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

// Browser SpeechRecognition Removed

// --- Backend Voice Logic (Offline) ---
async function toggleListening() {
    const btn = document.getElementById('mic-btn');
    const input = document.getElementById('user-input');

    // Visual State
    btn.classList.add('listening');
    playSound('listening');
    input.placeholder = "LISTENING (Offline Mode)...";

    try {
        // Call Python Backend
        console.log("Requesting backend listener...");
        let transcript = await eel.listen_voice()();

        btn.classList.remove('listening');
        input.placeholder = "COMMAND...";

        if (transcript && !transcript.startsWith("Error")) {
            input.value = transcript;
            // sendMessage(); // Removed Auto-Send to allow verification
        } else if (transcript) {
            console.error(transcript); // Log error
            playSound('error');
        }
    } catch (e) {
        console.error("Backend voice error:", e);
        btn.classList.remove('listening');
        input.placeholder = "COMMAND...";
        playSound('error');
    }
}

function speakText(text) {
    if (syn.speaking) syn.cancel();

    // Remove markdown symbols for cleaner speech
    const cleanText = text.replace(/[*_`#]/g, '');

    const utterance = new SpeechSynthesisUtterance(cleanText);
    utterance.rate = 1.1; // Slightly faster
    utterance.pitch = 0.9; // Slightly deeper

    // Try to find a good voice
    const voices = syn.getVoices();
    const preferred = voices.find(v => v.name.includes("Microsoft David") || v.name.includes("Google US English"));
    if (preferred) utterance.voice = preferred;

    syn.speak(utterance);
}

function playSound(type) {
    console.log("Playing Sound:", type);
    const audio = document.getElementById(`sfx-${type}`);
    if (audio) {
        audio.currentTime = 0;
        audio.play().catch(e => console.log("Audio play failed:", e));
    }
}

async function sendMessage() {
    let inputField = document.getElementById("user-input");
    let message = inputField.value.trim();

    if (!message) return;

    // Display User Message Immediately
    displayMessage(message, 'user');
    inputField.value = "";

    // Set UI to processing state
    setUiState('processing');

    try {
        // Call Python function
        let response = await eel.process_user_input(message)();

        // If Python returns properly, we assume it's done. 
        // Note: Python calling display_jarvis_response is what actually shows the text
        // But we can reset state here.
        setUiState('idle');

        if (response) {
            console.log("Brain ACK:", response);
        }
    } catch (e) {
        console.error("Communication Error:", e);
        displayMessage("ERROR: CONNECTION TO CORE LOST", 'system-msg');
        setUiState('idle');
    }
}

// Allow Enter key to send
document.getElementById("user-input").addEventListener("keypress", function (event) {
    if (event.key === "Enter") {
        sendMessage();
    }
});

// Exposed function for Python to call
eel.expose(display_jarvis_response);
function display_jarvis_response(text) {
    displayMessage(text, 'jarvis');
    // Ensure state is idle when message received (redundant safety)
    setUiState('idle');
}

eel.expose(set_ui_state);
function setUiState(state) {
    let container = document.querySelector('.container');
    if (state === 'processing') {
        container.classList.add('processing');
    } else {
        container.classList.remove('processing');
    }
}

function displayMessage(text, type) {
    let chatBox = document.getElementById("chat-box");
    let msgDiv = document.createElement("div");

    msgDiv.className = `message ${type}`;

    // Use marked.parse if it's a jarvis message (to support markdown)
    // User messages are kept as text to prevent XSS (basic)
    if (type === 'jarvis') {
        msgDiv.innerHTML = marked.parse(text);
    } else {
        msgDiv.textContent = text;
    }

    // Auto-scroll
    chatBox.appendChild(msgDiv);
    chatBox.scrollTop = chatBox.scrollHeight;

    // Speak if it's jarvis
    if (type === 'jarvis') {
        speakText(text);
        if (!text.includes("Listening")) playSound('ack');
    }
}

// System Status Polling
async function updateSystemStatus() {
    try {
        let stats = await eel.get_status()();
        if (stats) {
            // stats expected format: { cpu: 10, ram: 40 }
            let statusText = `CPU: ${stats.cpu}% | RAM: ${stats.ram}%`;
            document.getElementById("sys-status").innerText = statusText;
        }
    } catch (e) {
        console.log("Status update failed", e);
    }
}

// Poll every 2 seconds
setInterval(updateSystemStatus, 2000);

async function toggleCamera() {
    const btn = document.getElementById('cam-btn');

    // Visual State
    btn.classList.add('listening'); // reusing listening style for active state
    playSound('ack');
    displayMessage("ACTIVATING SENTINEL MODE...", 'system-msg');

    try {
        // Call Python Backend
        let result = await eel.activate_sentinel_mode()();

        btn.classList.remove('listening');

        if (result) {
            displayMessage(result, 'jarvis');
            speakText(result);
        }
    } catch (e) {
        console.error("Camera error:", e);
        btn.classList.remove('listening');
        playSound('error');
    }
}
