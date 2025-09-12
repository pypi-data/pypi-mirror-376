#!/usr/bin/env python3
"""
Audio Chat Terminal App with Gemini Integration
Real-time audio visualization and voice-to-text chat interface
"""

import asyncio
import io
import wave
import numpy as np
import sounddevice as sd
import pyperclip
from abc import ABC, abstractmethod
from typing import Optional, List, Callable
from dataclasses import dataclass
from enum import Enum
import tempfile
import os
import json
import threading
import sys
import select
import termios
import base64
import requests

from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text
from rich.live import Live
from rich.align import Align
from rich.columns import Columns
from rich import box
from rich.style import Style


class AppState(Enum):
    READY = "ready"
    RECORDING = "recording"
    PROCESSING = "processing"


@dataclass
class AudioConfig:
    sample_rate: int = 44100
    channels: int = 1
    chunk_size: int = 1024
    device: Optional[int] = None


class AIProvider(ABC):
    """Abstract base class for AI providers"""

    @abstractmethod
    async def send_audio(self, audio_data: bytes, metadata: dict) -> str:
        """Send audio data and return response"""
        pass

    @abstractmethod
    def configure(self, **kwargs):
        """Configure the provider"""
        pass


class GeminiProvider(AIProvider):
    """Gemini AI provider using API"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.configured = bool(self.api_key)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"

    def configure(self, **kwargs):
        if 'api_key' in kwargs:
            self.api_key = kwargs['api_key']
            self.configured = bool(self.api_key)

    async def send_audio(self, audio_data: bytes, metadata: dict) -> str:
        if not self.configured:
            return "❌ Gemini API key not found. Please set GEMINI_API_KEY environment variable."

        try:
            # Convert audio data to base64
            audio_b64 = base64.b64encode(audio_data).decode('utf-8')

            # Prepare the request
            url = f"{self.base_url}/models/gemini-1.5-flash:generateContent"
            params = {"key": self.api_key}

            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": "Transcribe only clear speech. Ignore breathing sounds, mouth noises, and filler sounds like 'uh', 'um'. Return only the actual words spoken."
                            },
                            {
                                "inlineData": {
                                    "mimeType": "audio/wav",
                                    "data": audio_b64
                                }
                            }
                        ]
                    }
                ]
            }

            # Make the API request
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: requests.post(url, params=params, json=payload, timeout=30)
            )

            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']['parts'][0]['text']
                    return content.strip()
                else:
                    return "❌ No response generated from Gemini"
            else:
                error_detail = response.json().get('error', {}).get('message', 'Unknown error')
                return f"❌ Gemini API error ({response.status_code}): {error_detail}"

        except requests.exceptions.Timeout:
            return "❌ Request timed out. Please try again."
        except requests.exceptions.RequestException as e:
            return f"❌ Network error: {str(e)}"
        except Exception as e:
            return f"❌ Error processing audio: {str(e)}"


class AudioCapture:
    """Handles real-time audio capture and visualization"""

    def __init__(self, config: AudioConfig):
        self.config = config
        self.is_recording = False
        self.audio_buffer = []
        self.current_volume = 0.0
        self.waveform_data = np.zeros(80)  # For terminal waveform display
        self.callbacks: List[Callable] = []

    def add_callback(self, callback: Callable):
        """Add callback for audio updates"""
        self.callbacks.append(callback)

    def _notify_callbacks(self):
        """Notify all callbacks of audio update"""
        for callback in self.callbacks:
            try:
                callback()
            except:
                pass

    def audio_callback(self, indata, frames, time, status):
        """Real-time audio callback"""
        if status:
            print(f"Audio status: {status}")

        # Calculate volume (RMS)
        volume_norm = np.sqrt(np.mean(indata**2))
        self.current_volume = min(volume_norm * 10, 1.0)  # Scale and cap at 1.0

        # Update waveform data (simple decimation for visualization)
        if len(indata) >= 80:
            # Downsample for waveform display
            decimated = indata[::len(indata)//80][:80]
            self.waveform_data = np.abs(decimated.flatten())

        # If recording, store the audio
        if self.is_recording:
            self.audio_buffer.extend(indata.flatten())

        # Notify UI to update
        self._notify_callbacks()

    async def start_stream(self):
        """Start audio stream"""
        self.stream = sd.InputStream(
            callback=self.audio_callback,
            channels=self.config.channels,
            samplerate=self.config.sample_rate,
            blocksize=self.config.chunk_size,
            device=self.config.device
        )
        self.stream.start()

    def start_recording(self):
        """Start recording audio"""
        self.audio_buffer = []
        self.is_recording = True

    def stop_recording(self) -> bytes:
        """Stop recording and return audio data as WAV bytes"""
        self.is_recording = False

        if not self.audio_buffer:
            return b""

        # Convert to WAV format
        audio_array = np.array(self.audio_buffer, dtype=np.float32)

        # Normalize audio
        if np.max(np.abs(audio_array)) > 0:
            audio_array = audio_array / np.max(np.abs(audio_array))

        # Convert to 16-bit PCM
        audio_16bit = (audio_array * 32767).astype(np.int16)

        # Create WAV file in memory
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(self.config.channels)
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.config.sample_rate)
            wav_file.writeframes(audio_16bit.tobytes())

        return wav_buffer.getvalue()

    def get_device_name(self) -> str:
        """Get current input device name"""
        try:
            devices = sd.query_devices()
            if self.config.device is None:
                device_info = sd.query_devices(kind='input')
            else:
                device_info = devices[self.config.device]
            return device_info['name']
        except:
            return "Unknown Device"

    def cleanup(self):
        """Cleanup audio resources"""
        if hasattr(self, 'stream'):
            self.stream.stop()
            self.stream.close()


class AudioChatUI:
    """Terminal UI for the audio chat application"""

    def __init__(self, audio_capture: AudioCapture, ai_provider: AIProvider):
        self.console = Console()
        self.audio_capture = audio_capture
        self.ai_provider = ai_provider
        self.state = AppState.READY
        self.last_response = "Welcome! Press SPACE to start recording your message."
        self.show_copy_button = False
        self.processing_task = None
        self.auto_copy = False  # Auto copy to clipboard setting
        self.notification_message = ""  # For temporary notifications
        self.notification_timeout = 0  # Notification display timeout

        # Add callback for audio updates
        self.audio_capture.add_callback(self._on_audio_update)

    def _on_audio_update(self):
        """Called when audio data is updated"""
        pass  # The live display will handle updates

    def _play_completion_sound(self):
        """Play a satisfying completion sound"""
        import threading
        def play_sound():
            try:
                # Generate a clean, satisfying completion sound
                duration = 0.15  # 150ms
                sample_rate = 44100
                frequencies = [523.25, 659.25, 783.99]  # C, E, G major chord
                
                # Create a pleasant chord progression
                samples = int(duration * sample_rate)
                t = np.linspace(0, duration, samples, False)
                
                # Create harmonious tones with gentle fade
                wave = np.zeros(samples)
                for i, freq in enumerate(frequencies):
                    tone = 0.3 * np.sin(freq * 2 * np.pi * t)
                    # Add gentle envelope
                    envelope = np.exp(-t * 3) * (0.3 + 0.7 * i / len(frequencies))
                    wave += tone * envelope
                
                # Normalize and play
                wave = wave / np.max(np.abs(wave)) * 0.3  # Keep volume reasonable
                sd.play(wave, sample_rate, blocking=False)
            except Exception:
                # If sound fails, continue silently
                pass
        
        # Play sound in background thread to avoid blocking UI
        threading.Thread(target=play_sound, daemon=True).start()

    def _show_notification(self, message: str, duration: float = 2.0):
        """Show a temporary notification message"""
        self.notification_message = message
        self.notification_timeout = duration

    def _create_waveform(self) -> Text:
        """Create waveform visualization"""
        waveform_chars = "▁▂▃▄▅▆▇█"
        waveform_str = ""

        for amplitude in self.audio_capture.waveform_data:
            # Scale amplitude to character range
            char_index = min(int(amplitude * len(waveform_chars) * 8), len(waveform_chars) - 1)
            waveform_str += waveform_chars[char_index]

        # Color based on state
        if self.state == AppState.RECORDING:
            return Text(waveform_str, style="bold red")
        elif self.state == AppState.PROCESSING:
            return Text(waveform_str, style="bold yellow")
        else:
            return Text(waveform_str, style="bold cyan")

    def _create_volume_bar(self) -> Text:
        """Create volume level bar"""
        bar_length = 30
        filled_length = int(self.audio_capture.current_volume * bar_length)

        bar = "█" * filled_length + "░" * (bar_length - filled_length)
        percentage = int(self.audio_capture.current_volume * 100)

        if self.state == AppState.RECORDING:
            style = "bold red"
        else:
            style = "bold green"

        return Text(f"Volume: {bar} {percentage}%", style=style)

    def _create_status_text(self) -> Text:
        """Create status message"""
        # Show notification if active
        if self.notification_timeout > 0:
            return Text(f"✅ {self.notification_message}", style="bold green")
        elif self.state == AppState.READY:
            return Text("Press SPACE to start recording...", style="white")
        elif self.state == AppState.RECORDING:
            return Text("● RECORDING - Press SPACE to send...", style="bold red")
        elif self.state == AppState.PROCESSING:
            return Text("⟳ Sending to Gemini...", style="bold yellow")
        else:
            return Text("Ready", style="white")

    def _create_response_panel(self) -> Panel:
        """Create Gemini response panel"""
        # Style the response text with bright white for better visibility
        if self.last_response.startswith("❌"):
            # Error messages in red
            response_text = Text(self.last_response, style="bold red")
        elif self.last_response == "Welcome! Press SPACE to start recording your message.":
            # Welcome message in cyan
            response_text = Text(self.last_response, style="cyan")
        else:
            # Transcribed text in bright white to make it pop
            response_text = Text(self.last_response, style="bright_white")

        if self.show_copy_button and self.last_response != "Welcome! Press SPACE to start recording your message.":
            title = "Gemini Response: [Press C to copy]"
        else:
            title = "Gemini Response:"

        return Panel(
            Align.left(response_text),
            title=title,
            box=box.ROUNDED,
            padding=(1, 2)
        )

    def create_layout(self) -> Layout:
        """Create the main UI layout"""
        layout = Layout()

        # Header
        device_name = self.audio_capture.get_device_name()
        status_indicator = "● Live" if self.state != AppState.PROCESSING else "⟳ Processing"

        header_text = Text()
        header_text.append(f"Input Device: {device_name}", style="white")
        header_text.append(" " * (50 - len(f"Input Device: {device_name}")))
        header_text.append(f"[{status_indicator}] {self.state.value.title()}",
                          style="bold green" if self.state == AppState.READY else "bold red")

        header = Panel(header_text, title="Audio Chat with Gemini", box=box.ROUNDED)

        # Waveform section
        waveform_content = Text("\n")
        waveform_content.append("Audio Waveform:\n", style="bold white")
        waveform_content.append(self._create_waveform())
        waveform_content.append("\n\n")
        waveform_content.append(self._create_volume_bar())
        waveform_content.append("\n")

        waveform_panel = Panel(Align.center(waveform_content), box=box.ROUNDED)

        # Status
        status_panel = Panel(self._create_status_text(), box=box.ROUNDED)

        # Response
        response_panel = self._create_response_panel()

        # Footer
        footer_text = Text("Controls: ", style="bold white")
        footer_text.append("[SPACE] Record/Send", style="bold cyan")
        footer_text.append(" | ", style="white")
        footer_text.append("[Q] Quit", style="bold red")
        footer_text.append(" | ", style="white")
        footer_text.append("[C] Copy Response", style="bold blue")
        footer_text.append(" | ", style="white")
        
        # Auto copy toggle display
        auto_copy_status = "ON" if self.auto_copy else "OFF"
        auto_copy_style = "bold green" if self.auto_copy else "bold yellow"
        footer_text.append(f"[A] Auto Copy: {auto_copy_status}", style=auto_copy_style)

        footer = Panel(footer_text, box=box.ROUNDED)

        # Arrange layout
        layout.split_column(
            Layout(header, size=3),
            Layout(waveform_panel, size=8),
            Layout(status_panel, size=3),
            Layout(response_panel, size=12),
            Layout(footer, size=3)
        )

        return layout

    async def _process_audio_async(self, audio_data: bytes):
        """Process audio in background to avoid blocking UI"""
        try:
            if audio_data and len(audio_data) > 44:  # Valid WAV file should be > 44 bytes
                # Send to AI provider
                response = await self.ai_provider.send_audio(audio_data, {})
                self.last_response = response
                self.show_copy_button = True
                
                # Play completion sound for successful transcription
                if response and not response.startswith("❌"):
                    self._play_completion_sound()
                
                # Auto copy if enabled
                if self.auto_copy and response and not response.startswith("❌"):
                    try:
                        pyperclip.copy(response)
                        self._show_notification("Auto-copied to clipboard!", 2.0)
                    except:
                        pass  # Ignore clipboard errors
            else:
                self.last_response = "❌ No audio recorded. Please try again."
                self.show_copy_button = False
        except Exception as e:
            self.last_response = f"❌ Error processing audio: {str(e)}"
            self.show_copy_button = False
        finally:
            self.state = AppState.READY
            self.processing_task = None

    async def handle_keypress(self, key: str):
        """Handle keyboard input"""
        if key == ' ':  # Space key
            if self.state == AppState.READY:
                # Start recording
                self.state = AppState.RECORDING
                self.audio_capture.start_recording()
            elif self.state == AppState.RECORDING:
                # Stop recording and start processing
                self.state = AppState.PROCESSING
                audio_data = self.audio_capture.stop_recording()
                
                # Start background task for API call
                self.processing_task = asyncio.create_task(self._process_audio_async(audio_data))

        elif key.lower() == 'c' and self.show_copy_button:
            # Copy response to clipboard
            try:
                pyperclip.copy(self.last_response)
                self._show_notification("Copied to clipboard!", 2.0)
            except:
                self._show_notification("Failed to copy", 1.5)
        
        elif key.lower() == 'a':
            # Toggle auto copy setting
            self.auto_copy = not self.auto_copy
            # Log to debug file
            with open("/tmp/audio_debug.log", "a") as f:
                f.write(f"Auto copy toggled to: {self.auto_copy}\n")
                f.flush()

    def _get_key(self):
        """Non-blocking keyboard input"""
        try:
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            try:
                # Set terminal to raw mode for single character input
                termios.tcsetattr(fd, termios.TCSADRAIN, termios.tcgetattr(fd))
                old_settings = termios.tcgetattr(fd)
                new_settings = old_settings[:]
                new_settings[3] &= ~(termios.ICANON | termios.ECHO)
                termios.tcsetattr(fd, termios.TCSADRAIN, new_settings)
                
                # Check if input is available
                if select.select([sys.stdin], [], [], 0.05)[0]:
                    key = sys.stdin.read(1)
                    return key
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        except Exception as e:
            # Log errors for debugging
            with open("/tmp/audio_debug.log", "a") as f:
                f.write(f"Key input error: {e}\n")
                f.flush()
        return None

    async def run(self):
        """Main application loop"""
        await self.audio_capture.start_stream()

        # Configure AI provider
        self.ai_provider.configure()

        self.running = True

        try:
            with Live(self.create_layout(), refresh_per_second=10, screen=False) as live:
                while self.running:
                    # Update the layout
                    live.update(self.create_layout())

                    # Check for key input
                    key = self._get_key()
                    if key:
                        # Log to file for debugging
                        with open("/tmp/audio_debug.log", "a") as f:
                            f.write(f"Key detected: '{key}' (ord: {ord(key)})\n")
                            f.flush()

                        if key == ' ':
                            with open("/tmp/audio_debug.log", "a") as f:
                                f.write("Handling SPACE key\n")
                                f.flush()
                            await self.handle_keypress(' ')
                        elif key.lower() == 'c':
                            with open("/tmp/audio_debug.log", "a") as f:
                                f.write("Handling C key\n")
                                f.flush()
                            await self.handle_keypress('c')
                        elif ord(key) == 27:  # ESC key
                            with open("/tmp/audio_debug.log", "a") as f:
                                f.write("Handling ESC key\n")
                                f.flush()
                            self.running = False
                        elif key.lower() == 'q':
                            with open("/tmp/audio_debug.log", "a") as f:
                                f.write("Handling Q key\n")
                                f.flush()
                            self.running = False
                        elif key.lower() == 'a':
                            with open("/tmp/audio_debug.log", "a") as f:
                                f.write("Handling A key\n")
                                f.flush()
                            await self.handle_keypress('a')

                    # Update notification timeout
                    if self.notification_timeout > 0:
                        self.notification_timeout -= 0.1
                        if self.notification_timeout <= 0:
                            self.notification_message = ""

                    await asyncio.sleep(0.1)

        except KeyboardInterrupt:
            pass
        except asyncio.CancelledError:
            pass
        finally:
            self.audio_capture.cleanup()


async def main():
    """Main entry point"""
    # Check dependencies
    try:
        import sounddevice as sd
        import pyperclip
        import rich
        import numpy
        import requests
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("Please install required packages:")
        print("pip install sounddevice pyperclip rich numpy requests")
        return

    # Initialize components
    config = AudioConfig()
    audio_capture = AudioCapture(config)
    ai_provider = GeminiProvider()

    # Create and run UI
    ui = AudioChatUI(audio_capture, ai_provider)

    print("Starting Audio Chat Application...")
    print("Press SPACE to record, ESC to quit")
    print("Make sure your microphone is working!")

    try:
        await ui.run()
    except KeyboardInterrupt:
        pass
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Application error: {e}")
    finally:
        audio_capture.cleanup()


def cli_main():
    """Console script entry point"""
    asyncio.run(main())


if __name__ == "__main__":
    cli_main()
