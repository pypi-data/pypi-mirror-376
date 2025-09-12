# Silent Speech 🎙️

Real-time audio visualization and voice-to-text chat interface powered by Google's Gemini AI.

![Python](https://img.shields.io/badge/python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-beta-yellow.svg)

## Features ✨

- 🎯 **Real-time Audio Capture** - Live microphone input with visual waveform
- 🤖 **Gemini AI Integration** - Accurate speech-to-text transcription
- 📋 **Auto Copy to Clipboard** - Toggleable automatic clipboard copying
- 🎨 **Rich Terminal UI** - Beautiful, responsive interface with color coding
- ⌨️ **Keyboard Controls** - Intuitive hotkeys for all functions
- 🔇 **Noise Filtering** - Intelligent filtering of breathing sounds and filler words
- 🚀 **Non-blocking Processing** - Responsive UI during transcription

## Installation 📦

### Via pip (Recommended)
```bash
pip install silent-speech
```

### From Source
```bash
git clone https://github.com/laspencer91/silent-speech.git
cd silent-speech
pip install -r requirements.txt
python -m silent_speech.main
```

## Quick Start 🚀

1. **Set up Gemini API Key**:
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

2. **Run the application**:
   ```bash
   silent-speech
   ```

3. **Start using**:
   - Press **SPACE** to start recording
   - Press **SPACE** again to stop and transcribe
   - Press **Q** to quit
   - Press **A** to toggle auto-copy
   - Press **C** to copy the last response

## System Requirements 🖥️

- **Python 3.8+**
- **Microphone access**
- **Internet connection** (for Gemini API)
- **Audio system**: PortAudio (usually pre-installed)

### Platform Support
- ✅ **Linux** (Full support)
- ✅ **macOS** (Full support)  
- ⚠️ **Windows** (Limited - requires WSL or compatible terminal)

## Configuration ⚙️

### Environment Variables
- `GEMINI_API_KEY` - Your Google Gemini API key (required)

### Audio Settings
The app automatically detects your default microphone. For advanced audio configuration, modify the `AudioConfig` class in `silent_speech/main.py`.

## Controls 🎮

| Key | Function |
|-----|----------|
| **SPACE** | Start/Stop recording |
| **Q** | Quit application |
| **C** | Copy last response |
| **A** | Toggle auto-copy |
| **ESC** | Quit application |

## API Key Setup 🔑

1. Visit [Google AI Studio](https://aistudio.google.com/app/apikey)
2. Create a new API key
3. Set the environment variable:
   ```bash
   # Linux/macOS
   echo 'export GEMINI_API_KEY="your-key-here"' >> ~/.bashrc
   source ~/.bashrc
   
   # Or for current session only
   export GEMINI_API_KEY="your-key-here"
   ```

## Troubleshooting 🔧

### Common Issues

**"No audio input detected"**
- Check microphone permissions
- Verify microphone is connected and working
- Try running: `python -c "import sounddevice; print(sounddevice.query_devices())"`

**"Gemini API key not found"**
- Ensure `GEMINI_API_KEY` environment variable is set
- Verify the API key is valid and active

**"Module 'tty' has no attribute 'cbreak'"**
- This typically occurs on Windows. Use WSL or a Unix-compatible terminal

**Audio dependency issues**
- Install system audio libraries:
  ```bash
  # Ubuntu/Debian
  sudo apt-get install portaudio19-dev python3-pyaudio
  
  # macOS
  brew install portaudio
  ```

## Development 🛠️

### Local Development
```bash
git clone https://github.com/laspencer91/silent-speech.git
cd silent-speech
pip install -e .
silent-speech
```

### Contributing
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License 📄

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments 🙏

- **Google Gemini AI** for speech transcription
- **Rich Library** for beautiful terminal UI
- **SoundDevice** for audio capture
- All contributors and users!

## Support 💬

- 🐛 **Issues**: [GitHub Issues](https://github.com/laspencer91/silent-speech/issues)
- 💡 **Feature Requests**: [GitHub Discussions](https://github.com/laspencer91/silent-speech/discussions)
- 📧 **Contact**: info@silentspeech.dev

---

Made with ❤️ by the Silent Speech Team