"""
Silent Speech - Audio Chat Terminal App with Gemini Integration

A real-time audio visualization and voice-to-text chat interface that uses
Google's Gemini AI for speech transcription.

Features:
- Real-time audio capture and visualization
- Voice-to-text transcription via Gemini AI
- Auto copy to clipboard functionality  
- Responsive terminal UI with Rich library
- Cross-platform keyboard input handling
"""

__version__ = "0.1.3"
__author__ = "Silent Speech Team"
__email__ = "info@silentspeech.dev"

from .main import main, cli_main

__all__ = ["main", "cli_main"]