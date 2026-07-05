"""Central logging setup for ShareBridge.

Kivy's default behaviour writes many timestamped log files under ~/.kivy/logs
(and can fail on Android), which is the source of the "log issues". We disable
that (via KIVY_NO_FILELOG in MainApplication) and instead keep ONE small
rotating log file that the user can export from Settings.

The file captures WARNING and above only — i.e. real problems — so the exported
log stays focused and useful for feedback e-mails.
"""
import logging
import os
from logging.handlers import RotatingFileHandler

LOG_FILENAME = "sharebridge.log"
FILE_LEVEL = logging.WARNING  # only problems (warnings + errors) go to the file

_log_path = None
_configured = False


def setup_file_logging(log_dir):
    """Create the single rotating log file and route problems into it.

    Returns the absolute path of the log file.
    """
    global _log_path, _configured

    os.makedirs(log_dir, exist_ok=True)
    _log_path = os.path.join(log_dir, LOG_FILENAME)

    if _configured:
        return _log_path

    handler = RotatingFileHandler(
        _log_path, maxBytes=512 * 1024, backupCount=1, encoding="utf-8"
    )
    handler.setLevel(FILE_LEVEL)
    handler.setFormatter(
        logging.Formatter("%(asctime)s [%(levelname)-8s] %(name)s: %(message)s")
    )

    # Attach to the ROOT logger so both stdlib loggers (services/*) and Kivy's
    # Logger (via propagation) land in the same file.
    root = logging.getLogger()
    if root.level == logging.NOTSET or root.level > FILE_LEVEL:
        root.setLevel(FILE_LEVEL)
    root.addHandler(handler)

    # Make Kivy's Logger propagate up so our file handler sees its records too.
    try:
        from kivy.logger import Logger
        Logger.propagate = True
    except Exception:
        pass

    # Silence the very chatty websockets frame logger.
    logging.getLogger("websockets").setLevel(logging.WARNING)

    _configured = True
    return _log_path


def get_log_path():
    """Path of the active log file, or None if logging isn't set up yet."""
    return _log_path
