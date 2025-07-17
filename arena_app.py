import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import base64
import json
import time

# --- Hugging Face CLIP Model ---
HUGGINGFACE_API_TOKEN = st.secrets["HUGGINGFACE_API_TOKEN"]
CLIP_API_URL = "https://api-inference.huggingface.co/models/openai/clip-vit-base-patch32"

headers_hf = {
    "Authorization": f"Bearer " + HUGGINGFACE_API_TOKEN,
    "Content-Type": "application/json"
}

def get_clip_score(image_bytes, prompt, retries=3, delay=3):
    base64_img = base64.b64encode(image_bytes).decode("utf-8")
    payload = {
        "inputs": {
            "image": base64_img,
            "text": prompt
        }
    }
    for attempt in range(retries):
        try:
            response = requests.post(CLIP_API_URL, headers=headers_hf, json=payload)
            if response.status_code != 200:
                st.warning(f"CLIP error (status {response.status_code}): {response.text}")
                time.sleep(delay)
                continue
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0]["score"]
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

# --- Streamlit UI ---
st.set_page_config(page_title="Are.na Visual Search with CLIP", layout="wide")
st.title("🧠 Are.na Visual Search (w/ CLIP & Test Mode)")

keyword = st.text_input("Enter a concept (e.g. 'watermelon', 'poster', 'zine')")
threshold = st.slider("Minimum CLIP match score", 0.1, 0.5, 0.28, step=0.01)

# 🔎 TEST IMAGE MODE
with st.expander("🧪 Test CLIP with known watermelon image"):
    if st.button("Run Test Image Match"):
        test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e4/Watermelon_cross_BNC.jpg/640px-Watermelon_cross_BNC.jpg"
        img_response = requests.get(test_url)
        score = get_clip_score(img_response.content, "watermelon")
        st.image(img_response.content, caption=f"Test Score: {score:.2f}")
        if score < threshold:
            st.warning("CLIP model might be sleeping or rate-limited. Try again or lower the threshold.")

# 🔍 MAIN SEARCH MODE
if st.button("Search Are.na"):
    if not keyword:
        st.warning("Please enter a keyword.")
    else:
        st.info(f"Searching visually for: **{keyword}** (CLIP score ≥ {threshold:.2f})")
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
                            img_bytes = img_response.content

                            score = get_clip_score(img_bytes, keyword)

                            if score >= threshold:
                                img = Image.open(BytesIO(img_bytes))
                                title = block.get("title", "")
                                caption = f"{title}\nScore: {score:.2f}" if title else f"Score: {score:.2f}"
                                cols[col_idx].image(img, caption=caption, use_column_width=True)
                                col_idx = (col_idx + 1) % 5
                                match_count += 1
                        except:
                            continue

            if match_count == 0:
                st.warning("No visually matching images found. Try a broader term or lower threshold.")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
