import asyncio
import json
import os
import sys
import wave
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional
import argparse

import pyaudio
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables from api.env
load_dotenv('api.env')


# --- CONFIGURATION ---
class Config:
    """Configuration management"""
    API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    MODEL_ID: str = 'models/lyria-realtime-exp'
    OUTPUT_DIR: Path = Path("recordings")

    # Audio settings
    FORMAT: int = pyaudio.paInt16
    CHANNELS: int = 2
    RATE: int = 48000
    CHUNK: int = 1024

    # Generation defaults
    DEFAULT_DURATION: int = 30
    DEFAULT_BPM: int = 90
    DEFAULT_BRIGHTNESS: float = 0.4
    DEFAULT_DENSITY: float = 0.5

    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.API_KEY:
            raise ValueError(
                "❌ API key not found!\n"
                "   Please create 'api.env' file with:\n"
                "   GEMINI_API_KEY=your-api-key-here"
            )
        cls.OUTPUT_DIR.mkdir(exist_ok=True)


class AudioRecorder:
    """Handles audio recording and playback"""

    def __init__(self, config: Config):
        self.config = config
        self.p: Optional[pyaudio.PyAudio] = None
        self.stream: Optional[pyaudio.Stream] = None
        self.wav_file: Optional[wave.Wave_write] = None
        self.frames_recorded: int = 0

    def __enter__(self):
        self.p = pyaudio.PyAudio()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.cleanup()

    def open(self, filename: Path):
        """Open audio stream and WAV file"""
        self.stream = self.p.open(
            format=self.config.FORMAT,
            channels=self.config.CHANNELS,
            rate=self.config.RATE,
            output=True,
            frames_per_buffer=self.config.CHUNK
        )

        self.wav_file = wave.open(str(filename), 'wb')
        self.wav_file.setnchannels(self.config.CHANNELS)
        self.wav_file.setsampwidth(self.p.get_sample_size(self.config.FORMAT))
        self.wav_file.setframerate(self.config.RATE)

    def write(self, audio_data: bytes):
        """Write audio data to stream and file"""
        if self.stream and self.wav_file:
            self.stream.write(audio_data)
            self.wav_file.writeframes(audio_data)
            self.frames_recorded += len(audio_data)

    def cleanup(self):
        """Clean up resources"""
        if self.wav_file:
            self.wav_file.close()
        if self.stream:
            self.stream.stop_stream()
            self.stream.close()
        if self.p:
            self.p.terminate()

    def get_duration(self) -> float:
        """Get recorded duration in seconds based on bytes captured"""
        if not self.p:
            return 0.0
        # Formula: total_bytes / (bytes_per_sample * channels * sample_rate)
        # For PCM 16-bit: 2 bytes per sample
        bytes_per_sample = 2  # 16-bit
        return self.frames_recorded / (bytes_per_sample * self.config.CHANNELS * self.config.RATE)


class ProgressDisplay:
    """Enhanced progress display"""

    @staticmethod
    def show_progress(current: float, total: int, extra: str = ""):
        """Show progress bar"""
        bar_length = 40
        progress = min(current / total, 1.0)
        filled = int(bar_length * progress)
        bar = "█" * filled + "░" * (bar_length - filled)
        percent = progress * 100
        # \r keeps the print on the same line
        print(f"\r⏳ [{bar}] {percent:.1f}% ({current:.1f}s / {total}s) {extra}", end='', flush=True)


async def receive_and_record(
        session,
        recorder: AudioRecorder,
        target_duration: int,
        stop_event: asyncio.Event
):
    """
    Background task: Receives audio stream and records it.
    """
    try:
        async for message in session.receive():
            if stop_event.is_set():
                break

            if message.server_content and message.server_content.audio_chunks:
                audio_data = message.server_content.audio_chunks[0].data
                recorder.write(audio_data)

                # Update visual progress based on ACTUAL audio received
                current_duration = recorder.get_duration()
                ProgressDisplay.show_progress(current_duration, target_duration)

    except asyncio.CancelledError:
        pass  # Normal shutdown
    except Exception as e:
        print(f"\n❌ Stream error: {e}")
        raise


async def generate_music(
        prompt: str,
        duration: int = Config.DEFAULT_DURATION,
        bpm: int = Config.DEFAULT_BPM,
        brightness: float = Config.DEFAULT_BRIGHTNESS,
        density: float = Config.DEFAULT_DENSITY,
        output_name: Optional[str] = None,
        save_metadata: bool = True
):
    """Generate music using Lyria API."""

    # Generate filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    if output_name:
        filename = Config.OUTPUT_DIR / f"{output_name}.wav"
        metadata_file = Config.OUTPUT_DIR / f"{output_name}_metadata.json"
    else:
        filename = Config.OUTPUT_DIR / f"lyria_{timestamp}.wav"
        metadata_file = Config.OUTPUT_DIR / f"lyria_{timestamp}_metadata.json"

    # Metadata
    metadata = {
        "timestamp": timestamp,
        "prompt": prompt,
        "target_duration": duration,
        "config": {
            "bpm": bpm,
            "brightness": brightness,
            "density": density
        }
    }

    print(f"\n{'=' * 60}")
    print(f"🎵 Lyria Music Generation")
    print(f"{'=' * 60}")
    print(f"📝 Prompt: {prompt}")
    print(f"⏱️  Target Audio: {duration}s")
    print(f"💾 Output: {filename}")
    print(f"{'=' * 60}\n")

    client = genai.Client(
        api_key=Config.API_KEY,
        http_options={'api_version': 'v1alpha'}
    )

    stop_event = asyncio.Event()

    try:
        with AudioRecorder(Config) as recorder:
            recorder.open(filename)

            async with client.aio.live.music.connect(model=Config.MODEL_ID) as session:
                # 1. Start the receiver background task
                receiver_task = asyncio.create_task(
                    receive_and_record(session, recorder, duration, stop_event)
                )

                # 2. Send configuration
                await session.set_weighted_prompts(
                    prompts=[types.WeightedPrompt(text=prompt, weight=1.0)]
                )
                await session.set_music_generation_config(
                    config=types.LiveMusicGenerationConfig(
                        bpm=bpm,
                        brightness=brightness,
                        density=density
                    )
                )

                print("🚀 Sending play command...")
                await session.play()

                # 3. SMART WAIT LOOP
                # Instead of sleeping for 'duration', we loop until we have enough DATA.
                # We add a timeout safety net (Target * 2) in case connection is slow.
                start_time = datetime.now()
                max_wait_seconds = (duration * 2) + 15

                while True:
                    current_audio_len = recorder.get_duration()
                    elapsed_real_time = (datetime.now() - start_time).total_seconds()

                    # Success Condition: We have enough audio
                    if current_audio_len >= duration:
                        break

                    # Failure Condition 1: The receiver task crashed or finished early (server hung up)
                    if receiver_task.done():
                        print("\n⚠️  Stream disconnected by server before target reached.")
                        break

                    # Failure Condition 2: Global timeout (prevent infinite loops)
                    if elapsed_real_time > max_wait_seconds:
                        print(f"\n⚠️  Timeout reached ({max_wait_seconds}s) waiting for audio.")
                        break

                    # Check frequency
                    await asyncio.sleep(0.1)

                # 4. Cleanup
                stop_event.set()
                receiver_task.cancel()
                try:
                    await receiver_task
                except asyncio.CancelledError:
                    pass

        print(f"\n\n✅ Recording complete!")
        print(f"📁 Saved to: {filename}")
        print(f"📊 Final Audio Duration: {recorder.get_duration():.2f}s")

        if save_metadata:
            metadata["actual_duration"] = recorder.get_duration()
            with open(metadata_file, 'w') as f:
                json.dump(metadata, indent=2, fp=f)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        raise


def interactive_mode():
    """Interactive mode for user input"""
    print("\n" + "=" * 60)
    print("🎵 Lyria Music Generator - Interactive Mode")
    print("=" * 60 + "\n")

    prompt = input("Your music prompt here-> ").strip()
    if not prompt:
        print("❌ Prompt cannot be empty!")
        sys.exit(1)

    duration_input = input(f"Duration in seconds (default: {Config.DEFAULT_DURATION})-> ").strip()
    duration = int(duration_input) if duration_input else Config.DEFAULT_DURATION

    # Optional params
    bpm_input = input(f"BPM (default: {Config.DEFAULT_BPM})-> ").strip()
    bpm = int(bpm_input) if bpm_input else Config.DEFAULT_BPM

    return {
        'prompt': prompt,
        'duration': duration,
        'bpm': bpm,
        'brightness': Config.DEFAULT_BRIGHTNESS,
        'density': Config.DEFAULT_DENSITY,
        'output_name': None,
        'save_metadata': True
    }


def parse_arguments():
    parser = argparse.ArgumentParser(description="Generate music with Google Gemini Lyria")
    parser.add_argument("prompt", nargs='?', type=str, default=None)
    parser.add_argument("-d", "--duration", type=int, default=Config.DEFAULT_DURATION)
    parser.add_argument("--bpm", type=int, default=Config.DEFAULT_BPM)
    parser.add_argument("--brightness", type=float, default=Config.DEFAULT_BRIGHTNESS)
    parser.add_argument("--density", type=float, default=Config.DEFAULT_DENSITY)
    parser.add_argument("-o", "--output", type=str, default=None)
    parser.add_argument("--api-key", type=str, default=None)
    parser.add_argument("-i", "--interactive", action="store_true")
    return parser.parse_args()


async def main():
    args = parse_arguments()
    if args.api_key: Config.API_KEY = args.api_key

    try:
        Config.validate()
    except ValueError as e:
        print(str(e))
        sys.exit(1)

    if args.interactive or args.prompt is None:
        params = interactive_mode()
    else:
        params = {
            'prompt': args.prompt,
            'duration': args.duration,
            'bpm': args.bpm,
            'brightness': args.brightness,
            'density': args.density,
            'output_name': args.output,
            'save_metadata': True
        }

    await generate_music(**params)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Fatal error: {e}")