from __future__ import absolute_import
import contextlib
import logging
import logging.handlers
import os
from pip._internal.compat import WINDOWS
from pip._internal.utils.misc import ensure_dir
try:
    import threading
except ImportError:
    import dummy_threading as threading  # type: ignore
try:
    from pip._vendor import colorama
except Exception:
    colorama = None
_log_state = threading.local()
_log_state.indentation = 0
@contextlib.contextmanager
def indent_log(num=2):
    _log_state.indentation += num
    try:
        yield
    finally:
        _log_state.indentation -= num
def get_indentation():
    return getattr(_log_state, 'indentation', 0)
class IndentingFormatter(logging.Formatter):
    def format(self, record):
        formatted = logging.Formatter.format(self, record)
        formatted = "".join([
            (" " * get_indentation()) + line
            for line in formatted.splitlines(True)
        ])
        return formatted
def _color_wrap(*colors):
    def wrapped(inp):
        return "".join(list(colors) + [inp, colorama.Style.RESET_ALL])
    return wrapped
class ColorizedStreamHandler(logging.StreamHandler):
    if colorama:
        COLORS = [
            (logging.ERROR, _color_wrap(colorama.Fore.RED)),
            (logging.WARNING, _color_wrap(colorama.Fore.YELLOW)),
        ]
    else:
        COLORS = []

    def __init__(self, stream=None, no_color=None):
        logging.StreamHandler.__init__(self, stream)
        self._no_color = no_color

        if WINDOWS and colorama:
            self.stream = colorama.AnsiToWin32(self.stream)

    def should_color(self):
        if not colorama or self._no_color:
            return False

        real_stream = (
            self.stream if not isinstance(self.stream, colorama.AnsiToWin32)
            else self.stream.wrapped
        )
        if hasattr(real_stream, "isatty") and real_stream.isatty():
            return True
        if os.environ.get("TERM") == "ANSI":
            return True
        return False
    def format(self, record):
        msg = logging.StreamHandler.format(self, record)

        if self.should_color():
            for level, color in self.COLORS:
                if record.levelno >= level:
                    msg = color(msg)
                    break
        return msg
class BetterRotatingFileHandler(logging.handlers.RotatingFileHandler):

    def _open(self):
        ensure_dir(os.path.dirname(self.baseFilename))
        return logging.handlers.RotatingFileHandler._open(self)
class MaxLevelFilter(logging.Filter):
    def __init__(self, level):
        self.level = level
    def filter(self, record):
        return record.levelno < self.level