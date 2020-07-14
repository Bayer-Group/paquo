from jpype import JClass

from paquo.jpype_backend import start_jvm

# ensure the jvm is running
start_jvm()

ArrayList = JClass("java.util.ArrayList")
BufferedImage = JClass('java.awt.image.BufferedImage')
File = JClass('java.io.File')
String = JClass('java.lang.String')

ColorTools = JClass('qupath.lib.common.ColorTools')
DefaultProject = JClass('qupath.lib.projects.DefaultProject')
DefaultProjectImageEntry = JClass('qupath.lib.projects.DefaultProject.DefaultProjectImageEntry')
GsonTools = JClass('qupath.lib.io.GsonTools')
ImageServerProvider = JClass('qupath.lib.images.servers.ImageServerProvider')
PathClass = JClass('qupath.lib.objects.classes.PathClass')
PathClassFactory = JClass('qupath.lib.objects.classes.PathClassFactory')
PathObjects = JClass("qupath.lib.objects.PathObjects")
Point2 = JClass("qupath.lib.geom.Point2")
ProjectIO = JClass('qupath.lib.projects.ProjectIO')
Projects = JClass('qupath.lib.projects.Projects')
ROIs = JClass("qupath.lib.roi.ROIs")
ServerTools = JClass('qupath.lib.images.servers.ServerTools')
