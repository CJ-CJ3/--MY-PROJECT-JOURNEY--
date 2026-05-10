"""
Sentence-by-sentence transcription using OpenAI Whisper (local, no API key).
Takes all .mp3 files from INPUT_FOLDER and saves transcripts into OUTPUT_FOLDER.
"""

from pathlib import Path
import whisper

# === CONFIG ===
INPUT_FOLDER = r"C:\Users\CJ\Desktop\NERB\input audio"
OUTPUT_FOLDER = r"C:\Users\CJ\Desktop\NERB\script\TRANSCRIPT"
MODEL_SIZE = "small"  # tiny, base, small, medium, large
LANGUAGE = None       # 'en' for English, or None for auto-detect

# Create output folder if it doesn't exist
Path(OUTPUT_FOLDER).mkdir(parents=True, exist_ok=True)

# Load Whisper model
print(f"Loading Whisper model '{MODEL_SIZE}'...")
model = whisper.load_model(MODEL_SIZE)
print("Model loaded.\n")

# Get all MP3 files
input_path = Path(INPUT_FOLDER)
mp3_files = sorted(input_path.glob("*.mp3"))

if not mp3_files:
    print(f"No MP3 files found in: {INPUT_FOLDER}")
else:
    for mp3_path in mp3_files:
        print(f"Transcribing: {mp3_path.name} ...")
        result = model.transcribe(str(mp3_path), language=LANGUAGE, verbose=False)

        # Build sentence-by-sentence transcript with timestamps
        sentences = []
        for seg in result["segments"]:
            start_time = seg["start"]
            end_time = seg["end"]
            text = seg["text"].strip()
            sentences.append(f"[{start_time:.2f} - {end_time:.2f}] {text}")

        # Save in output folder with same name
        output_file = Path(OUTPUT_FOLDER) / (mp3_path.stem + ".txt")
        output_file.write_text("\n".join(sentences), encoding="utf-8")

        print(f"Saved transcript: {output_file}")

print("\nAll files processed.")
