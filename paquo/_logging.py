import logging
import os
from contextlib import contextmanager, ExitStack, ContextDecorator, AbstractContextManager, suppress

from paquo.java import System, PrintStream, ByteArrayOutputStream, StandardCharsets


# fixme: use different way to configure
LOGLEVEL = os.environ.get('LOGLEVEL', 'WARNING').upper()
logging.basicConfig(level=LOGLEVEL)


class _JavaLoggingBase(AbstractContextManager):
    """reentrant logging abstraction for redirecting JVM output to python

    will currently flush logging output on exit
    """
    java_default = None  # REQUIRED IN SUBCLASSES
    java_setter = None  # REQUIRED IN SUBCLASSES
    _count = 0
    _java_buffer = None
    _logger = logging.getLogger("JVM")

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
                # note: these two lines should be atomic
                self.java_setter(ps)
                self._java_buffer = java_buffer
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """decrease reference count and cleanup if 0"""
        self._count = max(0, self._count - 1)
        self.flush_logs()  # flush logs no matter what
        if not self._count:
            # note: these two lines should be atomic
            self.java_setter(self.java_default)
            self._java_buffer = None

    def flush_logs(self):
        """flush the java buffer to the Logger"""
        # extract the buffer and clear it
        try:
            output = str(self._java_buffer.toString())
        except AttributeError:
            return
        finally:
            with suppress(AttributeError):
                self._java_buffer.reset()
        # assume JVM console output is one line per msg
        for line in output.splitlines():
            if not (line := line.strip()):
                continue
            # very basic conversion to logging methods
            if "WARN" in output:
                self._logger.warning(line)
            elif "ERR" in output:
                self._logger.error(line)
                # FIXME: SHOULD THIS RAISE AN EXCEPTION?
            else:
                self._logger.info(line)


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
        self._stdout = stdout
        self._stderr = stderr

    def __enter__(self):
        super().__enter__()
        if self._stderr:
            self.enter_context(_JavaLoggingStderr())
        if self._stdout:
            self.enter_context(_JavaLoggingStdout())
        return self
