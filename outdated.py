from __future__ import absolute_import
import datetime
import json
import logging
import os.path
import sys
from pip._vendor import lockfile
from pip._vendor.packaging import version as packaging_version
from pip._internal.compat import WINDOWS
from pip._internal.index import PackageFinder
from pip._internal.locations import USER_CACHE_DIR, running_under_virtualenv
from pip._internal.utils.filesystem import check_path_owner
from pip._internal.utils.misc import ensure_dir, get_installed_version
SELFCHECK_DATE_FMT = "%Y-%m-%dT%H:%M:%SZ"
logger = logging.getLogger(__name__)
class VirtualenvSelfCheckState(object):
    def __init__(self):
        self.statefile_path = os.path.join(sys.prefix, "pip-selfcheck.json")
        try:
            with open(self.statefile_path) as statefile:
                self.state = json.load(statefile)
        except (IOError, ValueError):
            self.state = {}

    def save(self, pypi_version, current_time):
        with open(self.statefile_path, "w") as statefile:
            json.dump(
                {
                    "last_check": current_time.strftime(SELFCHECK_DATE_FMT),
                    "pypi_version": pypi_version,
                },
                statefile,
                sort_keys=True,
                separators=(",", ":")
            )
class GlobalSelfCheckState(object):
    def __init__(self):
        self.statefile_path = os.path.join(USER_CACHE_DIR, "selfcheck.json")
        try:
            with open(self.statefile_path) as statefile:
                self.state = json.load(statefile)[sys.prefix]
        except (IOError, ValueError, KeyError):
            self.state = {}

    def save(self, pypi_version, current_time):
        if not check_path_owner(os.path.dirname(self.statefile_path)):
            return
        ensure_dir(os.path.dirname(self.statefile_path))
        with lockfile.LockFile(self.statefile_path):
            if os.path.exists(self.statefile_path):
                with open(self.statefile_path) as statefile:
                    state = json.load(statefile)
            else:
                state = {}

            state[sys.prefix] = {
                "last_check": current_time.strftime(SELFCHECK_DATE_FMT),
                "pypi_version": pypi_version,
            }

            with open(self.statefile_path, "w") as statefile:
                json.dump(state, statefile, sort_keys=True,
                          separators=(",", ":"))
def load_selfcheck_statefile():
    if running_under_virtualenv():
        return VirtualenvSelfCheckState()
    else:
        return GlobalSelfCheckState()
def pip_version_check(session, options):
    installed_version = get_installed_version("pip")
    if not installed_version:
        return
    pip_version = packaging_version.parse(installed_version)
    pypi_version = None
    try:
        state = load_selfcheck_statefile()

        current_time = datetime.datetime.utcnow()
        if "last_check" in state.state and "pypi_version" in state.state:
            last_check = datetime.datetime.strptime(
                state.state["last_check"],
                SELFCHECK_DATE_FMT
            )
            if (current_time - last_check).total_seconds() < 7 * 24 * 60 * 60:
                pypi_version = state.state["pypi_version"]

        if pypi_version is None:
            finder = PackageFinder(
                find_links=options.find_links,
                index_urls=[options.index_url] + options.extra_index_urls,
                allow_all_prereleases=False,
                trusted_hosts=options.trusted_hosts,
                process_dependency_links=options.process_dependency_links,
                session=session,
            )
            all_candidates = finder.find_all_candidates("pip")
            if not all_candidates:
                return
            pypi_version = str(
                max(all_candidates, key=lambda c: c.version).version
            )
            state.save(pypi_version, current_time)

        remote_version = packaging_version.parse(pypi_version)
        if (pip_version < remote_version and
                pip_version.base_version != remote_version.base_version):
            if WINDOWS:
                pip_cmd = "python -m pip"
            else:
                pip_cmd = "pip"
            logger.warning(
                pip_version, pypi_version, pip_cmd
            )
    except Exception:
        logger.debug(
            "There was an error checking the latest version of pip",
            exc_info=True,
        )