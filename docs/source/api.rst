Paquo API
=========

QuPathProjects
--------------

`Paquo`'s most used class is the :class:`QuPathProject`. Through it you're accessing images, annotation,
metadata and everything that QuPath has to offer (|:sweat_smile:| let us know if something's missing!)

.. autoclass:: paquo.projects.QuPathProject
   :members:

QuPathPathClasses
-----------------

Classes are used to group your annotation into *(you've guessed it)* classes. :class:`QuPathPathClasses` can
have names, a color and they can be children of other classes. If you want to create a new `QuPathPathClass`
just instantiate it by providing a name and an optional color and optional parent class.

.. autoclass:: paquo.classes.QuPathPathClass
   :members:

QuPathProjectImageEntries
-------------------------

Images in `paquo` cannot exist on their own and are always bound to a `QuPathProject`.
You access them via :meth:`QuPathProject.images` or you make a new one from a file via
:meth:`QuPathProject.add_image`. Images let you set a description, provide you with
interfaces for metadata and properties and give you access to the various QuPath annotation
and detections objects through the :class:`QuPathPathObjectHierarchy`.


.. autoclass:: paquo.images.QuPathProjectImageEntry
   :members:

.. autoclass:: paquo.images.QuPathImageType

    .. autoattribute:: BRIGHTFIELD_H_DAB

    .. autoattribute:: BRIGHTFIELD_H_E

    .. autoattribute:: BRIGHTFIELD_OTHER

    .. autoattribute:: FLUORESCENCE

    .. autoattribute:: OTHER

    .. autoattribute:: UNSET

.. note::
    There's an additional :class:`paquo.images.ImageProvider` class which will be introduced
    when `paquo` settles on its implementation. See
    `Paquo Issue #13 <https://github.com/bayer-science-for-a-better-life/paquo/issues/13>`_.

QuPathPathObjectHierarchy
-------------------------

The hierarchy is accessed via `QuPathProjectImageEntry.hierarchy`. It contains proxy objects that
allow you to access annotations and detections, as well as importing and exporting them to
`geojson <https://geojson.org>`_.

.. autoclass:: paquo.hierarchy.QuPathPathObjectHierarchy
   :members:

QuPathPathObjects
-----------------

Annotations and detections are encapsulated via :class:`QuPathPathAnnotationObjects`.

.. autoclass:: paquo.pathobjects._PathROIObject
    :members:

.. autoclass:: paquo.pathobjects.QuPathPathAnnotationObject
    :show-inheritance:

    .. autoattribute:: description

.. autoclass:: paquo.pathobjects.QuPathPathDetectionObject
    :show-inheritance:

.. autoclass:: paquo.pathobjects.QuPathPathTileObject
    :show-inheritance:

QuPathColor
-----------

Colors in QuPath are represented as non-human-friendly integers. :class:`QuPathColor` provides
a nicer interface to allow more intuitive color handling.

.. autoclass:: paquo.colors.QuPathColor
   :members:

And more...
-----------

If anything is not documented and you would love to know more about it, open an issue and let us know!
We're happy to provide more documentation and clear things up! |:sparkling_heart:|
