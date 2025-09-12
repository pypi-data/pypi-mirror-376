import importlib
import os
import pkgutil


def recursive_import(package_name, package_path):
    for _, name, ispkg in pkgutil.iter_modules([package_path]):
        full_name = f"{package_name}.{name}"
        _ = importlib.import_module(full_name)
        if ispkg:
            sub_path = os.path.join(package_path, name)
            recursive_import(full_name, sub_path)
