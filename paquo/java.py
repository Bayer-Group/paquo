from distutils.util import strtobool
import os

from paquo.jpype_backend import start_jvm, JClass

RUNNING_ON_RTD = strtobool(os.environ.get('READTHEDOCS', 'false'))
if RUNNING_ON_RTD:
    def start_jvm(*args, **kwargs):
        pass

    class JClass:
        def __init__(self, *args, **kwargs):
            pass


# ensure the jvm is running
start_jvm()

ArrayList = JClass("java.util.ArrayList")
BufferedImage = JClass('java.awt.image.BufferedImage')
File = JClass('java.io.File')
Integer = JClass('java.lang.Integer')
String = JClass('java.lang.String')
URI = JClass('java.net.URI')

ColorTools = JClass('qupath.lib.common.ColorTools')
DefaultProject = JClass('qupath.lib.projects.DefaultProject')
DefaultProjectImageEntry = JClass('qupath.lib.projects.DefaultProject.DefaultProjectImageEntry')
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