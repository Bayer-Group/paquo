# Paquo examples

In this directory you'll find examples for common problems and how to solve them
with `paquo`. **Please be aware that until `paquo` reaches it's first stable
major release, things are bound to change dramatically.** We're trying to keep
the examples up to date with current best practices, but it might be possible
that there's already better ways to do this.

To get started setup a python environment with `paquo` (follow the docs on how
to install). Change to the examples directory and run:

```console
user@computer:~$ python prepare_resources.py
```

This will create a folder `images` and a folder `projects` with example data.
These are required for all of the examples to run. Refer to the examples to
quickly learn how to solve a certain problem with paquo. In case your specific
problem does not have an example yet, feel free to open a new issue in `paquo`'s
issue tracker. If you already have a solution for a problem and think it might
have value for others (_NOTE: it always does!_) feel free to fork the `paquo`
repository and create a Pull Request adding the new example.

```console
user@computer:~$ python example_project_with_classes.py
```

**NOTE:** modifying a project from python while it's opened in QuPath will cause
issues. It's best to not access a project from QuPath and Python simultaneously.

If anything is unclear or confusing, open an issue. We're happy to help and
always keen on improving the documentation and instructions! :sparkling_heart:
