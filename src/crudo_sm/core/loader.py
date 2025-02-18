# loader.py
# -*- coding: utf-8 -*-
from os.path import (
    join,
    isdir,
    dirname,
    exists,
    basename,
)
import sys
from os import listdir
import importlib.util as pymod
import traceback
from enum import Enum
from crudo_sm.core import shield
from crudo_sm.core import logging
from crudo_sm.settings.common import CONFIG
from crudo_sm.core.module_tracker import ModuleTracker

class MenuAliases(Enum):
    MENU = 'menu_'
    SUB = 'sub_'
    SEP = '_'
    EXC = '__'
    EXT = '.py'
    MAIN_PACK = 'main.py'


def load_scripts_and_directories(directory='', module_source="", depth=6, finalize_logs=False):
    """
    Load Python script modules and collect directories for nested menus.
    Use 'sub_' prefix for directories loaded into the main menu.
    Only directories that start with 'sub_' will be used for further traversal.
    """
    logger = logging.ScriptManagerLogger.get_instance(CONFIG)
    if finalize_logs:
        logger.print_error_buffer()
        logger.write_logs()
        logger.clear_logs()
        return

    exclude_list = {".", "__"}
    scripts = {}
    directories = {}

    if not isdir(directory) or depth <= 0:
        # Return empty if the path is invalid or depth limit is reached
        return scripts, directories

    for item in listdir(directory):
        """ Exclude all files which patern matcher from processing"""
        has_unsafe_imports = "-"
        has_unsafe_decorator = False
        reason = "Initial check"
        error_message = "-"

        if any( item.startswith(pattern) for pattern in exclude_list):
            continue

        item_path = join(directory, item)
        # print("item_path start loop: ", directory, "ITEM: ",item)

        """ Module loading"""
        if item.endswith(MenuAliases.EXT.value) or (
            isdir(item_path) and not item.startswith(MenuAliases.MENU.value)
            and not item.startswith(MenuAliases.SUB.value)
        ):
            try:
                spec = None
                module = None
                is_package_main = False
                item_path_to_check = item_path
                user_module_name = item[:-3] if item.endswith('.py') else item  # use DIR-NAME for packages

                if isdir(item_path):
                    main_path = join(item_path, MenuAliases.MAIN_PACK.value)
                    # print("PACKAGE PATH :", main_path)
                    if exists(main_path) and shield.has_operator_dictionary(main_path):
                        item_path_to_check = main_path
                        is_package_main = True

                        # Package safety check here
                        is_unsafe = shield.UnsafeModuleChecker(item_path)
                        unsafe_findings, (has_unsafe_decorator, unsafe_reason) = is_unsafe.check_package()

                        if unsafe_findings:
                            findings_str = "; ".join(f"{basename(f)}: {i}" for f, i in unsafe_findings.items())
                            if not has_unsafe_decorator:
                                logger.log_module(
                                    module_source,
                                    item,
                                    findings_str,
                                    "Package has unsafe imports",
                                    'Blocked package without @unsafe decorator'
                                )
                                continue
                            else:
                                has_unsafe_imports = findings_str
                                reason = f"@unsafe used ({unsafe_reason})"


                        # Skip the regular unsafe check for packages
                        is_valid, validation_reason, error_message = shield.validate_module(item_path_to_check)
                        if not is_valid:
                            logger.log_module(module_source, item, has_unsafe_imports, validation_reason, error_message)
                            continue
                    else:
                        continue

                elif shield.has_operator_dictionary(item_path):
                    """ Static OPERATOR checking"""
                    # Regular module check (non-package)
                    # print(item_path_to_check)
                    has_unsafe_imports, (has_unsafe_decorator, reason) = shield.check_unsafe_modules(item_path_to_check)
                    if has_unsafe_imports and not has_unsafe_decorator:
                        has_unsafe_imports = f"{str(has_unsafe_imports)[1:-1]}" if has_unsafe_imports else "-"
                        # print(str(has_unsafe_imports))
                        reason = f"@unsafe used ({reason})" if has_unsafe_decorator else "@unsafe not specified"
                        logger.log_module(module_source, item, has_unsafe_imports, reason, 'Blocked module without @unsafe decorator')
                        continue

                    is_valid, validation_reason, error_message = shield.validate_module(item_path_to_check)
                    if not is_valid:
                        logger.log_module(module_source, item, has_unsafe_imports, validation_reason, error_message)
                        continue

                """ Module sys.path constructor"""
                if is_package_main:
                    # Add parent directory (containing the package directory) to sys.path
                    """ OFF for debug purposes"""
                    # package_parent = dirname(item_path)
                    # if package_parent not in sys.path:
                    #     sys.path.insert(0, package_parent)

                    # Create a proper package module name based on location
                    package_name = user_module_name  # This is already the directory name
                    spec = pymod.spec_from_file_location(
                        package_name,
                        item_path_to_check,
                        submodule_search_locations=[
                            item_path,
                        ]  # Enable package imports
                    )
                    module = pymod.module_from_spec(spec)
                    ModuleTracker.track_module(package_name)
                    ModuleTracker.track_module(f"{package_name}.main")

                    # Register both the package and the main module in sys.modules
                    sys.modules[package_name] = module
                    sys.modules[f"{package_name}.main"] = module
                else:
                    # Regular module loading
                    spec = pymod.spec_from_file_location(user_module_name, item_path_to_check)
                    module = pymod.module_from_spec(spec)
                    ModuleTracker.track_module(user_module_name)

                """Add to the module"""
                module.__dict__["unsafe"] = shield.unsafe
                spec.loader.exec_module(module)

                """ Runtime OPERATOR checking"""
                if not hasattr(module, "OPERATOR") or not isinstance(module.OPERATOR, dict):
                    continue

                scripts[user_module_name] = module
                has_unsafe_imports = f"{str(has_unsafe_imports)}" if has_unsafe_imports else "-"
                reason = f"@unsafe used ({reason})" if has_unsafe_decorator else "Safe module"
                logger.log_module(module_source, item, has_unsafe_imports, reason, "-")

            except Exception as e:
                logger.log_module(module_source, item, has_unsafe_imports, reason, traceback.format_exc())
                continue

        elif isdir(item_path):
            """
                Process directory as SUB_menu
            """
            if item.startswith(MenuAliases.SUB.value ) and MenuAliases.SEP.value in item:
                parts = item.split(MenuAliases.SEP.value, 2)
                if len(parts) == 3:
                    _, category, name = parts
                    directories[name] = (item_path, category)

    return scripts, directories
