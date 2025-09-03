# 🔍 Руководство по диагностике ошибок сборки

Это руководство поможет вам понять и исправить ошибки в процессе сборки Android APK.

## 📋 Быстрая диагностика

### 1. Запуск диагностического скрипта
```bash
# Сделать скрипт исполняемым
chmod +x debug_build.sh

# Запустить диагностику
./debug_build.sh
```

### 2. Локальное тестирование
```bash
# Сделать скрипт исполняемым
chmod +x test_build_locally.sh

# Запустить локальный тест
./test_build_locally.sh
```

### 3. Анализ логов GitHub Actions
```bash
# Скачать лог из GitHub Actions и проанализировать
python analyze_errors.py logs/buildozer_build.log
```

## 🚨 Типичные ошибки и решения

### 1. **SDK Installation Errors**
```
❌ build-tools folder not found
❌ Aidl not found
❌ platform android-33 not found
```

**Решение:**
- Проверить переменные `ANDROID_HOME`, `ANDROID_NDK_HOME`
- Убедиться, что SDK компоненты установлены
- Создать символические ссылки для buildozer

### 2. **License Acceptance Errors**
```
❌ Skipping following packages as the license is not accepted
```

**Решение:**
```bash
echo 'y' | sdkmanager --licenses
```

### 3. **Path Configuration Errors**
```
❌ sdkmanager path does not exist
```

**Решение:**
```bash
# Создать символические ссылки
ln -sf "$ANDROID_HOME/cmdline-tools/latest/bin/sdkmanager" "$ANDROID_HOME/tools/bin/sdkmanager"
```

### 4. **Dependency Conflicts**
```
❌ Conflict detected: 'kivy' inducing dependencies ('sdl2',), and 'webview'
```

**Решение:**
- Использовать `p4a.bootstrap = sdl2` вместо `webview`
- Проверить совместимость зависимостей

### 5. **Compilation Errors (libffi)**
```
❌ LT_SYS_SYMBOL_USCORE: possibly undefined macro
❌ autoreconf: error: /usr/bin/autoconf failed
```

**Решение:**
```bash
# Установить autotools
sudo apt-get install -y autoconf automake libtool libtool-bin

# Установить переменные окружения
export LT_SYS_SYMBOL_USCORE=no
export P4A_USE_SYSTEM_LIBFFI=1
export P4A_LIBFFI_SKIP=1
export P4A_RECIPE_BLACKLIST=libffi
```

### 6. **Configuration Errors**
```
❌ android.bootstrap is deprecated
❌ android.arch is deprecated
```

**Решение:**
- Заменить `android.bootstrap` на `p4a.bootstrap`
- Заменить `android.arch` на `android.archs`

## 🔧 Инструменты диагностики

### 1. **debug_build.sh**
- Проверяет окружение
- Анализирует Android SDK
- Проверяет конфигурацию buildozer
- Выводит системную информацию

### 2. **test_build_locally.sh**
- Имитирует GitHub Actions окружение
- Тестирует конфигурацию buildozer
- Проверяет зависимости Python

### 3. **analyze_errors.py**
- Анализирует логи на предмет известных ошибок
- Предлагает конкретные решения
- Классифицирует ошибки по типам

## 📊 Анализ логов GitHub Actions

### 1. **Скачивание логов**
```bash
# Скачать лог из GitHub Actions
gh run download <run-id>
```

### 2. **Анализ ошибок**
```bash
# Проанализировать лог
python analyze_errors.py logs/buildozer_build.log
```

### 3. **Поиск конкретных ошибок**
```bash
# Поиск ошибок SDK
grep -i "build-tools\|aidl\|platform" logs/buildozer_build.log

# Поиск ошибок лицензий
grep -i "license" logs/buildozer_build.log

# Поиск ошибок компиляции
grep -i "error\|failed" logs/buildozer_build.log
```

## 🎯 Стратегия отладки

### 1. **Первый уровень - Базовая диагностика**
- Запустить `debug_build.sh`
- Проверить переменные окружения
- Убедиться в наличии всех компонентов SDK

### 2. **Второй уровень - Локальное тестирование**
- Запустить `test_build_locally.sh`
- Протестировать конфигурацию buildozer
- Проверить зависимости Python

### 3. **Третий уровень - Анализ логов**
- Скачать логи из GitHub Actions
- Запустить `analyze_errors.py`
- Следовать предложенным решениям

### 4. **Четвертый уровень - Итеративное исправление**
- Применить исправления по одному
- Тестировать после каждого изменения
- Документировать успешные решения

## 📝 Создание отчетов об ошибках

### 1. **Структура отчета**
```
## Описание ошибки
- Что произошло
- Когда произошло
- Ожидаемое поведение

## Логи и диагностика
- Вывод debug_build.sh
- Релевантные части логов
- Результат analyze_errors.py

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

### 2. **Полезные команды для сбора информации**
```bash
# Системная информация
uname -a
python --version
java -version
buildozer --version

# Android SDK информация
echo $ANDROID_HOME
echo $ANDROID_NDK_HOME
ls -la $ANDROID_HOME
ls -la $ANDROID_NDK_HOME

# Конфигурация buildozer
grep -E "^(android\.|p4a\.)" buildozer.spec
```

## 🚀 Быстрые исправления

### 1. **Полная переустановка SDK**
```bash
rm -rf android-sdk android-ndk
# Запустить GitHub Actions заново
```

### 2. **Очистка buildozer кэша**
```bash
rm -rf .buildozer
buildozer android clean
```

### 3. **Сброс переменных окружения**
```bash
unset ANDROID_HOME ANDROID_NDK_HOME
# Перезапустить терминал
```

## 📞 Получение помощи

### 1. **Проверить существующие issues**
- GitHub Issues в репозитории
- python-for-android issues
- buildozer issues

### 2. **Создать новый issue**
- Использовать шаблон отчета об ошибке
- Приложить логи и диагностику
- Указать версии всех компонентов

### 3. **Сообщество**
- python-for-android Discord
- Kivy Discord
- Stack Overflow с тегами kivy, buildozer, python-for-android
