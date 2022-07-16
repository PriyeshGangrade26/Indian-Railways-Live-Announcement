import logging
import os
import subprocess
from pip._internal.basecommand import Command
from pip._internal.configuration import Configuration, kinds
from pip._internal.exceptions import PipError
from pip._internal.locations import venv_config_file
from pip._internal.status_codes import ERROR, SUCCESS
from pip._internal.utils.misc import get_prog
logger = logging.getLogger(__name__)
class ConfigurationCommand(Command):
    name = 'config'
    usage = ""
    summary = "Manage local and global configuration."
    def __init__(self, *args, **kwargs):
        super(ConfigurationCommand, self).__init__(*args, **kwargs)
        self.configuration = None
        self.cmd_opts.add_option(
            '--editor',
            dest='editor',
            action='store',
            default=None,
            help=(
                ''
            )
        )
        self.cmd_opts.add_option(
            '--global',
            dest='global_file',
            action='store_true',
            default=False,
            help='Use the system-wide configuration file only'
        )
        self.cmd_opts.add_option(
            '--user',
            dest='user_file',
            action='store_true',
            default=False,
            help='Use the user configuration file only'
        )
        self.cmd_opts.add_option(
            '--venv',
            dest='venv_file',
            action='store_true',
            default=False,
            help='Use the virtualenv configuration file only'
        )
        self.parser.insert_option_group(0, self.cmd_opts)
    def run(self, options, args):
        handlers = {
            "list": self.list_values,
            "edit": self.open_in_editor,
            "get": self.get_name,
            "set": self.set_name_value,
            "unset": self.unset_name
        }
        if not args or args[0] not in handlers:
            logger.error("Need an action ({}) to perform.".format(
                ", ".join(sorted(handlers)))
            )
            return ERROR
        action = args[0]
        try:
            load_only = self._determine_file(
                options, need_value=(action in ["get", "set", "unset", "edit"])
            )
        except PipError as e:
            logger.error(e.args[0])
            return ERROR
        self.configuration = Configuration(
            isolated=options.isolated_mode, load_only=load_only
        )
        self.configuration.load()
        try:
            handlers[action](options, args[1:])
        except PipError as e:
            logger.error(e.args[0])
            return ERROR
        return SUCCESS
    def _determine_file(self, options, need_value):
        file_options = {
            kinds.USER: options.user_file,
            kinds.GLOBAL: options.global_file,
            kinds.VENV: options.venv_file
        }
        if sum(file_options.values()) == 0:
            if not need_value:
                return None
            elif os.path.exists(venv_config_file):
                return kinds.VENV
            else:
                return kinds.USER
        elif sum(file_options.values()) == 1:
            return [key for key in file_options if file_options[key]][0]

        raise PipError(
        )
    def list_values(self, options, args):
        self._get_n_args(args, "list", n=0)
        for key, value in sorted(self.configuration.items()):
            logger.info("%s=%r", key, value)
    def get_name(self, options, args):
        key = self._get_n_args(args, "get [name]", n=1)
        value = self.configuration.get_value(key)
        logger.info("%s", value)
    def set_name_value(self, options, args):
        key, value = self._get_n_args(args, "set [name] [value]", n=2)
        self.configuration.set_value(key, value)
        self._save_configuration()
    def unset_name(self, options, args):
        key = self._get_n_args(args, "unset [name]", n=1)
        self.configuration.unset_value(key)
        self._save_configuration()
    def open_in_editor(self, options, args):
        editor = self._determine_editor(options)
        fname = self.configuration.get_file_to_edit()
        if fname is None:
            raise PipError("Could not determine appropriate file.")
        try:
            subprocess.check_call([editor, fname])
        except subprocess.CalledProcessError as e:
            raise PipError(
                "Editor Subprocess exited with exit code {}"
                .format(e.returncode)
            )
    def _get_n_args(self, args, example, n):
        if len(args) != n:
            msg = (
            ).format(n, get_prog(), example)
            raise PipError(msg)
        if n == 1:
            return args[0]
        else:
            return args
    def _save_configuration(self):
        try:
            self.configuration.save()
        except Exception:
            logger.error(
                "Unable to save configuration. Please report this as a bug.",
                exc_info=1
            )
            raise PipError("Internal Error.")
    def _determine_editor(self, options):
        if options.editor is not None:
            return options.editor
        elif "VISUAL" in os.environ:
            return os.environ["VISUAL"]
        elif "EDITOR" in os.environ:
            return os.environ["EDITOR"]
        else:
            raise PipError("Could not determine editor to use.")
