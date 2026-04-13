import streamlit as st
from PIL import Image, ImageDraw, ImageOps
import io
import math
import zipfile

# --- UI STYLE ---
st.set_page_config(page_title="AD Creator Pro", layout="wide")
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button {
        background: linear-gradient(90deg, #1a1a1a 0%, #434343 100%);
        color: white; border: none; border-radius: 8px; height: 3.5em; width: 100%; font-weight: bold;
    }
    [data-testid="stSidebar"] { background-color: white; border-right: 1px solid #eee; }
    </style>
    """, unsafe_allow_html=True)

# --- IMAGE ENGINE ---
def safe_process(file, c_h, c_w):
    try:
        img = Image.open(file)
        img = ImageOps.exif_transpose(img).convert("RGB")
        w, h = img.size
        # Watermark crop
        ch_px, cw_px = int(h * (c_h / 100)), int(w * (c_w / 100))
        img = img.crop((cw_px, ch_px, w - cw_px, h - ch_px))
        # Center Crop to Square for professional look
        w, h = img.size
        min_dim = min(w, h)
        img = img.crop(((w - min_dim)//2, (h - min_dim)//2, (w + min_dim)//2, (h + min_dim)//2))
        img.thumbnail((800, 800), Image.Resampling.LANCZOS)
        return img
    except:
        return None

def build_pro_ad(batch, settings):
    if not batch: return None
    
    canvas_w, canvas_h = settings['size']
    footer_h = settings['footer']
    canvas = Image.new('RGB', (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)
    
    num = len(batch)
    cols = 2 if num > 1 else 1
    rows = math.ceil(num / cols)
    
    gap = 24
    grid_w = canvas_w - (gap * (cols + 1))
    grid_h = (canvas_h - footer_h - 60) - (gap * (rows + 1))
    
    cell_w, cell_h = grid_w // cols, grid_h // rows

    for i, img in enumerate(batch):
        if img is None: continue
        img_res = img.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
        x = gap + (i % cols) * (cell_w + gap)
        y = gap + (i // cols) * (cell_h + gap) + 40 # Offset for top margin
        canvas.paste(img_res, (x, y))
        
        # ID Circle
        draw.ellipse([x+10, y+10, x+50, y+50], fill="black")
        draw.text((x+22, y+18), str(i+1), fill="white")

    # Footer
    f_y = canvas_h - footer_h
    draw.rectangle([0, f_y, canvas_w, canvas_h], fill=settings['color'])
    draw.text((40, f_y + 25), f"PROPERTY: {settings['addr'].upper()}", fill="white")
    draw.text((canvas_w - 300, f_y + 25), f"INQUIRY: {settings['handle']}", fill="white")
    
    return canvas

# --- INTERFACE ---
st.title("🏙️ AD Creator Pro")

with st.sidebar:
    st.header("Settings")
    handle = st.text_input("Contact Handle", "@DEAAM")
    addr = st.text_input("Location", "Singapore")
    accent = st.color_picker("Brand Color", "#1a1a1a")
    st.divider()
    c_h = st.slider("Remove Top/Bottom %", 0, 30, 10)
    c_w = st.slider("Remove Sides %", 0, 30, 0)
    st.divider()
    mode = st.radio("Size", ["Square", "Vertical"])
    per_ad = st.slider("Photos per ad", 1, 6, 4)

files = st.file_uploader("Upload HQ Photos", accept_multiple_files=True)

if files:
    # 1. Process
    with st.spinner("Preparing..."):
        imgs = [safe_process(f, c_h, c_w) for f in files]
        imgs = [i for i in imgs if i is not None] # Remove any errors

    if imgs:
        settings = {
            'size': (1080, 1080) if mode == "Square" else (1080, 1920),
            'footer': 100 if mode == "Square" else 180,
            'handle': handle, 'addr': addr, 'color': accent, 'per_set': per_ad
        }

        # 2. Actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✨ GENERATE ALL"):
                zip_io = io.BytesIO()
                with zipfile.ZipFile(zip_io, 'w') as zf:
                    batches = [imgs[i:i + per_ad] for i in range(0, len(imgs), per_ad)]
                    for idx, b in enumerate(batches):
                        ad = build_pro_ad(b, settings)
                        buf = io.BytesIO()
                        ad.save(buf, format="JPEG", quality=95)
                        zf.writestr(f"ad_{idx+1}.jpg", buf.getvalue())
                st.download_button("📥 DOWNLOAD ZIP", zip_io.getvalue(), "property_ads.zip")

        # 3. Preview
        st.divider()
        st.subheader("Design Preview")
        preview = build_pro_ad(imgs[:per_ad], settings)
        if preview:
            st.image(preview, use_container_width=True)
else:
    st.info("Upload photos to begin. Your ads will appear here.")
