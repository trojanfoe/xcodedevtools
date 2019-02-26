#!/usr/bin/python

"""Copy dylibs into the build folder.

Usage: copy_dylibs.py 

- Searches the target executable for dylibs to copy.
- Any dependent dylibs that reside in /usr/local/lib or /opt/local/lib are copied into
  $TARGET_BUILD_DIR/$FRAMEWORKS_FOLDER_PATH.
- All 'install name' values are adjusted so libraries are found within the app bundle, relative to
  @rpath@.
- All libraries are code-signed, if $CODE_SIGN_IDENTITY is set.
"""

import sys, os, imp, traceback, shutil, subprocess, re
from sets import Set

frameworks_folder = None

# Module and library install_name changes:
# {
#    dylib_path : [ old_name, new_name ], ..., [old_name, new_name]
#    ...
# }
install_names = {}

# List of dylibs copied
copied_dylibs = Set()

def copy_dylib(src):
    global copied_dylibs

    (dylib_path, dylib_filename) = os.path.split(src)
    dest = os.path.join(frameworks_folder, dylib_filename)

    if os.path.exists(dest):
        print "'{0}' already exists, so not copying".format(dest)
        return

    shutil.copyfile(src, dest)
        
    #cmdline = ['lipo', src, '-extract', 'x86_64', '-output', dest]
    #print "Running", " ".join(cmdline)
    #exitcode = subprocess.call(cmdline)
    #if exitcode != 0:
    #    raise RuntimeError("Failed to copy '{0}' to '{1}'".format(src, dest))

    os.chmod(dest, 0644)
    copied_dylibs.add(dest)
    copy_dependencies(dest)

def copy_dependencies(file):
    global install_names

    (file_path, file_filename) = os.path.split(file)
    pipe = subprocess.Popen(['otool', '-L', file], stdout=subprocess.PIPE)
    while True:
        line = pipe.stdout.readline()
        if line == '':
            break
        # 	/opt/local/lib/libz.1.dylib (compatibility version 1.0.0, current version 1.2.8)
        m = re.match(r'\s*(\S+)\s*\(compatibility version .+\)$', line)
        if m:
            dep = m.group(1)
            (dep_path, dep_filename) = os.path.split(dep)
            if dep_path == '' or dep_path == '/opt/local/lib' or dep_path == '/usr/local/lib':
                dest = os.path.join(frameworks_folder, dep_filename)

                list = []
                if file in install_names:
                    list = install_names[file]
                list.append([dep, '@rpath/' + dep_filename])
                install_names[file] = list

                if dep_path == '':
                    dep = os.path.join('/usr/local/lib', dep_filename)

                copy_dylib(dep)
    
def change_install_names():
    for dylib in install_names.keys():
        (dylib_path, dylib_filename) = os.path.split(dylib)
        list = install_names[dylib]
        for install_name in list:
            old_name = install_name[0]
            new_name = install_name[1]
            #print dylib, "old=", old_name, "new=", new_name
            (old_name_path, old_name_filename) = os.path.split(old_name)
            if dylib_filename == old_name_filename:
                cmdline = ['install_name_tool', '-id', new_name, dylib]
            else:
                cmdline = ['install_name_tool', '-change', old_name, new_name, dylib]
            print "Running", " ".join(cmdline)
            exitcode = subprocess.call(cmdline)
            if exitcode != 0:
                raise RuntimeError("Failed to change '{0}' to '{1}' in '{2}".format(old_name, new_name, dylib))
    
def codesign():
    if not 'CODE_SIGN_IDENTITY' in os.environ:
        print "Not code-signing as $CODE_SIGN_IDENTITY is not set"
        return
    for dylib in copied_dylibs:
        cmdline = ['codesign', '--force', '--sign', os.environ['CODE_SIGN_IDENTITY'], dylib]
        print "Running", " ".join(cmdline)
        exitcode = subprocess.call(cmdline)
        if exitcode != 0:
            raise RuntimeError("Failed to codesign '{0}".format(dylib))
        
def main():
    global frameworks_folder
    
    # Only work during builds
    action = 'build'
    if 'ACTION' in os.environ:
        action = os.environ['ACTION']
    if action != 'build':
        return 0
        
    # Set-up output directories within app bundle
    build_dir = os.environ['TARGET_BUILD_DIR']
    frameworks_path = os.environ['FRAMEWORKS_FOLDER_PATH']
    executable_path = os.environ['EXECUTABLE_PATH']

    executable_file = os.path.join(build_dir, executable_path)
    
    frameworks_folder = os.path.join(build_dir, frameworks_path)
    if not os.path.exists(frameworks_folder):
        os.makedirs(frameworks_folder)

    copy_dependencies(executable_file)

    change_install_names()
    
    codesign()

if __name__ == "__main__":
    exitcode = 99
    try:
        exitcode = main()
    except Exception as e:
        print traceback.format_exc()
    sys.exit(exitcode)