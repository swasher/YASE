import swatch
import json
from .common_data_classes import Swatch, ColorMode, SwatchType
from models import Color

# deprecated
# # Эти функции теперь являются частью логики модели
# def create_swatch_from_data(data: dict, is_normalized: bool) -> Swatch:
#     """Создает объект Swatch из словаря данных."""
#     return Swatch(
#         name=data['name'],
#         type=SwatchType(data['type']),
#         mode=ColorMode(data['data']['mode']),
#         color=Color.create_from_data(data['data'], is_normalized=is_normalized)
#     )

# deprecated
# def swatch_to_data(swatch: Swatch) -> dict:
#     """Преобразует объект Swatch в словарь для сохранения."""
#     return {
#         'name': swatch.name,
#         'type': swatch.type.value,
#         'data': swatch.color.to_data()
#     }


class SwatchModel:
    """
    Модель данных. Управляет списком образцов и операциями с файлами.
    Не зависит от UI (Tkinter).
    """

    def __init__(self):
        self.swatches: list[Swatch] = []
        self.file_path: str | None = None

    # --- Методы-помощники (теперь инкапсулированы в классе) ---

    @staticmethod
    def _create_swatch_from_data(data: dict, is_normalized: bool) -> Swatch:
        """Создает объект Swatch из словаря данных."""
        return Swatch(
            name=data['name'],
            type=SwatchType(data['type']),
            mode=ColorMode(data['data']['mode']),
            color=Color.create_from_data(data['data'], is_normalized=is_normalized)
        )

    @staticmethod
    def _swatch_to_data(swatch: Swatch) -> dict:
        """Преобразует объект Swatch в словарь для сохранения."""
        return {
            'name': swatch.name,
            'type': swatch.type.value,
            'data': swatch.color.to_data()
        }

    # --- Основной API для Контроллера ---

    def get_swatches(self) -> list[Swatch]:
        """Возвращает список всех образцов."""
        return self.swatches

    def get_swatch(self, index: int) -> Swatch:
        """Возвращает образец по индексу."""
        return self.swatches[index]

    def load_from_ase(self, filename: str) -> None:
        """Загружает данные из ASE файла. При ошибке выбрасывает исключение."""
        raw_swatches = swatch.parse(filename)
        self.swatches = [self._create_swatch_from_data(raw, is_normalized=True) for raw in raw_swatches]
        self.file_path = filename

    def save_to_ase(self, filename: str | None = None) -> str:
        """Сохраняет данные в ASE файл. Возвращает путь к файлу."""
        path_to_save = filename or self.file_path
        if not path_to_save:
            raise ValueError("File path is not specified for saving.")

        raw_swatches = [self._swatch_to_data(sw) for sw in self.swatches]
        swatch.write(raw_swatches, path_to_save)
        self.file_path = path_to_save
        return path_to_save

    def export_to_json(self, filename: str) -> None:
        """Экспортирует данные в JSON."""
        data_to_export = [self._swatch_to_data(sw) for sw in self.swatches]
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(data_to_export, f, ensure_ascii=False, indent=2)

    def add_swatch(self, swatch: Swatch) -> None:
        """Добавляет новый образец в список."""
        self.swatches.append(swatch)

    def update_swatch(self, index: int, updated_swatch: Swatch) -> None:
        """Обновляет существующий образец."""
        if 0 <= index < len(self.swatches):
            self.swatches[index] = updated_swatch

    def delete_swatch(self, index: int) -> None:
        """Удаляет образец по индексу."""
        if 0 <= index < len(self.swatches):
            del self.swatches[index]

    # --- НОВЫЕ МЕТОДЫ, НЕОБХОДИМЫЕ КОНТРОЛЛЕРУ ---

    def get_file_path(self) -> str | None:
        """Возвращает текущий путь к файлу."""
        return self.file_path

    def has_file_path(self) -> bool:
        """Проверяет, был ли файл уже сохранен (есть ли у него путь)."""
        return self.file_path is not None

    def create_default_swatch(self) -> Swatch:
        """
        Создает и возвращает образец по умолчанию (черный цвет).
        Эта логика теперь находится здесь, а не в контроллере.
        """
        default_data = {
            "name": "New Swatch",
            "type": "Spot",
            "data": {"mode": "RGB", "values": [0, 0, 0]}
        }
        # is_normalized=False, т.к. значения [0,0,0] - это 0-255, а не 0-1
        return self._create_swatch_from_data(default_data, is_normalized=False)

    def clear(self):
        """Очищает текущий список образцов и сбрасывает путь к файлу."""
        self.swatches.clear()
        self.file_path = None
