Xcode Development Tools
=======================

This repo contains Xcode scripts:

`copy_dylibs.py` is used to detect `.dylib`s within the executable file that need to be
copied into the `.app`s `Framework`.  It also detects dependent libraries that also need
to be copied.  Once copied it modifies the `.dylib`s using `install_name_tool` to fix
their references to use `@rpath` rather than their original path.

`bump_buildnum.py` This file is used to bump the version number of `.app`s if any
source files have changed.