from models import SwatchModel
from views import SwatchEditorView
from models import Swatch


class SwatchController:
    """
    Контроллер связывает действия пользователя в View с логикой в Model.
    """
    def __init__(self, model: SwatchModel, view: SwatchEditorView):
        self.model = model
        self.view = view

    def _update_view(self):
        """
        Централизованный метод для обновления всего View на основе текущего состояния Модели.
        Это ключевая концепция: Модель - единственный источник правды.
        """
        swatches = self.model.get_swatches()
        file_path = self.model.get_file_path()
        self.view.update_swatches(swatches)
        self.view.update_title(file_path)

    def run_initial_load(self, file_path: str | None):
        """Загрузка файла при старте приложения, если он указан в config.ini."""
        if not file_path:
            self._update_view() # Просто отрисовываем пустой интерфейс
            return
        try:
            self.model.load_from_ase(file_path)
        except Exception as e:
            # На раннем этапе View может быть еще не готов к показу messagebox,
            # поэтому можно ограничиться выводом в консоль или отложить показ ошибки.
            # Но для простоты сразу используем View.
            self.view.show_error("Initial Load Error", str(e))
        finally:
            self._update_view()

    # --- Обработчики команд из меню ---

    def new_swatch_file(self):
        """Создает новый, пустой список образцов."""
        # В будущем здесь можно добавить диалог с подтверждением,
        # если есть несохраненные изменения.
        self.model.clear()
        self._update_view()

    def load_ase_dialog(self):
        """Обрабатывает нажатие 'Load' в меню."""
        filename = self.view.ask_open_filename()
        if not filename:
            return  # Пользователь отменил выбор файла

        try:
            self.model.load_from_ase(filename)
            self._update_view()
            self.view.show_info("Load", f"Successfully loaded from {filename}")
        except Exception as e:
            self.view.show_error("Error", f"Failed to load ASE file: {e}")

    def save_ase(self):
        """Обрабатывает нажатие 'Save'."""
        if not self.model.has_file_path():
            # Если проект еще не сохранялся, перенаправляем на 'Save As...'
            self.save_ase_as_dialog()
            return

        try:
            saved_path = self.model.save_to_ase()
            self._update_view() # Обновляем заголовок, если нужно
            self.view.show_info("Save", f"Saved to {saved_path}")
        except Exception as e:
            self.view.show_error("Error", f"Failed to save ASE file: {e}")

    def save_ase_as_dialog(self):
        """Обрабатывает нажатие 'Save As...'."""
        filename = self.view.ask_save_as_filename(".ase", [("ASE files", "*.ase")])
        if not filename:
            return

        try:
            # Передаем новый путь в модель
            self.model.save_to_ase(filename)
            self._update_view() # Обновляем заголовок окна с новым путем
            self.view.show_info("Save As", f"Saved to {filename}")
        except Exception as e:
            self.view.show_error("Error", f"Failed to save ASE file: {e}")

    def export_json_dialog(self):
        """Обрабатывает нажатие 'Export Json'."""
        filename = self.view.ask_save_as_filename(".json", [("JSON files", "*.json")])
        if not filename:
            return
        try:
            self.model.export_to_json(filename)
            self.view.show_info("Export JSON", f"Exported to {filename}")
        except Exception as e:
            self.view.show_error("Error", f"Failed to export to JSON: {e}")

    # --- Обработчики редактирования ---

    def add_swatch(self):
        """Обрабатывает нажатие 'Add'."""
        # Создаем новый образец по умолчанию
        default_swatch = self.model.create_default_swatch()
        self.model.add_swatch(default_swatch)

        # Обновляем интерфейс, чтобы новый образец появился
        self._update_view()

        # Сразу открываем окно редактирования для нового образца
        new_index = len(self.model.get_swatches()) - 1
        self.edit_swatch(new_index)

    def edit_swatch(self, index: int):
        """Открывает окно редактирования для выбранного образца."""
        try:
            swatch_to_edit = self.model.get_swatch(index)
            # View отвечает за отображение окна, передаем ему нужные данные
            self.view.open_edit_window(index, swatch_to_edit)
        except IndexError:
            self.view.show_error("Error", "Swatch not found. It might have been deleted.")

    def save_edited_swatch(self, index: int, updated_swatch: Swatch):
        self.model.update_swatch(index, updated_swatch)
        self._update_view()

    def delete_swatch(self, index: int):
        self.model.delete_swatch(index)
        self._update_view()
