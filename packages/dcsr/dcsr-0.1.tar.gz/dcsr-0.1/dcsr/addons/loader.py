import importlib.util
import pathlib
import sys

class AddonLoader:
    def __init__(self, orchestrator=None):
        self.addons = {}
        self.orchestrator = orchestrator

    def load_addon(self, path: str, name: str = None):
        path = pathlib.Path(path)
        addon_name = name or path.stem
        spec = importlib.util.spec_from_file_location(addon_name, path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[addon_name] = module
        spec.loader.exec_module(module)
        self.addons[addon_name] = module

        if self.orchestrator and hasattr(module, "register"):
            module.register(self.orchestrator)

        return module

    def call_addon(self, addon_name: str, func: str, *args, **kwargs):
        addon = self.addons.get(addon_name)
        if not addon:
            raise ValueError(f"Addon '{addon_name}' not loaded")
        if not hasattr(addon, func):
            raise AttributeError(f"Addon '{addon_name}' has no function '{func}'")
        return getattr(addon, func)(*args, **kwargs)
