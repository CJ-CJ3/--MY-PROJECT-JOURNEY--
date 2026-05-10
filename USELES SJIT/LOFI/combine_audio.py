from pydub import AudioSegment
from pydub.utils import mediainfo
import os
import sys

# ── Configuration ─────────────────────────────────────────────────────
AUDIO_DIR = "AUDIO"
OUTPUT_FILE = "combined_output.mp3"
CHAPTERS_FILE = "chapters.txt"
SUPPORTED_FORMATS = (".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma")

CROSSFADE_MS = 3000    # 3-second crossfade between tracks
FADE_IN_MS = 2000      # 2-second fade-in on the very first track
FADE_OUT_MS = 5000     # 5-second fade-out on the very last track

# Normalization settings (all tracks converted to these before combining)
TARGET_SAMPLE_RATE = 44100  # Hz
TARGET_CHANNELS = 2         # stereo
TARGET_SAMPLE_WIDTH = 2     # 16-bit


def load_audio(filepath):
    """Load an audio file, letting FFmpeg auto-detect the format."""
    try:
        audio = AudioSegment.from_file(filepath)
        if len(audio) > 0 and audio.dBFS > -120:
            return audio
    except Exception:
        pass

    ext = os.path.splitext(filepath)[1].lower().lstrip(".")
    format_map = {
        "mp3": "mp3", "wav": "wav", "ogg": "ogg", "flac": "flac",
        "m4a": "mp4", "aac": "aac", "wma": "asf",
    }
    fmt = format_map.get(ext, ext)

    try:
        audio = AudioSegment.from_file(filepath, format=fmt)
        if len(audio) > 0:
            return audio
    except Exception:
        pass

    for try_fmt in ["mp3", "wav", "mp4", "ogg", "flac"]:
        try:
            audio = AudioSegment.from_file(filepath, format=try_fmt)
            if len(audio) > 0:
                return audio
        except Exception:
            continue

    return None


def normalize_track(audio):
    """Normalize a track to consistent sample rate, channels, and bit depth."""
    audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)
    audio = audio.set_channels(TARGET_CHANNELS)
    audio = audio.set_sample_width(TARGET_SAMPLE_WIDTH)
    return audio


def format_timestamp(ms):
    """Convert milliseconds to HH:MM:SS or MM:SS timestamp string."""
    total_seconds = int(ms / 1000)
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


def clean_track_name(filename):
    """
    Derive a chapter title from a filename.
    Strips extension, leading track numbers, and common separators.
    '01 - My Song.mp3'  →  'My Song'
    '03_intro.flac'     →  'intro'
    """
    name = os.path.splitext(filename)[0]

    # Strip leading digits + optional separator (e.g. "01 - ", "03_", "1. ")
    import re
    name = re.sub(r"^\d+[\s._\-–—]*", "", name)

    # Replace underscores with spaces
    name = name.replace("_", " ").strip()

    # Fallback: if stripping left nothing, use original stem
    if not name:
        name = os.path.splitext(filename)[0]

    return name


def generate_chapters(chapter_data, chapters_file, total_ms):
    """
    Print and save YouTube-compatible chapter timestamps.
    chapter_data: list of (start_ms, track_name)
    """
    print(f"\n{'=' * 60}")
    print(f"📑 YOUTUBE CHAPTERS")
    print(f"{'=' * 60}")
    print(f"   (Copy-paste into your YouTube description)\n")

    lines = []
    for start_ms, name in chapter_data:
        timestamp = format_timestamp(start_ms)
        line = f"{timestamp} {name}"
        lines.append(line)
        print(f"   {line}")

    # Summary
    print(f"\n   ── Total: {len(lines)} chapter(s) | {format_timestamp(total_ms)} duration")

    # Write to file
    with open(chapters_file, "w", encoding="utf-8") as f:
        f.write("YOUTUBE CHAPTERS\n")
        f.write("=" * 40 + "\n\n")
        for line in lines:
            f.write(line + "\n")
        f.write(f"\nTotal duration: {format_timestamp(total_ms)}\n")

    print(f"   💾 Saved to: {chapters_file}\n")


def smooth_crossfade_combine(audio_dir, output_file):
    """Combine all audio files with smooth crossfades and a final fade-out."""

    # ── 1. Gather & sort audio files ──────────────────────────────────
    audio_files = sorted(
        [
            os.path.join(audio_dir, f)
            for f in os.listdir(audio_dir)
            if f.lower().endswith(SUPPORTED_FORMATS)
        ]
    )

    if not audio_files:
        print(f"❌ No audio files found in: {audio_dir}")
        return

    print(f"📂 Found {len(audio_files)} audio file(s):\n")
    for i, f in enumerate(audio_files, 1):
        print(f"   {i}. {os.path.basename(f)}")

    print(f"\n⚙️  Crossfade: {CROSSFADE_MS}ms | Fade-in: {FADE_IN_MS}ms | Fade-out: {FADE_OUT_MS}ms")
    print(f"⚙️  Target: {TARGET_SAMPLE_RATE}Hz, {TARGET_CHANNELS}ch, {TARGET_SAMPLE_WIDTH * 8}-bit")
    print(f"{'=' * 60}")

    # ── 2. Load and normalize all tracks ──────────────────────────────
    tracks = []
    for i, filepath in enumerate(audio_files):
        filename = os.path.basename(filepath)
        print(f"\n🔄 Loading ({i + 1}/{len(audio_files)}): {filename}")

        audio = load_audio(filepath)

        if audio is None:
            print(f"   ⚠️  SKIPPED — could not read file")
            continue

        print(f"   📊 Raw: {len(audio)}ms | {audio.frame_rate}Hz | "
              f"{audio.channels}ch | {audio.sample_width * 8}-bit | "
              f"dBFS: {audio.dBFS:.1f}")

        if audio.dBFS == float('-inf') or audio.dBFS < -100:
            print(f"   ⚠️  WARNING: Track appears to be silent! (dBFS={audio.dBFS})")
            print(f"   ⚠️  Skipping this file.")
            continue

        audio = normalize_track(audio)
        duration_sec = len(audio) / 1000

        print(f"   ✅ Normalized: {duration_sec:.1f}s | dBFS: {audio.dBFS:.1f}")
        tracks.append((filename, audio))

    if not tracks:
        print("\n❌ No valid audio was loaded. Nothing to export.")
        print("💡 Make sure FFmpeg is installed: choco install ffmpeg")
        print("💡 Try playing the source files to make sure they have audio.")
        return

    print(f"\n✅ Successfully loaded {len(tracks)} track(s)")

    # ── 3. Apply fade-in to first track ───────────────────────────────
    first_name, first_track = tracks[0]
    fade_in = min(FADE_IN_MS, len(first_track) // 2)
    first_track = first_track.fade_in(fade_in)
    tracks[0] = (first_name, first_track)
    print(f"\n🔊 Fade-in  ({fade_in}ms) → {first_name}")

    # ── 4. Apply fade-out to last track ───────────────────────────────
    last_name, last_track = tracks[-1]
    fade_out = min(FADE_OUT_MS, len(last_track) // 2)
    last_track = last_track.fade_out(fade_out)
    tracks[-1] = (last_name, last_track)
    print(f"🔇 Fade-out ({fade_out}ms) → {last_name}")

    # ── 5. Crossfade all tracks together (with chapter tracking) ──────
    print(f"\n🎵 Combining {len(tracks)} tracks with {CROSSFADE_MS}ms crossfade...\n")

    combined = tracks[0][1]
    chapter_data = [(0, clean_track_name(tracks[0][0]))]  # first track at 0:00
    print(f"   ✅ Start: {tracks[0][0]} ({len(combined)}ms)")

    for i in range(1, len(tracks)):
        name, track = tracks[i]

        max_crossfade = min(len(combined) // 2, len(track) // 2)
        safe_crossfade = min(CROSSFADE_MS, max_crossfade)

        if safe_crossfade <= 0:
            # Chapter starts where the combined audio currently ends
            chapter_start_ms = len(combined)
            combined = combined + track
            print(f"   ✅ Appended (no crossfade, track too short) → {name}")
        else:
            # During crossfade, the new track begins before the old one ends.
            # The new track's audible start = combined length - crossfade
            chapter_start_ms = len(combined) - safe_crossfade
            if safe_crossfade < CROSSFADE_MS:
                print(f"   ⚠️  Reduced crossfade to {safe_crossfade}ms for: {name}")
            combined = combined.append(track, crossfade=safe_crossfade)
            print(f"   ✅ Crossfaded ({safe_crossfade}ms) → {name}")

        chapter_data.append((chapter_start_ms, clean_track_name(name)))

    # ── 6. Final check ────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    print(f"📊 Combined audio stats:")
    print(f"   Duration:     {len(combined)}ms ({len(combined) / 1000:.1f}s)")
    print(f"   Sample rate:  {combined.frame_rate}Hz")
    print(f"   Channels:     {combined.channels}")
    print(f"   Bit depth:    {combined.sample_width * 8}-bit")
    print(f"   Volume (dBFS): {combined.dBFS:.1f}")

    if combined.dBFS == float('-inf') or combined.dBFS < -100:
        print(f"\n❌ ERROR: Combined audio is silent! Something went wrong.")
        return

    # ── 7. Generate YouTube chapters ──────────────────────────────────
    generate_chapters(chapter_data, CHAPTERS_FILE, len(combined))

    # ── 8. Export ─────────────────────────────────────────────────────
    total_ms = len(combined)
    minutes, seconds = divmod(total_ms / 1000, 60)
    hours, minutes = divmod(minutes, 60)

    if hours >= 1:
        print(f"⏱️  Total duration: {int(hours)}h {int(minutes)}m {seconds:.1f}s")
    else:
        print(f"⏱️  Total duration: {int(minutes)}m {seconds:.1f}s")

    print(f"💾 Exporting to: {output_file}")

    out_ext = os.path.splitext(output_file)[1].lower().lstrip(".")
    export_params = {
        "mp3":  {"format": "mp3", "bitrate": "320k", "parameters": ["-q:a", "0"]},
        "wav":  {"format": "wav"},
        "flac": {"format": "flac"},
        "ogg":  {"format": "ogg", "codec": "libvorbis"},
    }
    params = export_params.get(out_ext, {"format": out_ext})

    combined.export(output_file, **params)

    file_size_mb = os.path.getsize(output_file) / (1024 * 1024)
    print(f"✅ Done! File size: {file_size_mb:.1f} MB")
    print(f"🎧 Output: {output_file}\n")


if __name__ == "__main__":
    smooth_crossfade_combine(AUDIO_DIR, OUTPUT_FILE)