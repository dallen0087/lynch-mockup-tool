
import streamlit as st
from PIL import Image, ImageOps
import numpy as np
import zipfile
import io
import os

# Shirt color templates
shirt_templates = {
    "WHITE": "assets/WHITE.jpg",
    "BLACK": "assets/BLACK.jpg",
    "NAVY BLUE": "assets/NAVY_BLUE.jpg",
    "MAROON": "assets/MAROON.jpg",
    "GREEN": "assets/GREEN.jpg",
    "BABY BLUE": "assets/BABY_BLUE.jpg",
    "PINK": "assets/PINK.jpg",
    "YELLOW": "assets/YELLOW.jpg"
}

# Use alpha channel from transparent guide to detect placement box
placement_guide = Image.open("assets/PLACEMENT_GUIDE.png").convert("RGBA")
alpha = np.array(placement_guide.split()[-1])
mask = alpha < 10  # threshold: nearly transparent
ys, xs = np.where(mask)
box_x0, box_y0, box_x1, box_y1 = xs.min(), ys.min(), xs.max(), ys.max()

# Recolor logic
light_colors = ["WHITE", "PINK", "YELLOW"]
dark_colors = ["BLACK", "NAVY BLUE", "MAROON", "GREEN", "BABY BLUE"]

st.title("👕 LynchMockup_Tool_v1")
st.write("Upload one or more transparent PNG designs. They will be auto-placed and recolored onto all t-shirt colors using the PNG placement guide.")

uploaded_files = st.file_uploader("Upload PNG files", type=["png"], accept_multiple_files=True)

if uploaded_files:
    output_zip = io.BytesIO()
    with zipfile.ZipFile(output_zip, 'w') as zipf:
        for uploaded in uploaded_files:
            design = Image.open(uploaded).convert("RGBA")
            alpha = design.split()[-1]
            bbox = alpha.getbbox()
            cropped = design.crop(bbox)

            box_w, box_h = box_x1 - box_x0, box_y1 - box_y0
            aspect = cropped.width / cropped.height
            if aspect > (box_w / box_h):
                new_w = box_w
                new_h = int(new_w / aspect)
            else:
                new_h = box_h
                new_w = int(new_h * aspect)

            resized = cropped.resize((new_w, new_h), Image.Resampling.LANCZOS)
            resized_alpha = resized.split()[-1]

            for color, path in shirt_templates.items():
                base = Image.open(path).convert("RGBA")
                recolor = "white" if color in dark_colors else "black"
                fill = Image.new("RGBA", resized.size, color=recolor)
                fill.putalpha(resized_alpha)

                mock = base.copy()
                px = box_x0 + (box_w - new_w) // 2
                py = box_y0 + (box_h - new_h) // 2
                mock.paste(fill, (px, py), fill)

                filename = f"{uploaded.name.split('.')[0]}_{color.replace(' ', '_')}.jpg"
                img_bytes = io.BytesIO()
                mock.convert("RGB").save(img_bytes, format="JPEG")
                zipf.writestr(filename, img_bytes.getvalue())

    st.success("Mockups ready! Click below to download.")
    st.download_button("📦 Download ZIP", output_zip.getvalue(), file_name="mockups.zip", mime="application/zip")
