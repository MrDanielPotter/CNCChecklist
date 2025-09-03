import io, os, logging
from datetime import datetime
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

logger = logging.getLogger(__name__)

FONT_NAME = "DejaVuSans"
FONT_PATH = os.path.join(os.path.dirname(__file__), "assets", "fonts", "DejaVuSans.ttf")

def ensure_font():
    logger.info("Проверка наличия шрифта")
    if not os.path.exists(FONT_PATH):
        logger.error(f"Шрифт не найден: {FONT_PATH}")
        raise RuntimeError("Шрифт DejaVuSans.ttf не найден. Его скачает GitHub Actions, либо положите вручную в app/assets/fonts/")
    if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
        logger.info("Регистрация шрифта")
        pdfmetrics.registerFont(TTFont(FONT_NAME, FONT_PATH))
        logger.info("Шрифт зарегистрирован")
    else:
        logger.info("Шрифт уже зарегистрирован")

def _draw_text(c, x, y, text, size=10):
    c.setFont(FONT_NAME, size)
    c.drawString(x, y, text)

def shrink_image_to_jpeg_bytes(path:str, max_px:int=1600, quality:int=80)->bytes:
    logger.info(f"Обработка изображения: {path}")
    try:
        im = Image.open(path).convert("RGB")
        original_size = im.size
        im.thumbnail((max_px,max_px))
        new_size = im.size
        logger.info(f"Изображение изменено с {original_size} на {new_size}")
        
        bio = io.BytesIO()
        im.save(bio, format="JPEG", quality=quality, optimize=True)
        result_size = len(bio.getvalue())
        logger.info(f"Изображение сжато до {result_size} байт")
        return bio.getvalue()
    except Exception as e:
        logger.error(f"Ошибка при обработке изображения {path}: {e}")
        raise

def generate_pdf(report, out_path:str):
    logger.info(f"Генерация PDF отчета: {out_path}")
    logger.info(f"Заказ: {report['order']}")
    
    try:
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
        logger.info("Шапка отчета создана")

        # Таблица (простая разметка)
        _draw_text(c, m, y, "Пункты:", 12); y -= 6*mm
        logger.info("Начало создания таблицы пунктов")
        
        for b in report["blocks"]:
            logger.info(f"Обработка блока: {b['title']}")
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
                    logger.info("Новая страница PDF")
                    c.showPage(); y = H - m; ensure_font()

        # Фото блоком в конце
        logger.info("Обработка фотографий")
        for b in report["blocks"]:
            photos = []
            for it in b["items"]:
                photos += it.get("photos", [])
            if photos:
                logger.info(f"Добавление {len(photos)} фотографий для блока: {b['title']}")
                c.showPage(); y = H - m; ensure_font()
                _draw_text(c, m, y, f"Фото – {b['title']}", 12); y -= 10*mm
                for p in photos:
                    logger.info(f"Добавление фото: {p}")
                    img_bytes = shrink_image_to_jpeg_bytes(p)
                    bio = io.BytesIO(img_bytes)
                    iw, ih = Image.open(io.BytesIO(img_bytes)).size
                    ratio = (A4[0]-2*m)/iw
                    pw, ph = iw*ratio, ih*ratio
                    if y - ph < m: 
                        logger.info("Новая страница для фото")
                        c.showPage(); y = H - m; ensure_font()
                    c.drawImage(bio, m, y-ph, width=pw, height=ph)
                    y -= (ph + 8*mm)
        c.showPage()
        c.save()
        logger.info(f"PDF отчет успешно создан: {out_path}")
    except Exception as e:
        logger.error(f"Ошибка при создании PDF отчета: {e}")
        raise
