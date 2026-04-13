import streamlit as st
from PIL import Image, ImageDraw
import io
import math
import zipfile
import datetime

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
def process_img(file):
    """Shrinks image immediately to make uploading faster"""
    img = Image.open(file).convert("RGB")
    # Resize high-res photos to 1200px max to save memory
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
        img_cropped = img.crop((0, int(cut), w, int(h - cut)))
        img_cropped.thumbnail((cell_w - 40, cell_h - 40), Image.Resampling.LANCZOS)
        
        pos_x = (i % cols) * cell_w + (cell_w - img_cropped.width) // 2
        pos_y = 50 + (i // cols) * cell_h + (cell_h - img_cropped.height) // 2
        canvas.paste(img_cropped, (int(pos_x), int(pos_y)))
        
        # Number Badge
        item_id = batch_idx * settings['per_set'] + i + 1
        draw.rectangle([pos_x, pos_y, pos_x+50, pos_y+50], fill="black")
        draw.text((pos_x+18, pos_y+15), str(item_id), fill="white")

    # Branding Footer
    draw.rectangle([0, c_h - footer_h, c_w, c_h], fill=settings['color'])
    draw.text((60, c_h - footer_h - 80), f"📍 {settings['address'].upper()}", fill="black")
    draw.text((c_w // 2 - 130, c_h - (footer_h // 2) - 10), f"DM TO ORDER: {settings['handle']}", fill="white")
    return canvas

# --- MAIN INTERFACE ---
st.title("🚀 AD Creator")

with st.sidebar:
    st.header("Step 1: Setup")
    brand_handle = st.text_input("Social Handle", "@DEAAM")
    prop_addr = st.text_input("Property Address", "Street Name")
    brand_color = st.color_picker("Theme Color", "#007AFF")
    target = st.selectbox("Format", ["Square (Post)", "Vertical (Story)"])
    imgs_per_set = st.slider("Photos per ad", 1, 9, 4)
    if st.button("🗑️ Clear All"):
        st.rerun()

st.markdown("### 1. Upload Photos")
uploaded_files = st.file_uploader("Select images", accept_multiple_files=True)

if uploaded_files:
    # Process images only when uploaded
    processed_images = [process_img(f) for f in uploaded_files]
    
    settings = {
        'size': (1080, 1080) if "Square" in target else (1080, 1920),
        'footer': 120 if "Square" in target else 250,
        'handle': brand_handle, 'color': brand_color,
        'per_set': imgs_per_set, 'address': prop_addr
    }

    st.markdown("### 2. Generate")
    if st.button("CREATE ADS"):
        with st.spinner("Processing your photos..."):
            batches = [processed_images[i:i + imgs_per_set] for i in range(0, len(processed_images), imgs_per_set)]
            zip_buf = io.BytesIO()
            with zipfile.ZipFile(zip_buf, "a", zipfile.ZIP_DEFLATED) as zip_file:
                for idx, batch in enumerate(batches):
                    final_ad = create_ad(batch, idx, settings)
                    buf = io.BytesIO()
                    final_ad.save(buf, format='JPEG', quality=85)
                    zip_file.writestr(f"ad_{idx+1}.jpg", buf.getvalue())
            
            st.success("Ads generated successfully!")
            st.download_button("📥 DOWNLOAD ALL", zip_buf.getvalue(), "ads.zip")

    st.divider()
    st.subheader("Preview")
    st.image(create_ad(processed_images[:imgs_per_set], 0, settings), use_container_width=True)
