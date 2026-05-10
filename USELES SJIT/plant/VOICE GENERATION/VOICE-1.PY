"""
Gemini Text-to-Speech (Free)
Splits long text into sections, generates each, combines into one WAV.
Model: gemini-2.5-flash-preview-tts
Output saved to /output folder
"""

import os
import re
import wave
import time
from datetime import datetime
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load API key from .env
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    print("❌ GEMINI_API_KEY not found in .env file")
    exit(1)

client = genai.Client(api_key=API_KEY)

# ─────────────────────────────────────────────
# OUTPUT FOLDER
# ─────────────────────────────────────────────
OUTPUT_FOLDER = "output"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)


def get_pasted_text():
    """Capture pasted multi-line text. Press Enter twice to confirm."""
    print("\nPaste your text below, then press Enter TWICE to confirm:")
    print("-" * 50)

    lines = []
    empty_count = 0

    while True:
        try:
            line = input()
            if line.strip() == "":
                empty_count += 1
                if empty_count >= 2:
                    break
                lines.append("")
            else:
                empty_count = 0
                lines.append(line)
        except EOFError:
            break

    return "\n".join(lines).strip()


def split_text(text, max_chars=200):
    """Split text into chunks by sentences."""
    text = re.sub(r'\n+', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks = []
    current = ""

    for sentence in sentences:
        if len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            parts = re.split(r'(?<=,)\s+', sentence)
            for part in parts:
                if len(current) + len(part) + 1 > max_chars:
                    if current:
                        chunks.append(current.strip())
                    current = part
                else:
                    current = f"{current} {part}".strip()
        elif len(current) + len(sentence) + 1 > max_chars:
            chunks.append(current.strip())
            current = sentence
        else:
            current = f"{current} {sentence}".strip()

    if current:
        chunks.append(current.strip())

    return chunks


def generate_section(text, voice):
    """Generate audio for one text section."""
    response = client.models.generate_content(
        model="gemini-2.5-flash-preview-tts",
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice,
                    )
                )
            ),
        ),
    )
    return response.candidates[0].content.parts[0].inline_data.data


def save_wav(audio_data, filepath):
    """Save raw PCM data as WAV."""
    with wave.open(filepath, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(24000)
        wf.writeframes(audio_data)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
VOICES = ["Zephyr", "Puck", "Charon", "Kore", "Fenrir", "Aoede", "Leda", "Orus", "Perseus"]

print("=" * 50)
print("  🔊 Gemini TTS — Long Text Support (Free)")
print("=" * 50)
print(f"  📂 Output folder: {os.path.abspath(OUTPUT_FOLDER)}")

# Voice selection
print("\n🎤 Available Voices:")
for i, v in enumerate(VOICES, 1):
    print(f"  {i}. {v}")

voice_input = input("\nChoose voice (name or number): ").strip()

if voice_input.isdigit():
    idx = int(voice_input) - 1
    voice = VOICES[idx] if 0 <= idx < len(VOICES) else "Kore"
else:
    voice = next((v for v in VOICES if v.lower() == voice_input.lower()), "Kore")

# File name
name_input = input("File name (without .wav, default: output): ").strip()
if not name_input:
    # Auto name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    name_input = f"tts_{timestamp}"

filename = os.path.join(OUTPUT_FOLDER, f"{name_input}.wav")

# Text input
text = get_pasted_text()

if not text:
    print("❌ No text entered.")
    exit(1)

# Split into sections
sections = split_text(text, max_chars=200)

print(f"\n{'=' * 50}")
print(f"  Voice    : {voice}")
print(f"  Text len : {len(text)} characters")
print(f"  Sections : {len(sections)}")
print(f"  Save to  : {filename}")
print(f"{'=' * 50}")

for i, section in enumerate(sections, 1):
    print(f"  📄 {i}: \"{section[:80]}{'...' if len(section) > 80 else ''}\"")

# Generate each section
all_audio = []

for i, section in enumerate(sections, 1):
    print(f"\n🔄 [{i}/{len(sections)}] Generating...")
    print(f"   \"{section[:100]}{'...' if len(section) > 100 else ''}\"")

    try:
        audio = generate_section(section, voice)
        all_audio.append(audio)
        print(f"   ✅ Done ({len(audio):,} bytes)")

        if i < len(sections):
            print(f"   ⏳ Waiting 3s...")
            time.sleep(3)

    except Exception as e:
        print(f"   ❌ Failed: {e}")
        if "429" in str(e) or "rate" in str(e).lower():
            print(f"   ⏳ Rate limited. Waiting 30s...")
            time.sleep(30)
            try:
                audio = generate_section(section, voice)
                all_audio.append(audio)
                print(f"   ✅ Retry OK")
            except Exception as e2:
                print(f"   ❌ Retry failed: {e2}")

if not all_audio:
    print("\n❌ No audio generated.")
    exit(1)

combined = b"".join(all_audio)
save_wav(combined, filename)

print(f"\n{'=' * 50}")
print(f"  🎉 DONE!")
print(f"  📁 File     : {filename}")
print(f"  📂 Folder   : {os.path.abspath(OUTPUT_FOLDER)}")
print(f"  🎤 Voice    : {voice}")
print(f"  📄 Sections : {len(sections)}")
print(f"  ⏱️  Duration : ~{len(combined) / (24000 * 2):.1f} seconds")
print(f"{'=' * 50}")