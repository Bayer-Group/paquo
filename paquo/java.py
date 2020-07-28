from distutils.util import strtobool
from distutils.version import LooseVersion
import os
import warnings

from paquo.jpype_backend import start_jvm, JClass

# we can extend this as when we add more testing against different versions
MIN_QUPATH_VERSION = LooseVersion('0.2.1')  # FIXME: this is bound to change


# let sphinx docs be generated without requiring an installed qupath
RUNNING_ON_RTD = strtobool(os.environ.get('READTHEDOCS', 'false'))
if RUNNING_ON_RTD:
    def start_jvm(*args, **kwargs):
        return MIN_QUPATH_VERSION

    class JClass:
        def __init__(self, *args, **kwargs):
            pass


# ensure the jvm is running
qupath_version = start_jvm()
if qupath_version is None or qupath_version < MIN_QUPATH_VERSION:
    # let's not exit for now but warn the user that
    warnings.warn(f"QUPATH '{qupath_version}' UNTESTED OR UNSUPPORTED")


ArrayList = JClass("java.util.ArrayList")
BufferedImage = JClass('java.awt.image.BufferedImage')
ByteArrayOutputStream = JClass("java.io.ByteArrayOutputStream")
File = JClass('java.io.File')
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
ImageServerProvider = JClass('qupath.lib.images.servers.ImageServerProvider')
PathAnnotationObject = JClass("qupath.lib.objects.PathAnnotationObject")
PathClass = JClass('qupath.lib.objects.classes.PathClass')
PathClassFactory = JClass('qupath.lib.objects.classes.PathClassFactory')
PathDetectionObject = JClass("qupath.lib.objects.PathDetectionObject")
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

WKBWriter = JClass("org.locationtech.jts.io.WKBWriter")
WKBReader = JClass("org.locationtech.jts.io.WKBReader")

IOException = JClass("java.io.IOException")
URISyntaxException = JClass("java.net.URISyntaxException")
