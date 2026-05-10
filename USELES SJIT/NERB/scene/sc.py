import os
from dotenv import load_dotenv
import google.generativeai as genai

# ---------------------------
# LOAD API KEY FROM .env FILE
# ---------------------------

# Path to your env file
ENV_PATH = r"C:\Users\CJ\Desktop\NERB\scene\api_key.env"
load_dotenv(ENV_PATH)

# Get API key from env
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ GEMINI_API_KEY not found in api_key.env")

# Configure Gemini
genai.configure(api_key=api_key)

# ---------------------------
# CONFIGURATION
# ---------------------------
TRANSCRIPT_FOLDER = r"C:\Users\CJ\Desktop\NERB\script\TRANSCRIPT"
OUTPUT_FILE = r"C:\Users\CJ\Desktop\NERB\scene_plan.txt"

MODEL_NAME = "gemini-2.0-flash"

# ---------------------------
# GEMINI PROMPT FUNCTION
# ---------------------------

def extract_scene_info(transcript_text):
    prompt = f"""
    You are a YouTube scene timing assistant.

    Given the transcript below, break it into scenes.
    For each scene:
    1. Suggest a START and END time in seconds.
    2. Extract 2-4 important keywords for visuals.

    Return ONLY in this format:
    start-end : keyword1, keyword2, keyword3

    Example:
    1-4 : farming, crop yields
    4-9 : silk production, silk weaving

    Transcript:
    {transcript_text}
    """
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    return response.text.strip()

# ---------------------------
# MAIN SCRIPT
# ---------------------------

def main():
    all_results = []
    for filename in sorted(os.listdir(TRANSCRIPT_FOLDER)):
        if filename.lower().endswith(".txt"):
            file_path = os.path.join(TRANSCRIPT_FOLDER, filename)
            with open(file_path, "r", encoding="utf-8") as f:
                transcript = f.read()

            print(f"Processing {filename}...")
            scene_data = extract_scene_info(transcript)
            all_results.append(f"--- {filename} ---\n{scene_data}\n")

    with open(OUTPUT_FILE, "w", encoding="utf-8") as out_file:
        out_file.write("\n".join(all_results))

    print(f"\n✅ Scene data saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
