import streamlit as st
from PIL import Image, ImageDraw, ImageOps
import io
import math
import zipfile

# --- CRITICAL STABILITY SETTINGS ---
st.set_page_config(page_title="AD Creator Pro", layout="wide")

# --- LIGHTWEIGHT IMAGE ENGINE ---
def ultra_light_process(file, c_h, c_w):
    try:
        # Load and immediately shrink to save memory
        img = Image.open(file)
        img = ImageOps.exif_transpose(img).convert("RGB")
        
        # Resize first! This is the secret to stopping the crashes.
        # We shrink it to 1000px max height/width immediately.
        img.thumbnail((1000, 1000), Image.Resampling.LANCZOS)
        
        w, h = img.size
        # Watermark/Edge Crop
        ch_px, cw_px = int(h * (c_h / 100)), int(w * (c_w / 100))
        img = img.crop((cw_px, ch_px, w - cw_px, h - ch_px))
        
        # Final Square Crop
        w, h = img.size
        min_dim = min(w, h)
        img = img.crop(((w - min_dim)//2, (h - min_dim)//2, (w + min_dim)//2, (h + min_dim)//2))
        return img
    except Exception as e:
        return None

def build_grid(batch, settings):
    if not batch: return None
    canvas_w, canvas_h = settings['size']
    footer_h = settings['footer']
    canvas = Image.new('RGB', (canvas_w, canvas_h), "white")
    draw = ImageDraw.Draw(canvas)
    
    num = len(batch)
    cols = 2 if num > 1 else 1
    rows = math.ceil(num / cols)
    
    gap = 20
    grid_w = canvas_w - (gap * (cols + 1))
    grid_h = (canvas_h - footer_h - 40) - (gap * (rows + 1))
    cell_w, cell_h = grid_w // cols, grid_h // rows

    for i, img in enumerate(batch):
        if img:
            img_res = img.resize((cell_w, cell_h), Image.Resampling.LANCZOS)
            x = gap + (i % cols) * (cell_w + gap)
            y = gap + (i // cols) * (cell_h + gap) + 20
            canvas.paste(img_res, (x, y))
            # Black badge
            draw.rectangle([x, y, x+40, y+40], fill="black")
            draw.text((x+15, y+12), str(i+1), fill="white")

    # Branding
    f_y = canvas_h - footer_h
    draw.rectangle([0, f_y, canvas_w, canvas_h], fill=settings['color'])
    draw.text((40, f_y + 20), f"UNIT: {settings['addr'].upper()}", fill="white")
    draw.text((canvas_w - 280, f_y + 20), f"CONTACT: {settings['handle']}", fill="white")
    return canvas

# --- INTERFACE ---
st.title("🏙️ AD Creator Pro")

with st.sidebar:
    st.header("Step 1: Info")
    handle = st.text_input("Social Handle", "@DEAAM")
    addr = st.text_input("Property", "Singapore")
    accent = st.color_picker("Color", "#1a1a1a")
    st.divider()
    st.header("Step 2: Clean")
    c_h = st.slider("Crop Top/Bottom %", 0, 30, 10)
    c_w = st.slider("Crop Sides %", 0, 30, 0)
    st.divider()
    mode = st.radio("Style", ["Square", "Vertical"])
    per_ad = st.slider("Photos per ad", 1, 6, 4)

# THE UPLOADER
files = st.file_uploader("Upload 2-10 Photos", accept_multiple_files=True)

if files:
    # Process images one by one to keep memory low
    imgs = []
    progress_bar = st.progress(0)
    for idx, f in enumerate(files):
        processed = ultra_light_process(f, c_h, c_w)
        if processed:
            imgs.append(processed)
        progress_bar.progress((idx + 1) / len(files))

    if imgs:
        settings = {
            'size': (1080, 1080) if mode == "Square" else (1080, 1920),
            'footer': 80 if mode == "Square" else 150,
            'handle': handle, 'addr': addr, 'color': accent, 'per_set': per_ad
        }

        if st.button("🚀 CREATE ALL ADS"):
            zip_io = io.BytesIO()
            with zipfile.ZipFile(zip_io, 'w') as zf:
                batches = [imgs[i:i + per_ad] for i in range(0, len(imgs), per_ad)]
                for idx, b in enumerate(batches):
                    ad = build_grid(b, settings)
                    buf = io.BytesIO()
                    ad.save(buf, format="JPEG", quality=80) # Lower quality = faster download
                    zf.writestr(f"ad_{idx+1}.jpg", buf.getvalue())
            st.download_button("📥 DOWNLOAD NOW", zip_io.getvalue(), "ads.zip")

        st.divider()
        st.subheader("Preview")
        st.image(build_grid(imgs[:per_ad], settings), use_container_width=True)
else:
    st.write("Waiting for photos...")
