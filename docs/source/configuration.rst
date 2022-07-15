Configuration
=============

.. note::
    `Paquo` uses `dynaconf <https://www.dynaconf.com/>`_ for configuration management.

`Paquo`\ s internal settings are configurable via a `.paquo.toml` file or via environment variables.
If anything remains unclear after reading this section, please open an issue in the github repository!

The .paquo.toml file
--------------------

To configure you `paquo` installation you can  place a `.paquo.toml` file in a spot where `paquo` can find it.
To list all possible locations *(note: it's very many)* run:

.. code-block:: console

    user@computer:~$ python -m paquo config --search-tree

This will output all search locations. These partially depend on where you run `paquo` from, which allows you
to override certain settings for a project you're working on by having a custom `.paquo.toml` file in a
project related location.

To get a default template for the `.paquo.toml` run:

.. code-block:: console

    user@computer:~$ python -m paquo config --list --default

This outputs the contents of the default paquo config toml:

.. literalinclude:: ../../paquo/.paquo.defaults.toml
    :language: toml
    :linenos:

.. tip::
    If you want to store this in the directory `./config` run

    .. code-block:: console

        user@computer:~$ python -m paquo config -l -o `./config`

    This will write a `.paquo.toml` file in the specified directory |:tada:|
    (The directory must already exist)




Environment variables
---------------------

All `paquo` settings can also be overridden by environment variables. Just prefix the particular
setting with :code:`PAQUO_` (single underscore!) and set the environment variable to what you
want it to be.

    PAQUO_QUPATH_DIR = :code:`""`
        if set will skip search and try to use qupath from this folder

    PAQUO_QUPATH_SEARCH_DIRS
        defaults to all default installation locations for QuPath this can be set to the folders that will be
        searched for QuPath installations.

    PAQUO_QUPATH_SEARCH_DIR_REGEX = :code:`"(?i)qupath.*"`
        used to regex match qupath_dirs during search

    PAQUO_QUPATH_SEARCH_CONDA = :code:`true`
        should the conda installed QuPath be considered?

    PAQUO_QUPATH_PREFER_CONDA = :code:`true`
        should the conda installed QuPath be preferred over another locally installed QuPath

    PAQUO_JAVA_OPTS = :code:`["-XX:MaxRAMPercentage=50",]`
        a list of JVM options passed to the java virtual machine

    PAQUO_MOCK_BACKEND = :code:`false`
        an internal setting which allows building the docs without having qupath installed

    PAQUO_CLI_FORCE_LOG_LEVEL_ERROR = :code:`true`
        only show paquo errors on cli

    PAQUO_WARN_MICROSOFT_STORE_PYTHON = :code:`true`
        windows only, warn if paquo is run via a microsoft store python


Verifying the config
--------------------

The easiest way to verify if your current configuration is correct is to run the command below,
which will output something like the following to the console, and represents your current config:

.. code-block:: console

    user@computer:~$ python -m paquo config --list
    # current paquo configuration
    # ===========================
    # format: TOML
    qupath_dir = ""
    qupath_search_dirs = [ "/usr/local",]
    qupath_search_dir_regex = "(?i)qupath.*"
    qupath_search_conda = true
    qupath_prefer_conda = true
    java_opts = [ "-XX:MaxRAMPercentage=50",]
    mock_backend = false

.. note::
    Or if you want to go directly via `dynaconf` you can run

    .. code-block:: console

        user@computer:~$ dynaconf -i paquo.settings list


Logging
-------

Paquo uses Python's :code:`logging` for console debug output. There's two logger namespaces for paquo:
"paquo" and "qupath". "paquo" logs :code:`paquo` internal things and the java loggers are reroutet through
the "qupath" logger.
