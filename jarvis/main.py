#!/usr/bin/env python3
"""
BRO - Cognitive AI Assistant
Entry Point
"""
import sys
import os
from jarvis.ui.main_window import MainWindow

from jarvis.utils.logger import setup_logger

logger = setup_logger("BRO_Main")

def main():
    logger.info("🚀 Starting BRO GLASS-HUD...")
    app = MainWindow()
    app.mainloop()

if __name__ == "__main__":
    main()
