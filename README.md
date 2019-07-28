Xcode Development Tools
=

copy_dylibs.py
==
`copy_dylibs.py` is used to detect `.dylib`s within the executable file that need to be copied into the app's `Framework` folder.  It does this recurisvely.  Only `.dylib`s that reside in `/usr/local`, `/opt/local` or `/User` are copied as it's assumed any others are system standard libraries and will be available on the end-user system.

Once copied, it modifies the `.dylib`s using `install_name_tool` to fix their references to use `@rpath` rather than their original path.

Xcode will provide all the information the script needs via environment variables, however additional (apparently unlinked) `.dylib`s can be specifed on the command line. This is useful for libraries that are loaded via `dlopen()` and therefore cannot be detected by the script.

Configuring
---
In order to configure `copy_dylibs.py` into your Xcode project:

- Add this repo as a submodule in a directory called `tools` within the workspace using `git submodule add https://github.com/trojanfoe/xcodedevtools tools`.
- Select the project settings of the **app target** and in the *Build Phases* tab press the `+` above *Target Dependencies* and select *New Run Script Phase*.
- In the new *Run Script* section simply add `../tools/copy_dylibs.py` in the topbox (depending on the relative location of the `tools` directory).


Code Signing
---
This script used to also code sign the `.dylib`s, however that has been removed in favour of passing `--deep` to the Code-signing app via *Other Code Signing Flags* in the project settings.

bump_buildnum.py
==
`bump_buildnum.py` This file is used to bump the version number of `.app`s if any source files have changed.
