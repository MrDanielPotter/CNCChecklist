import json, hashlib, time, os
from typing import Any, Dict, Optional
from kivy.app import App

def _p(path:str)->str:
    app = App.get_running_app()
    os.makedirs(app.user_data_dir, exist_ok=True)
    return os.path.join(app.user_data_dir, path)

def sha(text:str)->str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()

def load_json(name:str, default:Any)->Any:
    p = _p(name)
    if not os.path.exists(p): return default
    try:
        with open(p,"r",encoding="utf-8") as f: return json.load(f)
    except Exception: return default

def save_json(name:str, data:Any)->None:
    tmp = _p(name+".tmp")
    with open(tmp,"w",encoding="utf-8") as f: json.dump(data,f,ensure_ascii=False,indent=2)
    os.replace(tmp,_p(name))

def now_ts()->float: return time.time()
