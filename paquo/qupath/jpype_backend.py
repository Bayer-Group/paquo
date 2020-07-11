from contextlib import contextmanager, nullcontext
import jpype

from paquo.qupath.util import find_qupath


@contextmanager
def jvm_running():
    if not jpype.isJVMStarted():
        # For the time being, we assume qupath is our JVM of choice
        app_dir, runtime_dir, jvm_path, jvm_options = find_qupath()
        # This is not really needed, but beware we might need SL4J classes (see warning)
        jpype.addClassPath(str(app_dir / '*'))
        jpype.startJVM(str(jvm_path), *jvm_options, convertStrings=False)
    yield


def java_import(name, cm=nullcontext):
    with cm():
        return jpype.JClass(name)
