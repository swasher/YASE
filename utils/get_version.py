import os
import sys
import tomllib


def get_version_from_pyproject(filename="pyproject.toml") -> str:
    if hasattr(sys, "_MEIPASS"):
        # Работаем в PyInstaller-сборке
        path = os.path.join(sys._MEIPASS, filename)
    else:
        # Работаем в исходном виде (например, при разработке)
        base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        path = os.path.join(base_path, filename)

    with open(path, "rb") as f:
        data = tomllib.load(f)
    return data["project"]["version"]
