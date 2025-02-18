"""
    File manipulation utils library
"""
from pathlib import Path
import shutil

def path_existance(app_path: str) -> str:
    """
    Creates a directory for the plugin if it doesn't exist and returns the path.
    """
    plugin_path = Path(app_path).expanduser().resolve()
    plugin_path.parent.mkdir(parents=True, exist_ok=True)
    return str(plugin_path)

def copy_file(src_path, dest_path, is_exist) -> None:
    """
    Ensures the directory for the destination file exists, creates it if necessary,
    and then copies the file from the source to the destination.
    """
    # Ensure the parent directory of the destination path exists
    dest_directory = Path(dest_path).expanduser().resolve()
    dest_directory.parent.mkdir(parents=True, exist_ok=True)
    if is_exist and Path(dest_path).exists():
        pass
    else:
        try:
            shutil.copy(src_path, str(dest_directory / Path(src_path).name))
            # print(f"File copied from {src_path} to {dest_path}")
        except Exception as e:
            print(f"Error copying file: {e}")
