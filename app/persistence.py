import json, hashlib, time, os, logging
from typing import Any, Dict, Optional
from kivy.app import App

logger = logging.getLogger(__name__)

def _p(path:str)->str:
    app = App.get_running_app()
    os.makedirs(app.user_data_dir, exist_ok=True)
    return os.path.join(app.user_data_dir, path)

def sha(text:str)->str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_json(name:str, default:Any)->Any:
    p = _p(name)
    logger.debug(f"Попытка загрузить JSON файл: {name}")
    if not os.path.exists(p): 
        logger.debug(f"Файл {name} не найден, возвращаем значение по умолчанию")
        return default
    try:
        with open(p,"r",encoding="utf-8") as f: 
            data = json.load(f)
            logger.debug(f"Файл {name} успешно загружен")
            return data
    except Exception as e: 
        logger.error(f"Ошибка при загрузке файла {name}: {e}")
        return default

def save_json(name:str, data:Any)->None:
    logger.debug(f"Сохранение JSON файла: {name}")
    try:
        tmp = _p(name+".tmp")
        with open(tmp,"w",encoding="utf-8") as f: 
            json.dump(data,f,ensure_ascii=False,indent=2)
        os.replace(tmp,_p(name))
        logger.debug(f"Файл {name} успешно сохранен")
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла {name}: {e}")
        raise

def now_ts()->float: return time.time()
