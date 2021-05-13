# Meson Wrap DataBase

This is an experiment at importing all meson ports from wrapdb into a single
git repository to make contribution as easy as a simple Pull Request.

## How to test a wrap

Clone this repository locally, and set the `wraps` option with a coma separated
list of wraps that needs to be built.

For example to test libjpeg-turbo and zlib:
```sh
meson setup builddir -Dwraps=libjpeg-turbo,zlib
meson compile -C builddir
```

## How to contribute new wraps

- Write [`my-project.wrap`](https://mesonbuild.com/Wrap-dependency-system-manual.html)
  file and add it in `subprojects/` directory.

- If upstream project's build system is not Meson, a port can be added in
  `subprojects/packagefiles/my-project/meson.build` and
  `patch_directory = my-subproject` should be added into the wrap file.
  Note that the whole `subprojects/packagefiles/my-project` subtree will be
  copied onto the upstream's source tree, but it is generally not accepted to
  override upstream files.

- Add your release tag in `releases.txt`. The format is
  `<project-name>_<project-version>-<revision>`, one tag per line.
  For example `glib_2.68.0-1` where `glib` is the project name and must match
  `glib.wrap` file, `2.68.0` is upstream version and `1` is the first revision
  in wrapdb.

- Create Pull Request with your changes, once merged it will be available to
  everyone using `meson wrap install my-project`.

## How to import one of those wraps into my project

TODO: `meson wrap install libjpeg-turbo` should be modified to pull
`libjpeg-turbo.wrap` from this repository's releases.
