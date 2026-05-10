import requests

# ==============================
# CONFIGURATION
# ==============================
SECRET_KEY = "sk_Mewr35R8nHRA59BwCrn73nMihDgwgiyX"  # Replace with your secret key

# ==============================
# FUNCTION TO GENERATE IMAGE
# ==============================
def generate_image(prompt, aspect="1:1", model="sdxl", filename="output.png"):
    # Map aspect ratio to width & height
    aspect_map = {
        "1:1": (512, 512),
        "16:9": (1024, 576),
        "9:16": (512, 1024),
    }

    if aspect not in aspect_map:
        raise ValueError("Invalid aspect ratio. Choose from '1:1', '16:9', '9:16'.")

    width, height = aspect_map[aspect]

    # Build URL
    url = (
        f"https://image.pollinations.ai/prompt/{prompt}"
        f"?width={width}&height={height}&model={model}&branding=false"
    )

    # Headers with secret key
    headers = {
        "Authorization": f"Bearer {SECRET_KEY}"
    }

    # GET request
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        # Save image
        with open(filename, "wb") as f:
            f.write(response.content)
        print(f"✅ Image saved as {filename}")
    else:
        print(f"❌ Error {response.status_code}: {response.text}")


# ==============================
# USAGE EXAMPLES
# ==============================
# 1. Portrait 9:16, SDXL
generate_image(
    prompt="a futuristic city at sunset, cinematic, ultra detailed",
    aspect="9:16",
    model="sdxl",
    filename="city_9_16.png"
)
