import io, math, datetime
from pathlib import Path
import streamlit as st
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter

HERE = Path(__file__).parent
FONT = str(HERE / "NotoSansKannada.ttf")
ART = HERE / "shrine.jpeg"          # the pencil sketch (keep next to app.py)
OY = 240                            # extra height added on top for the shrine
W, H = 1080, 1207 + OY
YEL, BLK, NAVY = (230, 189, 0), (17, 17, 17), (29, 42, 68)

# ---- FIXED PARTS (edit here only if the template ever changes) ----
TITLE = "ನಿತ್ಯ ಸತ್ಯ"
FOOTER = ": ಲೋಕಾ ಸಮಸ್ತಾ ಸುಖಿನೋಭವಂತು :"
WATERMARK = "ಗುರುರಾಜ್"
ART_OPACITY = 1.0                   # shrine line darkness (1.0 = full black ink)
ART_CENTER = (540, 135)             # centre of the shrine (above the title)
ART_HEIGHT = 240                    # height of the shrine in pixels
QUOTE_BOX = (200, 345 + OY, 660, 580)   # x, y, width, height of the quote area
WM_ALPHA = 85                       # watermark strength (0-255)


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
    lay = smooth((200, 130), lambda dr, S: (comma(dr, S, 60, 40), comma(dr, S, 138, 40)))
    img.paste(lay, (825, 235 + OY), lay)
    op = lay.rotate(180)
    img.paste(op, (40, 880 + OY), op)


def compass(img, cx, cy):
    def fn(dr, S):
        c = 55
        dr.ellipse(((c - 37) * S, (c - 37) * S, (c + 37) * S, (c + 37) * S), outline=NAVY, width=3 * S)
        dr.ellipse(((c - 31) * S, (c - 31) * S, (c + 31) * S, (c + 31) * S), outline=NAVY, width=2 * S)
        pts = []
        for i in range(16):
            ang = math.radians(i * 22.5 - 90)
            rad = 29 if i % 4 == 0 else (17 if i % 4 == 2 else 6)
            pts.append(((c + rad * math.cos(ang)) * S, (c + rad * math.sin(ang)) * S))
        dr.polygon(pts, fill=NAVY)
        dr.ellipse(((c - 4) * S, (c - 4) * S, (c + 4) * S, (c + 4) * S), fill=YEL)
    lay = smooth((110, 110), fn)
    img.paste(lay, (cx - 55, cy - 55), lay)


_art_cache = {}


def art_layer():
    """Pencil sketch -> transparent ink layer (paper turns see-through, lines stay)."""
    if "a" in _art_cache:
        return _art_cache["a"]
    g = ImageOps.grayscale(Image.open(ART))
    g = ImageOps.autocontrast(g, cutoff=1)
    # push light paper to pure white, keep the dark pencil lines
    g = g.point(lambda v: 255 if v > 215 else int(255 * (v / 215) ** 1.3))
    ink = ImageOps.invert(g)                       # 255 = line, 0 = paper
    box = ink.point(lambda v: 255 if v > 40 else 0).getbbox()
    if box:
        ink = ink.crop(box)                        # trim empty paper margin
    ratio = ART_HEIGHT / ink.height
    ink = ink.resize((int(ink.width * ratio), ART_HEIGHT), Image.LANCZOS)
    ink = ink.filter(ImageFilter.UnsharpMask(radius=1.2, percent=140, threshold=2))
    ink = ink.point(lambda v: min(255, int(v * 1.25 * ART_OPACITY)))
    layer = Image.new("RGBA", ink.size, (22, 14, 0, 0))
    layer.putalpha(ink)
    _art_cache["a"] = layer
    return layer


def make_image(quote: str) -> Image.Image:
    # warm gradient: brighter gold in the middle, deeper at the edges
    mask = Image.radial_gradient("L").resize((W, H))
    img = Image.composite(Image.new("RGB", (W, H), (214, 170, 0)),
                          Image.new("RGB", (W, H), (244, 205, 18)), mask)

    # sacred artwork sits at the very back, behind everything
    if ART.exists():
        a = art_layer()
        img.paste(a, (ART_CENTER[0] - a.width // 2, ART_CENTER[1] - a.height // 2), a)

    d = ImageDraw.Draw(img)
    d.text((W / 2, 100 + OY), TITLE, font=font(68), fill=BLK, anchor="mm")
    d.rectangle((360, 163 + OY, 500, 166 + OY), fill=BLK)
    d.rectangle((580, 163 + OY, 720, 166 + OY), fill=BLK)
    d.polygon([(540, 152 + OY), (552, 165 + OY), (540, 178 + OY), (528, 165 + OY)], fill=BLK)
    d.text((500, 1120 + OY), FOOTER, font=font(44), fill=BLK, anchor="mm")

    for x0, y0, x1, y1 in [(124, 222, 788, 245), (124, 222, 146, 882), (906, 368, 928, 945),
                           (264, 1005, 806, 1027), (830, 1005, 928, 1027), (906, 968, 928, 1027)]:
        d.rectangle((x0, y0 + OY, x1, y1 + OY), fill=BLK)

    quote_marks(img)
    compass(img, 1008, 1135 + OY)

    # fixed watermark: thin, tilted, faint
    wm = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(wm).text((W / 2, 650 + OY), WATERMARK, font=font(130, 500),
                            fill=(0, 0, 0, WM_ALPHA), anchor="mm")
    wm = wm.rotate(19, center=(W / 2, 650 + OY), resample=Image.BICUBIC)
    img.paste(wm, (0, 0), wm)

    # daily quote, auto-fit
    d = ImageDraw.Draw(img)
    bx, by, bw, bh = QUOTE_BOX
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
