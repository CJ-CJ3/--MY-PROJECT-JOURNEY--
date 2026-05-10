# pip install openai
# or: pip install openai==latest if you need newest features
from openai import OpenAI
import base64
import time

A4F_API_KEY = "ddc-a4f-c4533cabf05b4559a2f92b5d6fc9ecf8"
A4F_BASE_URL = "https://api.a4f.co/v1"

client = OpenAI(api_key=A4F_API_KEY, base_url=A4F_BASE_URL)

MODEL = "provider-8/imagen-4"
PROMPT = "portrait of an elderly sailor,pixel art"

def generate_imagen4(prompt: str, out_path: str = "imagen4.png", retries=3):
    for attempt in range(1, retries + 1):
        try:
            # request b64_json so we can save the image reliably
            resp = client.images.generate(
                model=MODEL,
                prompt=prompt,
                size="1024x1024",
                n=1,
                response_format="b64_json"
            )
            b64 = resp.data[0].b64_json
            img_bytes = base64.b64decode(b64)
            with open(out_path, "wb") as f:
                f.write(img_bytes)
            print(f"Saved image to {out_path}")
            return out_path

        except Exception as e:
            # Basic handling: catch rate limit / transient errors and retry with backoff
            err_text = str(e).lower()
            if "rate" in err_text or "429" in err_text or "too many requests" in err_text:
                backoff = 2 ** attempt
                print(f"Rate limited or transient error (attempt {attempt}). Backing off {backoff}s...")
                time.sleep(backoff)
                continue
            # quota / 402 or model not allowed are likely unrecoverable here
            print("Failed:", e)
            raise

# Optionally: verify model exists for your account (helps confirm Free availability)
def model_available(model_name=MODEL):
    models = client.models.list()  # should return a list you can search
    for m in models.data:
        if getattr(m, "id", None) == model_name or getattr(m, "name", None) == model_name:
            return True
    return False

if __name__ == "__main__":
    if not model_available():
        print(f"Warning: {MODEL} not listed for your account. It might still be callable but check dashboard.")
    generate_imagen4(PROMPT, out_path="imagen4.png")
    # keep at least ~12s between calls to stay under 5 RPM when looping
    # time.sleep(12)
