import os
import re
import time
from dotenv import load_dotenv
from openai import OpenAI

# Load environment variables from .env file
load_dotenv()

# --- CONFIG ---
API_KEY = os.getenv("OPENROUTER_API_KEY")
FOLDER = r"C:\Users\Never\Desktop\LOFI\AUDIO"

# Check if API key exists
if not API_KEY:
    print("❌ Error: OPENROUTER_API_KEY not found in .env file!")
    print("Create a .env file with: OPENROUTER_API_KEY=your_key_here")
    exit()

# Try multiple free models in order
FREE_MODELS = [
    "google/gemma-3-4b-it:free",
    "mistralai/mistral-small-3.1-24b-instruct:free",
    "qwen/qwen3-14b:free",
    "deepseek/deepseek-r1-0528-qwen3-8b:free",
]

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

# Get all audio files
audio_extensions = ('.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac', '.wma')
files = [f for f in os.listdir(FOLDER) if f.lower().endswith(audio_extensions)]

if not files:
    print("No audio files found!")
    exit()

print(f"Found {len(files)} audio files.\n")

# Extract original names (without extension) into a list
original_names = []
for f in files:
    name_without_ext = os.path.splitext(f)[0]
    original_names.append(name_without_ext)

# Display original names
print("Original file names:")
print("-" * 40)
for i, name in enumerate(original_names, 1):
    print(f"  {i}. {name}")
print("-" * 40)
print()

# Create prompt with the list of original names
names_list_str = "\n".join([f"{i + 1}. {name}" for i, name in enumerate(original_names)])

prompt = f"""I have {len(original_names)} audio files with these names:

{names_list_str}

Generate a NEW lofi-style name for EACH file. These should sound like chill lofi hip-hop track titles.
Examples of the vibe: "midnight rain", "sleepy cafe", "3am thoughts", "sun dusted windows", "still with you", "ash on my hoodie", "wyd"

Rules:
- Output EXACTLY {len(original_names)} names, one per line
- Match the order: line 1 = new name for file 1, line 2 = new name for file 2, etc.
- No numbering, no quotes, no extra text, no explanations
- Keep names short (1-3 words max)
- Make each one unique and aesthetic
- Lowercase only
- No special characters except spaces

Output ONLY the {len(original_names)} new names, nothing else:"""

print("Sending names to AI for transformation...\n")

# Try each model with retries
response = None
for model in FREE_MODELS:
    for attempt in range(3):
        try:
            print(f"Trying {model} (attempt {attempt + 1})...")
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
            )
            print(f"✅ Success with {model}\n")
            break
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                print(f"⚠️ Rate limited, waiting 10 seconds...")
                time.sleep(10)
            else:
                print(f"❌ Error: {e}")
                break

    if response:
        break

if not response:
    print("❌ All models failed. Try again in a few minutes.")
    exit()

# Parse new names from response
raw = response.choices[0].message.content.strip()
new_names_raw = [line.strip() for line in raw.split('\n') if line.strip()]

# Clean names (remove numbering, quotes, special chars)
new_names = []
for name in new_names_raw:
    name = re.sub(r'^\d+[\.\)\-\s]+', '', name)  # remove numbering
    name = name.strip('"\'')  # remove quotes
    name = re.sub(r'[<>:"/\\|?*]', '', name)  # remove invalid filename chars
    name = name.strip()
    if name:
        new_names.append(name)

# Make sure we have enough names
if len(new_names) < len(files):
    print(f"⚠️ AI generated {len(new_names)} names but need {len(files)}.")
    print("Adding fallback names...\n")
    for i in range(len(new_names), len(files)):
        new_names.append(f"lofi beat {i + 1}")

# Trim if too many names
new_names = new_names[:len(files)]

# Preview renames before applying
print("=" * 60)
print("PREVIEW - Rename Mapping")
print("=" * 60)

rename_map = []
for i, old_file in enumerate(files):
    ext = os.path.splitext(old_file)[1]
    new_name = f"{new_names[i]}{ext}"

    # Handle duplicates
    counter = 2
    final_new_name = new_name
    while os.path.exists(os.path.join(FOLDER, final_new_name)) or \
            any(r[1] == final_new_name for r in rename_map):
        base = new_names[i]
        final_new_name = f"{base} {counter}{ext}"
        counter += 1

    rename_map.append((old_file, final_new_name))
    print(f"  [{i + 1}] {original_names[i]}")
    print(f"       → {new_names[i]}\n")

# Confirm
print("=" * 60)
confirm = input("Proceed with renaming? (y/n): ").strip().lower()

if confirm in ['yes', 'y']:
    print("\nRenaming files...\n")
    for old_name, new_name in rename_map:
        old_path = os.path.join(FOLDER, old_name)
        new_path = os.path.join(FOLDER, new_name)
        os.rename(old_path, new_path)
        print(f"✅ {old_name} → {new_name}")
    print(f"\n🎵 Done! Renamed {len(rename_map)} files.")
else:
    print("❌ Cancelled. No files were renamed.")