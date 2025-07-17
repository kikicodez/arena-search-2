import streamlit as st
import requests
from PIL import Image
from io import BytesIO

# --- Search Are.na Channels ---
def search_arena_channels(keyword, max_channels=5):
    url = f"https://api.are.na/v2/search/channels?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['channels'][:max_channels]

# --- Get Content Blocks from a Channel ---
def get_blocks_from_channel(slug, max_blocks=30):
    url = f"https://api.are.na/v2/channels/{slug}/contents"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['contents'][:max_blocks]

# --- Streamlit UI ---
st.set_page_config(page_title="Are.na Visual Search", layout="wide")
st.title("🎯 Are.na Visual Search")
st.markdown("Enter a keyword to find **images that reference it** in their title or note.")

keyword = st.text_input("🔍 Search Are.na for images related to...")

if st.button("Search"):
    if not keyword:
        st.warning("Please enter a keyword.")
    else:
        st.info(f"Searching Are.na channels for: **{keyword}**")
        try:
            keyword_lower = keyword.lower()
            matching_images = []
            channels = search_arena_channels(keyword)

            for channel in channels:
                blocks = get_blocks_from_channel(channel['slug'])

                for block in blocks:
                    if block.get('class') == 'Image':
                        title = block.get('title', '') or ''
                        description = block.get('description', '') or ''
                        if keyword_lower in title.lower() or keyword_lower in description.lower():
                            img_url = block['image']['original']['url']
                            matching_images.append((img_url, title))

            if not matching_images:
                st.warning("No image blocks matched your keyword inside these channels.")
            else:
                cols = st.columns(5)
                col_idx = 0
                for img_url, title in matching_images:
                    try:
                        img_response = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"})
                        if not img_response.headers.get("Content-Type", "").startswith("image/"):
                            continue
                        img = Image.open(BytesIO(img_response.content))
                        cols[col_idx].image(img, caption=title, use_column_width=True)
                        col_idx = (col_idx + 1) % 5
                    except Exception:
                        continue

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
