# 🔧 Инструменты диагностики и отладки CNC Checklist

Этот набор инструментов поможет вам быстро диагностировать и исправить ошибки в процессе сборки Android APK.

## 🚀 Быстрый старт

### 1. Автоматическое исправление
```bash
# Запустить все автоматические исправления
python auto_fix.py

# Или через Makefile
make quick-fix
```

### 2. Диагностика окружения
```bash
# Полная диагностика
make debug

# Или напрямую
./debug_build.sh
```

### 3. Локальное тестирование
```bash
# Тестирование конфигурации
make test

# Или напрямую
./test_build_locally.sh
```

## 📋 Доступные инструменты

### 🔍 Диагностические инструменты

| Инструмент | Описание | Команда |
|------------|----------|---------|
| `debug_build.sh` | Полная диагностика окружения | `./debug_build.sh` |
| `test_build_locally.sh` | Локальное тестирование | `./test_build_locally.sh` |
| `auto_fix.py` | Автоматические исправления | `python auto_fix.py` |

### 📊 Анализ и мониторинг

| Инструмент | Описание | Команда |
|------------|----------|---------|
| `analyze_errors.py` | Анализ логов на ошибки | `python analyze_errors.py logs/buildozer_build.log` |
| `monitor_github_actions.py` | Мониторинг GitHub Actions | `python monitor_github_actions.py status` |

### 🛠️ Утилиты

| Инструмент | Описание | Команда |
|------------|----------|---------|
| `Makefile` | Удобные команды | `make help` |
| `DEBUGGING_GUIDE.md` | Подробное руководство | Читать документацию |

## 🎯 Типичные сценарии использования

### Сценарий 1: Первая настройка
```bash
# 1. Автоматические исправления
python auto_fix.py

# 2. Проверка окружения
make debug

# 3. Локальное тестирование
make test
```

### Сценарий 2: Ошибка в GitHub Actions
```bash
# 1. Мониторинг статуса
make monitor

# 2. Скачивание логов (если есть RUN_ID)
make download-logs RUN_ID=123456789

# 3. Анализ ошибок
make analyze LOG_FILE=logs/run_123456789_logs.txt
```

### Сценарий 3: Локальная сборка
```bash
# 1. Проверка конфигурации
make validate-config

# 2. Проверка SDK
make check-sdk
make check-ndk

# 3. Сборка
make build-local
```

### Сценарий 4: Полная диагностика
```bash
# 1. Полная проверка
make full-check

# 2. Очистка и пересборка
make clean
make build-local
```

## 🔧 Команды Makefile

### Основные команды
```bash
make help              # Показать справку
make debug             # Диагностика окружения
make test              # Локальное тестирование
make clean             # Очистка временных файлов
make quick-fix         # Быстрые исправления
```

### Анализ и мониторинг
```bash
make monitor           # Статус GitHub Actions
make monitor-live      # Живой мониторинг
make analyze LOG_FILE=logs/buildozer_build.log  # Анализ логов
make download-logs RUN_ID=123456789             # Скачивание логов
```

### Проверки
```bash
make validate-config   # Проверка buildozer.spec
make check-sdk         # Проверка Android SDK
make check-ndk         # Проверка Android NDK
make full-check        # Полная проверка
```

### Сборка
```bash
make build-local       # Локальная сборка APK
make install-deps      # Установка зависимостей
```

## 🚨 Типичные ошибки и решения

### 1. SDK Installation Errors
```
❌ build-tools folder not found
❌ Aidl not found
❌ platform android-33 not found
```
**Решение:** `make check-sdk` → проверить ANDROID_HOME

### 2. License Errors
```
❌ Skipping following packages as the license is not accepted
```
**Решение:** `echo 'y' | sdkmanager --licenses`

### 3. Path Configuration
```
❌ sdkmanager path does not exist
```
**Решение:** Создать символические ссылки

### 4. Dependency Conflicts
```
❌ Conflict detected: 'kivy' inducing dependencies ('sdl2',), and 'webview'
```
**Решение:** Использовать `p4a.bootstrap = sdl2`

### 5. Compilation Errors
```
❌ LT_SYS_SYMBOL_USCORE: possibly undefined macro
❌ autoreconf: error: /usr/bin/autoconf failed
```
**Решение:** `export LT_SYS_SYMBOL_USCORE=no` + blacklist libffi

## 📊 Анализ логов

### Автоматический анализ
```bash
# Анализ лога с предложениями по исправлению
python analyze_errors.py logs/buildozer_build.log
```

### Ручной поиск
```bash
# Поиск ошибок SDK
grep -i "build-tools\|aidl\|platform" logs/buildozer_build.log

# Поиск ошибок лицензий
grep -i "license" logs/buildozer_build.log

# Поиск ошибок компиляции
grep -i "error\|failed" logs/buildozer_build.log
```

## 🔍 Мониторинг GitHub Actions

### Статус последних запусков
```bash
make monitor
```

### Живой мониторинг
```bash
make monitor-live
```

### Скачивание логов
```bash
# Нужен GITHUB_TOKEN и RUN_ID
export GITHUB_TOKEN=your_token_here
make download-logs RUN_ID=123456789
```

## 🛠️ Настройка окружения

### Переменные окружения
```bash
export ANDROID_HOME=/path/to/android-sdk
export ANDROID_NDK_HOME=/path/to/android-ndk
export ANDROID_SDK_ROOT=$ANDROID_HOME
export GITHUB_TOKEN=your_token_here
export GITHUB_REPOSITORY=owner/repo
```

### Установка зависимостей
```bash
# Python зависимости
pip install buildozer kivy requests

# Системные зависимости (Ubuntu/Debian)
sudo apt-get install -y autoconf automake libtool libtool-bin pkg-config
```

## 📝 Создание отчетов

### Структура отчета об ошибке
```
## Описание ошибки
- Что произошло
- Когда произошло
- Ожидаемое поведение

## Логи и диагностика
- Вывод make debug
- Релевантные части логов
- Результат python analyze_errors.py

## Предпринятые действия
- Что уже пробовали
- Какие исправления применили
- Результат каждого действия

## Окружение
- OS и версия
- Python версия
- Buildozer версия
- Android SDK версии
```

## 🎯 Стратегия отладки

### 1. Автоматические исправления
```bash
python auto_fix.py
```

### 2. Диагностика
```bash
make debug
```

### 3. Локальное тестирование
```bash
make test
```

### 4. Анализ логов
```bash
python analyze_errors.py logs/buildozer_build.log
```

### 5. Итеративные исправления
- Применить исправления по одному
- Тестировать после каждого изменения
- Документировать успешные решения

## 📞 Получение помощи

### 1. Проверить существующие issues
- GitHub Issues в репозитории
- python-for-android issues
- buildozer issues

### 2. Создать новый issue
- Использовать шаблон отчета об ошибке
- Приложить логи и диагностику
- Указать версии всех компонентов

### 3. Сообщество
- python-for-android Discord
- Kivy Discord
- Stack Overflow с тегами kivy, buildozer, python-for-android

## 🔗 Полезные ссылки

- [python-for-android Documentation](https://python-for-android.readthedocs.io/)
- [Buildozer Documentation](https://buildozer.readthedocs.io/)
- [Kivy Documentation](https://kivy.org/doc/stable/)
- [Android SDK Documentation](https://developer.android.com/studio/command-line)

---

**💡 Совет:** Начните с `python auto_fix.py` для автоматического исправления большинства типичных проблем!
