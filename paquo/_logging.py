import atexit
import logging
import re
from contextlib import AbstractContextManager
from contextlib import ContextDecorator
from contextlib import ExitStack
from contextlib import contextmanager
from contextlib import suppress
from typing import Iterable
from typing import List
from typing import Tuple

from paquo.java import ByteArrayOutputStream
from paquo.java import LogManager
from paquo.java import PrintStream
from paquo.java import StandardCharsets
from paquo.java import System

__all__ = ['get_logger', 'redirect']

# === qupath logging setup ============================================

# by default, silence the qupath java logging if nothing is configured
# https://docs.python.org/3/howto/logging.html#configuring-logging-for-a-library
logging.getLogger('qupath').addHandler(logging.NullHandler())

# set the java log level to DEBUG
# and filter in the 'qupath' logger on the python side
if LogManager:
    LogManager.setDebug()


@atexit.register
def _java_log_cleanup():
    # NOTE: qupath's ImageServer Threads provide debug output that's
    #   only emitted once the interpreter is cleaned up. Since at
    #   that point we've already left the contextmanager for log
    #   redirection, we'll just switch the qupath loglevel to Warn
    #   and emit a debug message on the python side.
    if LogManager:
        LogManager.setWarn()
    get_logger('qupath').debug("switching java logger to warn for silent thread cleanup")


# --- logging methods -------------------------------------------------

def get_logger(name):
    """return a logger instance"""
    return logging.getLogger(name)


class _JavaLoggingBase(AbstractContextManager):
    """reentrant logging abstraction for redirecting JVM output to python

    will currently flush logging output on exit
    """
    java_default = None  # REQUIRED IN SUBCLASSES
    java_setter = None  # REQUIRED IN SUBCLASSES
    _count = 0
    _java_buffer = None
    _logger = logging.getLogger("qupath")
    _java_log_entry_match = re.compile(r"""^
        (?P<timestamp>[0-9:.]+)
        [ ]\[(?P<logger>[^]]+)]
        [ ]\[(?P<level>[^]]+)]
        [ ](?P<origin>[^ ]+)
        [ ]-[ ](?P<msg>.*)
        $
    """, re.VERBOSE).match

    @contextmanager
    def _stop_redirection_on_error(self):
        # reuse stdio reset in case __enter__ crashes
        with ExitStack() as stack:
            stack.push(self)
            yield
            # we did not crash!
            stack.pop_all()

    def __enter__(self):
        """increase reference count and redirect stdio"""
        self._count += 1
        with self._stop_redirection_on_error():
            if self._java_buffer is None:
                java_buffer = ByteArrayOutputStream()
                ps = PrintStream(
                    java_buffer,
                    True,
                    StandardCharsets.UTF_8.name()
                )
                # note: these two lines should be made atomic
                self.java_setter(ps)
                self._java_buffer = java_buffer
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """decrease reference count and cleanup if 0"""
        self._count = max(0, self._count - 1)
        self.flush_logs()  # flush logs no matter what
        if not self._count:
            # note: these two lines should be made atomic
            self.java_setter(self.java_default)
            self._java_buffer = None

    def flush_logs(self):
        """flush the java buffer to the Logger"""
        # extract the buffer and clear it
        try:
            output = str(self._java_buffer.toString())
        except AttributeError:  # pragma: no cover
            return
        with suppress(AttributeError):
            self._java_buffer.reset()
        # assume JVM console output is one line per msg
        for (origin, level), entry in self.iter_logs(output):
            if "WARN" in level:
                self._logger.warning("[%s] [%s] - %s", origin, level, entry)
            elif "ERR" in level:
                self._logger.error("[%s] [%s] - %s", origin, level, entry)  # pragma: no cover
            elif "DEBUG" in level:
                self._logger.debug("[%s] [%s] - %s", origin, level, entry)
            else:
                self._logger.info("[%s] [%s] - %s", origin, level, entry)

    def iter_logs(self, output: str) -> Iterable[Tuple[Tuple[str, str], str]]:
        """iterate the individual log messages"""
        entry: List[str] = []
        info = ('NONE', 'NONE')
        for line in output.splitlines(keepends=True):
            if not line.strip():
                continue  # pragma: no cover
            m = self.__class__._java_log_entry_match(line)
            if m:
                if entry:
                    yield info, "".join(entry).rstrip()
                    entry.clear()
                info = (
                    m.group('origin'),
                    m.group('level').strip().upper(),
                )
                entry.append(m.group('msg'))
            else:
                entry.append(line)  # pragma: no cover
        if entry:
            yield info, "".join(entry).rstrip()


class _JavaLoggingStdout(_JavaLoggingBase):
    java_default = System.out
    java_setter = System.setOut


class _JavaLoggingStderr(_JavaLoggingBase):
    java_default = System.err
    java_setter = System.setErr


# noinspection PyPep8Naming
class redirect(ExitStack, ContextDecorator):
    """convenient contextdecorator for redirecting JVM output"""

    def __init__(self, stdout=True, stderr=True):
        super().__init__()
        self._stdout = _JavaLoggingStdout if stdout else None
        self._stderr = _JavaLoggingStderr if stderr else None

    def __enter__(self):
        super().__enter__()
        if self._stderr:
            self.enter_context(self._stderr())
        if self._stdout:
            self.enter_context(self._stdout())
        return self
