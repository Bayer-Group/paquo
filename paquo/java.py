from jpype import JClass
from paquo.jpype_backend import start_jvm

# ensure the jvm is running
start_jvm()

JArrayList = JClass("java.util.ArrayList")
JBufferedImage = JClass('java.awt.image.BufferedImage')
JFile = JClass('java.io.File')
JString = JClass('java.lang.String')

JColorTools = JClass('qupath.lib.common.ColorTools')
JDefaultProject = JClass('qupath.lib.projects.DefaultProject')
JDefaultProjectImageEntry = JClass('qupath.lib.projects.DefaultProject.DefaultProjectImageEntry')
JGsonTools = JClass('qupath.lib.io.GsonTools')
JImageServerProvider = JClass('qupath.lib.images.servers.ImageServerProvider')
JPathClass = JClass('qupath.lib.objects.classes.PathClass')
JPathClassFactory = JClass('qupath.lib.objects.classes.PathClassFactory')
JPathObjects = JClass("qupath.lib.objects.PathObjects")
JPoint2 = JClass("qupath.lib.geom.Point2")
JProjectIO = JClass('qupath.lib.projects.ProjectIO')
JProjects = JClass('qupath.lib.projects.Projects')
JROIs = JClass("qupath.lib.roi.ROIs")
JServerTools = JClass('qupath.lib.images.servers.ServerTools')
