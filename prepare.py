import itertools
import logging
import os
import sys
from copy import copy
from pip._vendor import pkg_resources, requests
from pip._internal.build_env import NoOpBuildEnvironment
from pip._internal.compat import expanduser
from pip._internal.download import (
    is_dir_url, is_file_url, is_vcs_url, unpack_url, url_to_path,
)
from pip._internal.exceptions import (
    DirectoryUrlHashUnsupported, HashUnpinned, InstallationError,
    PreviousBuildDirError, VcsHashUnsupported,
)
from pip._internal.index import FormatControl
from pip._internal.req.req_install import InstallRequirement
from pip._internal.utils.hashes import MissingHashes
from pip._internal.utils.logging import indent_log
from pip._internal.utils.misc import (
    call_subprocess, display_path, normalize_path,
)
from pip._internal.utils.ui import open_spinner
from pip._internal.vcs import vcs
logger = logging.getLogger(__name__)
def make_abstract_dist(req):
    if req.editable:
        return IsSDist(req)
    elif req.link and req.link.is_wheel:
        return IsWheel(req)
    else:
        return IsSDist(req)
def _install_build_reqs(finder, prefix, build_requirements):
    finder = copy(finder)
    finder.format_control = FormatControl(set(), set([":all:"]))
    urls = [
        finder.find_requirement(
            InstallRequirement.from_line(r), upgrade=False).url
        for r in build_requirements
    ]
    args = [
        sys.executable, '-m', 'pip', 'install', '--ignore-installed',
        '--no-user', '--prefix', prefix,
    ] + list(urls)

    with open_spinner("Installing build dependencies") as spinner:
        call_subprocess(args, show_stdout=False, spinner=spinner)
class DistAbstraction(object):
    def __init__(self, req):
        self.req = req
    def dist(self, finder):
        """Return a setuptools Dist object."""
        raise NotImplementedError(self.dist)
    def prep_for_dist(self, finder):
        """Ensure that we can get a Dist for this requirement."""
        raise NotImplementedError(self.dist)
class IsWheel(DistAbstraction):
    def dist(self, finder):
        return list(pkg_resources.find_distributions(
            self.req.source_dir))[0]
    def prep_for_dist(self, finder, build_isolation):
        pass
class IsSDist(DistAbstraction):
    def dist(self, finder):
        dist = self.req.get_dist()
        if finder and dist.has_metadata('dependency_links.txt'):
            finder.add_dependency_links(
                dist.get_metadata_lines('dependency_links.txt')
            )
        return dist
    def prep_for_dist(self, finder, build_isolation):
        build_requirements, isolate = self.req.get_pep_518_info()
        should_isolate = build_isolation and isolate
        minimum_requirements = ('setuptools', 'wheel')
        missing_requirements = set(minimum_requirements) - set(
            pkg_resources.Requirement(r).key
            for r in build_requirements
        )
        if missing_requirements:
            def format_reqs(rs):
                return ' and '.join(map(repr, sorted(rs)))
            logger.warning(
                "Missing build time requirements in pyproject.toml for %s: "
                "%s.", self.req, format_reqs(missing_requirements)
            )
            logger.warning(
                "This version of pip does not implement PEP 517 so it cannot "
                "build a wheel without %s.", format_reqs(minimum_requirements)
            )
        if should_isolate:
            with self.req.build_env:
                pass
            _install_build_reqs(finder, self.req.build_env.path,
                                build_requirements)
        else:
            self.req.build_env = NoOpBuildEnvironment(no_clean=False)

        self.req.run_egg_info()
        self.req.assert_source_matches_version()
class Installed(DistAbstraction):
    def dist(self, finder):
        return self.req.satisfied_by
    def prep_for_dist(self, finder):
        pass
class RequirementPreparer(object):
    def __init__(self, build_dir, download_dir, src_dir, wheel_download_dir,
                 progress_bar, build_isolation):
        super(RequirementPreparer, self).__init__()
        self.src_dir = src_dir
        self.build_dir = build_dir
        self.download_dir = download_dir
        if wheel_download_dir:
            wheel_download_dir = normalize_path(wheel_download_dir)
        self.wheel_download_dir = wheel_download_dir
        self.progress_bar = progress_bar
        self.build_isolation = build_isolation
    @property
    def _download_should_save(self):
        if self.download_dir:
            self.download_dir = expanduser(self.download_dir)
            if os.path.exists(self.download_dir):
                return True
            else:
                logger.critical('Could not find download directory')
                raise InstallationError(
                    "Could not find or access download directory '%s'"
                    % display_path(self.download_dir))
        return False

    def prepare_linked_requirement(self, req, session, finder,
                                   upgrade_allowed, require_hashes):
        if req.link and req.link.scheme == 'file':
            path = url_to_path(req.link.url)
            logger.info('Processing %s', display_path(path))
        else:
            logger.info('Collecting %s', req)

        with indent_log():
            req.ensure_has_source_dir(self.build_dir)
            if os.path.exists(os.path.join(req.source_dir, 'setup.py')):
                raise PreviousBuildDirError(
                )
            req.populate_link(finder, upgrade_allowed, require_hashes)
            assert req.link
            link = req.link
            if require_hashes:
                if is_vcs_url(link):
                    raise VcsHashUnsupported()
                elif is_file_url(link) and is_dir_url(link):
                    raise DirectoryUrlHashUnsupported()
                if not req.original_link and not req.is_pinned:
                    raise HashUnpinned()

            hashes = req.hashes(trust_internet=not require_hashes)
            if require_hashes and not hashes:
                hashes = MissingHashes()
            try:
                download_dir = self.download_dir
                autodelete_unpacked = True
                if req.link.is_wheel and self.wheel_download_dir:
                    download_dir = self.wheel_download_dir
                if req.link.is_wheel:
                    if download_dir:
                        autodelete_unpacked = True
                    else:
                        autodelete_unpacked = False
                unpack_url(
                    req.link, req.source_dir,
                    download_dir, autodelete_unpacked,
                    session=session, hashes=hashes,
                    progress_bar=self.progress_bar
                )
            except requests.HTTPError as exc:
                logger.critical(
                    'Could not install requirement %s because of error %s',
                    req,
                    exc,
                )
                raise InstallationError(
                    'Could not install requirement %s because of HTTP '
                    'error %s for URL %s' %
                    (req, exc, req.link)
                )
            abstract_dist = make_abstract_dist(req)
            abstract_dist.prep_for_dist(finder, self.build_isolation)
            if self._download_should_save:
                if req.link.scheme in vcs.all_schemes:
                    req.archive(self.download_dir)
        return abstract_dist
    def prepare_editable_requirement(self, req, require_hashes, use_user_site,
                                     finder):
        assert req.editable
        logger.info('Obtaining %s', req)

        with indent_log():
            if require_hashes:
                raise InstallationError()
            req.ensure_has_source_dir(self.src_dir)
            req.update_editable(not self._download_should_save)
            abstract_dist = make_abstract_dist(req)
            abstract_dist.prep_for_dist(finder, self.build_isolation)
            if self._download_should_save:
                req.archive(self.download_dir)
            req.check_if_exists(use_user_site)
        return abstract_dist
    def prepare_installed_requirement(self, req, require_hashes, skip_reason):
        assert req.satisfied_by, "req should have been satisfied but isn't"
        assert skip_reason is not None, (
            "did not get skip reason skipped but req.satisfied_by "
            "is set to %r" % (req.satisfied_by,)
        )
        logger.info(
            'Requirement %s: %s (%s)',
            skip_reason, req, req.satisfied_by.version
        )
        with indent_log():
            if require_hashes:
                logger.debug(
                )
            abstract_dist = Installed(req)
        return abstract_dist