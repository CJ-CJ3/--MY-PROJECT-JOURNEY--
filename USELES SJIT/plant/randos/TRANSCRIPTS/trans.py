"""
Audio Transcription Script - GEOLOGY
With TIMESTAMPS enabled
"""

import os
from pathlib import Path
from datetime import datetime
import warnings

warnings.filterwarnings("ignore")

# ============== CONFIGURATION ==============
AUDIO_FOLDER = r"C:\Users\Never\Desktop\plant\PREAUDIO"
OUTPUT_FOLDER = r"C:\Users\Never\Desktop\plant\TRANSCRIPTS"
MODEL = "base"
INCLUDE_TIMESTAMPS = True  # ← ENABLED


# ===========================================


def transcribe_folder():
    audio_folder = Path(AUDIO_FOLDER)
    output_folder = Path(OUTPUT_FOLDER)

    if not audio_folder.exists():
        print(f"ERROR: Folder not found: {audio_folder}")
        input("Press Enter to exit...")
        return

    output_folder.mkdir(parents=True, exist_ok=True)

    audio_extensions = {'.mp3', '.wav', '.m4a', '.flac', '.ogg', '.wma', '.aac', '.mp4'}
    audio_files = sorted([f for f in audio_folder.iterdir()
                          if f.is_file() and f.suffix.lower() in audio_extensions])

    if not audio_files:
        print(f"No audio files found in: {audio_folder}")
        input("Press Enter to exit...")
        return

    total_size = sum(f.stat().st_size for f in audio_files) / (1024 * 1024)

    print("=" * 60)
    print("   GEOLOGY AUDIO TRANSCRIPTION")
    print("   (With Timestamps)")
    print("=" * 60)
    print(f"\nInput:  {audio_folder}")
    print(f"Output: {output_folder}")
    print(f"Model:  {MODEL}")
    print(f"\nFound {len(audio_files)} file(s) ({total_size:.1f} MB)")

    input("\nPress Enter to start...")

    print(f"\nLoading '{MODEL}' model...")

    import whisper
    model = whisper.load_model(MODEL, device="cpu")
    print("Model loaded!\n")

    start_time = datetime.now()

    for i, audio_file in enumerate(audio_files, 1):
        print(f"\n[{i}/{len(audio_files)}] {audio_file.name}")
        print("Transcribing... please wait...")

        try:
            result = model.transcribe(str(audio_file), fp16=False)

            # Format with timestamps
            lines = []
            for seg in result["segments"]:
                start_sec = seg["start"]
                end_sec = seg["end"]
                text = seg["text"].strip()

                # Format: [00:05 - 00:12] Text here
                start_fmt = f"{int(start_sec) // 60:02d}:{int(start_sec) % 60:02d}"
                end_fmt = f"{int(end_sec) // 60:02d}:{int(end_sec) % 60:02d}"

                lines.append(f"[{start_fmt} - {end_fmt}] {text}")

            transcript = "\n".join(lines)

            # Save
            output_file = output_folder / f"{audio_file.stem}_transcript.txt"

            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"Source: {audio_file.name}\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(transcript)

            print(f"✓ Saved: {output_file.name}")
            print(f"  Preview:\n{lines[0] if lines else 'No speech detected'}")

        except Exception as e:
            print(f"✗ Error: {e}")

    total_time = (datetime.now() - start_time).total_seconds() / 60

    print("\n" + "=" * 60)
    print(f"DONE! Completed in {total_time:.1f} minutes")
    print(f"Transcripts: {output_folder}")
    print("=" * 60)

    os.startfile(output_folder)
    input("\nPress Enter to exit...")


if __name__ == "__main__":
    transcribe_folder()