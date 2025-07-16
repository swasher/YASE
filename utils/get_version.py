import tomllib  # встроен в Python 3.11+


def get_version_from_pyproject(path="pyproject.toml") -> str:
    # with open(path, "rb") as f:
    #     data = tomllib.load(f)
    # return data["project"]["version"]
    return '1.1.1' # пока заглушка
