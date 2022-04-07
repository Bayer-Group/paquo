import warnings

from paquo._config import settings
from paquo._config import to_kwargs
from paquo._utils import QuPathVersion
from paquo.jpype_backend import JClass
from paquo.jpype_backend import start_jvm

# we can extend this as when we add more testing against different versions
MIN_QUPATH_VERSION = QuPathVersion('0.2.0')  # FIXME: this is bound to change


# allow paquo to be imported in case qupath and a jvm are not available
# Note: this renders paquo unusable. But we need it for example for the
#   sphinx docs to be generated without requiring an installed qupath.
if settings.mock_backend:  # pragma: no cover
    from unittest.mock import MagicMock
    from unittest.mock import create_autospec

    start_jvm = create_autospec(start_jvm, return_value=MIN_QUPATH_VERSION)
    # noinspection PyPep8Naming
    def JClass(jc, *_args, **_kwargs):  # noqa
        class _JClassType(type):
            def __getattr__(cls, key):
                return MagicMock()

        class _JClass(metaclass=_JClassType):
            f"""Java Class: {jc!r}"""
        return _JClass

# ensure the jvm is running
qupath_version = start_jvm(finder_kwargs=to_kwargs(settings))
if qupath_version is None:
    # let's not exit for now but warn the user:
    warnings.warn("COULD NOT DETECT QUPATH VERSION! UNSUPPORTED")  # pragma: no cover
elif qupath_version < MIN_QUPATH_VERSION:
    # let's not exit for now but warn the user:
    warnings.warn(f"QUPATH '{qupath_version}' IS UNTESTED OR UNSUPPORTED")  # pragma: no cover


class _Compatibility:
    """organizes QuPath version differences"""
    def __init__(self, version: "QuPathVersion | None") -> None:
        self.version = version

    def requires_missing_classes_json_fix(self) -> bool:
        # older QuPaths crash on project load when classes.json is missing
        # see: https://github.com/qupath/qupath/commit/be861cea80b9a8ef300e30d7985fd69791c2432e
        if self.version is None:
            return True
        else:
            return self.version <= QuPathVersion("0.2.0")

    def requires_annotation_json_fix(self) -> bool:
        # annotations changed between QuPath "0.2.3" and "0.3.x"
        # see: https://github.com/qupath/qupath/commit/fef5c43ce3f67e0e062677c407b395ef3e6e27c3
        if self.version is None:
            return True
        else:
            return self.version <= QuPathVersion("0.2.3")

    def supports_image_server_recovery(self) -> bool:
        # image_server server.json files are only guaranteed to be written since QuPath "0.2.0"
        # see: https://github.com/qupath/qupath/commit/39abee3012da9252ea988308848c5d802164e060
        if self.version is None:
            return False
        else:
            return self.version >= QuPathVersion("0.2.0")

    def supports_logmanager(self) -> bool:
        # the logmanager class was only added with 0.2.0-m10
        # see: https://github.com/qupath/qupath/commit/15b844703b686f7a9a64c50194ebe22fc46924a5
        if self.version is None:
            return False
        else:
            return self.version >= QuPathVersion("0.2.0-m10")


compatibility = _Compatibility(qupath_version)


ArrayList = JClass("java.util.ArrayList")
BufferedImage = JClass('java.awt.image.BufferedImage')
ByteArrayOutputStream = JClass("java.io.ByteArrayOutputStream")
File = JClass('java.io.File')
Files = JClass('java.nio.file.Files')
Integer = JClass('java.lang.Integer')
PrintStream = JClass('java.io.PrintStream')
StandardCharsets = JClass("java.nio.charset.StandardCharsets")
String = JClass('java.lang.String')
System = JClass('java.lang.System')
URI = JClass('java.net.URI')

ColorTools = JClass('qupath.lib.common.ColorTools')
DefaultProject = JClass('qupath.lib.projects.DefaultProject')
DefaultProjectImageEntry = JClass('qupath.lib.projects.DefaultProject.DefaultProjectImageEntry')
GeneralTools = JClass("qupath.lib.common.GeneralTools")
GeometryTools = JClass("qupath.lib.roi.GeometryTools")
GsonTools = JClass('qupath.lib.io.GsonTools')
ImageData = JClass('qupath.lib.images.ImageData')
ImageType = JClass('qupath.lib.images.ImageData.ImageType')
ImageServer = JClass('qupath.lib.images.servers.ImageServer')
ImageServers = JClass('qupath.lib.images.servers.ImageServers')  # NOTE: this is needed to make QuPath v0.3.0-rc1 work
ImageServerProvider = JClass('qupath.lib.images.servers.ImageServerProvider')

if compatibility.supports_logmanager():
    LogManager = JClass('qupath.lib.gui.logging.LogManager')
else:
    LogManager = None

PathAnnotationObject = JClass("qupath.lib.objects.PathAnnotationObject")
PathClass = JClass('qupath.lib.objects.classes.PathClass')
PathClassFactory = JClass('qupath.lib.objects.classes.PathClassFactory')
PathDetectionObject = JClass("qupath.lib.objects.PathDetectionObject")
PathIO = JClass("qupath.lib.io.PathIO")
PathObjectHierarchy = JClass('qupath.lib.objects.hierarchy.PathObjectHierarchy')
PathObjects = JClass("qupath.lib.objects.PathObjects")
PathROIObject = JClass("qupath.lib.objects.PathROIObject")
PathTileObject = JClass("qupath.lib.objects.PathTileObject")
Point2 = JClass("qupath.lib.geom.Point2")
ProjectIO = JClass('qupath.lib.projects.ProjectIO')
Projects = JClass('qupath.lib.projects.Projects')
ROI = JClass("qupath.lib.roi.interfaces.ROI")
ROIs = JClass("qupath.lib.roi.ROIs")
ServerTools = JClass('qupath.lib.images.servers.ServerTools')

EllipseROI = JClass("qupath.lib.roi.EllipseROI")
GeometryROI = JClass("qupath.lib.roi.GeometryROI")
LineROI = JClass("qupath.lib.roi.LineROI")
PointsROI = JClass("qupath.lib.roi.PointsROI")
PolygonROI = JClass("qupath.lib.roi.PolygonROI")
PolylineROI = JClass("qupath.lib.roi.PolylineROI")
RectangleROI = JClass("qupath.lib.roi.RectangleROI")

WKBWriter = JClass("org.locationtech.jts.io.WKBWriter")
WKBReader = JClass("org.locationtech.jts.io.WKBReader")

IOException = JClass("java.io.IOException")
ExceptionInInitializerError = JClass("java.lang.ExceptionInInitializerError")
URISyntaxException = JClass("java.net.URISyntaxException")
NegativeArraySizeException = JClass('java.lang.NegativeArraySizeException')
IllegalArgumentException = JClass('java.lang.IllegalArgumentException')
FileNotFoundException = JClass('java.io.FileNotFoundException')
NoSuchFileException = JClass('java.nio.file.NoSuchFileException')


def __getattr__(name):
    """lazy import some"""
    if name == "ProjectImportImagesCommand":
        warnings.warn(
            "ProjectImportImagesCommand will be removed from paquo.java",
            DeprecationWarning
        )
        return JClass('qupath.lib.gui.commands.ProjectImportImagesCommand')
    else:
        raise AttributeError(name)


# noinspection PyPep8Naming
def ProjectImportImagesCommand_getThumbnailRGB(server, _):
    # needs to be lazily imported to not emit threading info message
    pcmd = JClass('qupath.lib.gui.commands.ProjectImportImagesCommand')
    return pcmd.getThumbnailRGB(server, None)
