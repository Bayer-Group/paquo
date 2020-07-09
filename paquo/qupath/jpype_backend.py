from pathlib import Path
import jpype

from paquo.qupath.util import find_qupath


def start_jpype():
    if not jpype.isJVMStarted():
        # For the time being, we assume qupath is our JVM of choice
        app_dir, runtime_dir, jvm_path, jvm_options = find_qupath()
        # This is not really needed, but beware we might need SL4J classes (see warning)
        jpype.addClassPath(str(app_dir / '*'))
        # Our custom java libraries
        JAVA_VENDORED_PATH = Path(__file__).absolute().parent / 'vendored' / 'java' / 'jars'
        if JAVA_VENDORED_PATH.is_dir():
            jpype.addClassPath(str(JAVA_VENDORED_PATH / '*'))
        jpype.startJVM(str(jvm_path), convertStrings=False)


if __name__ == '__main__':
    start_jpype()
    BuildInfo = jpype.JClass('qupath.lib.gui.BuildInfo')
    # now this can be made easy with qupath
    print(BuildInfo.getInstance().getVersion())
