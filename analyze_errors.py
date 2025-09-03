#!/usr/bin/env python3
"""
Анализатор ошибок для GitHub Actions workflow
Помогает понять и классифицировать ошибки сборки
"""

import re
import sys
from typing import List, Dict, Tuple
from dataclasses import dataclass
from enum import Enum

class ErrorType(Enum):
    SDK_INSTALLATION = "SDK Installation"
    LICENSE_ACCEPTANCE = "License Acceptance"
    PATH_CONFIGURATION = "Path Configuration"
    DEPENDENCY_CONFLICT = "Dependency Conflict"
    COMPILATION_ERROR = "Compilation Error"
    CONFIGURATION_ERROR = "Configuration Error"
    PERMISSION_ERROR = "Permission Error"
    NETWORK_ERROR = "Network Error"
    UNKNOWN = "Unknown"

@dataclass
class ErrorPattern:
    pattern: str
    error_type: ErrorType
    description: str
    suggested_fix: str

# Паттерны ошибок и их решения
ERROR_PATTERNS = [
    ErrorPattern(
        pattern=r"build-tools folder not found",
        error_type=ErrorType.SDK_INSTALLATION,
        description="Build tools directory not found",
        suggested_fix="Check ANDROID_HOME path and ensure build-tools are installed"
    ),
    ErrorPattern(
        pattern=r"Aidl not found",
        error_type=ErrorType.SDK_INSTALLATION,
        description="AIDL tool not found",
        suggested_fix="Install build-tools package via sdkmanager"
    ),
    ErrorPattern(
        pattern=r"license is not accepted",
        error_type=ErrorType.LICENSE_ACCEPTANCE,
        description="Android SDK license not accepted",
        suggested_fix="Run: echo 'y' | sdkmanager --licenses"
    ),
    ErrorPattern(
        pattern=r"sdkmanager path.*does not exist",
        error_type=ErrorType.PATH_CONFIGURATION,
        description="sdkmanager not found at expected path",
        suggested_fix="Create symlink from cmdline-tools to tools/bin"
    ),
    ErrorPattern(
        pattern=r"platform android-\d+ not found",
        error_type=ErrorType.SDK_INSTALLATION,
        description="Android platform not installed",
        suggested_fix="Install platform via sdkmanager or use available platform"
    ),
    ErrorPattern(
        pattern=r"Conflict detected.*kivy.*webview",
        error_type=ErrorType.DEPENDENCY_CONFLICT,
        description="Kivy and webview bootstrap conflict",
        suggested_fix="Use sdl2 bootstrap instead of webview"
    ),
    ErrorPattern(
        pattern=r"LT_SYS_SYMBOL_USCORE.*undefined macro",
        error_type=ErrorType.COMPILATION_ERROR,
        description="libffi compilation error with autotools",
        suggested_fix="Set LT_SYS_SYMBOL_USCORE=no or blacklist libffi recipe"
    ),
    ErrorPattern(
        pattern=r"autoreconf.*failed with exit status",
        error_type=ErrorType.COMPILATION_ERROR,
        description="Autotools configuration failed",
        suggested_fix="Install autoconf, automake, libtool or use system libffi"
    ),
    ErrorPattern(
        pattern=r"End-of-central-directory signature not found",
        error_type=ErrorType.NETWORK_ERROR,
        description="Downloaded zip file is corrupted",
        suggested_fix="Retry download or use alternative URL"
    ),
    ErrorPattern(
        pattern=r"Requested API target \d+ is not available",
        error_type=ErrorType.CONFIGURATION_ERROR,
        description="Android API level not installed",
        suggested_fix="Install the required API level or update buildozer.spec"
    ),
    ErrorPattern(
        pattern=r"android\.bootstrap is deprecated",
        error_type=ErrorType.CONFIGURATION_ERROR,
        description="Deprecated buildozer.spec parameter",
        suggested_fix="Replace android.bootstrap with p4a.bootstrap"
    ),
    ErrorPattern(
        pattern=r"android\.arch.*deprecated",
        error_type=ErrorType.CONFIGURATION_ERROR,
        description="Deprecated buildozer.spec parameter",
        suggested_fix="Replace android.arch with android.archs"
    ),
]

def analyze_log_file(log_content: str) -> List[Tuple[ErrorType, str, str, str]]:
    """Анализирует лог файл и возвращает найденные ошибки"""
    errors = []
    
    for pattern in ERROR_PATTERNS:
        matches = re.finditer(pattern.pattern, log_content, re.IGNORECASE | re.MULTILINE)
        for match in matches:
            context = get_error_context(log_content, match.start(), match.end())
            errors.append((
                pattern.error_type,
                pattern.description,
                pattern.suggested_fix,
                context
            ))
    
    return errors

def get_error_context(log_content: str, start: int, end: int, context_lines: int = 3) -> str:
    """Получает контекст вокруг ошибки"""
    lines = log_content.split('\n')
    error_line_num = log_content[:start].count('\n')
    
    start_line = max(0, error_line_num - context_lines)
    end_line = min(len(lines), error_line_num + context_lines + 1)
    
    context_lines_list = lines[start_line:end_line]
    return '\n'.join(context_lines_list)

def print_analysis(errors: List[Tuple[ErrorType, str, str, str]]):
    """Выводит анализ ошибок"""
    if not errors:
        print("✅ No known errors found in the log")
        return
    
    print(f"🔍 Found {len(errors)} error(s):")
    print("=" * 80)
    
    # Группируем ошибки по типу
    error_groups = {}
    for error_type, description, fix, context in errors:
        if error_type not in error_groups:
            error_groups[error_type] = []
        error_groups[error_type].append((description, fix, context))
    
    for error_type, error_list in error_groups.items():
        print(f"\n📋 {error_type.value} ({len(error_list)} error(s)):")
        print("-" * 40)
        
        for i, (description, fix, context) in enumerate(error_list, 1):
            print(f"\n{i}. {description}")
            print(f"   💡 Fix: {fix}")
            print(f"   📄 Context:")
            for line in context.split('\n'):
                print(f"      {line}")
    
    print("\n" + "=" * 80)
    print("🎯 Recommended Actions:")
    
    # Приоритетные действия
    priority_actions = []
    for error_type, error_list in error_groups.items():
        if error_type == ErrorType.SDK_INSTALLATION:
            priority_actions.append("1. Fix Android SDK installation and paths")
        elif error_type == ErrorType.LICENSE_ACCEPTANCE:
            priority_actions.append("2. Accept Android SDK licenses")
        elif error_type == ErrorType.DEPENDENCY_CONFLICT:
            priority_actions.append("3. Resolve dependency conflicts (use sdl2 bootstrap)")
        elif error_type == ErrorType.COMPILATION_ERROR:
            priority_actions.append("4. Fix compilation issues (libffi, autotools)")
        elif error_type == ErrorType.CONFIGURATION_ERROR:
            priority_actions.append("5. Update buildozer.spec configuration")
    
    for action in priority_actions:
        print(f"   {action}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_errors.py <log_file>")
        print("Example: python analyze_errors.py logs/buildozer_build.log")
        sys.exit(1)
    
    log_file = sys.argv[1]
    
    try:
        with open(log_file, 'r', encoding='utf-8') as f:
            log_content = f.read()
        
        print(f"🔍 Analyzing log file: {log_file}")
        print(f"📊 Log size: {len(log_content)} characters")
        print()
        
        errors = analyze_log_file(log_content)
        print_analysis(errors)
        
    except FileNotFoundError:
        print(f"❌ Log file not found: {log_file}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error analyzing log: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
