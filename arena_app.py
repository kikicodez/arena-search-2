import streamlit as st
import requests
from PIL import Image
from io import BytesIO

# --- ARE.NA API SEARCH FOR BLOCKS ---
def search_arena_blocks(keyword, max_results=50):
    url = f"https://api.are.na/v2/search/contents?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()

    # Filter only Image blocks
    image_blocks = [
        block for block in data.get("contents", [])
        if block.get("class") == "Image" and block.get("image", {}).get("original", {}).get("url")
    ]
    return image_blocks[:max_results]

# --- STREAMLIT UI ---

st.set_page_config(page_title="Are.na Visual Search", layout="wide")
st.title("🎯 Are.na Visual Search")
st.markdown("Type a keyword to find **images across Are.na** matching your concept. (e.g., `watermelon`, `architecture`, `texture`, `zine`)")

keyword = st.text_input("🔍 Search Are.na for images related to...")

if st.button("Search"):
    if not keyword:
        st.warning("Please enter a keyword.")
    else:
        st.info(f"Searching Are.na for images related to **{keyword}**...")
        try:
            image_blocks = search_arena_blocks(keyword)
            if not image_blocks:
                st.warning("No images found for this keyword.")
            else:
                cols = st.columns(5)
                col_idx = 0
                for block in image_blocks:
                    try:
                        img_url = block['image']['original']['url']
                        title = block.get('title', '[No Title]')
                        img_response = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"})
                        if not img_response.headers.get("Content-Type", "").startswith("image/"):
                            continue
                        img_data = img_response.content
                        img = Image.open(BytesIO(img_data))
                        cols[col_idx].image(img, caption=title, use_column_width=True)
                        col_idx = (col_idx + 1) % 5
                    except Exception:
                        continue  # silently skip bad blocks
        except Exception as e:
            st.error(f"⚠️ Error: {e}")
