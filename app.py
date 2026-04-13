import streamlit as st
from PIL import Image, ImageDraw, ImageOps
import io
import zipfile

st.set_page_config(page_title="AD Creator", layout="centered")

def process_single_image(file, crop_percent):
    """Process one image at a time to save memory"""
    try:
        img = Image.open(file)
        img = ImageOps.exif_transpose(img).convert("RGB")
        # Kill the resolution immediately to save the server
        img.thumbnail((800, 800), Image.Resampling.NEAREST)
        
        # Crop
        w, h = img.size
        cut = int(h * (crop_percent / 100))
        img = img.crop((0, cut, w, h - cut))
        
        # Square
        w, h = img.size
        side = min(w, h)
        return img.crop(((w-side)//2, (h-side)//2, (w+side)//2, (h+side)//2))
    except:
        return None

st.title("🚀 Professional AD Creator")

# Minimal sidebar to prevent re-run lag
addr = st.sidebar.text_input("Property", "Location")
handle = st.sidebar.text_input("Contact", "@Handle")
color = st.sidebar.color_picker("Theme", "#000000")
crop_val = st.sidebar.slider("Crop Status Bars %", 0, 20, 10)

files = st.file_uploader("Upload Photos (Max 8 for stability)", accept_multiple_files=True)

if files:
    if st.button("CONVERT & DOWNLOAD"):
        zip_io = io.BytesIO()
        with zipfile.ZipFile(zip_io, 'w') as zf:
            # PROCESS IMAGES ONE BY ONE
            processed_imgs = []
            for f in files:
                p = process_single_image(f, crop_val)
                if p: processed_imgs.append(p)
            
            # GENERATE COLLAGES (4 per page)
            for idx in range(0, len(processed_imgs), 4):
                batch = processed_imgs[idx:idx+4]
                canvas = Image.new('RGB', (1080, 1080), "white")
                draw = ImageDraw.Draw(canvas)
                
                # Grid
                for i, img in enumerate(batch):
                    img_scaled = img.resize((530, 530), Image.Resampling.NEAREST)
                    x = (i % 2) * 540 + 5
                    y = (i // 2) * 540 + 5
                    canvas.paste(img_scaled, (x, y))
                
                # Simple Ribbon
                draw.rectangle([0, 1000, 1080, 1080], fill=color)
                draw.text((40, 1020), f"{addr.upper()} | {handle}", fill="white")
                
                buf = io.BytesIO()
                canvas.save(buf, format="JPEG", quality=75)
                zf.writestr(f"ad_{idx//4 + 1}.jpg", buf.getvalue())
        
        st.success("Ads Created!")
        st.download_button("📥 DOWNLOAD ALL", zip_io.getvalue(), "property_ads.zip")
