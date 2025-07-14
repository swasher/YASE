from abc import ABC, abstractmethod
from dataclasses import dataclass
from colormath.color_objects import LabColor, sRGBColor, CMYKColor
from colormath.color_conversions import convert_color
from typing import List, Union, Type
from classes import ColorMode

class Color(ABC):
    colormath_class = None  # будет переопределен в подклассах

    @abstractmethod
    def to_normalized(self) -> List[float]:
        """Конвертирует значения в нормализованный формат [0-1]"""
        pass

    @abstractmethod
    def to_user(self) -> List[float]:
        """Конвертирует значения в пользовательский формат"""
        pass

    @abstractmethod
    def to_colormath(self):
        """Возвращает объект colormath для конвертации"""
        pass

    @classmethod
    @abstractmethod
    def from_colormath(cls, color):
        """Создает объект цвета из colormath объекта"""
        pass

    @classmethod
    @abstractmethod
    def get_metadata(cls) -> tuple[list[str], list[tuple[float, float]]]:
        """Инкапсулируем метаданные о названиях каналов и диапазоне, в котором может меняться числовое значение канала (со стороны юзера)"""
        pass

    def convert_to(self, target_mode: ColorMode) -> 'Color':
        """Конвертирует цвет в другой формат"""
        # Определяем класс цвета по целевому режиму
        target_class = {
            ColorMode.RGB: ColorRGB,
            ColorMode.CMYK: ColorCMYK,
            ColorMode.LAB: ColorLAB
        }[target_mode]

        # Используем colormath для конвертации
        source_colormath = self.to_colormath()
        data_from_colormath = convert_color(source_colormath, target_class.colormath_class)

        # Создаем новый объект нужного типа
        return target_class.from_colormath(data_from_colormath)

    @staticmethod
    def create_from_data(data: dict, is_normalized: bool) -> 'Color':
        """
        Создает объект Color из словаря данных.
        is_normalized: указывает, являются ли значения в data['values']
                       нормализованными (0-1) или пользовательскими (0-255 и т.д.).
        """
        values = data['values']
        # Убираем "масло масляное" - передаем строку напрямую
        color_class = Color.get_class_by_mode(data['mode'])

        # Используем переданный флаг
        return color_class(*values, is_normalized=is_normalized)

    def to_data(self) -> dict:
        """Преобразует объект Color в словарь"""
        return {
            'mode': self.mode.value,
            'values': self.to_normalized()
        }

    @classmethod
    def get_class_by_mode(cls, mode: Union[str, ColorMode]) -> Type['Color']:
        """
        Фабричный метод для получения класса цвета по его режиму.
        Принимает строку ('RGB') или член Enum (ColorMode.RGB).
        """
        # 1. Преобразуем строку в Enum, если необходимо
        if isinstance(mode, str):
            try:
                mode = ColorMode(mode.upper())
            except ValueError:
                raise ValueError(f"Неизвестный цветовой режим: {mode}")

        # 2. Используем словарь для поиска класса
        color_class_map = {
            ColorMode.RGB: ColorRGB,
            ColorMode.CMYK: ColorCMYK,
            ColorMode.LAB: ColorLAB
        }

        # 3. Возвращаем класс или вызываем ошибку, если его нет в карте
        found_class = color_class_map.get(mode)
        if not found_class:
            # Эта ошибка возникнет, если ColorMode расширится, а карта - нет
            raise NotImplementedError(f"Класс для режима {mode.value} не реализован.")

        return found_class

    def to_hex(self) -> str:
        """Возвращает HEX-представление цвета, используя RGB"""
        try:
            rgb_color = self.convert_to(ColorMode.RGB)
            rgb = rgb_color.to_user()
            return '#{:02x}{:02x}{:02x}'.format(*[int(round(c)) for c in rgb])
        except Exception:
            return "#888888"


class ColorRGB(Color):
    mode = ColorMode.RGB
    colormath_class = sRGBColor

    def __init__(self, r: float, g: float, b: float, is_normalized: bool = False):
        if is_normalized:
            self._r, self._g, self._b = r, g, b
        else:
            self._r = r / 255.0
            self._g = g / 255.0
            self._b = b / 255.0

    def to_normalized(self) -> List[float]:
        return [self._r, self._g, self._b]

    def to_user(self) -> List[float]:
        return [round(self._r * 255), round(self._g * 255), round(self._b * 255)]

    def to_colormath(self) -> sRGBColor:
        return sRGBColor(self._r, self._g, self._b)


    # @classmethod
    # def from_colormath(cls, color: sRGBColor) -> 'ColorRGB':
    #     return cls(color.rgb_r, color.rgb_g, color.rgb_b, is_normalized=True)

    # @classmethod
    # def from_colormath(cls, color: sRGBColor) -> 'ColorRGB':
    #     """
    #     Создает наш объект из объекта colormath, принудительно
    #     ограничивая значения в диапазоне [0.0, 1.0] для обработки
    #     цветов, выходящих за пределы охвата sRGB.
    #     """
    #     # Ограничиваем каждое значение: оно не может быть меньше 0.0 и больше 1.0
    #     clamped_r = max(0.0, min(color.rgb_r, 1.0))
    #     clamped_g = max(0.0, min(color.rgb_g, 1.0))
    #     clamped_b = max(0.0, min(color.rgb_b, 1.0))
    #
    #     return cls(clamped_r, clamped_g, clamped_b, is_normalized=True)

    # Новая, правильная версия с использованием API colormath
    @classmethod
    def from_colormath(cls, color: sRGBColor) -> 'ColorRGB':
        """
        Создает наш объект из объекта colormath, используя встроенную
        в библиотеку возможность получения значений, ограниченных
        цветовым охватом sRGB (gamut clamping).
        """
        # Используем .clamped_rgb_... атрибуты, которые гарантированно
        # возвращают значения в диапазоне [0.0, 1.0].
        return cls(color.clamped_rgb_r, color.clamped_rgb_g, color.clamped_rgb_b, is_normalized=True)

    @classmethod
    def get_metadata(cls) -> tuple[list[str], list[tuple[float, float]]]:
        return ["R", "G", "B"], [(0, 255)] * 3

class ColorLAB(Color):
    mode = ColorMode.LAB
    colormath_class = LabColor

    def __init__(self, l: float, a: float, b: float, is_normalized: bool):
        if is_normalized:
            self._l, self._a, self._b = l, a, b
        else:
            self._l, self._a, self._b = l / 100, a, b

    def to_normalized(self) -> List[float]:
        return [self._l, self._a, self._b]

    def to_user(self) -> List[float]:
        return [round(self._l * 100), round(self._a), round(self._b)]

    def to_colormath(self) -> LabColor:
        return LabColor(self._l * 100, self._a, self._b)

    @classmethod
    def from_colormath(cls, color: LabColor) -> 'ColorLAB':
        return cls(color.lab_l / 100, color.lab_a, color.lab_b, is_normalized=True)

    @classmethod
    def get_metadata(cls) -> tuple[list[str], list[tuple[float, float]]]:
        return ["L", "a", "b"], [(0, 100), (-128, 127), (-128, 127)]

class ColorCMYK(Color):
    mode = ColorMode.CMYK
    colormath_class = CMYKColor

    def __init__(self, c: float, m: float, y: float, k: float, is_normalized: bool = False):
        if is_normalized:
            self._c, self._m, self._y, self._k = c, m, y, k
        else:
            self._c = c / 100.0
            self._m = m / 100.0
            self._y = y / 100.0
            self._k = k / 100.0

    def to_normalized(self) -> List[float]:
        return [self._c, self._m, self._y, self._k]

    def to_user(self) -> List[float]:
        return [round(v * 100) for v in [self._c, self._m, self._y, self._k]]

    def to_colormath(self) -> CMYKColor:
        return CMYKColor(self._c, self._m, self._y, self._k)

    @classmethod
    def get_metadata(cls) -> tuple[list[str], list[tuple[float, float]]]:
        return ["C", "M", "Y", "K"], [(0, 100)] * 4

    @classmethod
    def from_colormath(cls, color: CMYKColor) -> 'ColorCMYK':
        return cls(color.cmyk_c, color.cmyk_m, color.cmyk_y, color.cmyk_k, is_normalized=True)
