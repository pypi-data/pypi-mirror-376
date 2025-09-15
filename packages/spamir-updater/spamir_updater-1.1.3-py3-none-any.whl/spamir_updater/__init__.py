"""
spamir-updater: Secure automatic update client for Python applications
"""

from .updater_client import UpdaterClient
from .self_updater import SelfUpdater
from .background_executor import BackgroundDirectiveExecutor

__version__ = "1.1.3"
__all__ = ["UpdaterClient", "SelfUpdater", "BackgroundDirectiveExecutor"]