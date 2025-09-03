# Makefile для CNC Checklist - диагностика и сборка

.PHONY: help debug test analyze monitor clean install-deps

# Цвета для вывода
RED=\033[0;31m
GREEN=\033[0;32m
YELLOW=\033[1;33m
BLUE=\033[0;34m
NC=\033[0m # No Color

help: ## Показать справку
	@echo "$(BLUE)CNC Checklist - Инструменты диагностики и сборки$(NC)"
	@echo ""
	@echo "$(YELLOW)Доступные команды:$(NC)"
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}' $(MAKEFILE_LIST)

debug: ## Запустить диагностику окружения
	@echo "$(BLUE)🔍 Запуск диагностики окружения...$(NC)"
	@chmod +x debug_build.sh
	@./debug_build.sh

test: ## Запустить локальное тестирование
	@echo "$(BLUE)🧪 Запуск локального тестирования...$(NC)"
	@chmod +x test_build_locally.sh
	@./test_build_locally.sh

analyze: ## Анализировать логи (требует файл лога)
	@echo "$(BLUE)🔍 Анализ логов...$(NC)"
	@if [ -z "$(LOG_FILE)" ]; then \
		echo "$(RED)❌ Укажите файл лога: make analyze LOG_FILE=logs/buildozer_build.log$(NC)"; \
		exit 1; \
	fi
	@python analyze_errors.py $(LOG_FILE)

monitor: ## Мониторить GitHub Actions
	@echo "$(BLUE)📊 Мониторинг GitHub Actions...$(NC)"
	@python monitor_github_actions.py status

monitor-live: ## Живой мониторинг последнего запуска
	@echo "$(BLUE)📊 Живой мониторинг...$(NC)"
	@python monitor_github_actions.py monitor

download-logs: ## Скачать логи последнего неудачного запуска
	@echo "$(BLUE)📥 Скачивание логов...$(NC)"
	@if [ -z "$(RUN_ID)" ]; then \
		echo "$(RED)❌ Укажите ID запуска: make download-logs RUN_ID=123456789$(NC)"; \
		exit 1; \
	fi
	@python monitor_github_actions.py download $(RUN_ID)

install-deps: ## Установить зависимости для диагностики
	@echo "$(BLUE)📦 Установка зависимостей...$(NC)"
	@pip install requests
	@echo "$(GREEN)✅ Зависимости установлены$(NC)"

clean: ## Очистить временные файлы
	@echo "$(BLUE)🧹 Очистка временных файлов...$(NC)"
	@rm -rf logs/
	@rm -rf .buildozer/
	@rm -rf bin/
	@echo "$(GREEN)✅ Очистка завершена$(NC)"

build-local: ## Локальная сборка (требует Android SDK)
	@echo "$(BLUE)🔨 Локальная сборка APK...$(NC)"
	@if [ -z "$(ANDROID_HOME)" ]; then \
		echo "$(RED)❌ ANDROID_HOME не установлен$(NC)"; \
		exit 1; \
	fi
	@buildozer android debug

validate-config: ## Проверить конфигурацию buildozer.spec
	@echo "$(BLUE)✅ Проверка конфигурации...$(NC)"
	@if [ ! -f "buildozer.spec" ]; then \
		echo "$(RED)❌ buildozer.spec не найден$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ buildozer.spec найден$(NC)"
	@echo "$(YELLOW)Ключевые настройки:$(NC)"
	@grep -E "^(android\.|p4a\.)" buildozer.spec || echo "Нет настроек android/p4a"

check-sdk: ## Проверить установку Android SDK
	@echo "$(BLUE)📱 Проверка Android SDK...$(NC)"
	@if [ -z "$(ANDROID_HOME)" ]; then \
		echo "$(RED)❌ ANDROID_HOME не установлен$(NC)"; \
		exit 1; \
	fi
	@if [ ! -d "$(ANDROID_HOME)" ]; then \
		echo "$(RED)❌ ANDROID_HOME директория не существует$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ ANDROID_HOME: $(ANDROID_HOME)$(NC)"
	@echo "$(YELLOW)Содержимое SDK:$(NC)"
	@ls -la "$(ANDROID_HOME)" | head -10

check-ndk: ## Проверить установку Android NDK
	@echo "$(BLUE)🔧 Проверка Android NDK...$(NC)"
	@if [ -z "$(ANDROID_NDK_HOME)" ]; then \
		echo "$(RED)❌ ANDROID_NDK_HOME не установлен$(NC)"; \
		exit 1; \
	fi
	@if [ ! -d "$(ANDROID_NDK_HOME)" ]; then \
		echo "$(RED)❌ ANDROID_NDK_HOME директория не существует$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✅ ANDROID_NDK_HOME: $(ANDROID_NDK_HOME)$(NC)"

full-check: debug check-sdk check-ndk validate-config ## Полная проверка окружения
	@echo "$(GREEN)✅ Полная проверка завершена$(NC)"

quick-fix: ## Быстрые исправления типичных проблем
	@echo "$(BLUE)🔧 Применение быстрых исправлений...$(NC)"
	@echo "$(YELLOW)1. Очистка кэша buildozer...$(NC)"
	@rm -rf .buildozer/ || true
	@echo "$(YELLOW)2. Создание директории bin...$(NC)"
	@mkdir -p bin/
	@echo "$(YELLOW)3. Проверка прав на скрипты...$(NC)"
	@chmod +x debug_build.sh test_build_locally.sh || true
	@echo "$(GREEN)✅ Быстрые исправления применены$(NC)"

# Примеры использования
examples: ## Показать примеры использования
	@echo "$(BLUE)📚 Примеры использования:$(NC)"
	@echo ""
	@echo "$(YELLOW)Диагностика:$(NC)"
	@echo "  make debug                    # Полная диагностика"
	@echo "  make test                     # Локальное тестирование"
	@echo "  make full-check              # Полная проверка"
	@echo ""
	@echo "$(YELLOW)Анализ логов:$(NC)"
	@echo "  make analyze LOG_FILE=logs/buildozer_build.log"
	@echo "  make download-logs RUN_ID=123456789"
	@echo ""
	@echo "$(YELLOW)Мониторинг:$(NC)"
	@echo "  make monitor                 # Статус последних запусков"
	@echo "  make monitor-live            # Живой мониторинг"
	@echo ""
	@echo "$(YELLOW)Сборка:$(NC)"
	@echo "  make build-local             # Локальная сборка"
	@echo "  make clean                   # Очистка"
	@echo ""
	@echo "$(YELLOW)Исправления:$(NC)"
	@echo "  make quick-fix               # Быстрые исправления"
	@echo "  make install-deps            # Установка зависимостей"
