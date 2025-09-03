"""
Конфигурация логирования для приложения CNC Checklist
"""
import logging
import logging.handlers
import os
from datetime import datetime
from kivy.app import App

def setup_logging():
    """Настройка системы логирования"""
    
    # Получаем директорию приложения
    app = App.get_running_app()
    if app:
        log_dir = app.user_data_dir
    else:
        log_dir = os.path.expanduser("~")
    
    # Создаем директорию для логов если её нет
    os.makedirs(log_dir, exist_ok=True)
    
    # Путь к файлу лога
    log_file = os.path.join(log_dir, "cnc_checklist.log")
    
    # Создаем форматтер
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    
    # Удаляем существующие обработчики
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    # Обработчик для файла с ротацией
    file_handler = logging.handlers.RotatingFileHandler(
        log_file, 
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Добавляем обработчики
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Настраиваем логгеры для внешних библиотек
    logging.getLogger('kivy').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)
    logging.getLogger('reportlab').setLevel(logging.WARNING)
    
    # Логируем начало работы
    logger = logging.getLogger(__name__)
    logger.info("="*50)
    logger.info("Запуск приложения CNC Checklist")
    logger.info(f"Версия: 1.3")
    logger.info(f"Директория логов: {log_dir}")
    logger.info(f"Файл лога: {log_file}")
    logger.info("="*50)
    
    return logger

def log_app_info():
    """Логирование информации о приложении"""
    logger = logging.getLogger(__name__)
    
    try:
        import platform
        import sys
        
        logger.info(f"Платформа: {platform.platform()}")
        logger.info(f"Python версия: {sys.version}")
        logger.info(f"Архитектура: {platform.architecture()}")
        
        # Информация о Kivy
        try:
            import kivy
            logger.info(f"Kivy версия: {kivy.__version__}")
        except ImportError:
            logger.warning("Kivy не найден")
            
        # Информация о Android
        try:
            from kivy.utils import platform as kivy_platform
            logger.info(f"Kivy платформа: {kivy_platform}")
        except Exception as e:
            logger.warning(f"Не удалось определить Kivy платформу: {e}")
            
    except Exception as e:
        logger.error(f"Ошибка при получении информации о системе: {e}")

def log_performance(func):
    """Декоратор для логирования производительности функций"""
    import functools
    import time
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(func.__module__)
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            logger.debug(f"Функция {func.__name__} выполнена за {execution_time:.3f} секунд")
            return result
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Ошибка в функции {func.__name__} после {execution_time:.3f} секунд: {e}")
            raise
    
    return wrapper

class AuditLogger:
    """Класс для аудита действий пользователя"""
    
    def __init__(self):
        self.logger = logging.getLogger("audit")
        self.logger.setLevel(logging.INFO)
        
        # Создаем отдельный файл для аудита
        app = App.get_running_app()
        if app:
            audit_file = os.path.join(app.user_data_dir, "audit.log")
        else:
            audit_file = "audit.log"
            
        audit_handler = logging.FileHandler(audit_file, encoding='utf-8')
        audit_formatter = logging.Formatter(
            '%(asctime)s - AUDIT - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        audit_handler.setFormatter(audit_formatter)
        self.logger.addHandler(audit_handler)
    
    def log_session_start(self, order_number: str):
        """Логирование начала сессии"""
        self.logger.info(f"СЕССИЯ_НАЧАЛО - Заказ: {order_number}")
    
    def log_session_end(self, order_number: str, completed: bool):
        """Логирование завершения сессии"""
        status = "ЗАВЕРШЕНА" if completed else "ПРЕРВАНА"
        self.logger.info(f"СЕССИЯ_КОНЕЦ - Заказ: {order_number}, Статус: {status}")
    
    def log_item_completion(self, item_id: str, status: bool, critical: bool):
        """Логирование завершения пункта"""
        status_text = "ВЫПОЛНЕН" if status else "НЕ_ВЫПОЛНЕН"
        critical_text = " (КРИТИЧЕСКИЙ)" if critical else ""
        self.logger.info(f"ПУНКТ_{status_text} - ID: {item_id}{critical_text}")
    
    def log_master_bypass(self, item_id: str, master_name: str):
        """Логирование обхода критического пункта мастером"""
        self.logger.info(f"ОБХОД_КРИТИЧЕСКОГО - Пункт: {item_id}, Мастер: {master_name}")
    
    def log_pin_attempt(self, pin_type: str, success: bool):
        """Логирование попытки ввода PIN"""
        status = "УСПЕШНО" if success else "НЕУДАЧНО"
        self.logger.info(f"PIN_{status} - Тип: {pin_type}")
    
    def log_pdf_generation(self, order_number: str, file_path: str):
        """Логирование генерации PDF"""
        self.logger.info(f"PDF_СОЗДАН - Заказ: {order_number}, Файл: {file_path}")
    
    def log_email_send(self, order_number: str, recipients: list, success: bool):
        """Логирование отправки email"""
        status = "УСПЕШНО" if success else "ОШИБКА"
        self.logger.info(f"EMAIL_{status} - Заказ: {order_number}, Получатели: {recipients}")

# Глобальный экземпляр аудитора
audit_logger = AuditLogger()
