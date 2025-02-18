#context_tab.py
"""
interface builder
"""

# python modules
import os
from os.path import join, isdir
import sys
import types
from pathlib import Path

from crudo_sm.core.module_tracker import ModuleTracker

# sys.path.insert(0, os.path.abspath(join(os.path.dirname(__file__), "..")))
# Own modules
from crudo_sm.utils import string_utils, file_utils
from crudo_sm.core import loader
from crudo_sm.user_interface import preferences, buttons
from crudo_sm.settings.common import CONFIG

# Import Maya modules
import maya.cmds as cmds

# Global variables to keep track of previous paths and menu directories
previous_network_path = None
previous_local_path = None
previous_local_menu_dirs = set()
previous_network_menu_dirs = set()


def get_icon(icon_title="/idtools.png"):
    """Return icon folder"""
    icon_dir = (
        os.path.normpath(
            join(os.path.abspath(join(os.path.dirname(__file__), "..")), "icon")
        )
        + icon_title
    )
    return icon_dir


def clear_menu_items(menu_name):
    """
    Clear all items from the given menu without deleting the menu itself.
    """
    if cmds.menu(menu_name, exists=True):
        items = cmds.menu(menu_name, query=True, itemArray=True) or []
        for item in items:
            cmds.deleteUI(item, menuItem=True)


def rescan_and_update():
    """
    Rescan the script paths, reload the configuration, and update
    all context menus.
    """
    # Print what we racking before cleanup
    # ModuleTracker.print_tracked()
    # Clean up modules
    ModuleTracker.clean_tracked_modules()
    # Force Python to do garbage collection
    import gc
    gc.collect()
    # Reload config and rebuild menus
    CONFIG.reload()
    ui_context_menu(force_update=True)
    cmds.warning("All User modules has been updated")

def add_top_level_menu(menu_name, menu_label, parent="MayaWindow"):
    """
    Create or update a top-level menu in Maya.
    """
    if not cmds.menu(menu_name, exists=True):
        cmds.menu(menu_name, label=menu_label, parent=parent, tearOff=True)
    return f"{parent}|{menu_name}"


def add_submenu(parent, dir_name, dir_path, script_location, source, depth=4):
    """
    Create a submenu under the specified parent and populate it with scripts.
    """
    if depth <= 0:
        return

    submenu = cmds.menuItem(
        label=dir_name.replace("_", " "), parent=parent, subMenu=True, tearOff=True
    )
    scripts, directories = loader.load_scripts_and_directories(
        directory=dir_path, module_source=source, depth=depth - 1, finalize_logs=False
    )

    # Organize and add scripts
    categories = {}
    for script_name, module in scripts.items():
        category = module.OPERATOR.get("category", "Uncategorized")
        categories.setdefault(category, []).append((script_name, module))

    for category, script_list in sorted(categories.items()):
        cmds.menuItem(parent=submenu, divider=True, dividerLabel=category)
        for script_name, module in script_list:
            add_item(submenu, script_name, module, script_location)

    # Add nested submenus for directories
    for sub_dir_name, (sub_dir_path, sub_category) in directories.items():
        if sub_category:
            cmds.menuItem(parent=submenu, divider=True, dividerLabel=sub_category)
        add_submenu(submenu, sub_dir_name, sub_dir_path, script_location, source, depth - 1)


def add_item(parent: str, name:str , module: types.ModuleType, menu_location: str="") -> None:
    """ Create a menu item for a script module under the specified parent.
    Args:
        parent    (str): "MayaWindow|{MY_MENU}" name of menu parent to >
        name      (str): Item name as default argument if get("name") is None
        module (module): Which contain module context like OPERATOR etc.

    return:
        None  
    """
    script_label = module.OPERATOR.get("name", name)
    
    if not menu_location:
        icons_dir = Path()
    else:
        icons_dir = Path(menu_location) / "icons"
    
    if icons_dir.exists():
        icon = str(icons_dir / module.OPERATOR.get("icon", ""))
    else:
        icon = ""

    # print("\nModule name: ", script_label)
    # print("----Icon path: ", icon, "\n----Icons dir: ", icons_dir)    
    cmds.menuItem(
        label=script_label,
        i=icon, 
        parent=parent, 
        c=lambda *args, mod=module: mod.execute(),
    )


def create_top_level_menu(source, directory, paths_changed):
    """
    Create or update top-level menus based on the given directory and source.
    """
    global previous_local_menu_dirs, previous_network_menu_dirs
    current_menu_dirs = set()

    # print(f"\n\n{source} START.previous_menu_dirs: ",
    #       previous_local_menu_dirs if source == "Local" else previous_network_menu_dirs)

    if os.path.isdir(directory):
        for item in os.listdir(directory):
            item_path = join(directory, item)
            if isdir(item_path) and item.startswith("menu_"):
                menu_name = string_utils.format_menu_name(item.lstrip("menu_"))
                menu_label = item.lstrip("menu_").replace("_", " ")
                # print(f"Menu label: {menu_label}, Menu name: {menu_name}")
                current_menu_dirs.add(menu_name)

                menu_parent = add_top_level_menu(menu_name, menu_label)
                clear_menu_items(menu_name)

                scripts, directories = loader.load_scripts_and_directories(
                    directory=item_path, module_source=source, finalize_logs=False
                )

                # Add categorized scripts and submenus
                categories = {}
                for script_name, module in scripts.items():
                    category = module.OPERATOR.get("category", "Uncategorized")
                    categories.setdefault(category, []).append((script_name, module))

                # Assign category for submenu
                for dir_name, (dir_path, category) in directories.items():
                    categories.setdefault(string_utils.convert_to_title_case(category), []).append((dir_name, dir_path))

                for category, script_list in sorted(categories.items()):
                    cmds.menuItem(
                        parent=menu_parent, divider=True, dividerLabel=category
                    )
                    for name, item in script_list:
                        if isinstance(item, str):  # Directory
                            add_submenu(menu_parent, name, item, directory, source, depth=4)
                        else:  
                            # Script module
                            add_item(menu_parent, name, item, directory)


    menu_changed = previous_network_menu_dirs != current_menu_dirs
    # Determine which menus have been removed
    if paths_changed or menu_changed:
        previous_dirs = (
            previous_local_menu_dirs
            if source == "Local"
            else previous_network_menu_dirs
        )
        removed_menus = previous_dirs - current_menu_dirs
        for menu_name in removed_menus:
            if cmds.menu(menu_name, exists=True):
                cmds.deleteUI(menu_name)

        # Update the correct previous menu set
        if source == "Local":
            previous_local_menu_dirs = current_menu_dirs
        else:
            previous_network_menu_dirs = current_menu_dirs


def ui_context_menu(force_update=False):
    global CONFIG, previous_network_path, previous_local_path
    CONFIG.reload()

    # # #
    # Get current paths
    local_scripts_path = file_utils.path_existance(
        CONFIG.get_local_param("userScripts", "local_path")
    )
    network_scripts_path = CONFIG.get_local_param("userScripts", "network_path")

    # # #
    # Determine if paths have changed or force_update is True
    local_paths_changed = local_scripts_path != previous_local_path or force_update
    network_paths_changed = (
        network_scripts_path != previous_network_path or force_update
    )

    # # #
    # Update previous paths
    previous_local_path = local_scripts_path
    previous_network_path = network_scripts_path

    # # #
    # Always create the default menu for settings and updates
    menu_label = CONFIG.get_core_param("general", "title")
    context_menu_name = "ScriptMateDefaultContextMenu"

    if not cmds.menu(context_menu_name, exists=True):
        cmds.menu(
            context_menu_name, label=menu_label, parent="MayaWindow", tearOff=True
        )

    # # #
    # Clear existing menu items
    clear_menu_items(context_menu_name)

    # Load scripts and directories for the Default menu
    scripts, directories = loader.load_scripts_and_directories(
        directory=local_scripts_path, module_source="Local", finalize_logs=False
    )

    # Parrent menu to the Maya main Window
    currParent = f"MayaWindow|{context_menu_name}"
    categories = {}
    for script_name, module in scripts.items():
        category = module.OPERATOR.get("category", "Uncategorized")
        if category not in categories:
            categories[category] = []
        categories[category].append((script_name, module))

    # Include top-level 'sub_' directories in the main menu
    for dir_name, (dir_path, category) in directories.items():
        if category not in categories:
            categories[category] = []
        categories[category].append((dir_name, dir_path))

    # Create menu items for each category
    for category, script_list in sorted(categories.items()):
        cmds.menuItem(parent=currParent, divider=True, dividerLabel=category)
        for name, item in script_list:
            if isinstance(item, str):  # If item is a directory path
                add_submenu(currParent, name, item, local_scripts_path, "Local",  depth=4)
            else:  
                # If item is a script module
                # print("Local script PATH: ", local_scripts_path)
                add_item(currParent, name, item, local_scripts_path)

    # Add "Help" sub menu
    help_menu = "HelpMenu"
    cmds.menuItem(parent=currParent, divider=True, dividerLabel="Help")
    cmds.menuItem(
        help_menu,
        label="Help",
        parent=currParent,
        image=get_icon("/help.svg"),
        subMenu=True,
        tearOff=True,
    )
    help_parent = f"MayaWindow|{context_menu_name}|{help_menu}"
    cmds.menuItem(
        "documentation",
        label="Documentation",
        image=get_icon("/documentation.svg"),
        parent=help_parent,
        c=lambda *args: buttons.WebButton(
            CONFIG.get_core_param("links", "documentation")
        ).web_button(),
    )
    # Add "Settings" and "Update" options
    cmds.menuItem(parent=currParent, divider=True, dividerLabel="Settings")
    cmds.menuItem(
        "SettingsMenu",
        label="Settings",
        parent=currParent,
        image=get_icon("/settings.svg"),
        subMenu=True,
        tearOff=True,
    )
    preferencesParent = f"MayaWindow|{context_menu_name}|SettingsMenu"
    cmds.menuItem(
        "preferences",
        label="Preferences",
        image=get_icon("/settings.svg"),
        parent=preferencesParent,
        c=lambda *args: preferences.show(),
    )
    cmds.menuItem(
        "update_scripts",
        label="Update Scripts",
        image=get_icon("/update.svg"),
        parent=preferencesParent,
        c=lambda *args: rescan_and_update(),
    )

    # Create menus for Local and Network scripts
    create_top_level_menu("Local", local_scripts_path, local_paths_changed)
    create_top_level_menu("Network", network_scripts_path, network_paths_changed)
    loader.load_scripts_and_directories(finalize_logs=True)


def add_menus():
    print("crudo_usm: context menu load starting")
    ui_context_menu(force_update=True)
    print("crudo_usm: context menu load success")
