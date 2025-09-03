"""
Модуль для мониторинга производительности приложения CNC Checklist
"""
import time
import logging
import psutil
import threading
from typing import Dict, List, Optional
from dataclasses import dataclass, field
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """Метрика производительности"""
    name: str
    start_time: float
    end_time: Optional[float] = None
    duration: Optional[float] = None
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    details: Dict = field(default_factory=dict)

class PerformanceMonitor:
    """Монитор производительности приложения"""
    
    def __init__(self):
        self.metrics: List[PerformanceMetric] = []
        self.active_metrics: Dict[str, PerformanceMetric] = {}
        self.system_metrics: List[Dict] = []
        self.monitoring = False
        self.monitor_thread: Optional[threading.Thread] = None
        
    def start_metric(self, name: str, details: Dict = None) -> str:
        """Начать измерение метрики"""
        metric_id = f"{name}_{int(time.time() * 1000)}"
        metric = PerformanceMetric(
            name=name,
            start_time=time.time(),
            details=details or {}
        )
        self.active_metrics[metric_id] = metric
        logger.debug(f"Начато измерение: {name} (ID: {metric_id})")
        return metric_id
    
    def end_metric(self, metric_id: str) -> PerformanceMetric:
        """Завершить измерение метрики"""
        if metric_id not in self.active_metrics:
            logger.warning(f"Метрика {metric_id} не найдена")
            return None
            
        metric = self.active_metrics.pop(metric_id)
        metric.end_time = time.time()
        metric.duration = metric.end_time - metric.start_time
        
        # Получаем системные метрики
        try:
            process = psutil.Process()
            metric.memory_usage = process.memory_info().rss / 1024 / 1024  # MB
            metric.cpu_usage = process.cpu_percent()
        except Exception as e:
            logger.warning(f"Не удалось получить системные метрики: {e}")
            
        self.metrics.append(metric)
        logger.info(f"Завершено измерение: {metric.name} - {metric.duration:.3f}с, "
                   f"Память: {metric.memory_usage:.1f}MB, CPU: {metric.cpu_usage:.1f}%")
        
        return metric
    
    def get_metrics_summary(self) -> Dict:
        """Получить сводку по метрикам"""
        if not self.metrics:
            return {"message": "Нет данных о производительности"}
            
        total_metrics = len(self.metrics)
        avg_duration = sum(m.duration for m in self.metrics if m.duration) / total_metrics
        max_duration = max(m.duration for m in self.metrics if m.duration)
        min_duration = min(m.duration for m in self.metrics if m.duration)
        
        avg_memory = sum(m.memory_usage for m in self.metrics if m.memory_usage) / total_metrics
        max_memory = max(m.memory_usage for m in self.metrics if m.memory_usage)
        
        return {
            "total_metrics": total_metrics,
            "avg_duration": avg_duration,
            "max_duration": max_duration,
            "min_duration": min_duration,
            "avg_memory_mb": avg_memory,
            "max_memory_mb": max_memory,
            "active_metrics": len(self.active_metrics)
        }
    
    def start_system_monitoring(self, interval: int = 30):
        """Начать мониторинг системных ресурсов"""
        if self.monitoring:
            logger.warning("Мониторинг уже запущен")
            return
            
        self.monitoring = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_system,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
        logger.info(f"Запущен мониторинг системных ресурсов (интервал: {interval}с)")
    
    def stop_system_monitoring(self):
        """Остановить мониторинг системных ресурсов"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=5)
        logger.info("Мониторинг системных ресурсов остановлен")
    
    def _monitor_system(self, interval: int):
        """Мониторинг системных ресурсов в отдельном потоке"""
        while self.monitoring:
            try:
                # Получаем системные метрики
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                
                # Получаем метрики процесса
                process = psutil.Process()
                process_memory = process.memory_info().rss / 1024 / 1024  # MB
                process_cpu = process.cpu_percent()
                
                metric = {
                    "timestamp": datetime.now().isoformat(),
                    "system_cpu": cpu_percent,
                    "system_memory_percent": memory.percent,
                    "system_memory_available_gb": memory.available / 1024 / 1024 / 1024,
                    "disk_usage_percent": disk.percent,
                    "disk_free_gb": disk.free / 1024 / 1024 / 1024,
                    "process_memory_mb": process_memory,
                    "process_cpu": process_cpu,
                    "active_metrics_count": len(self.active_metrics)
                }
                
                self.system_metrics.append(metric)
                
                # Ограничиваем количество метрик в памяти
                if len(self.system_metrics) > 1000:
                    self.system_metrics = self.system_metrics[-500:]
                
                # Логируем предупреждения
                if cpu_percent > 80:
                    logger.warning(f"Высокая загрузка CPU: {cpu_percent:.1f}%")
                if memory.percent > 85:
                    logger.warning(f"Высокое использование памяти: {memory.percent:.1f}%")
                if process_memory > 500:  # 500MB
                    logger.warning(f"Высокое использование памяти процессом: {process_memory:.1f}MB")
                
                time.sleep(interval)
                
            except Exception as e:
                logger.error(f"Ошибка при мониторинге системы: {e}")
                time.sleep(interval)
    
    def get_system_metrics_summary(self) -> Dict:
        """Получить сводку по системным метрикам"""
        if not self.system_metrics:
            return {"message": "Нет данных о системных метриках"}
        
        recent_metrics = self.system_metrics[-10:]  # Последние 10 измерений
        
        avg_cpu = sum(m["system_cpu"] for m in recent_metrics) / len(recent_metrics)
        avg_memory = sum(m["system_memory_percent"] for m in recent_metrics) / len(recent_metrics)
        avg_process_memory = sum(m["process_memory_mb"] for m in recent_metrics) / len(recent_metrics)
        
        return {
            "avg_system_cpu": avg_cpu,
            "avg_system_memory_percent": avg_memory,
            "avg_process_memory_mb": avg_process_memory,
            "total_measurements": len(self.system_metrics),
            "monitoring_active": self.monitoring
        }
    
    def export_metrics(self, filepath: str):
        """Экспорт метрик в файл"""
        try:
            import json
            
            data = {
                "performance_metrics": [
                    {
                        "name": m.name,
                        "duration": m.duration,
                        "memory_usage": m.memory_usage,
                        "cpu_usage": m.cpu_usage,
                        "details": m.details
                    }
                    for m in self.metrics
                ],
                "system_metrics": self.system_metrics[-100:],  # Последние 100 измерений
                "summary": self.get_metrics_summary(),
                "system_summary": self.get_system_metrics_summary(),
                "export_timestamp": datetime.now().isoformat()
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Метрики экспортированы в {filepath}")
            
        except Exception as e:
            logger.error(f"Ошибка при экспорте метрик: {e}")

# Глобальный экземпляр монитора
performance_monitor = PerformanceMonitor()

def monitor_performance(name: str, details: Dict = None):
    """Декоратор для мониторинга производительности функций"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            metric_id = performance_monitor.start_metric(name, details)
            try:
                result = func(*args, **kwargs)
                performance_monitor.end_metric(metric_id)
                return result
            except Exception as e:
                performance_monitor.end_metric(metric_id)
                raise
        return wrapper
    return decorator
