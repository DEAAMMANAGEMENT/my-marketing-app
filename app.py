import streamlit as st
from PIL import Image, ImageDraw
import io
import math
import zipfile

# --- PAGE SETUP ---
st.set_page_config(page_title="AD Creator", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        background: linear-gradient(to right, #007AFF, #00C6FF);
        color: white;
        border: none;
        font-weight: bold;
    }
    [data-testid="stFileUploader"] {
        background-color: #f9f9f9;
        border: 2px dashed #007AFF;
        border-radius: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- OPTIMIZED IMAGE ENGINE ---
@st.cache_data(show_spinner=False)
def process_uploaded_image(file_content):
    """Resizes image immediately to save memory and speed up upload"""
    img = Image.open(io.BytesIO(file_content)).convert("RGB")
    # Resize to a max width of 1200px to keep quality but drop file size
    w, h = img.size
    if w > 1200:
        new_h = int(h * (1200 / w))
        img = img.resize((1200, new_h), Image.Resampling.LANCZOS)
    return img

def create_ad(images, batch_idx, settings):
    c_w, c_h = settings['size']
    footer_h = settings['footer']
    canvas = Image.new('RGB', (c_w, c_h), "white")
    draw = ImageDraw.Draw(canvas)
    
    num_imgs = len(images)
    cols = math.ceil(math.sqrt(num_imgs))
    rows = math.ceil(num_imgs / cols)
    
    available_h = c_h - footer_h - 150
    cell_w, cell_h = c_w // cols, available_h // rows 

    for i, img in enumerate(images):
        w, h = img.size
        # Auto-crop phone bookmarks (top/bottom 8%)
        cut = 0.08 * h
        img_cropped = img.crop((0, cut, w, h - cut))
        img_cropped.thumbnail((cell_w - 40, cell_h - 40), Image.Resampling.LANCZOS)
        
        pos_x = (i % cols) * cell_w + (cell_w - img_cropped.
