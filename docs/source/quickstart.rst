Quickstart
==========

`Paquo` uses `shapely <https://shapely.readthedocs.io>`_ to provide a pythonic
interface to Qupath's annotations. It's recommended to make yourself familiar
with shapely.



Examples
--------

You can find the code for many use case examples
To get started setup a python environment with `paquo`. Git clone the repository and cd to the
examples directory.

.. code-block:: console

    user@computer:~$ git clone git@github.com:bayer-science-for-a-better-life/paquo.git
    user@computer:~$ cd paquo/examples
    user@computer:examples$ python prepare_resources.py

This will create a folder `images` and a folder `projects` with example data.
These are required for all of the examples to run. Refer to the examples to
quickly learn how to solve a certain problem with paquo. In case your specific
problem does not have an example yet, feel free to open a new issue in `paquo`'s
`issue tracker <https://github.com/bayer-science-for-a-better-life/paquo/issues>`_.

.. tip::
    If you already have a solution for a problem and think it might
    have value for others *(NOTE: it always does!)* feel free to fork the `paquo`
    repository and create a Pull Request adding the new example.


Reading annotations
^^^^^^^^^^^^^^^^^^^

To read annotations from an existing project follow the code as shown here:

.. literalinclude:: ../../examples/example_01_read_annotations.py
    :language: python
    :linenos:

Add annotations to a project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To add annotations to a project you simply need to define them as `shapely` Geometries and
then add them to your QuPath project as demonstrated here:

.. literalinclude:: ../../examples/example_02_add_annotations.py
    :language: python
    :linenos:

Predefine classes in a project
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Sometimes you might want to create projects with many predefined classes so that different users
wont mistype the class names, or that you can enforce a unique coloring scheme accross your projects.
Adding classes is as simple as:

.. literalinclude:: ../../examples/example_03_project_with_classes.py
    :language: python
    :linenos:

Add image metadata
^^^^^^^^^^^^^^^^^^

Especially in bigger projects it can be useful if you know, you annotated a certain image, or what's
the current state of the annotations. For those things it's best to use metadata like this:

.. literalinclude:: ../../examples/example_04_project_with_image_metadata.py
    :language: python
    :linenos:

Drawing tiled overlays
^^^^^^^^^^^^^^^^^^^^^^

If you want to display additional information on top of your image, that can be easily hidden by a user,
You can use `TileDetectionObjects` to build a grid containing measurement values:

.. literalinclude:: ../../examples/example_05_draw_tiles_on_image.py
    :language: python
    :linenos:

This will allow you to display extra data like this:

.. image:: _static/screenshot_example_05.png
    :width: 400
    :alt: Tile Overlay Example 05

More examples
^^^^^^^^^^^^^

We need your input! |:bow:|

.. tip::
    In case you need another example for the specific thing you'd like to do, please feel free to open a new
    issue on `paquo`'s `issue tracker <https://github.com/bayer-science-for-a-better-life/paquo/issues>`_.
    We'll try our best to help you |:+1:|
