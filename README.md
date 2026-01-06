# JARVIS V2.3 (Project GLASS-HUD)

The "BRO" AI Assistant is now a complete Desktop & Lifestyle environment.
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()

## 🚀 Quick Start
Run the new UI:
```bash
python ui/main_window.py
```

## ✨ New Features
1.  **Lifestyle Suite** (New in v2.3):
    *   **Calendar**: Visual scheduler.
    *   **Shopping**: Product tracker.
    *   **Phone**: Integrated dialer & logs.
2.  **Productivity Suite** (v2.2):
    *   **Notes**: Auto-saving markdown notebook.
    *   **Music**: Local audio player.
    *   **Settings**: Hot-swap AI models & personas.
3.  **GLASS-HUD UI**: Modern "Midnight Teal" interface.
    *   **Chat**: Threaded, typing effects, markdown-ready.
    *   **Dashboard**: Live system monitoring (CPU/RAM graphs).
    *   **Vision**: Visual Cortex control panel + **Auto Copilot** (Autonomous Screen Agent).
    *   **Web**: Neural browser interface.
2.  **Cognitive Brain**:
    *   **Semantic Router**: Uses vector embeddings to route intents.
    *   **Memory**: ChromaDB-backed long-term memory.
    *   **Local Logic**: `llama3.1` (8B) as the core reasoning engine.
3.  **High-Speed I/O**:
    *   **Hearing**: `Faster-Whisper` + **Real-Time Spectral Visualization**.
    *   **Vision**: `LLaVA` (7B) for image analysis.
    *   **Call Sentry**: AI Phone Screening server (FastAPI + Twilio).
4.  **Package Architecture**:
    *   Full python package (`pip install -e .`).
    *   Robust JSON tool parsing.

## 🛠️ Setup
1.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    pip install -e .
    ```
2.  **Pull Models**:
    ```bash
    ollama pull llama3.1
    ollama pull llava
    ollama pull nomic-embed-text
    ```
3.  **Playwright (for Web)**:
    ```bash
    playwright install chromium
    ```

## 📂 Project Structure
*   `jarvis/`
    *   `ui/` - All pages and components.
    *   `cognitive/` - Brain logic (Engine, Semantic Router).
    *   `voice/` - STT and TTS modules.
    *   `tools/` - Android, Web, Desktop automation tools.

Enjoy your new AI.
