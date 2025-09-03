# Обновление GitHub Actions для CNC Checklist

## Обзор изменений

Файл `.github/workflows/android-release.yml` был обновлен для соответствия стабильным версиям Android SDK, указанным в `buildozer.spec`, и добавлены дополнительные улучшения для мониторинга и диагностики сборки.

## 1. Соответствие buildozer.spec

### Стабильные версии Android SDK
- **Android Platform**: `android-33` (API 33)
- **Build Tools**: `34.0.0`
- **NDK**: `25.2.9519653`

### Переменные окружения
```yaml
env:
  ANDROID_PLATFORM: "android-33"
  ANDROID_BUILD_TOOLS: "34.0.0"
  ANDROID_NDK_VERSION: "25.2.9519653"
```

## 2. Новые возможности

### Выбор типа сборки
- **Manual trigger** с выбором типа сборки (debug/release)
- **Автоматическая сборка** debug при push в main

### Расширенная валидация
- **Проверка buildozer.spec** на соответствие стабильным версиям
- **Валидация секций** конфигурации
- **Проверка версий** Android SDK

### Улучшенное логирование
- **Детальные логи** всех этапов сборки
- **Системная информация** (Java, Python, дисковое пространство)
- **Размеры APK файлов**
- **Статус сборки** в summary

## 3. Структура workflow

### Основные этапы:
1. **Подготовка окружения**
   - Установка Java 17 (Temurin)
   - Установка Python 3.10
   - Установка системных зависимостей

2. **Установка Android SDK**
   - Command line tools
   - Platform tools
   - Android Platform 33
   - Build Tools 34.0.0
   - NDK 25.2.9519653

3. **Установка зависимостей**
   - Buildozer 1.5.0
   - Python пакеты
   - Шрифт DejaVuSans.ttf

4. **Валидация конфигурации**
   - Проверка buildozer.spec
   - Соответствие версий SDK

5. **Сборка APK**
   - Debug или Release сборка
   - Детальное логирование
   - Проверка результата

6. **Артефакты**
   - APK/AAB файлы (30 дней)
   - Логи сборки (7 дней)

## 4. Улучшения мониторинга

### Детальное логирование
```bash
# Системная информация
echo "=== ENV ==="; printenv | sort
echo "=== Versions ==="
java -version 2>&1
python --version 2>&1

# Информация о сборке
echo "Build type: $BUILD_TYPE"
echo "Target Android API: $ANDROID_PLATFORM"
echo "Build tools: $ANDROID_BUILD_TOOLS"
echo "NDK version: $ANDROID_NDK_VERSION"
```

### Валидация buildozer.spec
```python
# Проверка версий Android SDK
assert android_api == '33'
assert android_platform == 'android-33'
assert build_tools == '34.0.0'
assert ndk_version == '25.2.9519653'
```

### Проверка результата сборки
```bash
# Проверяем результат сборки
if [ -f "bin/*.apk" ]; then
  echo "APK build: SUCCESS"
  ls -la bin/*.apk
else
  echo "APK build: FAILED"
  exit 1
fi
```

## 5. Артефакты

### APK/AAB файлы
- **Имя**: `cnc-checklist-v1.3-{build_type}-apk`
- **Содержимое**: APK и AAB файлы
- **Хранение**: 30 дней

### Логи сборки
- **Имя**: `cnc-checklist-v1.3-ci-logs`
- **Содержимое**: 
  - Логи workflow
  - Логи buildozer
  - Логи python-for-android
- **Хранение**: 7 дней

## 6. GitHub Summary

### Автоматический отчет
```markdown
## CNC Checklist v1.3 – CI Build Summary

**Build Type**: debug/release
**System**: Java 17, Python 3.10
**Android SDK**: Platform android-33, Build Tools 34.0.0, NDK 25.2.9519653
**SDK root**: /github/workspace/android-sdk

**Build Outputs**:
- cncchecklist-1.3-debug.apk (XX MB)

**Build Status**: success/failure
```

## 7. Использование

### Автоматическая сборка
```bash
# При push в main ветку
git push origin main
# Автоматически запускается debug сборка
```

### Ручная сборка
```bash
# Через GitHub Actions UI
# Actions → Build Android APK → Run workflow
# Выбор: debug или release
```

### Параметры workflow_dispatch
- **build_type**: debug (по умолчанию) или release
- **Описание**: Build type (debug/release)

## 8. Совместимость

### Требования
- **Ubuntu 24.04** (latest)
- **Java 17** (Temurin)
- **Python 3.10**
- **Android SDK** с указанными версиями

### Поддерживаемые архитектуры
- **arm64-v8a** (как указано в buildozer.spec)

## 9. Отладка

### При проблемах со сборкой
1. **Проверьте логи** в артефактах
2. **Убедитесь** в соответствии версий SDK
3. **Проверьте** buildozer.spec на ошибки
4. **Используйте** детальные логи для диагностики

### Частые проблемы
- **Недостаток места** на диске
- **Проблемы с лицензиями** Android SDK
- **Конфликты версий** зависимостей
- **Ошибки в buildozer.spec**

## 10. Безопасность

### Переменные окружения
- **ANDROID_HOME**: Путь к Android SDK
- **ANDROID_NDK_HOME**: Путь к Android NDK
- **P4A_DEBUG**: Включение отладки python-for-android

### Артефакты
- **APK файлы** подписываются debug ключом
- **Логи** не содержат чувствительных данных
- **Временные файлы** очищаются автоматически

## Заключение

Обновленный workflow обеспечивает:
- **Стабильную сборку** с проверенными версиями SDK
- **Детальную диагностику** проблем сборки
- **Гибкость** в выборе типа сборки
- **Надежность** через валидацию конфигурации
- **Удобство** через автоматические отчеты

Все изменения обратно совместимы и не требуют изменений в существующем коде проекта.
