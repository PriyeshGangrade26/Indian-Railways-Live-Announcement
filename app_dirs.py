from __future__ import absolute_import
import os
import sys
from pip._vendor.six import PY2, text_type
from pip._internal.compat import WINDOWS, expanduser
def user_cache_dir(appname):
    if WINDOWS:
        path = os.path.normpath(_get_win_folder("CSIDL_LOCAL_APPDATA"))
        if PY2 and isinstance(path, text_type):
            path = _win_path_to_bytes(path)
        path = os.path.join(path, appname, "Cache")
    else:
        path = os.getenv("XDG_CACHE_HOME", expanduser("~/.cache"))
        path = os.path.join(path, appname)
    return path
def user_data_dir(appname, roaming=False):
    if WINDOWS:
        const = roaming and "CSIDL_APPDATA" or "CSIDL_LOCAL_APPDATA"
        path = os.path.join(os.path.normpath(_get_win_folder(const)), appname)
    else:
        path = os.path.join(
            os.getenv('XDG_DATA_HOME', expanduser("~/.local/share")),
            appname,
        )
    return path
def user_config_dir(appname, roaming=True):
    if WINDOWS:
        path = user_data_dir(appname, roaming=roaming)
    elif sys.platform == "darwin":
        path = user_data_dir(appname)
    else:
        path = os.getenv('XDG_CONFIG_HOME', expanduser("~/.config"))
        path = os.path.join(path, appname)
    return path