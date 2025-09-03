import os, time
from typing import Optional
from kivy.utils import platform

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
    if platform != "android": return True
    perms = [Permission.CAMERA, "android.permission.READ_MEDIA_IMAGES", "android.permission.READ_MEDIA_VISUAL_USER_SELECTED"]
    request_permissions(perms)
    return True

def take_photo_to(path:str)->Optional[str]:
    if platform != "android":
        # dev stub: copy placeholder if exists
        return None
    camera.take_picture(filename=path, on_complete=lambda p: None)
    # простая задержка; в реальном проекте лучше колбек
    t0 = time.time()
    while not os.path.exists(path) and time.time()-t0 < 20: time.sleep(0.2)
    return path if os.path.exists(path) else None

def choose_saf_folder()->Optional[str]:
    if platform != "android": return None
    chooser = Chooser(mime_type="vnd.android.document/directory", select_type=Chooser.DIRECTORY)
    uri = chooser.choose_dir()
    return uri

def create_saf_file(tree_uri:str, name:str, mime:str="application/pdf")->Optional[str]:
    if platform != "android": return None
    ss = SharedStorage()
    uri = ss.create_file(name=name, parent_document_tree=tree_uri, mime_type=mime)
    return uri

def write_bytes_to_saf(uri:str, data:bytes):
    if platform != "android": return False
    ss = SharedStorage()
    with ss.open_document(uri, "w") as f:
        f.write(data)
    return True
