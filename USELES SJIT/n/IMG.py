import requests
import base64
from PIL import Image
from io import BytesIO
import os


def generate_image(prompt, aspect_ratio="1:1", output_filename="output.png"):
    """
    Generate an image using Cloudflare Workers AI with aspect ratio control

    Args:
        prompt: Text description of the image
        aspect_ratio: "1:1" (square), "16:9" (landscape), or "9:16" (portrait)
        output_filename: Name of the output file
    """
    ACCOUNT_ID = os.getenv("CF_ACCOUNT_ID", "a162aaff4def8caa60e5a14c850455db")
    API_TOKEN = os.getenv("CF_API_TOKEN", "zG9vlt7xf88Pw-iU2PBgtupHK_zmuU0joBVTs_aM")

    # FLUX Schnell model endpoint
    url = f"https://api.cloudflare.com/client/v4/accounts/{ACCOUNT_ID}/ai/run/@cf/black-forest-labs/flux-1-schnell"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json"
    }

    # Adjust prompt based on aspect ratio to guide the model
    aspect_hints = {
        "1:1": "",  # Square - no modification needed
        "16:9": " [wide landscape composition]",  # Landscape
        "9:16": " [tall portrait composition]"  # Portrait
    }

    enhanced_prompt = prompt + aspect_hints.get(aspect_ratio, "")

    data = {
        "prompt": enhanced_prompt,
        "steps": 7  # 4-8 steps for quality
    }

    try:
        print(f"🎨 Generating {aspect_ratio} image for: '{prompt}'...")
        response = requests.post(url, headers=headers, json=data)
        response.raise_for_status()

        result = response.json()

        # Debug: print the response structure
        if not result.get("success"):
            print(f"❌ API Error: {result}")
            return None

        # Get image from result object
        image_base64 = result["result"]["image"]

        # Decode image
        image_data = base64.b64decode(image_base64)
        image = Image.open(BytesIO(image_data))

        # Resize/crop to desired aspect ratio
        image = resize_to_aspect_ratio(image, aspect_ratio)

        # Save the image
        image.save(output_filename)

        print(f"✅ Success! {aspect_ratio} image saved as '{output_filename}'")
        print(f"   Dimensions: {image.width}x{image.height}")
        return image

    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP Error: {e}")
        if response.text:
            print(f"   Response: {response.text}")
    except KeyError as e:
        print(f"❌ Missing key in response: {e}")
        print(f"   Full response: {response.json()}")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def resize_to_aspect_ratio(image, aspect_ratio):
    """
    Resize/crop image to specified aspect ratio
    """
    width, height = image.size

    if aspect_ratio == "16:9":
        # Landscape - 1920x1080 or scale proportionally
        target_ratio = 16 / 9
        if width / height > target_ratio:
            # Image is wider, crop width
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            image = image.crop((left, 0, left + new_width, height))
        else:
            # Image is taller, crop height
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            image = image.crop((0, top, width, top + new_height))
        # Scale to common 16:9 resolution
        image = image.resize((1920, 1080), Image.Resampling.LANCZOS)

    elif aspect_ratio == "9:16":
        # Portrait - 1080x1920 or scale proportionally
        target_ratio = 9 / 16
        if width / height > target_ratio:
            # Image is wider, crop width
            new_width = int(height * target_ratio)
            left = (width - new_width) // 2
            image = image.crop((left, 0, left + new_width, height))
        else:
            # Image is taller, crop height
            new_height = int(width / target_ratio)
            top = (height - new_height) // 2
            image = image.crop((0, top, width, top + new_height))
        # Scale to common 9:16 resolution (mobile/social media)
        image = image.resize((1080, 1920), Image.Resampling.LANCZOS)

    # For "1:1" or any other ratio, return as-is
    return image


def batch_generate(prompts, aspect_ratios=None):
    """
    Generate multiple images with different aspect ratios

    Args:
        prompts: List of prompt strings or single prompt string
        aspect_ratios: List of aspect ratios or single aspect ratio
    """
    if isinstance(prompts, str):
        prompts = [prompts]

    if aspect_ratios is None:
        aspect_ratios = ["1:1"]
    elif isinstance(aspect_ratios, str):
        aspect_ratios = [aspect_ratios]

    for i, prompt in enumerate(prompts):
        for ratio in aspect_ratios:
            filename = f"image_{i + 1}_{ratio.replace(':', 'x')}.png"
            generate_image(prompt, ratio, filename)
            print()  # Blank line between generations


# Example usage
if __name__ == "__main__":
    print("=" * 60)
    print("Cloudflare FLUX Image Generator with Aspect Ratio Control")
    print("=" * 60)
    print()


    print("Example 2: Landscape (16:9)")
    generate_image(
        "a serene mountain landscape at sunset,pixel art",
        aspect_ratio="16:9",
        output_filename="landscape_image.png"
    )
    print()
