#!/usr/bin/env python3
"""
🎵 Lyria Music Studio - Advanced Music Generator
================================================

An enhanced music generation tool powered by Google's Gemini Lyria API.
Features rich terminal UI, audio effects, and more.

Version: 2.0.0
"""

import asyncio
import json
import os
import sys
import wave
import struct
import random
import math
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable, Tuple
import argparse
import threading
import time

try:
    import pyaudio
    from google import genai
    from google.genai import types
    from dotenv import load_dotenv
except ImportError as e:
    print(f"❌ Missing dependency: {e}")
    print("   Install with: pip install pyaudio google-genai python-dotenv")
    sys.exit(1)

# Optional rich library for enhanced UI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
    from rich.table import Table
    from rich.prompt import Prompt, IntPrompt, FloatPrompt, Confirm
    from rich.layout import Layout
    from rich.live import Live
    from rich.text import Text
    from rich.style import Style
    from rich.markdown import Markdown
    from rich import box

    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# Optional audio processing libraries
try:
    import numpy as np

    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

load_dotenv('api.env')

# Suppress experimental warnings
import warnings

warnings.filterwarnings("ignore", category=UserWarning, message=".*Experimental.*")
warnings.filterwarnings("ignore", message=".*experimental.*")


# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION & CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

class AudioFormat(Enum):
    """Supported audio formats"""
    WAV = "wav"
    RAW = "raw"


class GenerationStatus(Enum):
    """Generation status states"""
    PENDING = auto()
    GENERATING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELLED = auto()


@dataclass
class AudioSettings:
    """Audio configuration settings"""
    format: int = pyaudio.paInt16
    channels: int = 2
    sample_rate: int = 48000
    chunk_size: int = 1024
    bytes_per_sample: int = 2  # 16-bit

    def get_bytes_per_second(self) -> int:
        return self.bytes_per_sample * self.channels * self.sample_rate


@dataclass
class GenerationConfig:
    """Music generation configuration"""
    prompt: str
    duration: int = 30
    bpm: int = 90
    brightness: float = 0.5
    density: float = 0.5
    temperature: float = 1.0

    # Audio effects
    fade_in: float = 0.0  # seconds
    fade_out: float = 0.0  # seconds
    normalize: bool = False

    # Output settings
    output_name: Optional[str] = None
    save_metadata: bool = True

    @staticmethod
    def auto_brightness() -> float:
        """Generate automatic brightness value"""
        return round(random.uniform(0.3, 0.7), 2)

    @staticmethod
    def auto_density() -> float:
        """Generate automatic density value"""
        return round(random.uniform(0.3, 0.7), 2)

    @staticmethod
    def auto_temperature() -> float:
        """Generate automatic temperature/chaos value"""
        return round(random.uniform(0.8, 1.2), 2)

    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        if not self.prompt or not self.prompt.strip():
            errors.append("Prompt cannot be empty")
        if self.duration < 5:
            errors.append("Duration must be at least 5 seconds")
        if self.duration > 300:
            errors.append("Duration cannot exceed 300 seconds (5 minutes)")
        if not 20 <= self.bpm <= 200:
            errors.append("BPM must be between 20 and 200")
        if self.fade_in < 0 or self.fade_out < 0:
            errors.append("Fade values cannot be negative")
        if self.fade_in + self.fade_out > self.duration:
            errors.append("Combined fade duration exceeds track duration")
        return errors


@dataclass
class GenerationResult:
    """Result of a music generation"""
    config: GenerationConfig
    status: GenerationStatus
    output_path: Optional[Path] = None
    actual_duration: float = 0.0
    error_message: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    generation_time: float = 0.0


class Config:
    """Global configuration management"""
    API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MODEL_ID: str = 'models/lyria-realtime-exp'

    # Directories
    BASE_DIR: Path = Path(__file__).parent if "__file__" in dir() else Path(".")
    OUTPUT_DIR: Path = BASE_DIR / "recordings"

    # Audio settings
    AUDIO: AudioSettings = AudioSettings()

    # Generation defaults
    DEFAULT_DURATION: int = 30
    DEFAULT_BPM: int = 90

    # Network settings
    MAX_RETRIES: int = 3
    RETRY_DELAY: float = 2.0
    TIMEOUT_MULTIPLIER: float = 2.0
    CONNECTION_TIMEOUT: float = 30.0

    @classmethod
    def initialize(cls):
        """Initialize configuration and directories"""
        cls.OUTPUT_DIR.mkdir(exist_ok=True)

    @classmethod
    def validate(cls) -> List[str]:
        """Validate configuration and return errors"""
        errors = []
        if not cls.API_KEY:
            errors.append(
                "API key not found! Create 'api.env' with: GEMINI_API_KEY=your-key"
            )
        return errors


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIO PROCESSING
# ═══════════════════════════════════════════════════════════════════════════════

class AudioProcessor:
    """Audio processing utilities"""

    @staticmethod
    def apply_fade(
            audio_data: bytes,
            sample_rate: int,
            channels: int,
            fade_in: float = 0.0,
            fade_out: float = 0.0
    ) -> bytes:
        """Apply fade in/out effects to audio data"""
        if not NUMPY_AVAILABLE:
            return audio_data

        if fade_in == 0.0 and fade_out == 0.0:
            return audio_data

        # Convert bytes to numpy array
        samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        total_samples = len(samples)

        # Apply fade in
        if fade_in > 0:
            fade_in_samples = int(fade_in * sample_rate * channels)
            fade_in_samples = min(fade_in_samples, total_samples)
            fade_in_curve = np.linspace(0, 1, fade_in_samples) ** 2  # Quadratic curve
            samples[:fade_in_samples] *= fade_in_curve

        # Apply fade out
        if fade_out > 0:
            fade_out_samples = int(fade_out * sample_rate * channels)
            fade_out_samples = min(fade_out_samples, total_samples)
            fade_out_curve = np.linspace(1, 0, fade_out_samples) ** 2
            samples[-fade_out_samples:] *= fade_out_curve

        return samples.astype(np.int16).tobytes()

    @staticmethod
    def normalize(audio_data: bytes, target_db: float = -3.0) -> bytes:
        """Normalize audio to target dB level"""
        if not NUMPY_AVAILABLE:
            return audio_data

        samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)

        if len(samples) == 0:
            return audio_data

        # Find peak
        peak = np.max(np.abs(samples))
        if peak == 0:
            return audio_data

        # Calculate gain needed
        target_linear = 10 ** (target_db / 20) * 32767
        gain = target_linear / peak

        # Apply gain with clipping protection
        samples = np.clip(samples * gain, -32768, 32767)

        return samples.astype(np.int16).tobytes()

    @staticmethod
    def get_peak_levels(audio_data: bytes, chunk_size: int = 4096) -> List[float]:
        """Get peak levels for visualization"""
        if not NUMPY_AVAILABLE:
            return []

        samples = np.frombuffer(audio_data, dtype=np.int16)
        peaks = []

        for i in range(0, len(samples), chunk_size):
            chunk = samples[i:i + chunk_size]
            if len(chunk) > 0:
                peak = np.max(np.abs(chunk)) / 32768.0
                peaks.append(peak)

        return peaks

    @staticmethod
    def calculate_rms(audio_data: bytes) -> float:
        """Calculate RMS level of audio"""
        if not NUMPY_AVAILABLE:
            return 0.0

        samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32)
        if len(samples) == 0:
            return 0.0

        return np.sqrt(np.mean(samples ** 2)) / 32768.0


# ═══════════════════════════════════════════════════════════════════════════════
# AUDIO RECORDER
# ═══════════════════════════════════════════════════════════════════════════════

class AudioRecorder:
    """Enhanced audio recording with buffering and real-time processing"""

    def __init__(self, audio_settings: AudioSettings):
        self.settings = audio_settings
        self.p: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.wav_file: Optional[wave.Wave_write] = None
        self.audio_buffer: bytearray = bytearray()
        self.frames_recorded: int = 0
        self._lock = threading.Lock()
        self._peak_level: float = 0.0
        self._is_playing: bool = False

    def __enter__(self):
        self.p = pyaudio.PyAudio()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def open(self, filename: Path, play_audio: bool = True):
        """Open audio stream and WAV file"""
        self._is_playing = play_audio

        if play_audio:
            self.stream = self.p.open(
                format=self.settings.format,
                channels=self.settings.channels,
                rate=self.settings.sample_rate,
                output=True,
                frames_per_buffer=self.settings.chunk_size
            )

        self.wav_file = wave.open(str(filename), 'wb')
        self.wav_file.setnchannels(self.settings.channels)
        self.wav_file.setsampwidth(self.p.get_sample_size(self.settings.format))
        self.wav_file.setframerate(self.settings.sample_rate)

    def write(self, audio_data: bytes):
        """Write audio data to stream and file"""
        with self._lock:
            if self.stream and self._is_playing:
                try:
                    self.stream.write(audio_data)
                except Exception:
                    pass  # Handle buffer underrun gracefully

            if self.wav_file:
                self.wav_file.writeframes(audio_data)

            self.audio_buffer.extend(audio_data)
            self.frames_recorded += len(audio_data)

            # Update peak level for visualization
            if NUMPY_AVAILABLE and len(audio_data) > 0:
                samples = np.frombuffer(audio_data, dtype=np.int16)
                self._peak_level = np.max(np.abs(samples)) / 32768.0

    def get_audio_data(self) -> bytes:
        """Get all recorded audio data"""
        with self._lock:
            return bytes(self.audio_buffer)

    def get_duration(self) -> float:
        """Get recorded duration in seconds"""
        return self.frames_recorded / self.settings.get_bytes_per_second()

    def get_peak_level(self) -> float:
        """Get current peak level (0.0 to 1.0)"""
        return self._peak_level

    def reset(self):
        """Reset buffer for retry"""
        with self._lock:
            self.audio_buffer = bytearray()
            self.frames_recorded = 0
            self._peak_level = 0.0

    def cleanup(self):
        """Clean up resources"""
        if self.wav_file:
            self.wav_file.close()
            self.wav_file = None
        if self.stream:
            try:
                self.stream.stop_stream()
                self.stream.close()
            except Exception:
                pass
            self.stream = None
        if self.p:
            self.p.terminate()
            self.p = None


# ═══════════════════════════════════════════════════════════════════════════════
# VISUALIZATION
# ═══════════════════════════════════════════════════════════════════════════════

class Visualizer:
    """Real-time audio visualization"""

    BARS = "▁▂▃▄▅▆▇█"

    @classmethod
    def level_bar(cls, level: float, width: int = 20) -> str:
        """Create a level meter bar"""
        filled = int(level * width)
        bar_chars = []

        for i in range(width):
            if i < filled:
                bar_chars.append("█")
            else:
                bar_chars.append("░")

        return "".join(bar_chars)

    @classmethod
    def waveform(cls, audio_data: bytes, width: int = 60) -> str:
        """Generate ASCII waveform representation"""
        if not NUMPY_AVAILABLE or len(audio_data) == 0:
            return "─" * width

        samples = np.frombuffer(audio_data, dtype=np.int16)

        # Downsample to width
        chunk_size = max(1, len(samples) // width)
        peaks = []
        for i in range(0, len(samples), chunk_size):
            chunk = samples[i:i + chunk_size]
            if len(chunk) > 0:
                peaks.append(np.max(np.abs(chunk)) / 32768.0)

        # Map to characters
        chars = " ▁▂▃▄▅▆▇█"
        result = []
        for peak in peaks[:width]:
            idx = min(int(peak * len(chars)), len(chars) - 1)
            result.append(chars[idx])

        return "".join(result)


# ═══════════════════════════════════════════════════════════════════════════════
# PROGRESS DISPLAY
# ═══════════════════════════════════════════════════════════════════════════════

class ProgressDisplay(ABC):
    """Abstract base for progress displays"""

    @abstractmethod
    def update(self, current: float, total: float, **kwargs):
        pass

    @abstractmethod
    def complete(self, message: str):
        pass

    @abstractmethod
    def error(self, message: str):
        pass

    @abstractmethod
    def info(self, message: str):
        pass


class SimpleProgressDisplay(ProgressDisplay):
    """Simple terminal progress display"""

    def __init__(self):
        self.last_update = 0

    def update(self, current: float, total: float, **kwargs):
        now = time.time()
        if now - self.last_update < 0.1:  # Rate limit updates
            return
        self.last_update = now

        bar_length = 40
        progress = min(current / total, 1.0) if total > 0 else 0
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        percent = progress * 100

        level = kwargs.get('level', 0.0)
        level_bar = Visualizer.level_bar(level, 10)

        print(f"\r⏳ [{bar}] {percent:5.1f}% ({current:.1f}s/{total}s) |{level_bar}|", end='', flush=True)

    def complete(self, message: str):
        print(f"\n✅ {message}")

    def error(self, message: str):
        print(f"\n❌ {message}")

    def info(self, message: str):
        print(f"\n⚠️  {message}")


class RichProgressDisplay(ProgressDisplay):
    """Rich terminal progress display"""

    def __init__(self):
        self.progress = None
        self.task = None

    def start(self, total: float, description: str = "Generating"):
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=40),
            TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
            TextColumn("({task.completed:.1f}s / {task.total:.0f}s)"),
            TimeElapsedColumn(),
            console=console
        )
        self.progress.start()
        self.task = self.progress.add_task(description, total=total)

    def update(self, current: float, total: float, **kwargs):
        if self.progress and self.task is not None:
            self.progress.update(self.task, completed=current)

    def complete(self, message: str):
        if self.progress:
            self.progress.stop()
        console.print(f"\n[bold green]✅ {message}[/]")

    def error(self, message: str):
        if self.progress:
            self.progress.stop()
        console.print(f"\n[bold red]❌ {message}[/]")

    def info(self, message: str):
        if self.progress:
            self.progress.stop()
        console.print(f"\n[bold yellow]⚠️  {message}[/]")

    def stop(self):
        if self.progress:
            self.progress.stop()

    def restart(self, total: float, description: str = "Generating"):
        """Restart progress for retry"""
        self.stop()
        self.start(total, description)


# ═══════════════════════════════════════════════════════════════════════════════
# MUSIC GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class MusicGenerator:
    """Core music generation engine"""

    def __init__(self, config: Config):
        self.config = config
        self.client = None

    def _create_client(self):
        """Create API client"""
        return genai.Client(
            api_key=self.config.API_KEY,
            http_options={'api_version': 'v1alpha'}
        )

    async def _receive_and_record(
            self,
            session,
            recorder: AudioRecorder,
            target_duration: int,
            stop_event: asyncio.Event,
            progress: Optional[ProgressDisplay] = None
    ):
        """Background task to receive and record audio stream"""
        last_data_time = time.time()
        timeout_seconds = 20  # Consider connection dead after 20s of no data

        try:
            async for message in session.receive():
                if stop_event.is_set():
                    break

                if message.server_content and message.server_content.audio_chunks:
                    audio_data = message.server_content.audio_chunks[0].data
                    recorder.write(audio_data)
                    last_data_time = time.time()

                    if progress:
                        progress.update(
                            recorder.get_duration(),
                            target_duration,
                            level=recorder.get_peak_level()
                        )
                else:
                    # Check for timeout even when receiving empty messages
                    if time.time() - last_data_time > timeout_seconds:
                        raise RuntimeError("No audio data received for too long")

        except asyncio.CancelledError:
            pass
        except Exception as e:
            error_msg = str(e)
            # Check if we have enough audio despite the error
            if recorder.get_duration() >= target_duration * 0.9:
                return  # Close enough, consider it done
            raise RuntimeError(f"Stream error: {error_msg}")

    async def _generate_with_retry(
            self,
            gen_config: GenerationConfig,
            filename: Path,
            play_audio: bool,
            progress_display: ProgressDisplay
    ) -> Tuple[bytes, float]:
        """Generate music with retry logic"""

        last_error = None

        for attempt in range(self.config.MAX_RETRIES):
            if attempt > 0:
                wait_time = self.config.RETRY_DELAY * (attempt + 1)
                progress_display.info(f"Retry {attempt}/{self.config.MAX_RETRIES - 1} in {wait_time:.0f}s...")
                await asyncio.sleep(wait_time)

                if RICH_AVAILABLE and isinstance(progress_display, RichProgressDisplay):
                    progress_display.restart(gen_config.duration, f"Generating (attempt {attempt + 1})")

            client = self._create_client()
            stop_event = asyncio.Event()

            try:
                with AudioRecorder(self.config.AUDIO) as recorder:
                    recorder.open(filename, play_audio=play_audio)

                    async with client.aio.live.music.connect(model=self.config.MODEL_ID) as session:
                        # Start receiver task
                        receiver_task = asyncio.create_task(
                            self._receive_and_record(
                                session, recorder, gen_config.duration,
                                stop_event, progress_display
                            )
                        )

                        # Configure generation
                        await session.set_weighted_prompts(
                            prompts=[types.WeightedPrompt(text=gen_config.prompt, weight=1.0)]
                        )
                        await session.set_music_generation_config(
                            config=types.LiveMusicGenerationConfig(
                                bpm=gen_config.bpm,
                                brightness=gen_config.brightness,
                                density=gen_config.density
                            )
                        )

                        # Start playback
                        await session.play()

                        # Wait for target duration with timeout
                        max_wait = (gen_config.duration * self.config.TIMEOUT_MULTIPLIER) + 30
                        wait_start = time.time()

                        while True:
                            current_duration = recorder.get_duration()
                            elapsed = time.time() - wait_start

                            if current_duration >= gen_config.duration:
                                break

                            if receiver_task.done():
                                # Check if task failed
                                try:
                                    receiver_task.result()
                                except Exception as e:
                                    raise e
                                break

                            if elapsed > max_wait:
                                break

                            await asyncio.sleep(0.05)

                        # Cleanup
                        stop_event.set()
                        receiver_task.cancel()
                        try:
                            await receiver_task
                        except asyncio.CancelledError:
                            pass
                        except Exception:
                            pass

                    # Get final audio data
                    audio_data = recorder.get_audio_data()
                    actual_duration = recorder.get_duration()

                    # Check if we got enough audio
                    if actual_duration >= gen_config.duration * 0.5:
                        return audio_data, actual_duration
                    else:
                        raise RuntimeError(f"Insufficient audio generated: {actual_duration:.1f}s")

            except Exception as e:
                last_error = e
                error_str = str(e)

                # Don't retry on certain errors
                if "API key" in error_str or "authentication" in error_str.lower():
                    raise

                if attempt < self.config.MAX_RETRIES - 1:
                    if RICH_AVAILABLE:
                        console.print(f"\n[yellow]⚠️  Attempt {attempt + 1} failed: {error_str}[/]")
                    else:
                        print(f"\n⚠️  Attempt {attempt + 1} failed: {error_str}")
                    continue
                else:
                    raise

        raise last_error or RuntimeError("Generation failed after all retries")

    async def generate(
            self,
            gen_config: GenerationConfig,
            play_audio: bool = True,
            progress_display: Optional[ProgressDisplay] = None
    ) -> GenerationResult:
        """Generate music with the given configuration"""

        # Validate configuration
        errors = gen_config.validate()
        if errors:
            return GenerationResult(
                config=gen_config,
                status=GenerationStatus.FAILED,
                error_message="; ".join(errors)
            )

        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if gen_config.output_name:
            filename = self.config.OUTPUT_DIR / f"{gen_config.output_name}.wav"
        else:
            # Create a safe filename from prompt
            safe_prompt = "".join(c if c.isalnum() else "_" for c in gen_config.prompt[:30])
            filename = self.config.OUTPUT_DIR / f"lyria_{timestamp}_{safe_prompt}.wav"

        # Ensure unique filename
        counter = 1
        original_stem = filename.stem
        while filename.exists():
            filename = filename.with_stem(f"{original_stem}_{counter}")
            counter += 1

        start_time = time.time()
        result = GenerationResult(
            config=gen_config,
            status=GenerationStatus.GENERATING
        )

        # Create progress display if not provided
        if progress_display is None:
            if RICH_AVAILABLE:
                progress_display = RichProgressDisplay()
                progress_display.start(gen_config.duration)
            else:
                progress_display = SimpleProgressDisplay()
        elif RICH_AVAILABLE and isinstance(progress_display, RichProgressDisplay):
            progress_display.start(gen_config.duration)

        try:
            # Generate with retry logic
            audio_data, actual_duration = await self._generate_with_retry(
                gen_config, filename, play_audio, progress_display
            )

            # Post-processing
            if audio_data and (gen_config.fade_in > 0 or gen_config.fade_out > 0 or gen_config.normalize):
                processed_data = audio_data

                if gen_config.normalize:
                    processed_data = AudioProcessor.normalize(processed_data)

                if gen_config.fade_in > 0 or gen_config.fade_out > 0:
                    processed_data = AudioProcessor.apply_fade(
                        processed_data,
                        self.config.AUDIO.sample_rate,
                        self.config.AUDIO.channels,
                        gen_config.fade_in,
                        gen_config.fade_out
                    )

                # Rewrite file with processed audio
                if processed_data != audio_data:
                    with wave.open(str(filename), 'wb') as wav_file:
                        wav_file.setnchannels(self.config.AUDIO.channels)
                        wav_file.setsampwidth(self.config.AUDIO.bytes_per_sample)
                        wav_file.setframerate(self.config.AUDIO.sample_rate)
                        wav_file.writeframes(processed_data)

            # Update result
            result.status = GenerationStatus.COMPLETED
            result.output_path = filename
            result.actual_duration = actual_duration
            result.generation_time = time.time() - start_time

            # Save metadata
            if gen_config.save_metadata:
                metadata_file = filename.with_suffix('.json')
                metadata = {
                    "prompt": gen_config.prompt,
                    "target_duration": gen_config.duration,
                    "actual_duration": actual_duration,
                    "bpm": gen_config.bpm,
                    "brightness": gen_config.brightness,
                    "density": gen_config.density,
                    "temperature": gen_config.temperature,
                    "fade_in": gen_config.fade_in,
                    "fade_out": gen_config.fade_out,
                    "normalized": gen_config.normalize,
                    "timestamp": timestamp,
                    "generation_time": result.generation_time
                }
                with open(metadata_file, 'w') as f:
                    json.dump(metadata, f, indent=2)

            progress_display.complete(f"Saved to: {filename}")

        except KeyboardInterrupt:
            result.status = GenerationStatus.CANCELLED
            result.error_message = "Cancelled by user"
            progress_display.error("Generation cancelled")
            # Clean up partial file
            if filename.exists():
                filename.unlink()

        except Exception as e:
            result.status = GenerationStatus.FAILED
            result.error_message = str(e)
            progress_display.error(f"Generation failed: {e}")
            # Clean up partial file
            if filename.exists():
                filename.unlink()

        finally:
            if RICH_AVAILABLE and isinstance(progress_display, RichProgressDisplay):
                progress_display.stop()

        return result


# ═══════════════════════════════════════════════════════════════════════════════
# USER INTERFACE
# ═══════════════════════════════════════════════════════════════════════════════

class UserInterface:
    """User interface handler"""

    def __init__(self, generator: MusicGenerator):
        self.generator = generator

    def print_header(self):
        """Print application header"""
        if RICH_AVAILABLE:
            header = """
╔══════════════════════════════════════════════════════════════╗
║                  🎵 LYRIA MUSIC STUDIO 🎵                    ║
║              Advanced AI Music Generation                     ║
╚══════════════════════════════════════════════════════════════╝
            """
            console.print(Panel(header.strip(), style="bold magenta"))
        else:
            print("\n" + "=" * 60)
            print("🎵 LYRIA MUSIC STUDIO - Advanced AI Music Generation")
            print("=" * 60 + "\n")

    def interactive_menu(self) -> Optional[GenerationConfig]:
        """Interactive menu for generation configuration"""
        self.print_header()

        if RICH_AVAILABLE:
            console.print("\n[bold]What would you like to do?[/]")
            console.print("  [cyan]1.[/] Generate from custom prompt")
            console.print("  [cyan]0.[/] Exit")

            choice = Prompt.ask("\nYour choice", choices=["0", "1"], default="1")
        else:
            print("\nWhat would you like to do?")
            print("  1. Generate from custom prompt")
            print("  0. Exit")
            choice = input("\nYour choice [1]: ").strip() or "1"

        if choice == "0":
            return None
        elif choice == "1":
            return self._custom_prompt_flow()

        return None

    def _custom_prompt_flow(self) -> GenerationConfig:
        """Flow for custom prompt generation"""
        # Auto-generate values for brightness, density, temperature
        auto_brightness = GenerationConfig.auto_brightness()
        auto_density = GenerationConfig.auto_density()
        auto_temperature = GenerationConfig.auto_temperature()

        if RICH_AVAILABLE:
            console.print("\n[bold cyan]📝 Custom Prompt Generation[/]")
            prompt = Prompt.ask("Enter your music prompt")
            duration = IntPrompt.ask("Duration (seconds)", default=Config.DEFAULT_DURATION)
            bpm = IntPrompt.ask("BPM", default=Config.DEFAULT_BPM)

            # Show auto-generated values
            console.print(
                f"\n[dim]Auto settings: Brightness={auto_brightness}, Density={auto_density}, Chaos={auto_temperature}[/]")

            # Effects
            if Confirm.ask("Apply audio effects?", default=False):
                fade_in = FloatPrompt.ask("Fade in (seconds)", default=0.0)
                fade_out = FloatPrompt.ask("Fade out (seconds)", default=0.0)
                normalize = Confirm.ask("Normalize audio?", default=False)
            else:
                fade_in = fade_out = 0.0
                normalize = False
        else:
            print("\n📝 Custom Prompt Generation")
            prompt = input("Enter your music prompt: ").strip()
            duration = int(input(f"Duration [{Config.DEFAULT_DURATION}]: ").strip() or Config.DEFAULT_DURATION)
            bpm = int(input(f"BPM [{Config.DEFAULT_BPM}]: ").strip() or Config.DEFAULT_BPM)

            # Show auto-generated values
            print(f"\nAuto settings: Brightness={auto_brightness}, Density={auto_density}, Chaos={auto_temperature}")

            fade_in = fade_out = 0.0
            normalize = False

        return GenerationConfig(
            prompt=prompt,
            duration=duration,
            bpm=bpm,
            brightness=auto_brightness,
            density=auto_density,
            temperature=auto_temperature,
            fade_in=fade_in,
            fade_out=fade_out,
            normalize=normalize
        )


# ═══════════════════════════════════════════════════════════════════════════════
# CLI ARGUMENT PARSER
# ═══════════════════════════════════════════════════════════════════════════════

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="🎵 Lyria Music Studio - Advanced AI Music Generation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python lyria.py "epic orchestral cinematic music"
  python lyria.py -i
  python lyria.py "trap beat" --bpm 140 --fade-out 2.0 --normalize
        """
    )

    # Positional
    parser.add_argument("prompt", nargs='?', type=str, default=None,
                        help="Music generation prompt")

    # Generation options
    gen_group = parser.add_argument_group('Generation Options')
    gen_group.add_argument("-d", "--duration", type=int, default=Config.DEFAULT_DURATION,
                           help=f"Duration in seconds (default: {Config.DEFAULT_DURATION})")
    gen_group.add_argument("--bpm", type=int, default=Config.DEFAULT_BPM,
                           help=f"Beats per minute (default: {Config.DEFAULT_BPM})")

    # Audio effects
    fx_group = parser.add_argument_group('Audio Effects')
    fx_group.add_argument("--fade-in", type=float, default=0.0,
                          help="Fade in duration in seconds")
    fx_group.add_argument("--fade-out", type=float, default=0.0,
                          help="Fade out duration in seconds")
    fx_group.add_argument("--normalize", action="store_true",
                          help="Normalize audio levels")

    # Output options
    out_group = parser.add_argument_group('Output Options')
    out_group.add_argument("-o", "--output", type=str, default=None,
                           help="Output filename (without extension)")
    out_group.add_argument("--no-play", action="store_true",
                           help="Don't play audio during generation")
    out_group.add_argument("--no-metadata", action="store_true",
                           help="Don't save metadata JSON")

    # Other options
    parser.add_argument("-i", "--interactive", action="store_true",
                        help="Run in interactive mode")
    parser.add_argument("--api-key", type=str, default=None,
                        help="Gemini API key (overrides env)")
    parser.add_argument("-v", "--version", action="version", version="Lyria Studio 2.0.0")

    return parser.parse_args()


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Main application entry point"""
    args = parse_arguments()

    # Override API key if provided
    if args.api_key:
        Config.API_KEY = args.api_key

    # Initialize configuration
    Config.initialize()

    # Validate configuration
    errors = Config.validate()
    if errors:
        for error in errors:
            if RICH_AVAILABLE:
                console.print(f"[red]❌ {error}[/]")
            else:
                print(f"❌ {error}")
        sys.exit(1)

    # Create generator
    generator = MusicGenerator(Config)
    ui = UserInterface(generator)

    # Determine generation config
    gen_config: Optional[GenerationConfig] = None

    if args.interactive or args.prompt is None:
        # Interactive mode
        while True:
            gen_config = ui.interactive_menu()
            if gen_config is None:
                if RICH_AVAILABLE:
                    console.print("\n[bold cyan]👋 Thanks for using Lyria Studio![/]")
                else:
                    print("\n👋 Thanks for using Lyria Studio!")
                return

            result = await generator.generate(gen_config, play_audio=not args.no_play)

            # Ask to continue
            if RICH_AVAILABLE:
                if not Confirm.ask("\nGenerate another track?", default=True):
                    break
            else:
                if input("\nGenerate another? [Y/n]: ").strip().lower() == 'n':
                    break

    else:
        # Direct prompt mode - auto-generate brightness, density, temperature
        gen_config = GenerationConfig(
            prompt=args.prompt,
            duration=args.duration,
            bpm=args.bpm,
            brightness=GenerationConfig.auto_brightness(),
            density=GenerationConfig.auto_density(),
            temperature=GenerationConfig.auto_temperature(),
            fade_in=args.fade_in,
            fade_out=args.fade_out,
            normalize=args.normalize,
            output_name=args.output,
            save_metadata=not args.no_metadata
        )

    if gen_config:
        # Print generation info
        if RICH_AVAILABLE:
            info_table = Table(box=box.ROUNDED, show_header=False)
            info_table.add_column("Key", style="cyan")
            info_table.add_column("Value")
            info_table.add_row("Prompt", gen_config.prompt)
            info_table.add_row("Duration", f"{gen_config.duration}s")
            info_table.add_row("BPM", str(gen_config.bpm))
            info_table.add_row("Brightness", f"{gen_config.brightness:.2f} [dim](auto)[/]")
            info_table.add_row("Density", f"{gen_config.density:.2f} [dim](auto)[/]")
            info_table.add_row("Chaos", f"{gen_config.temperature:.2f} [dim](auto)[/]")
            if gen_config.fade_in > 0 or gen_config.fade_out > 0:
                info_table.add_row("Fades", f"In: {gen_config.fade_in}s, Out: {gen_config.fade_out}s")
            if gen_config.normalize:
                info_table.add_row("Normalize", "Yes")

            console.print(Panel(info_table, title="🎵 Generation Settings"))

        result = await generator.generate(gen_config, play_audio=not args.no_play)

        if result.status == GenerationStatus.COMPLETED and RICH_AVAILABLE:
            console.print(f"\n[bold green]🎉 Generation complete![/]")
            console.print(f"[dim]File: {result.output_path}[/]")
            console.print(f"[dim]Duration: {result.actual_duration:.1f}s | Time: {result.generation_time:.1f}s[/]")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        if RICH_AVAILABLE:
            console.print("\n[yellow]👋 Interrupted by user[/]")
        else:
            print("\n👋 Interrupted by user")
    except Exception as e:
        if RICH_AVAILABLE:
            console.print(f"\n[bold red]💥 Fatal error: {e}[/]")
            console.print_exception()
        else:
            print(f"\n💥 Fatal error: {e}")
        sys.exit(1)