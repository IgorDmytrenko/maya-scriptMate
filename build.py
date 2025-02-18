#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import os.path
import shutil
import datetime
import subprocess
import tarfile
import json

TIME_STAMP = datetime.datetime.now().strftime("%Y_%m_%d_%H%M")

def get_json_value(path='', object_name='', value_name=''):
    """
    Function to get key names from a JSON config file and return the requested value.
    :param path: Path to the JSON config file.
    :param object_name: The object to look up in the JSON data.
    :param value_name: The value name to extract from the specified object.
    :return: The requested value, or None if not found.
    """
    if not path:
        print("Error: No path provided for the JSON file.")
        return None

    try:
        with open(path, 'r') as jsonfile:
            json_data = json.load(jsonfile)

        # Get the list of objects for the specified key
        object_list = json_data.get(object_name)
        if not object_list or not isinstance(object_list, list):
            print(f"Error: Object '{object_name}' not found or is not a list.")
            return None

        # Assume the first object in the list and try to get the specified value
        for obj in object_list:
            if value_name in obj:
                return obj[value_name]

        print(f"Error: Value '{value_name}' not found in object '{object_name}'.")
        return None

    except (json.JSONDecodeError, FileNotFoundError) as e:
        print(f"Error reading JSON file: {e}")
        return None


def get_git_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return "unknown_branch"

def build() -> None:
    settings_path = "./src/crudo_sm/settings/config.json"
    addon_name = get_json_value(
        path=settings_path,
        object_name="general",
        value_name="addon_name",
    )
    addon_version = get_json_value(
        path=settings_path,
        object_name="general",
        value_name="version",
    )
    branch_name = get_git_branch()
    src_dir = "./src/"
    build_dir = "./builds"
    maya_module_file = "crudo_sm.mod"
    readme_file = "README.md"

    # Create the new build directory
    new_build = os.path.join(build_dir, f"{addon_name}_{addon_version}_{branch_name}_{TIME_STAMP}")
    addon_dir = os.path.join(new_build, addon_name)
    os.makedirs(new_build)

    # Copy the necessary files
    shutil.copyfile(os.path.join(src_dir, maya_module_file), os.path.join(new_build, maya_module_file))
    shutil.copyfile(readme_file, os.path.join(new_build, readme_file))

    # Create a temporary tar archive using git archive
    temp_archive_path = os.path.join(new_build, f"{addon_name}.tar")
    command = [
        "git",
        "archive",
        "--format=tar",
        f"--prefix={addon_name}/",
        "HEAD:src"
    ]
    with open(temp_archive_path, "wb") as temp_archive:
        subprocess.run(command, stdout=temp_archive, check=True)

    # Extract the tar archive to the addon directory
    with tarfile.open(temp_archive_path, "r") as tar:
        tar.extractall(new_build)

    # Clean up the temporary archive
    os.remove(temp_archive_path)

    # Create a zip archive of the new_build directory
    shutil.make_archive(new_build, 'zip', new_build)

    return None

if __name__ == "__main__":
    build()
