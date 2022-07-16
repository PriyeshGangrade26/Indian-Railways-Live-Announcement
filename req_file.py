from __future__ import absolute_import
import optparse
import os
import re
import shlex
import sys
from pip._vendor.six.moves import filterfalse
from pip._vendor.six.moves.urllib import parse as urllib_parse
from pip._internal import cmdoptions
from pip._internal.download import get_file_content
from pip._internal.exceptions import RequirementsFileParseError
from pip._internal.req.req_install import InstallRequirement
__all__ = ['parse_requirements']
SCHEME_RE = re.compile(r'^(http|https|file):', re.I)
COMMENT_RE = re.compile(r'(^|\s)+#.*$')
ENV_VAR_RE = re.compile(r'(?P<var>\$\{(?P<name>[A-Z0-9_]+)\})')
SUPPORTED_OPTIONS = [
    cmdoptions.constraints,
    cmdoptions.editable,
    cmdoptions.requirements,
    cmdoptions.no_index,
    cmdoptions.index_url,
    cmdoptions.find_links,
    cmdoptions.extra_index_url,
    cmdoptions.always_unzip,
    cmdoptions.no_binary,
    cmdoptions.only_binary,
    cmdoptions.pre,
    cmdoptions.process_dependency_links,
    cmdoptions.trusted_host,
    cmdoptions.require_hashes,
]
SUPPORTED_OPTIONS_REQ = [
    cmdoptions.install_options,
    cmdoptions.global_options,
    cmdoptions.hash,
]
SUPPORTED_OPTIONS_REQ_DEST = [o().dest for o in SUPPORTED_OPTIONS_REQ]
def parse_requirements(filename, finder=None, comes_from=None, options=None,
                       session=None, constraint=False, wheel_cache=None):
    if session is None:
        raise TypeError(
        )
    _, content = get_file_content(
        filename, comes_from=comes_from, session=session
    )
    lines_enum = preprocess(content, options)
    for line_number, line in lines_enum:
        req_iter = process_line(line, filename, line_number, finder,
                                comes_from, options, session, wheel_cache,
                                constraint=constraint)
        for req in req_iter:
            yield req
def preprocess(content, options):
    lines_enum = enumerate(content.splitlines(), start=1)
    lines_enum = join_lines(lines_enum)
    lines_enum = ignore_comments(lines_enum)
    lines_enum = skip_regex(lines_enum, options)
    lines_enum = expand_env_variables(lines_enum)
    return lines_enum
def process_line(line, filename, line_number, finder=None, comes_from=None,
                 options=None, session=None, wheel_cache=None,
                 constraint=False):
    parser = build_parser(line)
    defaults = parser.get_default_values()
    defaults.index_url = None
    if finder:
        defaults.format_control = finder.format_control
    args_str, options_str = break_args_options(line)
    if sys.version_info < (2, 7, 3):
        options_str = options_str.encode('utf8')
    opts, _ = parser.parse_args(shlex.split(options_str), defaults)
    line_comes_from = '%s %s (line %s)' % (
        '-c' if constraint else '-r', filename, line_number,
    )
    if args_str:
        isolated = options.isolated_mode if options else False
        if options:
            cmdoptions.check_install_build_global(options, opts)
        req_options = {}
        for dest in SUPPORTED_OPTIONS_REQ_DEST:
            if dest in opts.__dict__ and opts.__dict__[dest]:
                req_options[dest] = opts.__dict__[dest]
        yield InstallRequirement.from_line(
            args_str, line_comes_from, constraint=constraint,
            isolated=isolated, options=req_options, wheel_cache=wheel_cache
        )
    elif opts.editables:
        isolated = options.isolated_mode if options else False
        yield InstallRequirement.from_editable(
            opts.editables[0], comes_from=line_comes_from,
            constraint=constraint, isolated=isolated, wheel_cache=wheel_cache
        )
    elif opts.requirements or opts.constraints:
        if opts.requirements:
            req_path = opts.requirements[0]
            nested_constraint = False
        else:
            req_path = opts.constraints[0]
            nested_constraint = True
        if SCHEME_RE.search(filename):
            req_path = urllib_parse.urljoin(filename, req_path)
        elif not SCHEME_RE.search(req_path):
            req_path = os.path.join(os.path.dirname(filename), req_path)
        parser = parse_requirements(
            req_path, finder, comes_from, options, session,
            constraint=nested_constraint, wheel_cache=wheel_cache
        )
        for req in parser:
            yield req
    elif opts.require_hashes:
        options.require_hashes = opts.require_hashes
    elif finder:
        if opts.index_url:
            finder.index_urls = [opts.index_url]
        if opts.no_index is True:
            finder.index_urls = []
        if opts.extra_index_urls:
            finder.index_urls.extend(opts.extra_index_urls)
        if opts.find_links:
            value = opts.find_links[0]
            req_dir = os.path.dirname(os.path.abspath(filename))
            relative_to_reqs_file = os.path.join(req_dir, value)
            if os.path.exists(relative_to_reqs_file):
                value = relative_to_reqs_file
            finder.find_links.append(value)
        if opts.pre:
            finder.allow_all_prereleases = True
        if opts.process_dependency_links:
            finder.process_dependency_links = True
        if opts.trusted_hosts:
            finder.secure_origins.extend(
                ("*", host, "*") for host in opts.trusted_hosts)
def break_args_options(line):
    tokens = line.split(' ')
    args = []
    options = tokens[:]
    for token in tokens:
        if token.startswith('-') or token.startswith('--'):
            break
        else:
            args.append(token)
            options.pop(0)
    return ' '.join(args), ' '.join(options)
def build_parser(line):
    parser = optparse.OptionParser(add_help_option=False)

    option_factories = SUPPORTED_OPTIONS + SUPPORTED_OPTIONS_REQ
    for option_factory in option_factories:
        option = option_factory()
        parser.add_option(option)
    def parser_exit(self, msg):
        msg = 'Invalid requirement: %s\n%s' % (line, msg)
        raise RequirementsFileParseError(msg)
    parser.exit = parser_exit
    return parser
def join_lines(lines_enum):
    primary_line_number = None
    new_line = []
    for line_number, line in lines_enum:
        if not line.endswith('\\') or COMMENT_RE.match(line):
            if COMMENT_RE.match(line):
                line = ' ' + line
            if new_line:
                new_line.append(line)
                yield primary_line_number, ''.join(new_line)
                new_line = []
            else:
                yield line_number, line
        else:
            if not new_line:
                primary_line_number = line_number
            new_line.append(line.strip('\\'))
    if new_line:
        yield primary_line_number, ''.join(new_line)
def ignore_comments(lines_enum):
    for line_number, line in lines_enum:
        line = COMMENT_RE.sub('', line)
        line = line.strip()
        if line:
            yield line_number, line
def skip_regex(lines_enum, options):
    skip_regex = options.skip_requirements_regex if options else None
    if skip_regex:
        pattern = re.compile(skip_regex)
        lines_enum = filterfalse(lambda e: pattern.search(e[1]), lines_enum)
    return lines_enum
def expand_env_variables(lines_enum):
    for line_number, line in lines_enum:
        for env_var, var_name in ENV_VAR_RE.findall(line):
            value = os.getenv(var_name)
            if not value:
                continue
            line = line.replace(env_var, value)
        yield line_number, line