""" TIA Portal configuration module. This module is used to store the TIA Portal version. The TIA Portal version is stored in the config.ini file in the user's home directory. The config.ini file is created if it does not exist. The default version is V17. The user can change the version by calling the set_version function.

    Attributes:
        DATA_PATH (str): Path to the data directory.
        CONFIG_PATH (str): Path to the config.ini file.
        VERSION (TIAVersion): TIA Portal version.
        IS_WSL (bool): Whether the current environment is WSL.

"""

import configparser
import os
import platform
import subprocess
from pathlib import Path
import re

from tia_portal.version import TiaVersion


# Detect if running in WSL
def detect_wsl():
    """Detect if running in WSL environment.

    Returns:
        bool: True if running in WSL, False otherwise.
    """
    # Method 1: Check /proc/version
    try:
        with open("/proc/version", "r") as f:
            if "microsoft" in f.read().lower():
                return True
    except:
        pass

    # Method 2: Check for WSL environment variable
    if os.environ.get("WSL_DISTRO_NAME"):
        return True

    # Method 3: Check if platform is Linux and 'microsoft' is in the release
    if platform.system() == "Linux":
        try:
            with open("/proc/sys/kernel/osrelease", "r") as f:
                if "microsoft" in f.read().lower():
                    return True
        except:
            pass

    return False


IS_WSL = detect_wsl()
print(f"WSL detected: {IS_WSL}")

DATA_PATH = os.path.join(os.path.expanduser("~"), ".tia_portal")
CONFIG_PATH = os.path.join(DATA_PATH, "config.ini")
VERSION = TiaVersion.V19  # Default to V19 instead of V15_1


def wsl_path_to_windows(linux_path):
    """Convert a WSL path to a Windows path.

    Parameters:
        linux_path (str): WSL path to convert.

    Returns:
        str: The converted Windows path.
    """
    if not IS_WSL:
        return linux_path

    # Check if this already looks like a Windows path
    if re.match(r"^[A-Za-z]:\\", linux_path):
        return linux_path

    try:
        # Use wslpath to convert Linux path to Windows path
        result = subprocess.run(
            ["wslpath", "-w", linux_path], capture_output=True, text=True, check=True
        )
        win_path = result.stdout.strip()
        print(f"Converted: {linux_path} → {win_path}")
        return win_path
    except Exception as e:
        print(f"Error converting path {linux_path}: {e}")
        return linux_path


def windows_path_to_wsl(windows_path):
    """Convert a Windows path to a WSL path.

    Parameters:
        windows_path (str): Windows path to convert.

    Returns:
        str: The converted WSL path.
    """
    if not IS_WSL:
        return windows_path

    # Check if this already looks like a Linux path
    if windows_path.startswith("/"):
        return windows_path

    try:
        # Use wslpath to convert Windows path to Linux path
        result = subprocess.run(
            ["wslpath", "-u", windows_path], capture_output=True, text=True, check=True
        )
        linux_path = result.stdout.strip()
        print(f"Converted: {windows_path} → {linux_path}")
        return linux_path
    except Exception as e:
        print(f"Error converting path {windows_path}: {e}")
        return windows_path


def normalize_path(path):
    """Normalize a path based on the environment.
    If running in WSL, convert the path to Windows format.

    Parameters:
        path (str): Path to normalize.

    Returns:
        str: Normalized path.
    """
    if not path:
        return path

    if IS_WSL:
        # Already Windows path format
        if re.match(r"^[A-Za-z]:\\", path):
            return path
        return wsl_path_to_windows(path)
    return path


def get_data_path():
    """Get the data path in the appropriate format for the current environment.

    Returns:
        str: Data path in the appropriate format.
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
