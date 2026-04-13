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
        width: 100%; border-radius: 12px; height: 3.5em;
        background: linear-gradient(to right, #007AFF, #00C6FF);
        color: white; border: none; font-weight: bold;
    }
    [data-testid="stFileUploader"] {
        background-color: #f9f9f9; border: 2px dashed #007AFF; border-radius: 15px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- IMAGE ENGINE ---
def process_img(file, crop_h, crop_w):
    """Optimizes image immediately to prevent lag"""
    img = Image.open(file).convert("RGB")
    w, h = img.size
    
    # Manual Crop to remove watermarks/bars
    top_bottom = int(h * (crop_h / 100))
    left_right = int(w * (crop_w / 100))
    img = img.crop((left_right, top_bottom, w - left_right, h - top_bottom))
    
    # Resize for speed - keeping it under 1200px makes it 10x faster
    if img.width > 1200:
        new_h = int(img.height * (1200 / img.width))
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
    
    available_h = c_h - footer_h - 100
    cell_w, cell_h = c_w // cols, available_h // rows 

    for i, img in enumerate(images):
        temp_img = img.copy()
        temp_img.thumbnail((cell_w - 30, cell_h - 30), Image.Resampling.LANCZOS)
        
        pos_x = (i % cols) * cell_w + (cell_w - temp_img.width) // 2
        pos_y = 30 + (i // cols) * cell_h + (cell_h - temp_img.height) // 2
        canvas.paste(temp_img, (int(pos_x), int(pos_y)))
        
        # ID Badge
        item_id = batch_idx * settings['per_set'] + i + 1
        draw.rectangle([pos_x, pos_y, pos_x+45, pos_y+45], fill="black")
        draw.text((pos_x+15, pos_y+12), str(item_id), fill="white")

    # Branding Footer
    draw.rectangle([0, c_h - footer_h, c_w, c_h], fill=settings['color'])
    draw.text((50, c_h - footer_h - 70), f"📍 {settings['address'].upper()}", fill="black")
    draw.text((c_w // 2 - 120, c_h - (footer_h // 2) - 10), f"DM TO ORDER: {settings['handle']}", fill="white")
    return canvas

# --- INTERFACE ---
st.title("🚀 AD Creator")

with st.sidebar:
    st.header("1. Setup")
    brand_handle = st.text_input("Social Handle", "@DEAAM")
    prop_addr = st.text_input("Property Address", "Street Name")
    brand_color = st.color_picker("Theme Color", "#007AFF")
    
    st.divider()
    st.header("2. Crop Watermarks")
    c_h = st.slider("Remove Top/Bottom %", 0, 25, 8)
    c_w = st.slider("Remove Sides %", 0, 25, 0)
    
    st.divider()
    target = st.selectbox("Format", ["Square", "Vertical"])
    imgs_per_set = st.slider("Photos per ad", 1, 9, 4)
    if st.button("🗑️ Reset App"): st.rerun()

# MAIN AREA
st.markdown("### 1. Upload Photos")
uploaded_files = st.file_uploader("Upload images", accept_multiple_files=True, type=['jpg', 'jpeg', 'png'])

if uploaded_files:
    with st.spinner("Optimizing images for speed..."):
        all_processed = [process_img(f, c_h, c_w) for f in uploaded_files]
    
    settings = {
        'size': (1080, 1080) if target == "Square" else (1080, 1920),
        'footer': 120 if target == "Square" else 250,
        'handle': brand_handle, 'color': brand_color,
        'per_set': imgs_per_set, 'address': prop_addr
    }

    st.markdown("### 2. Result")
    if st.button("PREPARE ALL ADS"):
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED) as zip_file:
            batches = [all_processed[i:i + imgs_per_set] for i in range(0, len(all_processed), imgs_per_set)]
            for idx, batch in enumerate(batches):
                final_ad = create_ad(batch, idx, settings)
                buf = io.BytesIO()
                final_ad.save(buf, format='JPEG', quality=80)
                zip_file.writestr(f"ad_{idx+1}.jpg", buf.getvalue())
        
        st.success("All ads are ready!")
        st.download_button("📥 DOWNLOAD ZIP", zip_buf.getvalue(), "ads.zip")

    st.divider()
    st.subheader("Preview")
    st.image(create_ad(all_processed[:imgs_per_set], 0, settings), use_container_width=True)
