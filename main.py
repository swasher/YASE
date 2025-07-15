import os
import sys
import configparser

from views import SwatchEditorView
from controllers import SwatchController
from models import SwatchModel

def get_initial_file_path() -> str | None:
    """Определяет путь к файлу для загрузки на старте из config.ini."""
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    try:
        config_path = os.path.join(application_path, 'config.ini')
        config = configparser.ConfigParser()
        if config.read(config_path):
            config_swatch_name = config.get('Settings', 'swatch_file', fallback=None)
            if config_swatch_name:
                potential_path = os.path.join(application_path, config_swatch_name)
                if os.path.exists(potential_path):
                    return potential_path
    except configparser.Error as e:
        print(f"Error reading config file: {e}")

    return None


if __name__ == '__main__':
    # Шаг 1: Создаем все компоненты MVC
    model = SwatchModel()
    view = SwatchEditorView()  # Создаем View без контроллера

    # Шаг 2: Создаем Контроллер, передавая ему уже созданные Модель и Представление
    controller = SwatchController(model=model, view=view)

    # Шаг 3: Теперь, когда Контроллер готов, связываем его с Представлением.
    # Это позволит View завершить свою настройку (например, создать меню).
    view.set_controller(controller)

    # Шаг 4: Запускаем начальную загрузку через контроллер
    initial_file = get_initial_file_path()
    controller.run_initial_load(initial_file)

    # Шаг 5: Запускаем главный цикл приложения
    view.mainloop()
