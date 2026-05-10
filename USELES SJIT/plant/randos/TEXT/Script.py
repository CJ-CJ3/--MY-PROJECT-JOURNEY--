import os
import sys
import json
import base64
import requests
from pathlib import Path
from datetime import datetime

# ──────────────────────────────────────────────
# ENV / API KEY MANAGEMENT
# ──────────────────────────────────────────────

ENV_FILE = Path(__file__).parent / ".env"


def load_env():
    if not ENV_FILE.exists():
        return
    with open(ENV_FILE, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ[key.strip()] = value.strip().strip('"').strip("'")


def save_key_to_env(key: str, value: str):
    lines = []
    key_found = False
    if ENV_FILE.exists():
        with open(ENV_FILE, "r") as f:
            for line in f:
                if line.strip().startswith(f"{key}="):
                    lines.append(f'{key}="{value}"\n')
                    key_found = True
                else:
                    lines.append(line)
    if not key_found:
        lines.append(f'{key}="{value}"\n')
    with open(ENV_FILE, "w") as f:
        f.writelines(lines)
    print(f"\n✅ API key saved to {ENV_FILE}")


def get_api_key() -> str:
    load_env()
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if api_key:
        return api_key

    print("=" * 60)
    print("  ⚠️  OPENROUTER_API_KEY not found in .env file")
    print("=" * 60)
    print()
    print("  1. Go to https://openrouter.ai/keys")
    print("  2. Create a new key")
    print("  3. Paste it below")
    print()
    user_key = input("  Paste your API key: ").strip()
    if not user_key:
        print("\n❌ No key provided. Exiting.")
        sys.exit(1)
    save_key_to_env("OPENROUTER_API_KEY", user_key)
    print("🔄 Restarting...\n")
    os.execv(sys.executable, [sys.executable] + sys.argv)


# ──────────────────────────────────────────────
# AVAILABLE IMAGE MODELS
# ──────────────────────────────────────────────

IMAGE_MODELS = [
    {"id": "sourceful/riverflow-v2-pro", "name": "Riverflow V2 Pro (Best Quality)"},
    {"id": "sourceful/riverflow-v2-max-preview", "name": "Riverflow V2 Max Preview"},
    {"id": "sourceful/riverflow-v2-standard-preview", "name": "Riverflow V2 Standard"},
    {"id": "sourceful/riverflow-v2-fast-preview", "name": "Riverflow V2 Fast Preview"},
    {"id": "sourceful/riverflow-v2-fast", "name": "Riverflow V2 Fast"},
    {"id": "black-forest-labs/flux.2-pro", "name": "Flux 2 Pro"},
    {"id": "black-forest-labs/flux.2-max", "name": "Flux 2 Max"},
    {"id": "black-forest-labs/flux.2-flex", "name": "Flux 2 Flex"},
    {"id": "black-forest-labs/flux.2-klein-4b", "name": "Flux 2 Klein 4B"},
    {"id": "bytedance-seed/seedream-4.5", "name": "Seedream 4.5"},
]


def show_models():
    print("\n  Available image models:\n")
    for idx, m in enumerate(IMAGE_MODELS, 1):
        marker = "⭐" if idx == 1 else "  "
        print(f"  {marker} [{idx}] {m['name']}")
        print(f"        {m['id']}")
    print()


# ──────────────────────────────────────────────
# GENERATE IMAGE
# ──────────────────────────────────────────────

def generate_image(
    api_key: str,
    model: str,
    prompt: str,
    output_dir: str = "outputs",
) -> list[str]:
    """Generate image via OpenRouter using modalities: ['image']"""

    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)

    print(f"\n🎨 Generating image...")
    print(f"   Model:  {model}")
    print(f"   Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    print()

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
            }
        ],
        "modalities": ["image"],  # <-- THIS IS THE KEY
    }

    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=180,
        )

        # Check for HTML error
        content_type = response.headers.get("Content-Type", "")
        if "text/html" in content_type:
            print(f"❌ Got HTML response (status {response.status_code})")
            print(f"   Model '{model}' may not be available.")
            return []

        data = response.json()

        # Check for API error
        if "error" in data:
            error = data["error"]
            msg = error.get("message", str(error)) if isinstance(error, dict) else str(error)
            print(f"❌ API Error: {msg}")
            return []

        # Extract images from response
        return save_images(data, out_path)

    except requests.exceptions.Timeout:
        print("❌ Timed out (180s). Model might be overloaded. Try again.")
        return []
    except Exception as e:
        print(f"❌ Error: {e}")
        return []


def save_images(data: dict, out_path: Path) -> list[str]:
    """
    Extract images from OpenRouter response.
    Format: choices[0].message.images[].image_url.url (base64 data URL)
    """
    saved_files = []
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    choices = data.get("choices", [])
    if not choices:
        print("   ⚠️ No choices in response.")
        print(f"   Raw: {json.dumps(data, indent=2)[:500]}")
        return []

    for ci, choice in enumerate(choices):
        message = choice.get("message", {})

        # ── Method 1: message.images[] (official format from docs) ──
        images = message.get("images", [])
        for ii, image in enumerate(images):
            try:
                url = image.get("image_url", {}).get("url", "")
                img_bytes = decode_image(url)
                if img_bytes:
                    filename = out_path / f"image_{timestamp}_{ci}_{ii}.png"
                    with open(filename, "wb") as f:
                        f.write(img_bytes)
                    kb = len(img_bytes) / 1024
                    saved_files.append(str(filename))
                    print(f"   ✅ Saved: {filename} ({kb:.1f} KB)")
            except Exception as e:
                print(f"   ⚠️ Failed to save image {ii}: {e}")

        # ── Method 2: message.content as list with image parts ──
        content = message.get("content", "")
        if isinstance(content, list):
            for ii, item in enumerate(content):
                if not isinstance(item, dict):
                    continue
                item_type = item.get("type", "")
                if item_type == "image_url":
                    try:
                        url = item.get("image_url", {}).get("url", "")
                        img_bytes = decode_image(url)
                        if img_bytes:
                            filename = out_path / f"image_{timestamp}_{ci}_c{ii}.png"
                            with open(filename, "wb") as f:
                                f.write(img_bytes)
                            kb = len(img_bytes) / 1024
                            saved_files.append(str(filename))
                            print(f"   ✅ Saved: {filename} ({kb:.1f} KB)")
                    except Exception as e:
                        print(f"   ⚠️ Failed: {e}")

        # ── Method 3: message.content is a string with URL ──
        if isinstance(content, str) and content.strip():
            import re
            urls = re.findall(r'(https?://\S+\.(?:png|jpg|jpeg|webp)(?:\S*)?)', content)
            for ui, url in enumerate(urls):
                try:
                    img_bytes = requests.get(url.rstrip(')"\''), timeout=60).content
                    filename = out_path / f"image_{timestamp}_{ci}_u{ui}.png"
                    with open(filename, "wb") as f:
                        f.write(img_bytes)
                    kb = len(img_bytes) / 1024
                    saved_files.append(str(filename))
                    print(f"   ✅ Saved: {filename} ({kb:.1f} KB)")
                except Exception as e:
                    print(f"   ⚠️ Download failed: {e}")

    if not saved_files:
        print("   ⚠️ No images found in response.")
        print(f"   Debug — Full response:")
        print(f"   {json.dumps(data, indent=2)[:1000]}")

    return saved_files


def decode_image(url_or_data: str) -> bytes | None:
    """Decode a base64 data URL or download a regular URL."""
    if not url_or_data:
        return None

    # Base64 data URL: data:image/png;base64,iVBOR...
    if url_or_data.startswith("data:image"):
        try:
            _, b64_part = url_or_data.split(",", 1)
            return base64.b64decode(b64_part)
        except Exception:
            return None

    # Regular URL
    if url_or_data.startswith("http"):
        try:
            return requests.get(url_or_data, timeout=60).content
        except Exception:
            return None

    # Raw base64 (no prefix)
    try:
        return base64.b64decode(url_or_data)
    except Exception:
        return None


# ──────────────────────────────────────────────
# INTERACTIVE MODE
# ──────────────────────────────────────────────

def interactive_mode(api_key: str, model: str):
    print("\n" + "=" * 60)
    print(f"  🖼️  Image Generator — Interactive Mode")
    print(f"  Model: {model}")
    print()
    print(f"  Commands:")
    print(f"    'quit'    — exit")
    print(f"    'models'  — switch model")
    print(f"    'model'   — show current model")
    print("=" * 60)

    while True:
        print()
        try:
            prompt = input("📝 Prompt: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 Goodbye!")
            break

        if not prompt:
            continue

        cmd = prompt.lower()
        if cmd in ("quit", "exit", "q"):
            print("👋 Goodbye!")
            break

        if cmd == "models":
            show_models()
            try:
                pick = int(input("  Pick number: ")) - 1
                if 0 <= pick < len(IMAGE_MODELS):
                    model = IMAGE_MODELS[pick]["id"]
                    print(f"  ✅ Switched to: {model}")
                else:
                    print("  ⚠️ Invalid number.")
            except ValueError:
                print("  ⚠️ Cancelled.")
            continue

        if cmd == "model":
            print(f"  Current model: {model}")
            continue

        # Generate
        files = generate_image(api_key, model, prompt)
        if files:
            print(f"\n   🎉 {len(files)} image(s) saved to ./outputs/")


# ──────────────────────────────────────────────
# MAIN
# ──────────────────────────────────────────────

def main():
    api_key = get_api_key()
    print(f"🔑 Key loaded: {api_key[:12]}...{api_key[-4:]}")

    # Show models and let user pick
    show_models()

    print("  Pick a model number (Enter for [1] Riverflow V2 Pro):")
    try:
        pick = input("  > ").strip()
        if pick:
            idx = int(pick) - 1
            if 0 <= idx < len(IMAGE_MODELS):
                model = IMAGE_MODELS[idx]["id"]
            else:
                print("  ⚠️ Invalid. Using default.")
                model = IMAGE_MODELS[0]["id"]
        else:
            model = IMAGE_MODELS[0]["id"]
    except (ValueError, KeyboardInterrupt, EOFError):
        model = IMAGE_MODELS[0]["id"]

    print(f"\n  ✅ Using: {model}")

    interactive_mode(api_key, model)


if __name__ == "__main__":
    main()