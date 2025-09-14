"""
Constants
=========

This module contains constants used throughout the Starch code package.

"""

from pathlib import Path
from typing import Final

from platformdirs import (
    user_cache_path,
    user_config_path,
    user_data_path,
    user_log_path
)


# ─── package metadata ───────────────────────────────────────────────────────────── ✦ ─
#
__author__ = "Caleb Rice"
__email__ = "hyletic@proton.me"
__license__ = "MIT"

# VERSION_CONFIG: {"base":"0.1.0","phase":"a","build":8}
__version__ = "0.1.0a8"

    
# ─── constants ──────────────────────────────────────────────────────────────────── ✦ ─
#
PACKAGE_NAME: Final[str] = __package__.split(".")[-1]
STARCH_CACHE_PATH: Final[Path] = user_cache_path(PACKAGE_NAME, ensure_exists=True)
STARCH_CONFIG_PATH: Final[Path] = user_config_path(PACKAGE_NAME, ensure_exists=True)
STARCH_DATA_PATH: Final[Path] = user_data_path(PACKAGE_NAME, ensure_exists=True)
STARCH_LOG_PATH: Final[Path] = user_log_path(PACKAGE_NAME, ensure_exists=True)
STARCH_CONFIG_FILEPATH: Final[Path] = STARCH_CONFIG_PATH / "config.json"
STARCH_LOG_FILEPATH: Final[Path] = STARCH_LOG_PATH / f"{__package__}.log"

