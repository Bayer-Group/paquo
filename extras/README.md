# paquo - extras

We'll include some potentially interesting code snippets in here, in case they might be useful to someone.
Feel free to open issues if something is unclear.

### osx_app_shim

This snippet might come in handy for you, if you're interested in using a custom paquo script as an app on OSX.
The simple example uses paquo's commandline "open" subcommand to open a QuPath project, but you can easily adapt the
script to do whatever complex thing you want to achieve.

To create a usable OSX app install `py2app` in you conda environment and run:

```console
$> cd extras/osx_app_shim
$> python setup.py py2app -A
```

This will create an app in `extras/osx_app_shim/dist/PaquoOpenQpZip.app` in alias mode.
Please refer to the `py2app` documentation if you need the app to be portable.

You can now run
```console
$> cd extras/osx_app_shim/dist
$> open -a PaquoOpenQpZip.app ~/path-to-my-wonderful/example-qupath-project
```
and it will launch QuPath with the example-qupath-project.
