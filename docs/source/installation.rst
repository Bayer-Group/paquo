Installation
============

.. note::

    In its current incarnation `paquo` requires QuPath version `0.2.1` or higher. This is mainly
    because we're developing and testing against this version right now. But this is bound to
    change (and other versions might already be supported). Follow
    `Paquo Issue #19 <https://github.com/bayer-science-for-a-better-life/paquo/issues/19>`_ to be
    notified when we're starting to work on this.

There's multiple ways to install `paquo`. We offer pypi packages and will soon provide
conda packages too. Right now the easiest way to help develop is to setup your environment via conda.


Install paquo's dev environment
-------------------------------

.. tip::
    This is currently the best way to get started |:snake:|


While we're rushing towards getting our
`first official release <https://github.com/bayer-science-for-a-better-life/paquo/projects/1>`_ out, we're
constantly changing and improving the way paquo operates. If you think you have what it takes to live on the
bleeding edge of paquo development, the easiest way is to make sure you have `git` and `conda` and
`conda-devenv <https://github.com/ESSS/conda-devenv>`_ installed and then run:

.. code-block:: console

    user@computer:~$ git clone https://github.com/bayer-science-for-a-better-life/paquo.git
    user@computer:~$ cd paquo
    user@computer:paquo$ conda devenv --env PAQUO_DEVEL=True --print > environment.yml
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

`paquo` will be installable via `conda-forge <https://conda-forge.org/>`_ when we publish the first conda packages.


Install paquo via pip
---------------------

`paquo` is installable via `pypi`. Run:

.. code-block:: console

    user@computer:~$ pip install paquo

To get the latest release. You will have to install QuPath on your machine for paquo to work correctly. Also if
you want the latest development version, you can install via pip and a direct reference to the github repository:

.. code-block:: console

    user@computer:~$ pip install git+https://github.com/bayer-science-for-a-better-life/paquo.git

This will also require you to install QuPath. Make sure that for now, you install QuPath version `0.2.1`
or newer (get it `here <https://github.com/qupath/qupath/releases/tag/v0.2.1>`_). As long as you install
in the default directory paquo should be able to find it. If you have to install it somewhere else you need
to configure paquo so that it can find it. Check out the :ref:`Configuration` section to learn more.
