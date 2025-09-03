#!/usr/bin/env python3
"""
Автоматическое исправление типичных ошибок сборки
"""

import os
import sys
import subprocess
import shutil
from typing import List, Dict, Tuple
from pathlib import Path

class AutoFixer:
    def __init__(self):
        self.fixes_applied = []
        self.errors_found = []
    
    def log(self, message: str, level: str = "INFO"):
        """Логирование с цветами"""
        colors = {
            "INFO": "\033[0;34m",    # Blue
            "SUCCESS": "\033[0;32m", # Green
            "WARNING": "\033[1;33m", # Yellow
            "ERROR": "\033[0;31m",   # Red
            "RESET": "\033[0m"       # Reset
        }
        
        color = colors.get(level, colors["INFO"])
        reset = colors["RESET"]
        print(f"{color}[{level}]{reset} {message}")
    
    def run_command(self, command: str, check: bool = True) -> Tuple[bool, str]:
        """Выполнение команды с обработкой ошибок"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                capture_output=True, 
                text=True, 
                check=check
            )
            return True, result.stdout
        except subprocess.CalledProcessError as e:
            return False, e.stderr
    
    def check_android_sdk(self) -> bool:
        """Проверка Android SDK"""
        self.log("Проверка Android SDK...")
        
        android_home = os.getenv('ANDROID_HOME')
        if not android_home:
            self.log("ANDROID_HOME не установлен", "ERROR")
            return False
        
        if not os.path.exists(android_home):
            self.log(f"ANDROID_HOME директория не существует: {android_home}", "ERROR")
            return False
        
        self.log(f"✅ ANDROID_HOME: {android_home}", "SUCCESS")
        return True
    
    def check_android_ndk(self) -> bool:
        """Проверка Android NDK"""
        self.log("Проверка Android NDK...")
        
        ndk_home = os.getenv('ANDROID_NDK_HOME')
        if not ndk_home:
            self.log("ANDROID_NDK_HOME не установлен", "ERROR")
            return False
        
        if not os.path.exists(ndk_home):
            self.log(f"ANDROID_NDK_HOME директория не существует: {ndk_home}", "ERROR")
            return False
        
        self.log(f"✅ ANDROID_NDK_HOME: {ndk_home}", "SUCCESS")
        return True
    
    def fix_buildozer_spec(self) -> bool:
        """Исправление buildozer.spec"""
        self.log("Проверка buildozer.spec...")
        
        spec_file = Path("buildozer.spec")
        if not spec_file.exists():
            self.log("buildozer.spec не найден", "ERROR")
            return False
        
        # Читаем файл
        content = spec_file.read_text(encoding='utf-8')
        original_content = content
        
        # Исправления
        fixes = [
            # Замена deprecated android.bootstrap на p4a.bootstrap
            (r'android\.bootstrap\s*=', 'p4a.bootstrap ='),
            # Замена deprecated android.arch на android.archs
            (r'android\.arch\s*=', 'android.archs ='),
            # Убеждаемся, что используется sdl2 bootstrap
            (r'p4a\.bootstrap\s*=\s*webview', 'p4a.bootstrap = sdl2'),
        ]
        
        for pattern, replacement in fixes:
            import re
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                self.log(f"Исправлено: {pattern} -> {replacement}", "SUCCESS")
                self.fixes_applied.append(f"buildozer.spec: {pattern} -> {replacement}")
        
        # Записываем исправленный файл
        if content != original_content:
            spec_file.write_text(content, encoding='utf-8')
            self.log("✅ buildozer.spec исправлен", "SUCCESS")
            return True
        else:
            self.log("✅ buildozer.spec не требует исправлений", "SUCCESS")
            return True
    
    def fix_permissions(self) -> bool:
        """Исправление прав доступа к скриптам"""
        self.log("Исправление прав доступа...")
        
        scripts = [
            "debug_build.sh",
            "test_build_locally.sh",
            "analyze_errors.py",
            "monitor_github_actions.py",
            "auto_fix.py"
        ]
        
        for script in scripts:
            if os.path.exists(script):
                try:
                    os.chmod(script, 0o755)
                    self.log(f"✅ Права исправлены для {script}", "SUCCESS")
                    self.fixes_applied.append(f"Права доступа: {script}")
                except Exception as e:
                    self.log(f"❌ Ошибка исправления прав для {script}: {e}", "ERROR")
                    return False
        
        return True
    
    def clean_build_cache(self) -> bool:
        """Очистка кэша сборки"""
        self.log("Очистка кэша сборки...")
        
        cache_dirs = [".buildozer", "bin"]
        for cache_dir in cache_dirs:
            if os.path.exists(cache_dir):
                try:
                    shutil.rmtree(cache_dir)
                    self.log(f"✅ Удален кэш: {cache_dir}", "SUCCESS")
                    self.fixes_applied.append(f"Очистка кэша: {cache_dir}")
                except Exception as e:
                    self.log(f"❌ Ошибка удаления {cache_dir}: {e}", "ERROR")
                    return False
        
        # Создаем пустую директорию bin
        os.makedirs("bin", exist_ok=True)
        self.log("✅ Создана директория bin", "SUCCESS")
        
        return True
    
    def fix_environment_variables(self) -> bool:
        """Проверка и исправление переменных окружения"""
        self.log("Проверка переменных окружения...")
        
        required_vars = {
            'ANDROID_HOME': os.getenv('ANDROID_HOME'),
            'ANDROID_NDK_HOME': os.getenv('ANDROID_NDK_HOME'),
            'ANDROID_SDK_ROOT': os.getenv('ANDROID_SDK_ROOT')
        }
        
        missing_vars = []
        for var, value in required_vars.items():
            if not value:
                missing_vars.append(var)
            else:
                self.log(f"✅ {var}: {value}", "SUCCESS")
        
        if missing_vars:
            self.log(f"❌ Отсутствуют переменные: {', '.join(missing_vars)}", "ERROR")
            self.log("Установите переменные окружения:", "WARNING")
            for var in missing_vars:
                self.log(f"  export {var}=/path/to/{var.lower()}", "WARNING")
            return False
        
        return True
    
    def install_missing_dependencies(self) -> bool:
        """Установка отсутствующих зависимостей"""
        self.log("Проверка зависимостей Python...")
        
        required_packages = ['buildozer', 'kivy', 'requests']
        missing_packages = []
        
        for package in required_packages:
            success, _ = self.run_command(f"python -c 'import {package}'", check=False)
            if not success:
                missing_packages.append(package)
        
        if missing_packages:
            self.log(f"Установка отсутствующих пакетов: {', '.join(missing_packages)}", "WARNING")
            for package in missing_packages:
                success, output = self.run_command(f"pip install {package}", check=False)
                if success:
                    self.log(f"✅ Установлен {package}", "SUCCESS")
                    self.fixes_applied.append(f"Установлен пакет: {package}")
                else:
                    self.log(f"❌ Ошибка установки {package}: {output}", "ERROR")
                    return False
        else:
            self.log("✅ Все зависимости установлены", "SUCCESS")
        
        return True
    
    def create_logs_directory(self) -> bool:
        """Создание директории для логов"""
        self.log("Создание директории для логов...")
        
        try:
            os.makedirs("logs", exist_ok=True)
            self.log("✅ Директория logs создана", "SUCCESS")
            self.fixes_applied.append("Создана директория logs")
            return True
        except Exception as e:
            self.log(f"❌ Ошибка создания директории logs: {e}", "ERROR")
            return False
    
    def run_all_fixes(self) -> bool:
        """Запуск всех исправлений"""
        self.log("🔧 Запуск автоматических исправлений...", "INFO")
        self.log("=" * 50, "INFO")
        
        fixes = [
            ("Создание директории логов", self.create_logs_directory),
            ("Исправление прав доступа", self.fix_permissions),
            ("Очистка кэша сборки", self.clean_build_cache),
            ("Проверка buildozer.spec", self.fix_buildozer_spec),
            ("Проверка переменных окружения", self.fix_environment_variables),
            ("Установка зависимостей", self.install_missing_dependencies),
            ("Проверка Android SDK", self.check_android_sdk),
            ("Проверка Android NDK", self.check_android_ndk),
        ]
        
        all_success = True
        
        for fix_name, fix_func in fixes:
            self.log(f"\n🔧 {fix_name}...", "INFO")
            try:
                success = fix_func()
                if not success:
                    all_success = False
                    self.errors_found.append(fix_name)
            except Exception as e:
                self.log(f"❌ Ошибка в {fix_name}: {e}", "ERROR")
                all_success = False
                self.errors_found.append(fix_name)
        
        # Итоговый отчет
        self.log("\n" + "=" * 50, "INFO")
        self.log("📊 ИТОГОВЫЙ ОТЧЕТ", "INFO")
        self.log("=" * 50, "INFO")
        
        if self.fixes_applied:
            self.log(f"✅ Применено исправлений: {len(self.fixes_applied)}", "SUCCESS")
            for fix in self.fixes_applied:
                self.log(f"  • {fix}", "SUCCESS")
        
        if self.errors_found:
            self.log(f"❌ Найдено ошибок: {len(self.errors_found)}", "ERROR")
            for error in self.errors_found:
                self.log(f"  • {error}", "ERROR")
        
        if all_success:
            self.log("\n🎉 Все исправления применены успешно!", "SUCCESS")
            self.log("Теперь можно запустить: make debug", "INFO")
        else:
            self.log("\n⚠️  Некоторые исправления не удалось применить", "WARNING")
            self.log("Проверьте ошибки выше и исправьте их вручную", "WARNING")
        
        return all_success

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("Автоматическое исправление типичных ошибок сборки")
        print()
        print("Использование:")
        print("  python auto_fix.py          # Запуск всех исправлений")
        print("  python auto_fix.py --help   # Показать справку")
        print()
        print("Что исправляется:")
        print("  • Права доступа к скриптам")
        print("  • Очистка кэша сборки")
        print("  • Исправление buildozer.spec")
        print("  • Проверка переменных окружения")
        print("  • Установка зависимостей")
        print("  • Проверка Android SDK/NDK")
        return
    
    fixer = AutoFixer()
    success = fixer.run_all_fixes()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
