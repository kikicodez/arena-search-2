import streamlit as st
import requests
from PIL import Image
from io import BytesIO
import csv

# --- ARE.NA API FUNCTIONS ---

def search_arena_channels(keyword, max_channels=5):
    url = f"https://api.are.na/v2/search/channels?q={keyword}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['channels'][:max_channels]

def get_blocks_from_channel(slug, max_blocks=10):
    url = f"https://api.are.na/v2/channels/{slug}/contents"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()['contents'][:max_blocks]

# --- STREAMLIT UI SETUP ---

st.set_page_config(page_title="Are.na Image Fetcher", layout="wide")
st.title("📡 Are.na Image Fetcher")
st.markdown("Search Are.na channels by keyword and download a CSV of image metadata.")

keyword = st.text_input("🔍 Enter a keyword to search Are.na channels")

if st.button("Search and Download"):
    if not keyword:
        st.warning("Please enter a keyword.")
    else:
        st.info(f"Searching Are.na for: **{keyword}**")
        metadata_rows = []

        try:
            channels = search_arena_channels(keyword)
            if not channels:
                st.warning("No channels found.")

            for channel in channels:
                st.subheader(f"📁 {channel['title']}")
                blocks = get_blocks_from_channel(channel['slug'])
                cols = st.columns(5)
                col_idx = 0

                for block in blocks:
                    if block['class'] == 'Image':
                        try:
                            img_url = block['image']['original']['url']
                            title = block.get('title', '[No Title]')
                            note = block.get('description', '[No Description]')

                            # Fetch and validate image
                            img_response = requests.get(img_url, headers={"User-Agent": "Mozilla/5.0"})
                            if not img_response.headers.get("Content-Type", "").startswith("image/"):
                                continue  # skip non-image data

                            img_data = img_response.content
                            img = Image.open(BytesIO(img_data))

                            # Add to grid
                            cols[col_idx].image(img, caption=title, use_column_width=True)
                            col_idx = (col_idx + 1) % 5

                            # Collect metadata
                            img_name = img_url.split("/")[-1]
                            metadata_rows.append([img_name, title, note, img_url])

                        except Exception:
                            continue  # silently skip broken image blocks

            if metadata_rows:
                # Build CSV in-memory
                csv_buffer = BytesIO()
                writer = csv.writer(csv_buffer)
                writer.writerow(["Image Name", "Title", "Note", "Image URL"])
                writer.writerows(metadata_rows)
                csv_buffer.seek(0)

                st.success("✅ Done! Download your metadata below.")
                st.download_button("📄 Download Metadata CSV", csv_buffer, file_name="arena_metadata.csv", mime="text/csv")
            else:
                st.info("No usable images found in these channels.")

        except Exception as e:
            st.error(f"⚠️ Error: {e}")
