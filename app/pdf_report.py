import io, os
from datetime import datetime
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

FONT_NAME = "DejaVuSans"
FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "DejaVuSans.ttf")

def ensure_font():
    if not os.path.exists(FONT_PATH):
        raise RuntimeError("Шрифт DejaVuSans.ttf не найден. Его скачает GitHub Actions, либо положите вручную в app/assets/fonts/")
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))

def _draw_text(c, x, y, text, size=10):
    c.setFont(FONT_NAME, size)
    c.drawString(x, y, text)

def shrink_image_to_jpeg_bytes(path:str, max_px:int=1600, quality:int=80)->bytes:
    im = Image.open(path).convert("RGB")
    im.thumbnail((max_px,max_px))
    bio = io.BytesIO()
    im.save(bio, format="JPEG", quality=quality, optimize=True)
    return bio.getvalue()

def generate_pdf(report, out_path:str):
    ensure_font()
    c = canvas.Canvas(out_path, pagesize=A4)
    W, H = A4
    m = 12*mm
    y = H - m

    # Шапка
    c.setTitle(f"Отчёт CNC Checklist {report['order']}")
    _draw_text(c, m, y, f"Отчёт CNC Checklist – Нестинг", 14); y -= 8*mm
    _draw_text(c, m, y, f"Заказ: {report['order']}    Оператор: {report.get('operator','')}"); y -= 6*mm
    _draw_text(c, m, y, f"Дата начала: {report['started_at']}    Завершено: {report['completed_at']}"); y -= 6*mm
    _draw_text(c, m, y, f"Версия чек-листа: {report['version']}    Авто-№: {report['seq']}"); y -= 8*mm

    # Таблица (простая разметка)
    _draw_text(c, m, y, "Пункты:", 12); y -= 6*mm
    for b in report["blocks"]:
        _draw_text(c, m, y, b["title"], 11); y -= 5*mm
        for it in b["items"]:
            status = "✓" if it["status"] is True else ("✗" if it["status"] is False else "—")
            crit = " [КРИТ.]" if it["critical"] else ""
            line = f"{it['id']} {status}{crit}  {it['text']}"
            _draw_text(c, m+5*mm, y, line)
            y -= 5*mm
            _draw_text(c, m+10*mm, y, f"Нач: {it.get('started_at','')}  Оконч: {it.get('completed_at','')}  Длит: {it.get('duration_sec','')} сек.")
            y -= 5*mm
            if it.get("note"):
                _draw_text(c, m+10*mm, y, f"Заметка: {it['note']}")
                y -= 5*mm
            if it.get("bypassed_by_master"):
                _draw_text(c, m+10*mm, y, f"Обход критического: {it['bypassed_by_master']}")
                y -= 5*mm
            if y < 40*mm:
                c.showPage(); y = H - m; ensure_font()

    # Фото блоком в конце
    for b in report["blocks"]:
        photos = []
        for it in b["items"]:
            photos += it.get("photos", [])
        if photos:
            c.showPage(); y = H - m; ensure_font()
            _draw_text(c, m, y, f"Фото – {b['title']}", 12); y -= 10*mm
            for p in photos:
                img_bytes = shrink_image_to_jpeg_bytes(p)
                bio = io.BytesIO(img_bytes)
                iw, ih = Image.open(io.BytesIO(img_bytes)).size
                ratio = (A4[0]-2*m)/iw
                pw, ph = iw*ratio, ih*ratio
                if y - ph < m: c.showPage(); y = H - m; ensure_font()
                c.drawImage(bio, m, y-ph, width=pw, height=ph)
                y -= (ph + 8*mm)
    c.showPage()
    c.save()
