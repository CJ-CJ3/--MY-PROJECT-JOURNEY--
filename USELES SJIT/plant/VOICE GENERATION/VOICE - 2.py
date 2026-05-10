import requests
import os
import sys
import time
import subprocess
import platform
import tempfile
import base64
from pathlib import Path
from dotenv import load_dotenv


# ============================================================
# LOAD ENVIRONMENT VARIABLES FROM .env FILE
# ============================================================
load_dotenv()

ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID")
API_TOKEN = os.getenv("CF_API_TOKEN")

# Available voices for Aura 2
AVAILABLE_VOICES = {
    "1": {"name": "Asteria", "id": "aura-2-asteria-en", "desc": "Female - American, Warm & Professional"},
    "2": {"name": "Luna", "id": "aura-2-luna-en", "desc": "Female - American, Soft & Calm"},
    "3": {"name": "Stella", "id": "aura-2-stella-en", "desc": "Female - American, Warm & Expressive"},
    "4": {"name": "Athena", "id": "aura-2-athena-en", "desc": "Female - British, Refined & Elegant"},
    "5": {"name": "Hera", "id": "aura-2-hera-en", "desc": "Female - American, Authoritative"},
    "6": {"name": "Orion", "id": "aura-2-orion-en", "desc": "Male - American, Clear & Confident"},
    "7": {"name": "Arcas", "id": "aura-2-arcas-en", "desc": "Male - American, Warm & Friendly"},
    "8": {"name": "Perseus", "id": "aura-2-perseus-en", "desc": "Male - American, Deep & Authoritative"},
    "9": {"name": "Angus", "id": "aura-2-angus-en", "desc": "Male - Irish, Warm & Friendly"},
    "10": {"name": "Orpheus", "id": "aura-2-orpheus-en", "desc": "Male - American, Rich & Smooth"},
    "11": {"name": "Helios", "id": "aura-2-helios-en", "desc": "Male - British, Clear & Polished"},
    "12": {"name": "Zeus", "id": "aura-2-zeus-en", "desc": "Male - American, Strong & Commanding"},
}


def check_credentials():
    """Verify that credentials are loaded."""
    if not ACCOUNT_ID or not API_TOKEN:
        print("\n❌ ERROR: Missing Cloudflare credentials!")
        print("\n   Create a .env file in the same folder as this script with:")
        print("   ┌─────────────────────────────────────────────────┐")
        print("   │  CF_ACCOUNT_ID=your_account_id_here            │")
        print("   │  CF_API_TOKEN=your_api_token_here              │")
        print("   └─────────────────────────────────────────────────┘")
        print(f"\n   Expected .env location: {Path('.env').resolve()}")
        print("\n   You can find these at:")
        print("   • Account ID: Cloudflare Dashboard → Overview → right sidebar")
        print("   • API Token:  Cloudflare Dashboard → My Profile → API Tokens")
        sys.exit(1)
    else:
        print(f"   ✅ Credentials loaded (Account: ...{ACCOUNT_ID[-6:]})")


def display_voices():
    """Display available voices in a formatted table."""
    print("\n" + "=" * 65)
    print("  AVAILABLE VOICES")
    print("=" * 65)
    print(f"  {'#':<4} {'Name':<12} {'Description'}")
    print("-" * 65)
    for key, voice in AVAILABLE_VOICES.items():
        print(f"  {key:<4} {voice['name']:<12} {voice['desc']}")
    print("=" * 65)


def select_voice():
    """Let user select a voice interactively."""
    display_voices()
    while True:
        choice = input("\n🎤 Select a voice (1-12) [default: 1 - Asteria]: ").strip()
        if choice == "":
            choice = "1"
        if choice in AVAILABLE_VOICES:
            selected = AVAILABLE_VOICES[choice]
            print(f"   ✅ Selected: {selected['name']} - {selected['desc']}")
            return selected
        else:
            print("   ❌ Invalid choice. Please enter a number 1-12.")


def get_text_input():
    """Get text input from user - supports single line and multi-line."""
    print("\n" + "=" * 65)
    print("  TEXT INPUT")
    print("=" * 65)
    print("  1. Type text directly")
    print("  2. Load from a .txt file")
    print("  3. Multi-line text (type END on a new line to finish)")
    print("=" * 65)

    while True:
        choice = input("\n📝 Choose input method (1/2/3) [default: 1]: ").strip()
        if choice == "":
            choice = "1"

        if choice == "1":
            text = input("\n✏️  Enter your text: ").strip()
            if text:
                return text
            print("   ❌ Text cannot be empty.")

        elif choice == "2":
            filepath = input("\n📁 Enter file path: ").strip()
            filepath = filepath.strip('"').strip("'")
            if os.path.isfile(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read().strip()
                if text:
                    print(f"   ✅ Loaded {len(text)} characters from {filepath}")
                    return text
                print("   ❌ File is empty.")
            else:
                print(f"   ❌ File not found: {filepath}")

        elif choice == "3":
            print("\n✏️  Enter your text (type END on a new line when done):")
            lines = []
            while True:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            text = "\n".join(lines).strip()
            if text:
                return text
            print("   ❌ Text cannot be empty.")

        else:
            print("   ❌ Invalid choice. Enter 1, 2, or 3.")


def generate_speech(text, voice_id, output_filename="output.mp3"):
    """
    Generate speech using Cloudflare Workers AI Aura 2 TTS.

    Args:
        text: Text to convert to speech
        voice_id: The voice model ID (e.g., "aura-2-asteria-en")
        output_filename: Name of the output file

    Returns:
        Path to output file or None on failure
    """
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/deepgram/{voice_id}"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "text": text
    }

    try:
        print(f"\n🔊 Generating speech ({len(text)} chars)...")
        response = requests.post(url, headers=headers, json=data, timeout=120)
        response.raise_for_status()

        content_type = response.headers.get("Content-Type", "")

        if "json" in content_type:
            result = response.json()
            if not result.get("success"):
                print(f"❌ API Error: {result}")
                return None
            if "result" in result:
                audio_data = base64.b64decode(result["result"])
            else:
                print(f"❌ Unexpected JSON response: {result}")
                return None
        else:
            audio_data = response.content

        if not audio_data or len(audio_data) == 0:
            print("❌ Received empty audio data")
            return None

        output_path = Path(output_filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(audio_data)

        size_kb = len(audio_data) / 1024
        print(f"✅ Audio saved as '{output_filename}' ({size_kb:.1f} KB)")
        return str(output_path)

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if response.text:
            print(f"   Response: {response.text[:500]}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

    return None


def generate_long_speech(text, voice_id, output_filename="output.mp3", max_chunk=3000, delay=0.5):
    """Generate speech for long text by splitting into chunks."""
    chunks = split_text(text, max_chunk)
    print(f"\n📝 Text is long - split into {len(chunks)} chunk(s)")

    audio_parts = []
    for i, chunk in enumerate(chunks, 1):
        print(f"\n--- Chunk {i}/{len(chunks)} ({len(chunk)} chars) ---")
        preview = chunk[:60].replace("\n", " ")
        print(f"    \"{preview}...\"")

        temp_file = f"_temp_chunk_{i}.mp3"
        result = generate_speech(chunk, voice_id, temp_file)

        if result:
            audio_data = Path(temp_file).read_bytes()
            audio_parts.append(audio_data)
            try:
                os.unlink(temp_file)
            except OSError:
                pass
        else:
            print(f"⚠️  Failed on chunk {i}, skipping...")

        if i < len(chunks):
            time.sleep(delay)

    if not audio_parts:
        print("❌ No audio generated")
        return None

    combined = b"".join(audio_parts)
    output_path = Path(output_filename)
    output_path.write_bytes(combined)

    size_kb = len(combined) / 1024
    print(f"\n✅ Combined audio saved as '{output_filename}' ({size_kb:.1f} KB)")
    return str(output_path)


def split_text(text, max_length):
    """Split text into chunks at sentence boundaries."""
    if len(text) <= max_length:
        return [text]

    chunks = []
    remaining = text.strip()

    while remaining:
        if len(remaining) <= max_length:
            chunks.append(remaining)
            break

        split_pos = -1
        for delimiter in [". ", "! ", "? ", ".\n", "!\n", "?\n"]:
            pos = remaining.rfind(delimiter, 0, max_length)
            if pos > split_pos:
                split_pos = pos + len(delimiter) - 1

        if split_pos <= 0:
            for delimiter in [", ", "; ", "\n", " "]:
                pos = remaining.rfind(delimiter, 0, max_length)
                if pos > 0:
                    split_pos = pos + len(delimiter)
                    break

        if split_pos <= 0:
            split_pos = max_length

        chunk = remaining[:split_pos].strip()
        if chunk:
            chunks.append(chunk)
        remaining = remaining[split_pos:].strip()

    return chunks


def play_audio(filepath):
    """Play an audio file using available system tools."""
    system = platform.system()
    print(f"\n▶️  Playing {filepath}...")

    try:
        if system == "Windows":
            os.startfile(filepath)
        elif system == "Darwin":
            subprocess.run(["afplay", filepath], check=True)
        elif system == "Linux":
            for player in ["mpv", "ffplay", "aplay"]:
                try:
                    cmd = [player]
                    if player == "ffplay":
                        cmd.extend(["-nodisp", "-autoexit"])
                    elif player == "mpv":
                        cmd.append("--no-video")
                    cmd.append(filepath)
                    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except FileNotFoundError:
                    continue
            print("❌ No audio player found. Install mpv or ffplay.")
    except Exception as e:
        print(f"❌ Playback error: {e}")


def get_output_filename():
    """Ask user for output filename."""
    filename = input("\n💾 Output filename [default: output.mp3]: ").strip()
    if not filename:
        filename = "output.mp3"
    if not filename.lower().endswith((".mp3", ".wav", ".ogg")):
        filename += ".mp3"
    return filename


def main_menu():
    """Main interactive menu."""
    while True:
        print("\n")
        print("=" * 65)
        print("  🔊 CLOUDFLARE AURA 2 TEXT-TO-SPEECH GENERATOR")
        print("=" * 65)
        print("  1. Generate Speech (choose voice & text)")
        print("  2. List Available Voices")
        print("  3. Quick Generate (default voice - Asteria)")
        print("  4. Exit")
        print("=" * 65)

        choice = input("\n👉 Choose an option (1-4): ").strip()

        if choice == "1":
            voice = select_voice()
            text = get_text_input()
            output_file = get_output_filename()

            print(f"\n{'=' * 65}")
            print(f"  Voice:  {voice['name']} ({voice['desc']})")
            print(f"  Text:   \"{text[:60]}{'...' if len(text) > 60 else ''}\"")
            print(f"  Length: {len(text)} characters")
            print(f"  Output: {output_file}")
            print(f"{'=' * 65}")

            confirm = input("\n🚀 Generate? (y/n) [default: y]: ").strip().lower()
            if confirm in ("", "y", "yes"):
                if len(text) > 3000:
                    result = generate_long_speech(text, voice["id"], output_file)
                else:
                    result = generate_speech(text, voice["id"], output_file)

                if result:
                    play_choice = input("\n▶️  Play audio now? (y/n) [default: y]: ").strip().lower()
                    if play_choice in ("", "y", "yes"):
                        play_audio(result)

        elif choice == "2":
            display_voices()

        elif choice == "3":
            text = input("\n✏️  Enter text (Asteria voice): ").strip()
            if text:
                output_file = "quick_output.mp3"
                if len(text) > 3000:
                    result = generate_long_speech(text, "aura-2-asteria-en", output_file)
                else:
                    result = generate_speech(text, "aura-2-asteria-en", output_file)
                if result:
                    play_audio(result)
            else:
                print("   ❌ No text entered.")

        elif choice == "4":
            print("\n👋 Goodbye!")
            sys.exit(0)

        else:
            print("   ❌ Invalid choice. Enter 1-4.")


if __name__ == "__main__":
    print("\n" + "=" * 65)
    print("  🔊 CLOUDFLARE AURA 2 TEXT-TO-SPEECH GENERATOR")
    print("  Powered by Deepgram Aura 2 via Cloudflare Workers AI")
    print("=" * 65)

    check_credentials()
    main_menu()