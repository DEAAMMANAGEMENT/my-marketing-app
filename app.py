import streamlit as st
from PIL import Image, ImageDraw, ImageFilter
import io
import math
import zipfile
import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="AD Creator", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    /* Big Colorful Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3.5em;
        font-size: 18px !important;
        font-weight: bold !important;
        background: linear-gradient(to right, #007AFF, #00C6FF);
        color: white;
        border: none;
    }
    /* Upload Box Styling */
    [data-testid="stFileUploader"] {
        background-color: #f9f9f9;
        border: 2px dashed #007AFF;
        border-radius: 15px;
    }
    /* Simple Step Headers */
    .step-text {
        font-size: 20px;
        font-weight: bold;
        color: #333;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- IMAGE ENGINE ---
def create_ad(batch, batch_idx, settings):
    c_w, c_h = settings['size']
    footer_h = settings['footer']
    canvas = Image.new('RGB', (c_w, c_h), "white")
    draw = ImageDraw.Draw(canvas)
    
    num_imgs = len(batch)
    cols = math.ceil(math.sqrt(num_imgs))
    rows = math.ceil(num_imgs / cols)
    
    available_h = c_h - footer_h - 150
    cell_w, cell_h = c_w // cols, available_h // rows 

    for i, f in enumerate(batch):
        img = Image.open(f).convert("RGB")
        w, h = img.size
        # Auto-crop 8% to remove potential phone bookmarks
        cut = 0.08 * h
        img = img.crop((0, cut, w, h - cut))
        img.thumbnail((cell_w - 40, cell_h - 40), Image.Resampling.LANCZOS)
        
        pos_x = (i % cols) * cell_w + (cell_w - img.width) // 2
        pos_y = 50 + (i // cols) * cell_h + (cell_h - img.height) // 2
        canvas.paste(img, (int(pos_x), int(pos_y)))
        
        # Number Badge
        item_id = batch_idx * settings['per_set'] + i + 1
        draw.rectangle([pos_x, pos_y, pos_x+50, pos_y+50], fill="black")
        draw.text((pos_x+18, pos_y+15), str(item_id), fill="white")

    # Branding Footer
    draw.rectangle([0, c_h - footer_h, c_w, c_h], fill=settings['color'])
    draw.text((60, c_h - footer_h - 80), f"📍 {settings['address'].upper()}", fill="black")
    draw.text((c_w // 2 - 130, c_h - (footer_h // 2) - 10), f"DM TO ORDER: {settings['handle']}", fill="white")
    return canvas

# --- NAVIGATION FLOW ---
st.title("🚀 AD Creator")

# STEP 1: SIDEBAR (The Setup)
with st.sidebar:
    st.header("Step 1: Branding")
    brand_handle = st.text_input("Social Handle", "@DEAAM")
    prop_addr = st.text_input("Property Address", "Street Name")
    brand_color = st.color_picker("Theme Color", "#007AFF")
    
    st.divider()
    st.header("Step 2: Layout")
    target = st.selectbox("Format", ["Square (Post)", "Vertical (Story)"])
    imgs_per_set = st.slider("Photos per ad", 1, 9, 4)
    
    st.divider()
    if st.button("🗑️ Clear All"):
        st.rerun()

# MAIN AREA (Upload & Action)
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<p class="step-text">1. Upload Photos</p>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Choose images from gallery", accept_multiple_files=True)

with col2:
    st.markdown('<p class="step-text">2. Generate</p>', unsafe_allow_html=True)
    if uploaded_files:
        settings = {
            'size': (1080, 1080) if "Square" in target else (1080, 1920),
            'footer': 120 if "Square" in target else 250,
            'handle': brand_handle, 'color': brand_color,
            'per_set': imgs_per_set, 'address': prop_addr
        }
        
        if st.button("CREATE ADS"):
            batches = [uploaded_files[i:i + imgs_per_set] for i in range(0, len(uploaded_files), imgs_per_set)]
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED) as zip_file:
                for idx, batch in enumerate(batches):
                    img = create_ad(batch, idx, settings)
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=85)
                    zip_file.writestr(f"ad_{idx+1}.jpg", buf.getvalue())
            
            st.success(f"Ready! Created {len(batches)} ads.")
            st.download_button("📥 DOWNLOAD ALL", zip_buf.getvalue(), "ads.zip")

# LIVE PREVIEW
if uploaded_files:
    st.divider()
    st.subheader("Preview")
    st.image(create_ad(uploaded_files[:imgs_per_set], 0, settings), use_container_width=True)
