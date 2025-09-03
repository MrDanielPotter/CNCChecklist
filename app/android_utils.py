import os, time, logging
from typing import Optional
from kivy.utils import platform

logger = logging.getLogger(__name__)

# SAF & camera
if platform == "android":
    from android.permissions import request_permissions, Permission, check_permission
    from jnius import autoclass, cast
    from androidstorage4kivy import SharedStorage, Chooser
    from plyer import camera
else:
    request_permissions = None
    Permission = None
    SharedStorage = None
    Chooser = None
    camera = None

def ensure_permissions():
    if platform != "android": 
        logger.info("Платформа не Android, разрешения не требуются")
        return True
    logger.info("Запрос разрешений для Android")
    perms = [Permission.CAMERA, "android.permission.READ_MEDIA_IMAGES", "android.permission.READ_MEDIA_VISUAL_USER_SELECTED"]
    request_permissions(perms)
    logger.info("Разрешения запрошены")
    return True

def take_photo_to(path:str)->Optional[str]:
    logger.info(f"Попытка сделать фото и сохранить в: {path}")
    if platform != "android":
        logger.info("Платформа не Android, фото не доступно")
        return None
    try:
        camera.take_picture(filename=path, on_complete=lambda p: None)
        logger.info("Команда на съемку фото отправлена")
        # простая задержка; в реальном проекте лучше колбек
        t0 = time.time()
        while not os.path.exists(path) and time.time()-t0 < 20: 
            time.sleep(0.2)
        if os.path.exists(path):
            logger.info(f"Фото успешно сохранено: {path}")
            return path
        else:
            logger.warning("Фото не было создано в течение 20 секунд")
            return None
    except Exception as e:
        logger.error(f"Ошибка при съемке фото: {e}")
        return None

def choose_saf_folder()->Optional[str]:
    logger.info("Выбор папки через SAF")
    if platform != "android": 
        logger.info("Платформа не Android, SAF недоступен")
        return None
    try:
        chooser = Chooser(mime_type="vnd.android.document/directory", select_type=Chooser.DIRECTORY)
        uri = chooser.choose_dir()
        if uri:
            logger.info(f"Папка выбрана: {uri}")
        else:
            logger.info("Выбор папки отменен пользователем")
        return uri
    except Exception as e:
        logger.error(f"Ошибка при выборе папки: {e}")
        return None

def create_saf_file(tree_uri:str, name:str, mime:str="application/pdf")->Optional[str]:
    logger.info(f"Создание файла через SAF: {name}")
    if platform != "android": 
        logger.info("Платформа не Android, SAF недоступен")
        return None
    try:
        ss = SharedStorage()
        uri = ss.create_file(name=name, parent_document_tree=tree_uri, mime_type=mime)
        logger.info(f"Файл создан: {uri}")
        return uri
    except Exception as e:
        logger.error(f"Ошибка при создании файла через SAF: {e}")
        return None

def write_bytes_to_saf(uri:str, data:bytes):
    logger.info(f"Запись данных в SAF файл: {uri}")
    if platform != "android": 
        logger.info("Платформа не Android, SAF недоступен")
        return False
    try:
        ss = SharedStorage()
        with ss.open_document(uri, "w") as f:
            f.write(data)
        logger.info(f"Данные успешно записаны в файл: {uri}")
        return True
    except Exception as e:
        logger.error(f"Ошибка при записи данных в SAF файл: {e}")
        return False
