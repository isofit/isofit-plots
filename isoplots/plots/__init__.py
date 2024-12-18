import importlib
import pkgutil

# Auto-discovers the plot scripts
Modules = {
    name: importlib.import_module(f".{name}", __spec__.name)
    for imp, name, _ in pkgutil.iter_modules(__path__)
}
del Modules["template"]
