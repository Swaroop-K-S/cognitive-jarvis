# JARVIS V2 (Project GLASS-HUD)

The "BRO" AI Assistant has been upgraded to a modular, local-first architecture.

## 🚀 Quick Start
Run the new UI:
```bash
python ui/main_window.py
```

## ✨ New Features
1.  **GLASS-HUD UI**: Modern "Midnight Teal" interface with strict modularity.
    *   **Chat**: Threaded, typing effects, markdown-ready.
    *   **Dashboard**: Live system monitoring (CPU/RAM graphs).
    *   **Vision**: Visual Cortex control panel.
    *   **Web**: Neural browser interface.
2.  **Cognitive Brain**:
    *   **Semantic Router**: Uses vector embeddings (`nomic-embed-text`) to route intents (Remember vs Act vs Chat).
    *   **Local Logic**: `llama3.1` (8B) as the core reasoning engine.
3.  **High-Speed I/O**:
    *   **Hearing**: `Faster-Whisper` for ~0.5s speech recognition.
    *   **Vision**: `LLaVA` (7B) for image analysis + `UIAutomator` (XML) for 6x faster Android control.
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
