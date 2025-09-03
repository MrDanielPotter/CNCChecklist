"""
Модуль диагностики для приложения CNC Checklist
"""
import os
import sys
import logging
import json
import traceback
from datetime import datetime
from typing import Dict, List, Any
from kivy.app import App
from kivy.utils import platform

logger = logging.getLogger(__name__)

class DiagnosticsCollector:
    """Сборщик диагностической информации"""
    
    def __init__(self):
        self.app = App.get_running_app()
        
    def collect_system_info(self) -> Dict[str, Any]:
        """Сбор информации о системе"""
        info = {
            "timestamp": datetime.now().isoformat(),
            "platform": platform,
            "python_version": sys.version,
            "python_executable": sys.executable,
        }
        
        try:
            import platform as sys_platform
            info.update({
                "system": sys_platform.system(),
                "release": sys_platform.release(),
                "version": sys_platform.version(),
                "machine": sys_platform.machine(),
                "processor": sys_platform.processor(),
                "architecture": sys_platform.architecture(),
            })
        except Exception as e:
            info["system_info_error"] = str(e)
        
        # Информация о Kivy
        try:
            import kivy
            info["kivy_version"] = kivy.__version__
            info["kivy_data_dir"] = kivy.kivy_data_dir
        except Exception as e:
            info["kivy_info_error"] = str(e)
        
        # Информация о приложении
        if self.app:
            info.update({
                "app_version": getattr(self.app, 'APP_VERSION', 'Unknown'),
                "user_data_dir": self.app.user_data_dir,
                "app_name": self.app.name,
            })
        
        return info
    
    def collect_android_info(self) -> Dict[str, Any]:
        """Сбор информации об Android (если применимо)"""
        if platform != "android":
            return {"platform": "not_android"}
        
        info = {"platform": "android"}
        
        try:
            from jnius import autoclass
            
            # Информация о версии Android
            Build = autoclass('android.os.Build')
            info.update({
                "android_version": Build.VERSION.RELEASE,
                "api_level": Build.VERSION.SDK_INT,
                "device": Build.DEVICE,
                "model": Build.MODEL,
                "manufacturer": Build.MANUFACTURER,
                "brand": Build.BRAND,
            })
            
            # Информация о разрешениях
            try:
                from android.permissions import check_permission, Permission
                permissions = {
                    "camera": check_permission(Permission.CAMERA),
                    "read_media_images": check_permission("android.permission.READ_MEDIA_IMAGES"),
                    "read_media_visual": check_permission("android.permission.READ_MEDIA_VISUAL_USER_SELECTED"),
                }
                info["permissions"] = permissions
            except Exception as e:
                info["permissions_error"] = str(e)
                
        except Exception as e:
            info["android_info_error"] = str(e)
        
        return info
    
    def collect_app_state(self) -> Dict[str, Any]:
        """Сбор состояния приложения"""
        if not self.app:
            return {"error": "App not available"}
        
        state = {
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            # Информация о текущей сессии
            if hasattr(self.app, 'state') and self.app.state:
                state["current_session"] = {
                    "order_number": self.app.state.order_number,
                    "started_at": self.app.state.started_at,
                    "current_block": self.app.state.current_block_idx,
                    "current_item": self.app.state.current_item_idx,
                    "version": self.app.state.version,
                }
            else:
                state["current_session"] = None
            
            # Информация о настройках
            if hasattr(self.app, 'settings') and self.app.settings:
                settings_info = {
                    "pins_must_change": self.app.settings.pins_must_change,
                    "pin_error_count": self.app.settings.pin_error_count,
                    "pin_locked": bool(self.app.settings.pin_lock_until_ts),
                    "smtp_enabled": self.app.settings.smtp_enabled,
                    "report_seq": self.app.settings.report_seq,
                }
                state["settings"] = settings_info
            
            # Информация о текущем экране
            if hasattr(self.app, 'sm') and self.app.sm:
                state["current_screen"] = self.app.sm.current
            
        except Exception as e:
            state["app_state_error"] = str(e)
        
        return state
    
    def collect_file_info(self) -> Dict[str, Any]:
        """Сбор информации о файлах приложения"""
        if not self.app:
            return {"error": "App not available"}
        
        file_info = {
            "timestamp": datetime.now().isoformat(),
            "user_data_dir": self.app.user_data_dir,
        }
        
        try:
            # Проверяем наличие ключевых файлов
            key_files = [
                "settings.json",
                "session.json", 
                "history.json",
                "cnc_checklist.log",
                "audit.log"
            ]
            
            files_status = {}
            for filename in key_files:
                filepath = os.path.join(self.app.user_data_dir, filename)
                if os.path.exists(filepath):
                    stat = os.stat(filepath)
                    files_status[filename] = {
                        "exists": True,
                        "size": stat.st_size,
                        "modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                else:
                    files_status[filename] = {"exists": False}
            
            file_info["files"] = files_status
            
            # Размер директории
            total_size = 0
            file_count = 0
            for root, dirs, files in os.walk(self.app.user_data_dir):
                for file in files:
                    filepath = os.path.join(root, file)
                    try:
                        total_size += os.path.getsize(filepath)
                        file_count += 1
                    except OSError:
                        pass
            
            file_info["total_size_bytes"] = total_size
            file_info["total_files"] = file_count
            
        except Exception as e:
            file_info["file_info_error"] = str(e)
        
        return file_info
    
    def collect_error_logs(self) -> Dict[str, Any]:
        """Сбор информации об ошибках из логов"""
        if not self.app:
            return {"error": "App not available"}
        
        error_info = {
            "timestamp": datetime.now().isoformat(),
        }
        
        try:
            log_file = os.path.join(self.app.user_data_dir, "cnc_checklist.log")
            if os.path.exists(log_file):
                with open(log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Ищем строки с ошибками
                error_lines = [line.strip() for line in lines if 'ERROR' in line or 'CRITICAL' in line]
                error_info["error_count"] = len(error_lines)
                error_info["recent_errors"] = error_lines[-10:]  # Последние 10 ошибок
            else:
                error_info["log_file_exists"] = False
                
        except Exception as e:
            error_info["error_logs_error"] = str(e)
        
        return error_info
    
    def collect_all_diagnostics(self) -> Dict[str, Any]:
        """Сбор всей диагностической информации"""
        logger.info("Начало сбора диагностической информации")
        
        diagnostics = {
            "collection_timestamp": datetime.now().isoformat(),
            "system_info": self.collect_system_info(),
            "android_info": self.collect_android_info(),
            "app_state": self.collect_app_state(),
            "file_info": self.collect_file_info(),
            "error_logs": self.collect_error_logs(),
        }
        
        logger.info("Диагностическая информация собрана")
        return diagnostics
    
    def export_diagnostics(self, filepath: str = None) -> str:
        """Экспорт диагностической информации в файл"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"diagnostics_{timestamp}.json"
            if self.app:
                filepath = os.path.join(self.app.user_data_dir, filename)
            else:
                filepath = filename
        
        try:
            diagnostics = self.collect_all_diagnostics()
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(diagnostics, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Диагностическая информация экспортирована в {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Ошибка при экспорте диагностики: {e}")
            raise

def create_diagnostics_report() -> str:
    """Создать отчет диагностики"""
    collector = DiagnosticsCollector()
    return collector.export_diagnostics()

def log_exception(exc_type, exc_value, exc_traceback):
    """Обработчик необработанных исключений"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    logger = logging.getLogger(__name__)
    logger.critical("Необработанное исключение", exc_info=(exc_type, exc_value, exc_traceback))
    
    # Создаем диагностический отчет при критической ошибке
    try:
        collector = DiagnosticsCollector()
        diagnostics = collector.collect_all_diagnostics()
        diagnostics["exception"] = {
            "type": str(exc_type),
            "value": str(exc_value),
            "traceback": traceback.format_exception(exc_type, exc_value, exc_traceback)
        }
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        crash_file = f"crash_report_{timestamp}.json"
        if collector.app:
            crash_path = os.path.join(collector.app.user_data_dir, crash_file)
        else:
            crash_path = crash_file
            
        with open(crash_path, 'w', encoding='utf-8') as f:
            json.dump(diagnostics, f, ensure_ascii=False, indent=2)
            
        logger.critical(f"Отчет о сбое сохранен в {crash_path}")
        
    except Exception as e:
        logger.critical(f"Не удалось создать отчет о сбое: {e}")

# Устанавливаем обработчик необработанных исключений
sys.excepthook = log_exception
