import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import base64
import json
import time

# ✅ Final CLIP endpoint that supports inference
CLIP_API_URL = "https://api-inference.huggingface.co/models/sentence-transformers/clip-ViT-B-32"
HUGGINGFACE_API_TOKEN = st.secrets["HUGGINGFACE_API_TOKEN"]

headers_hf = {
    "Authorization": f"Bearer {HUGGINGFACE_API_TOKEN}",
    "Content-Type": "application/json"
}

def get_clip_score(image_bytes, prompt, retries=3, delay=2):
    payload = {
        "inputs": {
            "image": base64.b64encode(image_bytes).decode("utf-8"),
            "text": prompt
        }
    }
    for attempt in range(retries):
        try:
            response = requests.post(CLIP_API_URL, headers=headers_hf, json=payload)
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, list) and len(result) > 0:
                    return result[0].get("score", 0.0)
            else:
                st.warning(f"CLIP error (status {response.status_code}): {response.text}")
        except Exception as e:
            st.warning(f"CLIP exception: {e}")
        time.sleep(delay)
    return 0.0

# --- Are.na API ---
def search_arena_channels(keyword, max_channels=5):
    url = f"https://api.are.na/v2/search/channels?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['channels'][:max_channels]

def get_blocks_from_channel(slug, max_blocks=20):
    url = f"https://api.are.na/v2/channels/{slug}/contents"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['contents'][:max_blocks]

# --- UI ---
st.set_page_config(page_title="Are.na CLIP Search", layout="wide")
st.title("🔍 Are.na Visual Search (CLIP-powered)")
st.markdown("Find images on Are.na that visually match your concept using CLIP.")

keyword = st.text_input("Enter a visual concept (e.g. 'fruit', 'poster', 'zine')")
threshold = st.slider("Minimum CLIP match score", 0.1, 0.5, 0.28, step=0.01)

# 🧪 TEST MODE
with st.expander("🧪 Test CLIP with known watermelon image"):
    if st.button("Run test match"):
        test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Watermelon_cross_BNC.jpg/640px-Watermelon_cross_BNC.jpg"
        img_response = requests.get(test_url)
        score = get_clip_score(img_response.content, "watermelon")
        st.image(img_response.content, caption=f"CLIP Score: {score:.2f}")
        if score < threshold:
            st.warning("The model may be cold or slow. Try again or lower the threshold.")

# 🔍 SEARCH MODE
if st.button("Search Are.na"):
    if not keyword:
        st.warning("Please enter a keyword.")
    else:
        st.info(f"Searching Are.na visually for: **{keyword}** (CLIP ≥ {threshold:.2f})")
        try:
            channels = search_arena_channels(keyword)
            cols = st.columns(5)
            col_idx = 0
            match_count = 0

            for channel in channels:
                blocks = get_blocks_from_channel(channel["slug"])
                for block in blocks:
                    if block.get("class") == "Image":
                        try:
                            img_url = block["image"]["original"]["url"]
                            img_response = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"})

                            # Skip if not a real image
                            if not img_response.headers.get("Content-Type", "").startswith("image/"):
                                continue

                            img_bytes = img_response.content
                            score = get_clip_score(img_bytes, keyword)

                            if score >= threshold:
                                try:
                                    img = Image.open(BytesIO(img_bytes))
                                    title = block.get("title", "")
                                    caption = f"{title}\nScore: {score:.2f}" if title else f"Score: {score:.2f}"
                                    cols[col_idx].image(img, caption=caption, use_column_width=True)
                                    col_idx = (col_idx + 1) % 5
                                    match_count += 1
                                except Exception as e:
                                    st.warning(f"⚠️ Skipped a bad image block. Reason: {e}")
                                    continue

                        except Exception as e:
                            st.warning(f"⚠️ Failed to fetch an image. Reason: {e}")
                            continue

            if match_count == 0:
                st.warning("No matching images found. Try a broader keyword or lower threshold.")

        except Exception as e:
            st.error(f"❌ Error: {e}")
