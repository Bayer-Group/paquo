from jpype import JClass

from paquo.jpype_backend import start_jvm

# ensure the jvm is running
start_jvm()

ArrayList = JClass("java.util.ArrayList")
BufferedImage = JClass('java.awt.image.BufferedImage')
File = JClass('java.io.File')
Integer = JClass('java.lang.Integer')
String = JClass('java.lang.String')

ColorTools = JClass('qupath.lib.common.ColorTools')
DefaultProject = JClass('qupath.lib.projects.DefaultProject')
DefaultProjectImageEntry = JClass('qupath.lib.projects.DefaultProject.DefaultProjectImageEntry')
GeometryTools = JClass("qupath.lib.roi.GeometryTools")
GsonTools = JClass('qupath.lib.io.GsonTools')
ImageServerProvider = JClass('qupath.lib.images.servers.ImageServerProvider')
PathAnnotationObject = JClass("qupath.lib.objects.PathAnnotationObject")
PathClass = JClass('qupath.lib.objects.classes.PathClass')
PathClassFactory = JClass('qupath.lib.objects.classes.PathClassFactory')
PathObjectHierarchy = JClass('qupath.lib.objects.hierarchy.PathObjectHierarchy')
PathObjects = JClass("qupath.lib.objects.PathObjects")
Point2 = JClass("qupath.lib.geom.Point2")
ProjectIO = JClass('qupath.lib.projects.ProjectIO')
Projects = JClass('qupath.lib.projects.Projects')
ROI = JClass("qupath.lib.roi.interfaces.ROI")
ROIs = JClass("qupath.lib.roi.ROIs")
ServerTools = JClass('qupath.lib.images.servers.ServerTools')

WKBWriter = JClass("org.locationtech.jts.io.WKBWriter")
WKBReader = JClass("org.locationtech.jts.io.WKBReader")
