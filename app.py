import streamlit as st
from PIL import Image, ImageDraw, ImageOps, ImageFont
import io
import math
import zipfile

# --- PRO UI ---
st.set_page_config(page_title="AD Creator Pro", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #f0f2f5; }
    .stButton>button {
        background: linear-gradient(45deg, #1a1a1a, #4a4a4a);
        color: white; border-radius: 5px; height: 3.5em; width: 100%; border: none;
        letter-spacing: 1px; font-weight: bold;
    }
    [data-testid="stSidebar"] { background-color: #ffffff; }
    </style>
    """, unsafe_allow_html=True)

def process_and_crop(file, c_h, c_w, target_ratio=(1,1)):
    """Processes image and crops to a specific ratio for a clean grid"""
    img = Image.open(file)
    img = ImageOps.exif_transpose(img).convert("RGB")
    
    # Initial watermark crop
    w, h = img.size
    ch_px, cw_px = int(h * (c_h / 100)), int(w * (c_w / 100))
    img = img.crop((cw_px, ch_px, w - cw_px, h - ch_px))
    
    # Force aspect ratio (Square crop for the grid)
    w, h = img.size
    target_w, target_h = target_ratio
    current_ratio = w / h
    target_ratio_val = target_w / target_h
    
    if current_ratio > target_ratio_val:
        new_w = int(target_ratio_val * h)
        offset = (w - new_w) // 2
        img = img.crop((offset, 0, offset + new_w, h))
    else:
        new_h = int(w / target_ratio_val)
        offset = (h - new_h) // 2
        img = img.crop((0, offset, w, offset + new_h))
        
    img.thumbnail((800, 800), Image.Resampling.LANCZOS)
    return img

def build_luxury_ad(batch, settings):
    canvas_w, canvas_h = settings['size']
    footer_h = settings['footer']
    canvas = Image.new('RGB', (canvas_w, canvas_h), "#FFFFFF")
    draw = ImageDraw.Draw(canvas)
    
    num = len(batch)
    cols = 2 if num > 1 else 1
    rows = math.ceil(num / cols)
    
    # Grid Math
    gap = 20
    grid_w = canvas_w - (gap * (cols + 1))
    grid_h = (canvas_h - footer_h) - (gap * (rows + 1))
    
    cell_w = grid_w // cols
    cell_h = grid_h // rows

    for i, img in enumerate(batch):
        # Resize to fit cell exactly
        img_fit = img.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
        
        x = gap + (i % cols) * (cell_w + gap)
        y = gap + (i // cols) * (cell_h + gap)
        canvas.paste(img_fit, (x, y))
        
        # Subtle Number Badge
        badge_size = 40
        draw.rectangle([x, y, x + badge_size, y + badge_size], fill="#1a1a1a")
        draw.text((x + 15, y + 12), str(i+1), fill="white")

    # High-End Footer
    f_start_y = canvas_h - footer_h
    draw.rectangle([0, f_start_y, canvas_w, canvas_h], fill=settings['color'])
    
    # Text with padding
    draw.text((40, f_start_y + 20), f"PREMISES: {settings['addr'].upper()}", fill="white")
    draw.text((40, f_start_y + 50), "REGISTER YOUR INTEREST BELOW", fill="rgba(255,255,255,0.7)")
    draw.text((canvas_w - 300, f_start_y + 35), f"CONTACT: {settings['handle']}", fill="white")
    
    return canvas

# --- APP ---
st.title("🏙️ AD Creator Pro")

with st.sidebar:
    st.header("Brand Style")
    handle = st.text_input("Agent/Handle", "@DEAAM")
    addr = st.text_input("Property Name", "Skyline Apartment")
    accent = st.color_picker("Accent Color", "#1A1A1A")
    
    st.divider()
    st.header("Cleanup")
    c_h = st.slider("Crop Height %", 0, 30, 10)
    c_w = st.slider("Crop Width %", 0, 30, 0)
    
    st.divider()
    mode = st.radio("Size", ["Square (Post)", "Vertical (Story)"])
    per_ad = st.slider("Photos per grid", 1, 6, 4)

files = st.file_uploader("Upload HQ Photos", accept_multiple_files=True)

if files:
    with st.spinner("Refining images..."):
        imgs = [process_and_crop(f, c_h, c_w) for f in files]

    settings = {
        'size': (1080, 1080) if "Square" in mode else (1080, 1920),
        'footer': 120 if "Square" in mode else 220,
        'handle': handle, 'addr': addr, 'color': accent, 'per_set': per_ad
    }

    if st.button("✨ GENERATE LUXURY PACKAGE"):
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, 'w') as zf:
            batches = [imgs[i:i + per_ad] for i in range(0, len(imgs), per_ad)]
            for idx, b in enumerate(batches):
                ad = build_luxury_ad(b, settings)
                buf = io.BytesIO()
                ad.save(buf, format="JPEG", quality=95)
                zf.writestr(f"marketing_ad_{idx+1}.jpg", buf.getvalue())
        st.download_button("📥 DOWNLOAD ZIP", zip_io.getvalue(), "pro_ads.zip")

    st.divider()
    st.subheader("Live Result Preview")
    st.image(build_luxury_ad(imgs[:per_ad], settings), use_container_width=True)
