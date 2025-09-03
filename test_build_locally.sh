#!/bin/bash
# Скрипт для локального тестирования сборки (имитация GitHub Actions)

set -euo pipefail

echo "=== Local Build Test (GitHub Actions Simulation) ==="
echo "This script simulates the GitHub Actions environment locally"
echo ""

# Установка переменных окружения как в GitHub Actions
export ANDROID_HOME="$PWD/android-sdk"
export ANDROID_SDK_ROOT="$PWD/android-sdk"
export ANDROID_NDK_HOME="$PWD/android-ndk"
export PIP_DISABLE_PIP_VERSION_CHECK=1
export P4A_DEBUG="1"
export ANDROID_PLATFORM="android-12"
export ANDROID_BUILD_TOOLS="34.0.0"
export ANDROID_NDK_VERSION="25.2.9519653"
export ANDROIDAPI="32"
export ANDROIDMINAPI="32"
export LIBFFI_CFLAGS="-I/usr/include/arm-linux-gnueabihf"
export LIBFFI_LIBS="-lffi"
export AUTOCONF_VERSION="2.71"
export AUTOMAKE_VERSION="1.16"
export LT_SYS_SYMBOL_USCORE="no"
export P4A_USE_SYSTEM_LIBFFI="1"
export P4A_LIBFFI_SKIP="1"
export P4A_RECIPE_BLACKLIST="libffi"
export P4A_BOOTSTRAP="sdl2"
export P4A_BRANCH="develop"

echo "Environment variables set:"
echo "ANDROID_HOME: $ANDROID_HOME"
echo "ANDROID_NDK_HOME: $ANDROID_NDK_HOME"
echo "P4A_BOOTSTRAP: $P4A_BOOTSTRAP"
echo "P4A_BRANCH: $P4A_BRANCH"
echo ""

# Создание директории для логов
mkdir -p logs

# Запуск диагностики
echo "Running diagnostics..."
./debug_build.sh > logs/local_diagnostics.log 2>&1
echo "Diagnostics saved to logs/local_diagnostics.log"
echo ""

# Проверка buildozer.spec
echo "=== Buildozer.spec Validation ==="
if [ -f "buildozer.spec" ]; then
    echo "✅ buildozer.spec found"
    
    # Проверка ключевых настроек
    echo "Key settings:"
    grep -E "^(android\.|p4a\.)" buildozer.spec | while read line; do
        echo "  $line"
    done
else
    echo "❌ buildozer.spec not found"
    exit 1
fi
echo ""

# Попытка сборки (только проверка конфигурации)
echo "=== Buildozer Configuration Check ==="
if command -v buildozer >/dev/null 2>&1; then
    echo "Testing buildozer configuration..."
    if buildozer android debug --verbose 2>&1 | tee logs/local_build_test.log; then
        echo "✅ Buildozer configuration test passed"
    else
        echo "❌ Buildozer configuration test failed"
        echo "Check logs/local_build_test.log for details"
    fi
else
    echo "❌ Buildozer not installed"
    echo "Install with: pip install buildozer"
fi
echo ""

# Проверка зависимостей Python
echo "=== Python Dependencies Check ==="
echo "Checking required packages..."
python -c "
import sys
required_packages = ['kivy', 'buildozer']
missing_packages = []

for package in required_packages:
    try:
        __import__(package)
        print(f'✅ {package} is available')
    except ImportError:
        print(f'❌ {package} is missing')
        missing_packages.append(package)

if missing_packages:
    print(f'\\nMissing packages: {missing_packages}')
    print('Install with: pip install ' + ' '.join(missing_packages))
    sys.exit(1)
else:
    print('\\n✅ All required packages are available')
"
echo ""

echo "=== Local Test Complete ==="
echo "Check logs/ directory for detailed output"
echo "Files created:"
ls -la logs/ || echo "No logs directory found"
