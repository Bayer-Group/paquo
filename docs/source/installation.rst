Installation
============

.. note::

    In its current incarnation `paquo` requires QuPath version `0.2.1`. This is mainly because we're
    developing and testing against this version right now. But this is bound to change (and other
    versions might already be supported). Follow
    `Paquo Issue #19 <https://github.com/bayer-science-for-a-better-life/paquo/issues/19>`_ to be
    notified when we're starting to work on this.

There's multiple ways to install `paquo`. We plan to offer pypi packages (coming soon...
`Paquo Issue #20 <https://github.com/bayer-science-for-a-better-life/paquo/issues/19>`_) and
conda packages. Right now the easiest way to setup your environment is via conda.


Install paquo's dev environment
-------------------------------

.. tip::
    This is currently the best way to get started |:snake:|


While we're rushing towards getting our
`first official release <https://github.com/bayer-science-for-a-better-life/paquo/projects/1>`_ out, we're
constantly changing and improving the way paquo operates. If you think you have what it takes to live on the
bleeding edge of paquo development, the easiest way is to make sure you have `git` and `conda` installed and
then run:

.. code-block:: console

    user@computer:~$ git clone git@github.com:bayer-science-for-a-better-life/paquo.git
    user@computer:~$ cd paquo
    user@computer:paquo$ conda env create -f environment.yml

This will create a **paquo** conda environment with everything you need to get started. It installs a
special conda-packaged `QuPath <https://github.com/bayer-science-for-a-better-life/qupath-feedstock>`_
that we're currently using to develop `paquo` and also installs all the other things required to let
you get started. You should be able to run:

.. code-block:: console

    user@computer:paquo$ conda activate paquo
    (paquo) user@computer:paquo$ pytest

And you should see that all the tests pass |:heart:|



Install paquo via conda
-----------------------

`Paquo` will be installable via `conda-forge <https://conda-forge.org/>`_ when we publish the first release.


Install paquo via pip
---------------------

`Paquo` will be installable via `pypi` when we publish the first release. In the meantime if you can't wait,
you can install via pip and a direct reference to the github repository:

.. code-block:: console

    user@computer:~$ pip install git+https://github.com/bayer-science-for-a-better-life/paquo.git

This will also require you to install QuPath. Make sure that for now, you install QuPath version `0.2.1`
(get it `here <https://github.com/qupath/qupath/releases/tag/v0.2.1>`_). As long as you install in the
default directory paquo should be able to find it. If you have to install it somewhere else you need
to start your python scripts like this:

.. code-block:: python

    from paquo.jpype_backend import start_jvm, find_qupath
    MY_CUSTOM_QUPATH_DIR = "/home/user/my_custom_qupath_install/"
    start_jvm(finder=lambda: find_qupath([MY_CUSTOM_QUPATH_DIR]))

    from paquo.projects import QuPathProject
    ...

The above will change in the future when a better way to configure `paquo` is implemented. Follow
`Paquo Issue #3 <https://github.com/bayer-science-for-a-better-life/paquo/issues/3>`_ for updates.










