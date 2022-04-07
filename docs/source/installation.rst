Installation
============

.. note::

    `paquo` should work with any QuPath version starting with `0.2.0` or higher. Follow
    `Paquo Issue #19 <https://github.com/bayer-science-for-a-better-life/paquo/issues/19>`_ to be
    notified when we're starting to work on adding QuPath version tests to our CI.


Install paquo
-------------

`paquo` is installable via `pypi`. To get the newest stable version, run:

.. code-block:: console

    user@computer:~$ pip install paquo

You can also install it via `conda`:

.. code-block:: console

    user@computer:~$ conda install -c conda-forge paquo


Install QuPath
--------------

`paquo` requires a working QuPath installation. Please follow the instructions
`here <https://qupath.readthedocs.io/en/stable/docs/intro/installation.html>`_ on how to install QuPath on your
system. As long as you install in the default directory paquo should be able to find it without any additional
configuration. If you have installed QuPath in a different location, you need to configure paquo so that it can
find it. Check out the :ref:`Configuration` section to learn more.


.. tip::

    For your convenience we added a commandline option to the `paquo` commandline interface to
    simplify installing a specific version of QuPath. After having installed paquo, run:

    .. code-block:: console

        user@computer:~$ paquo get_qupath --install-path ./some-directory 0.3.2

    This will download the specified version and extract it to ./some-directory. It also prints
    some instructions on how to use paquo with the downloaded QuPath.


Install paquo's dev environment
-------------------------------

While we're rushing towards the next release, we're constantly changing and improving the way paquo operates.
If you think you have what it takes to live on the bleeding edge of paquo development, the easiest way is to
make sure you have `git` and `conda` and `conda-devenv <https://github.com/ESSS/conda-devenv>`_ installed and
then run:

.. code-block:: console

    user@computer:~$ git clone https://github.com/bayer-science-for-a-better-life/paquo.git
    user@computer:~$ cd paquo
    user@computer:paquo$ conda devenv --env PAQUO_DEVEL=True --print > environment.yml
    user@computer:paquo$ conda env create -f environment.yml

This will create a **paquo** conda environment with everything you need to get started. It installs a
special conda-packaged `QuPath <https://github.com/bayer-science-for-a-better-life/qupath-feedstock>`_
that we're currently using to develop `paquo` and also installs all the other things required. You
should now be able to run:

.. code-block:: console

    user@computer:paquo$ conda activate paquo
    (paquo) user@computer:paquo$ pytest

And you should see that all the tests pass |:heart:|
