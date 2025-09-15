"""
spamir-updater: Secure automatic update client for Python applications
"""

from .updater_client import UpdaterClient
from .self_updater import SelfUpdater

__version__ = "1.0.6"
__all__ = ["UpdaterClient", "SelfUpdater"]