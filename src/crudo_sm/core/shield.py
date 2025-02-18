# shield.py
import ast
import py_compile
import os
from crudo_sm.settings.common import CONFIG

def unsafe(func=None, reason=None):
    def decorator(f):
        f._is_unsafe = True
        f._unsafe_reason = reason or "No reason provided."
        return f

    if func is None:
        return decorator
    else:
        return decorator(func)


def validate_module(file_path):
    """
    Validate a Python module for syntax errors and unsafe imports.
    """
    # Check for syntax errors using py_compile
    try:
        py_compile.compile(file_path, doraise=True)
    except (py_compile.PyCompileError, IndentationError, SyntaxError, NameError) as e:
        return False, "Syntax Error", str(e)

    # Additional static analysis using AST to catch indentation errors
    try:
        with open(file_path, "r") as f:
            ast.parse(f.read(), filename=file_path)
    except (IndentationError, SyntaxError, NameError) as e:
        return False, "Syntax Error", str(e)
    return True, "Safe module", None


class UnsafeModuleChecker:
    UNSAFE_MODULES = CONFIG.get_core_param("security", "pymodules")
    
    def __init__(self, file_path):
        self.file_path = file_path
        self.unsafe_findings = {}
        self.has_unsafe_decorator = False
        self.decorator_reason = None

    def check_file(self):
        """
        Original check_unsafe_modules functionality.
        Returns tuple of (unsafe_imports, decorator_info)
        """
        with open(self.file_path, "r") as f:
            tree = ast.parse(f.read(), filename=self.file_path)

        has_unsafe_imports = []
        unsafe_decorator_info = (False, None)

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in self.UNSAFE_MODULES:
                        has_unsafe_imports.append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module in self.UNSAFE_MODULES:
                    has_unsafe_imports.append(node.module)

            elif isinstance(node, ast.FunctionDef):
                if node.decorator_list:
                    for decorator in node.decorator_list:
                        if isinstance(decorator, ast.Name) and decorator.id == "unsafe":
                            unsafe_decorator_info = (True, "No reason provided")
                        elif (isinstance(decorator, ast.Call) and
                              isinstance(decorator.func, ast.Name) and
                              decorator.func.id == "unsafe"):
                            reason = "No reason provided"
                            for keyword in decorator.keywords:
                                if keyword.arg == "reason":
                                    if isinstance(keyword.value, ast.Str):
                                        reason = keyword.value.s
                                    break
                            unsafe_decorator_info = (True, reason)

        return has_unsafe_imports, unsafe_decorator_info

    def check_package(self):
        """
        Check package and all its modules for unsafe imports.
        Also checks for @unsafe decorator in main.py
        Returns (unsafe_findings, decorator_info)
        """
        main_path = os.path.join(self.file_path, "main.py")

        # First check main.py for @unsafe decorator
        if os.path.exists(main_path):
            main_unsafe_imports, main_decorator_info = UnsafeModuleChecker(main_path).check_file()
            self.has_unsafe_decorator = main_decorator_info[0]
            self.decorator_reason = main_decorator_info[1]

        def scan_directory(dir_path):
            for item in os.listdir(dir_path):
                item_path = os.path.join(dir_path, item)

                if item.endswith('.py'):
                    checker = UnsafeModuleChecker(item_path)
                    unsafe_imports, _ = checker.check_file()
                    if unsafe_imports:
                        if not self.has_unsafe_decorator:
                            # Only track as unsafe if no @unsafe decorator in main.py
                            self.unsafe_findings[item_path] = unsafe_imports
                        else:
                            # If we have @unsafe, just record for information
                            self.unsafe_findings[item_path] = unsafe_imports

                elif os.path.isdir(item_path) and not item.startswith('__'):
                    scan_directory(item_path)

        if os.path.isfile(self.file_path):
            return self.check_file()
        else:
            scan_directory(self.file_path)
            return self.unsafe_findings, (self.has_unsafe_decorator, self.decorator_reason)


# Maintain backward compatibility
# - wrapper for the legacy call
def check_unsafe_modules(file_path):
    checker = UnsafeModuleChecker(file_path)
    return checker.check_file()


def has_operator_dictionary(file_path):
    """
    Check if a Python file defines a dictionary named 'OPERATOR'.
    """
    with open(file_path, "r") as f:
        tree = ast.parse(f.read(), filename=file_path)

    for node in ast.walk(tree):
        # Look for a top-level assignment to 'OPERATOR' that is a dictionary
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "OPERATOR":
                    if isinstance(node.value, ast.Dict):  # Check if it's a dictionary
                        return True
    return False
