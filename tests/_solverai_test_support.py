import contextlib
import importlib.util
import json
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock


PACKAGE_ROOT = Path(__file__).resolve().parents[1] / "solverai"


class FakeDataFrame:
    def __init__(self, data=None, columns=None):
        self.data = list(data or [])
        self.columns = list(columns or [])

    def to_csv(self, buffer, index=False):
        if self.columns:
            buffer.write(",".join(str(column) for column in self.columns))
            buffer.write("\n")

        for row in self.data:
            values = row
            if isinstance(row, dict):
                values = [row.get(column, "") for column in self.columns]
            buffer.write(",".join(str(value) for value in values))
            buffer.write("\n")


class FakeResponse:
    def __init__(self, status_code, text, headers=None):
        self.status_code = status_code
        self.text = text
        self.headers = dict(headers or {})


def json_response(status_code, payload, headers=None):
    return FakeResponse(status_code, json.dumps(payload), headers=headers)


def write_temp_text_file(directory, name, content):
    path = Path(directory) / name
    path.write_text(content, encoding="utf-8")
    return path


def _load_module(module_name, file_path, is_package=False):
    kwargs = {}
    if is_package:
        kwargs["submodule_search_locations"] = [str(PACKAGE_ROOT)]
    spec = importlib.util.spec_from_file_location(
        module_name,
        file_path,
        **kwargs,
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


@contextlib.contextmanager
def solverai_test_environment():
    saved_modules = {}
    names_to_restore = {"requests", "pandas"}
    names_to_restore.update(
        name for name in sys.modules
        if name == "solverai" or name.startswith("solverai.")
    )
    for name in names_to_restore:
        if name in sys.modules:
            saved_modules[name] = sys.modules[name]

    for name in list(sys.modules):
        if name == "solverai" or name.startswith("solverai."):
            del sys.modules[name]

    requests_module = types.ModuleType("requests")
    requests_module.get = Mock(name="requests.get")
    requests_module.post = Mock(name="requests.post")
    requests_module.patch = Mock(name="requests.patch")
    requests_module.delete = Mock(name="requests.delete")

    pandas_module = types.ModuleType("pandas")
    pandas_module.DataFrame = FakeDataFrame

    sys.modules["requests"] = requests_module
    sys.modules["pandas"] = pandas_module

    try:
        package = _load_module(
            "solverai",
            PACKAGE_ROOT / "__init__.py",
            is_package=True,
        )
        yield SimpleNamespace(
            package=package,
            requests=requests_module,
            pandas=pandas_module,
            module=lambda name: sys.modules[f"solverai.{name}"],
        )
    finally:
        for name in list(sys.modules):
            if name == "solverai" or name.startswith("solverai."):
                del sys.modules[name]
        sys.modules.pop("requests", None)
        sys.modules.pop("pandas", None)
        for name, module in saved_modules.items():
            sys.modules[name] = module
