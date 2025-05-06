""" TIA Portal configuration module. This module is used to store the TIA Portal version. The TIA Portal version is stored in the config.ini file in the user's home directory. The config.ini file is created if it does not exist. The default version is V17. The user can change the version by calling the set_version function.

    Attributes:
        DATA_PATH (str): Path to the data directory.
        CONFIG_PATH (str): Path to the config.ini file.
        VERSION (TIAVersion): TIA Portal version.
"""

import configparser
import os
import platform
from pathlib import Path
import re

from tia_portal.version import TiaVersion

DATA_PATH = os.path.join(os.path.expanduser("~"), ".tia_portal")
CONFIG_PATH = os.path.join(DATA_PATH, "config.ini")
VERSION = TiaVersion.V19  # Default to V19 instead of V15_1

def normalize_path(path):
    """Normalize a path.

    Parameters:
        path (str): Path to normalize.

    Returns:
        str: Normalized path.
    """
    if not path:
        return path
    return path

def get_data_path():
    """Get the data path.

    Returns:
        str: Data path.
    """
    return DATA_PATH

def load() -> None:
    """Load the TIA Portal version from the config.ini file. If the config.ini file does not exist, it is created. If the version is not specified in the config.ini file, the default version is used."""
    config = configparser.ConfigParser()

    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)

    if not os.path.exists(CONFIG_PATH):
        config["DEFAULT"] = {
            "version": "V19",
        }
        config["USER"] = {}
        config.write(open(CONFIG_PATH, "w", encoding="utf-8"))

    config.read(CONFIG_PATH)
    global VERSION
    VERSION = (
        TiaVersion[config["DEFAULT"]["version"]]
        if config["USER"].get("version") is None
        else TiaVersion[config["USER"]["version"]]
    )

    print(f"TIA Portal version set to: {VERSION.name}")

def set_version(version: TiaVersion) -> None:
    """Set the TIA Portal version.

    Parameters:
        version (TIAVersion): TIA Portal version.
    """
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)

    config["USER"]["version"] = version.name
    with open(CONFIG_PATH, "w", encoding="utf-8") as configfile:
        config.write(configfile)
