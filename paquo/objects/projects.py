import pathlib
from typing import Union
from paquo.qupath.jpype_backend import java_import, jvm_running

# import java classes
with jvm_running():
    _BufferedImage = java_import('java.awt.image.BufferedImage')
    # _DefaultProject = java_import('qupath.lib.projects.DefaultProject')
    # _Project = java_import('qupath.lib.projects.Project')
    _Projects = java_import('qupath.lib.projects.Projects')
    _ProjectIO = java_import('qupath.lib.projects.ProjectIO')
    _File = java_import('java.io.File')


class QuPathProject:

    def __init__(self, path: Union[str, pathlib.Path]):
        path = pathlib.Path(path)
        if path.is_file():
            self._project = _ProjectIO.loadProject(_File(str(path)), _BufferedImage)
        else:
            self._project = _Projects.createProject(_File(str(path)), _BufferedImage)

    # TODO: implement list/set interface
    #   image entries can be duplicated. but uri should be unique.
    # some list like proxy
    # images = []

    def __len__(self):
        # return len(self.images)
        return 0  # TODO

    @property
    def image_id(self):
        return self._project.IMAGE_ID

    @property
    def uri(self):
        return self._project.getURI().toString()

    @property
    def uri_previous(self):
        uri = self._project.getPreviousURI()
        if uri is None:
            return None
        return uri.toString()

    @property
    def path_classes(self):
        # self._project.getPathClasses()
        return []  # TODO

    @path_classes.setter
    def path_classes(self, path_class):
        # TODO: look for shapely abstraction to cast to PathClass
        # self._project.setPathClasses()
        pass  # TODO

    @property
    def path(self):
        return self._project.getPath()

    def save(self):
        self._project.syncChanges()

    @property
    def mask_image_names(self):
        return bool(self._project.getMaskImageNames())

    @mask_image_names.setter
    def mask_image_names(self, value: bool):
        self._project.setMaskImageNames(value)

    @property
    def name(self):
        return self._project.getName()

    def __repr__(self):
        name = self._project.getNameFromURI(self.uri)
        return f'<QuPathProject {name}>'

    @property
    def timestamp_creation(self):
        return self._project.getCreationTimestamp()

    @property
    def timestamp_modification(self):
        return self._project.getModificationTimestamp()

    @property
    def version(self):
        return self._project.getVersion()
