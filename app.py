import streamlit as st
from PIL import Image, ImageDraw, ImageFilter
import io
import math
import zipfile
import datetime

# --- PAGE SETUP ---
st.set_page_config(page_title="AdGen Pro", layout="wide")

# --- UI STYLING ---
st.markdown("""
    <style>
    /* Big Colorful Buttons */
    .stButton > button {
        width: 100%;
        border-radius: 12px;
        height: 3em;
        font-size: 18px !important;
        font-weight: bold !important;
        text-transform: uppercase;
    }
    /* Upload Box Styling */
    [data-testid="stFileUploader"] {
        background-color: #f0f2f6;
        border-radius: 15px;
        padding: 10px;
    }
    /* Step Headers */
    .step-header {
        font-size: 24px;
        font-weight: bold;
        color: #FF4B2B;
        margin-bottom: 10px;
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
        cut = (settings['crop'] / 100) * h
        img = img.crop((0, cut, w, h - cut))
        img.thumbnail((cell_w - 40, cell_h - 40), Image.Resampling.LANCZOS)
        
        pos_x = (i % cols) * cell_w + (cell_w - img.width) // 2
        pos_y = 50 + (i // cols) * cell_h + (cell_h - img.height) // 2
        canvas.paste(img, (int(pos_x), int(pos_y)))
        
        # Number Circle
        item_id = batch_idx * settings['per_set'] + i + 1
        draw.ellipse([pos_x, pos_y, pos_x+50, pos_y+50], fill="black")
        draw.text((pos_x+18, pos_y+15), str(item_id), fill="white")

    # Footer
    draw.rectangle([0, c_h - footer_h, c_w, c_h], fill=settings['color'])
    draw.text((60, c_h - footer_h - 80), f"📍 {settings['address'].upper()}", fill="black")
    draw.text((c_w // 2 - 130, c_h - (footer_h // 2) - 10), f"DM TO ORDER: {settings['handle']}", fill="white")
    return canvas

# --- NAVIGATION FLOW ---
st.title("🏡 Property Ad Creator")

# STEP 1: SIDEBAR SETUP
with st.sidebar:
    st.header("⚙️ 1. SETUP DETAILS")
    brand_handle = st.text_input("Your Social Name", "@DEAAM")
    prop_addr = st.text_input("Property Name/Address", "Orchard Road")
    brand_color = st.color_picker("Choose Theme Color", "#007AFF")
    
    st.divider()
    st.header("📐 2. LAYOUT")
    target = st.selectbox("Where will you post?", ["Instagram/Facebook", "TikTok/Stories"])
    imgs_per_set = st.slider("Photos per ad", 1, 9, 4)
    
    if st.button("🔄 Start New Project"):
        st.rerun()

# STEP 2 & 3: MAIN AREA
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<p class="step-header">📸 STEP 1: ADD PHOTOS</p>', unsafe_allow_html=True)
    uploaded_files = st.file_uploader("Tap here to select photos from your phone", accept_multiple_files=True)

with col2:
    st.markdown('<p class="step-header">📦 STEP 2: GET RESULTS</p>', unsafe_allow_html=True)
    if uploaded_files:
        settings = {
            'size': (1080, 1080) if "Instagram" in target else (1080, 1920),
            'footer': 120 if "Instagram" in target else 250,
            'crop': 8, 'handle': brand_handle, 'color': brand_color,
            'per_set': imgs_per_set, 'address': prop_addr
        }
        
        # PROMINENT DOWNLOAD BUTTON
        if st.button("🎨 CREATE MY ADS NOW"):
            batches = [uploaded_files[i:i + imgs_per_set] for i in range(0, len(uploaded_files), imgs_per_set)]
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED) as zip_file:
                for idx, batch in enumerate(batches):
                    img = create_ad(batch, idx, settings)
                    buf = io.BytesIO()
                    img.save(buf, format='JPEG', quality=85)
                    zip_file.writestr(f"property_ad_{idx+1}.jpg", buf.getvalue())
            
            st.success(f"Done! {len(batches)} Ads Created.")
            st.download_button("📥 DOWNLOAD ALL (ZIP FILE)", zip_buf.getvalue(), "my_property_ads.zip")

# PREVIEW
if uploaded_files:
    st.divider()
    st.subheader("👀 Preview of your first ad:")
    st.image(create_ad(uploaded_files[:imgs_per_set], 0, settings), use_container_width=True)
