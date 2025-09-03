#!/bin/bash
# Диагностический скрипт для отладки сборки Android APK

set -euo pipefail

echo "=== CNC Checklist Build Diagnostics ==="
echo "Timestamp: $(date -u +'%Y-%m-%d %H:%M:%S UTC')"
echo ""

# 1. Проверка окружения
echo "=== Environment Check ==="
echo "OS: $(uname -a)"
echo "Python: $(python --version 2>&1)"
echo "Java: $(java -version 2>&1 | head -1)"
echo "Buildozer: $(buildozer --version 2>&1 || echo 'Not installed')"
echo ""

# 2. Проверка Android SDK
echo "=== Android SDK Check ==="
if [ -n "${ANDROID_HOME:-}" ]; then
    echo "ANDROID_HOME: $ANDROID_HOME"
    if [ -d "$ANDROID_HOME" ]; then
        echo "✅ ANDROID_HOME directory exists"
        echo "SDK contents:"
        ls -la "$ANDROID_HOME" | head -10
    else
        echo "❌ ANDROID_HOME directory not found"
    fi
else
    echo "❌ ANDROID_HOME not set"
fi

if [ -n "${ANDROID_NDK_HOME:-}" ]; then
    echo "ANDROID_NDK_HOME: $ANDROID_NDK_HOME"
    if [ -d "$ANDROID_NDK_HOME" ]; then
        echo "✅ ANDROID_NDK_HOME directory exists"
    else
        echo "❌ ANDROID_NDK_HOME directory not found"
    fi
else
    echo "❌ ANDROID_NDK_HOME not set"
fi
echo ""

# 3. Проверка buildozer.spec
echo "=== Buildozer Configuration ==="
if [ -f "buildozer.spec" ]; then
    echo "✅ buildozer.spec found"
    echo "Key settings:"
    grep -E "^(android\.|p4a\.)" buildozer.spec | head -10
else
    echo "❌ buildozer.spec not found"
fi
echo ""

# 4. Проверка зависимостей
echo "=== Dependencies Check ==="
echo "Python packages:"
pip list | grep -E "(kivy|buildozer|python-for-android)" || echo "No relevant packages found"
echo ""

# 5. Проверка доступных платформ
echo "=== Available Android Platforms ==="
if [ -n "${ANDROID_HOME:-}" ] && [ -d "$ANDROID_HOME/platforms" ]; then
    echo "Available platforms:"
    ls -la "$ANDROID_HOME/platforms" || echo "No platforms found"
else
    echo "❌ Cannot check platforms - ANDROID_HOME not set or platforms directory missing"
fi
echo ""

# 6. Проверка build-tools
echo "=== Build Tools Check ==="
if [ -n "${ANDROID_HOME:-}" ] && [ -d "$ANDROID_HOME/build-tools" ]; then
    echo "Available build-tools:"
    ls -la "$ANDROID_HOME/build-tools" || echo "No build-tools found"
else
    echo "❌ Cannot check build-tools - ANDROID_HOME not set or build-tools directory missing"
fi
echo ""

# 7. Проверка NDK
echo "=== NDK Check ==="
if [ -n "${ANDROID_NDK_HOME:-}" ] && [ -d "$ANDROID_NDK_HOME" ]; then
    echo "NDK version:"
    if [ -f "$ANDROID_NDK_HOME/source.properties" ]; then
        grep "Pkg.Revision" "$ANDROID_NDK_HOME/source.properties" || echo "Version not found"
    else
        echo "source.properties not found"
    fi
else
    echo "❌ Cannot check NDK - ANDROID_NDK_HOME not set or directory missing"
fi
echo ""

# 8. Проверка переменных окружения
echo "=== Environment Variables ==="
echo "P4A_* variables:"
env | grep "^P4A_" | sort || echo "No P4A_ variables found"
echo ""
echo "ANDROID_* variables:"
env | grep "^ANDROID_" | sort || echo "No ANDROID_ variables found"
echo ""

# 9. Проверка доступного места на диске
echo "=== Disk Space ==="
df -h . || echo "Cannot check disk space"
echo ""

# 10. Проверка памяти
echo "=== Memory ==="
free -h || echo "Cannot check memory"
echo ""

echo "=== Diagnostics Complete ==="
