# Makefile for YASE Project

# .PHONY говорит make, что эти цели не являются файлами.
# Это предотвращает конфликты, если у вас вдруг появится папка с именем "clean".
.PHONY: all build dist clean rebuild

# .SILENT отключает вывод самих команд в консоль, оставляя только их результат (echo и т.д.).
.SILENT:

# --- Configuration ---
# Используем переменные, чтобы легко менять имена в одном месте.
SPEC_FILE = YASE.spec
DIST_DIR = dist
BUILD_DIR = build

# Файлы, которые нужно скопировать рядом с .exe
EXTRA_FILES = config.ini swatches.ase

VERSION = $(shell python -c "import tomllib; f = open('pyproject.toml', 'rb'); print(tomllib.load(f)['project']['version']); f.close()")
ARCHIVE_NAME = YASE-$(VERSION).7z

# --- Targets ---
# Цель по умолчанию
all: zip

# Шаг 1: Запуск PyInstaller для создания .exe в папке DIST_DIR
build:
	echo "Building executable with PyInstaller..."
	pyinstaller $(SPEC_FILE)

# Шаг 2: Копирование дополнительных файлов в папку с дистрибутивом.

dist: build
	echo "Copying extra files to $(DIST_DIR)..."
	cp $(EXTRA_FILES) $(DIST_DIR)/

# Очистка артефактов сборки
clean:
	echo "Cleaning up build artifacts..."
	rm -rf $(BUILD_DIR) $(DIST_DIR)
	# Также полезно удалять кэш Python
	find . -type d -name "__pycache__" -exec rm -r {} +

# Очень удобная команда: полная пересборка с нуля.
rebuild: clean all

# Шаг 3: Упаковка содержимого папки dist в ZIP
zip: dist
	@echo "Creating ZIP archive $(ARCHIVE_NAME)..."
	cd $(DIST_DIR) && 7z a -r ../$(ARCHIVE_NAME) .
