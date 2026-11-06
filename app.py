import io, datetime
from pathlib import Path
import streamlit as st
from PIL import Image, ImageDraw, ImageFont

FONT = str(Path(__file__).parent / "NotoSansKannada.ttf")
W, H = 1080, 1207
YEL, BLK, NAVY = (230, 189, 0), (17, 17, 17), (29, 42, 68)

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


def smooth(size, fn, S=4):
    """Draw shapes at S x size and shrink -> anti-aliased edges."""
    w, h = size
    big = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    fn(ImageDraw.Draw(big), S)
    return big.resize((w, h), Image.LANCZOS)


def comma(dr, S, cx, cy):
    """Round blob with a curved tail going down-left (like the 9 of a closing quote)."""
    r = 31
    dr.ellipse(((cx - r) * S, (cy - r) * S, (cx + r) * S, (cy + r) * S), fill=BLK)
    pts = []
    # curved tail: right edge of blob -> tip -> left edge of blob
    for t in range(0, 21):
        u = t / 20
        x = (1 - u) ** 2 * (cx + r) + 2 * (1 - u) * u * (cx + 26) + u ** 2 * (cx - 30)
        y = (1 - u) ** 2 * (cy + 4) + 2 * (1 - u) * u * (cy + 50) + u ** 2 * (cy + 68)
        pts.append((x * S, y * S))
    for t in range(0, 21):
        u = t / 20
        x = (1 - u) ** 2 * (cx - 30) + 2 * (1 - u) * u * (cx - 8) + u ** 2 * (cx - r)
        y = (1 - u) ** 2 * (cy + 68) + 2 * (1 - u) * u * (cy + 28) + u ** 2 * (cy + 4)
        pts.append((x * S, y * S))
    dr.polygon(pts, fill=BLK)


def quote_marks(img):
    # closing mark (top-right)
    lay = smooth((200, 130), lambda dr, S: (comma(dr, S, 60, 40), comma(dr, S, 138, 40)))
    img.paste(lay, (825, 235), lay)
    # opening mark (bottom-left) = same shape turned 180 degrees
    op = lay.rotate(180)
    img.paste(op, (40, 880), op)


def compass(img, cx, cy):
    def fn(dr, S):
        c = 55
        dr.ellipse(((c - 37) * S, (c - 37) * S, (c + 37) * S, (c + 37) * S), outline=NAVY, width=3 * S)
        dr.ellipse(((c - 31) * S, (c - 31) * S, (c + 31) * S, (c + 31) * S), outline=NAVY, width=2 * S)
        import math
        pts = []
        for i in range(16):
            ang = math.radians(i * 22.5 - 90)
            rad = [29, 7, 12, 7][i % 4] if i % 2 == 0 or True else 7
            rad = 29 if i % 4 == 0 else (17 if i % 4 == 2 else 6)
            pts.append(((c + rad * math.cos(ang)) * S, (c + rad * math.sin(ang)) * S))
        dr.polygon(pts, fill=NAVY)
        dr.ellipse(((c - 4) * S, (c - 4) * S, (c + 4) * S, (c + 4) * S), fill=YEL)
    lay = smooth((110, 110), fn)
    img.paste(lay, (cx - 55, cy - 55), lay)


def make_image(quote: str) -> Image.Image:
    img = Image.new("RGB", (W, H), YEL)

    # warm gradient: brighter gold in the middle, deeper at the edges
    mask = Image.radial_gradient("L").resize((W, H))
    img = Image.composite(Image.new("RGB", (W, H), (214, 170, 0)),
                          Image.new("RGB", (W, H), (244, 205, 18)), mask)

    d = ImageDraw.Draw(img)
    d.text((W / 2, 100), TITLE, font=font(68), fill=BLK, anchor="mm")
    # small ornament under the title
    d.rectangle((360, 163, 500, 166), fill=BLK)
    d.rectangle((580, 163, 720, 166), fill=BLK)
    d.polygon([(540, 152), (552, 165), (540, 178), (528, 165)], fill=BLK)
    d.text((500, 1120), FOOTER, font=font(44), fill=BLK, anchor="mm")

    for box in [(124, 222, 788, 245), (124, 222, 146, 882), (906, 368, 928, 945),
                (264, 1005, 806, 1027), (830, 1005, 928, 1027), (906, 968, 928, 1027)]:
        d.rectangle(box, fill=BLK)

    quote_marks(img)
    compass(img, 1008, 1135)

    # fixed watermark: thin, tilted, faint
    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(wm).text((W / 2, 650), WATERMARK, font=font(92, 300),
                            fill=(0, 0, 0, 62), anchor="mm")
    wm = wm.rotate(19, center=(W / 2, 650), resample=Image.BICUBIC)
    img.paste(wm, (0, 0), wm)

    # daily quote, auto-fit
    d = ImageDraw.Draw(img)
    bx, by, bw, bh = 200, 345, 660, 580
    quote = quote.strip()
    if quote:
        size = 110
        while size >= 22:
            f = font(size, 600)
            lh = size * 1.55
            lines = wrap(d, quote, f, bw)
            if len(lines) * lh <= bh:
                break
            size -= 2
        y = by + (bh - len(lines) * lh) / 2 + lh / 2
        for ln in lines:
            d.text((bx + bw / 2, y), ln, font=f, fill=(22, 14, 0), anchor="mm")
            y += lh
    return img


# ------------------------- phone-friendly page -------------------------
st.set_page_config(page_title="ನಿತ್ಯ ಸತ್ಯ", page_icon="🟡", layout="centered",
                   initial_sidebar_state="collapsed")
st.markdown("""
<style>
#MainMenu, footer, header [data-testid="stToolbar"] {visibility:hidden;}
.block-container {padding:1rem 0.8rem 2rem 0.8rem; max-width:640px;}
textarea {font-size:20px !important; line-height:1.5 !important;}
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
  width:100%; padding:0.8rem 1rem; font-size:18px; font-weight:700; border-radius:10px;
}
[data-testid="stFormSubmitButton"] > button {background:#e6bd00; color:#111; border:0;}
.stDownloadButton > button {background:#111; color:#fff; border:0;}
img {border-radius:10px;}
</style>
""", unsafe_allow_html=True)

st.markdown("### 🟡 ನಿತ್ಯ ಸತ್ಯ")

if "quote" not in st.session_state:
    st.session_state.quote = ""

with st.form("f", clear_on_submit=False):
    text = st.text_area("ಇಂದಿನ ಸುವಿಚಾರ", value=st.session_state.quote, height=170,
                        placeholder="ಇಲ್ಲಿ ಬರೆಯಿರಿ…", label_visibility="collapsed")
    ok = st.form_submit_button("✔ Make image")
if ok:
    st.session_state.quote = text

img = make_image(st.session_state.quote)
st.image(img)

buf = io.BytesIO()
img.save(buf, format="PNG")
st.download_button("⬇ Download image", buf.getvalue(),
                   file_name=f"nitya-satya-{datetime.date.today()}.png", mime="image/png")
st.caption("Phone: if the download goes to Files, long-press the image above → Save to Photos.")
