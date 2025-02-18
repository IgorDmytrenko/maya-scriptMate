import sys

class ModuleTracker:
    """
        Flushing modules cache from memmory
        when we updating our menus
    """
    _loaded_modules = set()

    @classmethod
    def track_module(cls, module_name):
        # print(f"FROM ModuleTracker: ", module_name)
        cls._loaded_modules.add(module_name)

    @classmethod
    def clean_tracked_modules(cls):
        # First remove all modules we tracking
        for module_name in cls._loaded_modules:
            if module_name in sys.modules:
                # Remove both the main module and any submodules
                to_remove = [
                    name for name in sys.modules
                    if name == module_name or name.startswith(f"{module_name}.")
                ]
                for name in to_remove:
                    sys.modules.pop(name, None)
                    # print(f"    Removed module: {name}")

        cls._loaded_modules.clear()

    @classmethod
    def print_tracked(cls):
        print("\nTracked modules:")
        for mod in cls._loaded_modules:
            print(f"- {mod}")
