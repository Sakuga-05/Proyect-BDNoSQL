"""
generate_images.py
Genera 54 imágenes turísticas sintéticas representativas de destinos colombianos.
Cada imagen tiene gradiente, formas geométricas temáticas y etiqueta de texto.
Salida: data/imagenes/<categoria>/<doc_id>.png
"""

import os
import math
import json
from PIL import Image, ImageDraw, ImageFont

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
IMG_DIR  = os.path.join(BASE_DIR, "data", "imagenes")
DOCS_JSON = os.path.join(BASE_DIR, "data", "documentos.json")

SIZE = 384  # CLIP input-friendly square

# ── Paletas temáticas (fondo degradado, acento) ────────────────────────────────
PALETTES = {
    "playa":     ((0, 105, 148),   (135, 206, 235), (255, 200, 100)),  # azul mar → cielo, arena
    "selva":     ((34, 85, 34),    (120, 190, 80),  (255, 220, 50)),   # verde selva, sol
    "ciudad":    ((60, 60, 100),   (140, 140, 200), (255, 180, 60)),   # noche urbana, luz
    "desierto":  ((180, 110, 30),  (240, 190, 90),  (80, 50, 20)),    # dunas, cielo seco
    "colonial":  ((120, 70, 30),   (210, 160, 90),  (220, 50, 50)),   # tierra, fachadas
    "montaña":   ((30, 60, 80),    (100, 160, 130), (200, 230, 200)), # niebla andina
    "pacifico":  ((10, 80, 80),    (0, 160, 140),   (180, 240, 220)), # Pacífico
    "caribeno":  ((0, 130, 180),   (0, 200, 160),   (255, 210, 120)), # Caribe turquesa
    "cafetero":  ((80, 50, 20),    (160, 110, 60),  (100, 160, 60)),  # café, montaña verde
    "llanura":   ((150, 120, 40),  (220, 190, 80),  (60, 120, 60)),   # sabana, vegetación
}

# Tema visual por doc_id / patrón de nombre
THEME_MAP = {
    "cartagena": "colonial", "san_andres": "caribeno", "medellin": "ciudad",
    "santa_marta": "playa",  "eje_cafetero": "cafetero", "amazonia": "selva",
    "bogota": "ciudad",      "nuqui": "pacifico",   "villa_de_leyva": "colonial",
    "llanos": "llanura",     "capurgana": "playa",  "tatacoa": "desierto",
    "guatape": "montaña",    "mompox": "colonial",  "providencia": "caribeno",
    "cali": "ciudad",        "valledupar": "ciudad","barranquilla": "caribeno",
    "pasto": "montaña",      "guajira": "desierto", "amazonas": "selva",
    "tayrona": "playa",      "rosario": "playa",    "baru": "playa",
    "cafe": "cafetero",      "libertador": "colonial",
}

def detect_theme(titulo: str) -> str:
    t = titulo.lower()
    for keyword, theme in THEME_MAP.items():
        if keyword.replace("_", " ") in t or keyword in t.replace(" ", "_"):
            return theme
    if any(w in t for w in ["isla", "playa", "caribe", "mar"]):
        return "playa"
    if any(w in t for w in ["selva", "amazon"]):
        return "selva"
    if any(w in t for w in ["ciudad", "capital", "urbana"]):
        return "ciudad"
    if any(w in t for w in ["colonial", "pueblo"]):
        return "colonial"
    return "montaña"


def gradient_bg(draw: ImageDraw.ImageDraw, c1: tuple, c2: tuple, size: int):
    """Rellena fondo con degradado vertical c1 → c2."""
    for y in range(size):
        t = y / size
        r = int(c1[0] * (1 - t) + c2[0] * t)
        g = int(c1[1] * (1 - t) + c2[1] * t)
        b = int(c1[2] * (1 - t) + c2[2] * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b))


def draw_shapes(draw: ImageDraw.ImageDraw, theme: str, accent: tuple, size: int):
    """Dibuja elementos geométricos temáticos."""
    s = size

    if theme == "playa":
        # Olas
        for i in range(3):
            y = s * 0.55 + i * 22
            draw.arc([0, y, s, y + 60], 0, 180, fill=(*accent, 160), width=4)
        # Sol
        draw.ellipse([s*0.65, s*0.08, s*0.88, s*0.31], fill=accent, outline=None)

    elif theme == "selva":
        # Árboles triangulares
        for x_off in [0.12, 0.38, 0.62, 0.85]:
            bx = int(s * x_off)
            draw.polygon([(bx, s*0.7), (bx-30, s*0.95), (bx+30, s*0.95)], fill=accent)
            draw.polygon([(bx, s*0.5), (bx-22, s*0.72), (bx+22, s*0.72)], fill=accent)

    elif theme == "ciudad":
        # Silueta urbana
        edificios = [(0.05, 0.40), (0.18, 0.25), (0.30, 0.45), (0.42, 0.30),
                     (0.54, 0.35), (0.66, 0.22), (0.78, 0.42), (0.90, 0.28)]
        for x_frac, h_frac in edificios:
            bx = int(s * x_frac)
            by = int(s * h_frac)
            bw = int(s * 0.10)
            draw.rectangle([bx, by, bx + bw, s], fill=accent)
            # Ventanas
            for wy in range(by + 8, s - 20, 20):
                draw.rectangle([bx+4, wy, bx+10, wy+12], fill=(255, 255, 200, 200))

    elif theme == "desierto":
        # Dunas
        for i, (x_frac, h_frac) in enumerate([(0.0, 0.62), (0.3, 0.54), (0.6, 0.60)]):
            cx = int(s * x_frac)
            cy = int(s * h_frac)
            draw.ellipse([cx - 120, cy, cx + 160, cy + 100], fill=accent)
        # Cactus simple
        draw.rectangle([s*0.78, s*0.42, s*0.82, s*0.75], fill=(60, 110, 40))
        draw.rectangle([s*0.68, s*0.50, s*0.82, s*0.55], fill=(60, 110, 40))

    elif theme == "colonial":
        # Arco y fachada
        w = int(s * 0.5)
        ox = int(s * 0.25)
        draw.rectangle([ox, int(s*0.35), ox+w, int(s*0.90)], fill=accent)
        draw.arc([ox, int(s*0.20), ox+w, int(s*0.60)], 180, 360, fill=accent, width=20)
        # Ventanas
        for xi in [ox+20, ox+w-45]:
            draw.rectangle([xi, int(s*0.50), xi+25, int(s*0.70)], fill=(200, 220, 255))

    elif theme == "montaña":
        # Montañas escalonadas
        peaks = [(0.1, 0.25), (0.35, 0.08), (0.6, 0.20), (0.85, 0.12)]
        for px, py in peaks:
            bx, by = int(s*px), int(s*py)
            draw.polygon([(bx, by), (bx-70, s), (bx+70, s)], fill=accent)
        # Nieve en cima
        for px, py in peaks[1:2]:
            bx, by = int(s*px), int(s*py)
            draw.polygon([(bx, by), (bx-25, by+35), (bx+25, by+35)], fill=(230, 240, 255))

    elif theme == "pacifico":
        # Ondas y ballena simple
        for i in range(4):
            y = s * 0.50 + i * 20
            draw.arc([-30, y, s+30, y + 80], 0, 180, fill=(*accent, 180), width=5)
        draw.ellipse([int(s*0.2), int(s*0.3), int(s*0.7), int(s*0.55)], fill=accent)

    elif theme == "caribeno":
        # Agua turquesa + sol + palmera
        draw.arc([0, int(s*0.55), s, int(s*0.85)], 0, 180, fill=accent, width=6)
        draw.ellipse([int(s*0.70), int(s*0.06), int(s*0.92), int(s*0.28)], fill=accent)
        # Palmera
        draw.rectangle([int(s*0.15), int(s*0.30), int(s*0.20), int(s*0.85)],
                       fill=(120, 80, 20))
        for angle, length in [(-0.4, 70), (0, 80), (0.5, 65)]:
            ex = int(s*0.175 + math.cos(math.pi/2 + angle) * length)
            ey = int(s*0.30 + math.sin(math.pi/2 + angle) * (-length))
            draw.line([(int(s*0.175), int(s*0.32)), (ex, ey)],
                      fill=(40, 130, 40), width=6)

    elif theme == "cafetero":
        # Montañas onduladas y planta de café
        draw.polygon([(0, int(s*0.55)), (int(s*0.25), int(s*0.28)),
                      (int(s*0.50), int(s*0.45)), (int(s*0.75), int(s*0.20)),
                      (s, int(s*0.40)), (s, s), (0, s)], fill=accent)
        # Granos de café
        for cx, cy in [(s*0.30, s*0.20), (s*0.55, s*0.14), (s*0.70, s*0.30)]:
            draw.ellipse([cx-10, cy-6, cx+10, cy+6], fill=(80, 30, 10))

    elif theme == "llanura":
        # Horizonte plano, aves
        draw.rectangle([0, int(s*0.60), s, s], fill=accent)
        draw.ellipse([int(s*0.4), int(s*0.25), int(s*0.7), int(s*0.50)],
                     fill=(200, 180, 60))
        for bx in [s*0.15, s*0.55, s*0.78]:
            draw.arc([bx, s*0.18, bx+24, s*0.27], 180, 360, fill=(60, 60, 80), width=3)


def wrap_text(text: str, max_chars: int = 22) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        if len(current) + len(word) + 1 <= max_chars:
            current = (current + " " + word).strip()
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines[:3]


def make_image(doc_id: str, titulo: str, categoria: str) -> str:
    theme = detect_theme(titulo)
    c1, c2, accent = PALETTES[theme]

    img = Image.new("RGB", (SIZE, SIZE))
    draw = ImageDraw.ImageDraw(img)

    gradient_bg(draw, c1, c2, SIZE)
    draw_shapes(draw, theme, accent, SIZE)

    # Banda inferior semi-opaca para texto
    overlay = Image.new("RGBA", (SIZE, 90), (0, 0, 0, 140))
    img.paste(overlay, (0, SIZE - 90), overlay)

    draw2 = ImageDraw.ImageDraw(img)
    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 16)
        font_sub   = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except Exception:
        font_title = ImageFont.load_default()
        font_sub   = font_title

    lines = wrap_text(titulo, 24)
    y_text = SIZE - 85
    for line in lines:
        draw2.text((12, y_text), line, fill=(255, 255, 255), font=font_title)
        y_text += 20

    draw2.text((12, SIZE - 18), f"{doc_id} · {categoria}", fill=(200, 200, 200), font=font_sub)

    out_dir = os.path.join(IMG_DIR, categoria)
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{doc_id}.png")
    img.save(path, "PNG")
    return path


def main():
    with open(DOCS_JSON) as f:
        docs = json.load(f)

    # Selección: destinos (20), paquetes (20), itinerarios (14)
    selected_cats = {"destinos", "paquetes", "itinerarios"}
    targets = [d for d in docs if d["categoria"] in selected_cats]
    # Para itinerarios tomamos los primeros 14
    iti_count = 0
    final = []
    for d in targets:
        if d["categoria"] == "itinerarios":
            if iti_count >= 14:
                continue
            iti_count += 1
        final.append(d)

    print(f"Generando {len(final)} imágenes...")
    generated = []
    for d in final:
        path = make_image(d["doc_id"], d["titulo"], d["categoria"])
        generated.append({"doc_id": d["doc_id"], "path": path, "categoria": d["categoria"]})
        print(f"  ✓ {d['doc_id']:12s}  {os.path.basename(path)}")

    print(f"\nTotal: {len(generated)} imágenes en {IMG_DIR}")
    return generated


if __name__ == "__main__":
    main()
