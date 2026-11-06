import io, datetime
from pathlib import Path
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

FONT = str(Path(__file__).parent / "NotoSansKannada.ttf")
W, H = 1080, 1207
YEL, BLK = (230, 189, 0), (17, 17, 17)

# ---- FIXED PARTS (edit here only if the template ever changes) ----
TITLE = "ನಿತ್ಯ ಸತ್ಯ"
FOOTER = ": ಲೋಕಾ ಸಮಸ್ತಾ ಸುಖಿನೋಭವಂತು :"
WATERMARK = "ಗುರುರಾಜ್"


def font(size, weight=700):
    f = ImageFont.truetype(FONT, int(size))
    try:
        f.set_variation_by_axes([weight, 100])
    except Exception:
        pass
    return f


def wrap(d, text, f, max_w):
    lines = []
    for para in text.split("\n"):
        words, line = para.split(), ""
        if not words:
            lines.append("")
            continue
        for w in words:
            t = f"{line} {w}".strip()
            if d.textlength(t, font=f) <= max_w or not line:
                line = t
            else:
                lines.append(line)
                line = w
        lines.append(line)
    return lines


def make_image(quote: str) -> Image.Image:
    img = Image.new("RGB", (W, H), YEL)
    d = ImageDraw.Draw(img)

    # title + footer
    d.text((W / 2, 100), TITLE, font=font(70), fill=BLK, anchor="mm")
    d.text((500, 1120), FOOTER, font=font(46), fill=BLK, anchor="mm")

    # frame
    for box in [(124, 222, 788, 245), (124, 222, 146, 882), (906, 368, 928, 945),
                (264, 1005, 806, 1027), (830, 1005, 928, 1027), (906, 968, 928, 1027)]:
        d.rectangle(box, fill=BLK)

    # quote marks (drawn as shapes so no extra font is needed)
    qf = font(300, 700)
    d.text((920, 350), "\u201D", font=qf, fill=BLK, anchor="mm")
    d.text((135, 1090), "\u201C", font=qf, fill=BLK, anchor="mm")

    # compass logo
    cx, cy = 1008, 1135
    d.ellipse((cx - 36, cy - 36, cx + 36, cy + 36), outline=(29, 42, 68), width=3)
    d.ellipse((cx - 30, cy - 30, cx + 30, cy + 30), outline=(29, 42, 68), width=2)
    d.polygon([(cx, cy - 28), (cx + 6, cy), (cx, cy + 28), (cx - 6, cy)], fill=(29, 42, 68))
    d.polygon([(cx - 28, cy), (cx, cy - 6), (cx + 28, cy), (cx, cy + 6)], fill=(29, 42, 68))

    # fixed watermark (rotated, faint)
    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(wm).text((W / 2, 640), WATERMARK, font=font(96, 400),
                            fill=(0, 0, 0, 95), anchor="mm")
    wm = wm.rotate(19, center=(W / 2, 640), resample=Image.BICUBIC)
    img.paste(wm, (0, 0), wm)

    # daily quote: auto-fit inside the frame
    d = ImageDraw.Draw(img)
    bx, by, bw, bh = 190, 290, 690, 640
    quote = quote.strip()
    if quote:
        size = 110
        while size >= 22:
            f = font(size)
            lh = size * 1.55
            lines = wrap(d, quote, f, bw)
            if len(lines) * lh <= bh:
                break
            size -= 2
        y = by + (bh - len(lines) * lh) / 2 + lh / 2
        for ln in lines:
            d.text((bx + bw / 2, y), ln, font=f, fill=BLK, anchor="mm")
            y += lh
    return img


st.set_page_config(page_title="ನಿತ್ಯ ಸತ್ಯ", page_icon="🟡", layout="centered")
st.title("ನಿತ್ಯ ಸತ್ಯ – Daily Quote")

quote = st.text_area("ಇಂದಿನ ಸುವಿಚಾರ (Today's quote)", height=160,
                     placeholder="ಇಲ್ಲಿ ಬರೆಯಿರಿ…")
img = make_image(quote)
st.image(img, use_container_width=True)

buf = io.BytesIO()
img.save(buf, format="PNG")
st.download_button("⬇ Download PNG", buf.getvalue(),
                   file_name=f"nitya-satya-{datetime.date.today()}.png",
                   mime="image/png", use_container_width=True)
