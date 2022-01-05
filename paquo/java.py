import warnings

from packaging.version import Version

from paquo._config import settings, to_kwargs
from paquo.jpype_backend import start_jvm, JClass

# we can extend this as when we add more testing against different versions
MIN_QUPATH_VERSION = Version('0.2.1')  # FIXME: this is bound to change

# allow paquo to be imported in case qupath and a jvm are not available
# Note: this renders paquo unusable. But we need it for example for the
#   sphinx docs to be generated without requiring an installed qupath.
if settings.mock_backend:  # pragma: no cover
    def start_jvm(*_args, **_kwargs):  # type: ignore
        return MIN_QUPATH_VERSION

    # noinspection PyPep8Naming
    def JClass(*_args, **_kwargs):
        class JClassType(type):
            def __getattr__(cls, key):
                pass

        class _JClass(metaclass=JClassType):
            pass
        return _JClass

# ensure the jvm is running
qupath_version = start_jvm(finder_kwargs=to_kwargs(settings))
if qupath_version is None or qupath_version < MIN_QUPATH_VERSION:
    # let's not exit for now but warn the user that
    warnings.warn(f"QUPATH '{qupath_version}' UNTESTED OR UNSUPPORTED")  # pragma: no cover


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
LogManager = JClass('qupath.lib.gui.logging.LogManager')
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
ProjectImportImagesCommand = JClass('qupath.lib.gui.commands.ProjectImportImagesCommand')
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
