# Xcode Development Tools

A small collection of scripts I have developed to make working with Xcode easier.

## copy_dylibs.py
`copy_dylibs.py` is used to detect and copy local dependencies into your app bundle.

A local dependency is a dynamic library that you will have built yourself or installed using a package management tool like homebrew or MacPorts.  They won't exist on the end-user system and therefore your app won't run on their system if you have used them.

Any dependency that resides outside of `/System` or `/usr/lib` is deemed a local dependency.

The script works by examining the main executable and looking for local dependencies and then copying them into the app bundle `Frameworks` folder.  Any local dependencies copied are themselves examined to see if they use any other local dependencies, ad infinitum.

When a local dependency is copied into the app bundle, its "install name" is adjusted in both the executable/dynamic library that references it and within the dependency itself.  The script changes the "install name" to use [`@rpath`](https://developer.apple.com/library/archive/documentation/DeveloperTools/Conceptual/DynamicLibraries/100-Articles/RunpathDependentLibraries.html) instead of an absolute path.

Xcode will provide all the information the script needs, via environment variables, however additional local dependencies can be specifed on the command line. This is useful for libraries that are loaded via `dlopen()` and therefore cannot be detected by the script.


### Configuring
In order to configure `copy_dylibs.py` into your Xcode project:

- Add this repo as a submodule in a directory of your choosing, for example `External`, using `git submodule add https://github.com/trojanfoe/xcodedevtools External`.
- Select the project settings of the **App Target** and in the *Build Phases* tab press the `+` top-left above *Target Dependencies* and select *New Run Script Phase*.
- In the new *Run Script* section put `python $PROJECT_DIR/External/copy_dylibs.py` in the top textbox, depending on where you added the submodule.
- You may also want to rename the *Run Script* to something like *Copy dylibs* to make it more obvious what it's doing.


### Code Signing
The script will code sign all `.dylib` files that it copies into the app bundle.

Previously I was relying on adding `--deep` to the *Other Code Signing Flags*, however I have noticed that has no effect when running an app on an iOS device and the embedded frameworks remain unsigned.  The `--deep` flag does work when running on the iOS Simulator or running a native macOS app, however to cover all cases I have put code signing back.

## bump_buildnum.py
`bump_buildnum.py` is used to manage build number versioning of your app bundle.

It works by maintaining a `.ver` file in the source tree that is incremented whenever a source file change is detected during a build.  The updated build number is then written into the `Info.plist` file to allow for automatic versioning.  Only the build version is incremented, and the main version needs to be incremented manually, based on feature updates that only you know about.

It is configured in a similar way to `copy_dylibs.py`.

I don't use it any longer so don't have much more to say about it, however if you find it useful let me know and I'll put more effort into documenting it.
