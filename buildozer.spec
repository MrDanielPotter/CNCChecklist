[app]
title = CNC Checklist
package.name = cncchecklist
package.domain = com.cnc.checklist

# исходники
source.dir = .
source.include_exts = py,kv,jpg,png,ttf

# версия приложения
version = 1.3

# ориентация
orientation = landscape
fullscreen = 0

# зависимости (python-for-android)
requirements = python3,kivy==2.3.0,pillow,reportlab,androidstorage4kivy,plyer,openssl

# исключаем проблемные рецепты
android.recipe_blacklist = libffi

# используем sdl2 bootstrap для Kivy
p4a.bootstrap = sdl2

# разрешения Android 13+
android.permissions = INTERNET, CAMERA, READ_MEDIA_IMAGES, READ_MEDIA_VISUAL_USER_SELECTED

# целевая/минимальная платформа
android.api = 32
android.minapi = 32
android.archs = arm64-v8a

# опционально: логи Kivy
# android.logcat_filters = *:S python:D

[buildozer]
# Пути берём из переменных окружения CI
android.sdk_dir = %(ANDROID_HOME)s
android.ndk_dir = %(ANDROID_NDK_HOME)s
log_level = 2
bin_dir = bin

[android]
# ускорение и стабильность сборки
accept_sdk_license = True
p4a.branch = master
# Стабильные версии Android SDK
android.platform = android-12
android.build_tools = 34.0.0
android.ndk = 25.2.9519653
