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

# --- Targets ---

# Цель по умолчанию (выполняется, если просто написать 'make')
# Она зависит от цели 'dist', то есть сначала выполнится 'dist'.
all: dist

# Шаг 1: Запуск PyInstaller для создания .exe в папке DIST_DIR
build:
	echo "Building executable with PyInstaller..."
	pyinstaller $(SPEC_FILE)

# Шаг 2: Копирование дополнительных файлов в папку с дистрибутивом.
# Эта цель зависит от 'build', поэтому она выполнится только после успешной сборки.
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
