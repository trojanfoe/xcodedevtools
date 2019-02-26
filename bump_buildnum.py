#!/usr/bin/env python
#
# Bump build number in Info.plist files if a source file have changed.
#
# usage: bump_buildnum.py buildnum.ver Info.plist [ ... Info.plist ]
#
# Copyright (c)2019 Andy Duplain <trojanfoe@gmail.com>
#

import sys, os, subprocess, re

def read_verfile(name):
    version = None
    build = None
    verfile = open(name, "r")
    for line in verfile:
        match = re.match(r"^version\s+(\S+)", line)
        if match:
            version = match.group(1).rstrip()
        match = re.match(r"^build\s+(\S+)", line)
        if match:
            build = int(match.group(1).rstrip())
    verfile.close()
    return (version, build)

def write_verfile(name, version, build):
    verfile = open(name, "w")
    verfile.write("version {0}\n".format(version))
    verfile.write("build {0}\n".format(build))
    verfile.close()
    return True

def set_plist_version(plistname, version, build):
    if not os.path.exists(plistname):
        print("{0} does not exist".format(plistname))
        return False

    plistbuddy = '/usr/libexec/Plistbuddy'
    if not os.path.exists(plistbuddy):
        print("{0} does not exist".format(plistbuddy))
        return False

    cmdline = [plistbuddy,
        "-c", "Set CFBundleShortVersionString {0}".format(version),
        "-c", "Set CFBundleVersion {0}".format(build),
        plistname]
    if subprocess.call(cmdline) != 0:
        print("Failed to update {0}".format(plistname))
        return False

    print("Updated {0} with v{1} ({2})".format(plistname, version, build))
    return True

def should_bump(vername, dirname):
    verstat = os.stat(vername)
    allnames = []
    for dirname, dirnames, filenames in os.walk(dirname):
        for filename in filenames:
            allnames.append(os.path.join(dirname, filename))

    for filename in allnames:
        filestat = os.stat(filename)
        if filestat.st_mtime > verstat.st_mtime:
            print("{0} is newer than {1}".format(filename, vername))
            return True

    return False

def upver(vername):
    (version, build) = read_verfile(vername)
    if version == None or build == None:
        print("Failed to read version/build from {0}".format(vername))
        return False

    # Bump the version number if any files in the same directory as the version file
    # have changed, including sub-directories.
    srcdir = os.path.dirname(vername)
    bump = should_bump(vername, srcdir)

    if bump:
        build += 1
        print("Incremented to build {0}".format(build))
        write_verfile(vername, version, build)
        print("Written {0}".format(vername))
    else:
        print("Staying at build {0}".format(build))

    return (version, build)

if __name__ == "__main__":
    if os.environ.has_key('ACTION') and os.environ['ACTION'] == 'clean':
        print("{0}: Not running while cleaning".format(sys.argv[0]))
        sys.exit(0)

    if len(sys.argv) < 3:
        print("Usage: {0} buildnum.ver Info.plist [... Info.plist]".format(sys.argv[0]))
        sys.exit(1)
    vername = sys.argv[1]

    (version, build) = upver(vername)
    if version == None or build == None:
        sys.exit(2)

    for i in range(2, len(sys.argv)):
        plistname = sys.argv[i]
        set_plist_version(plistname, version, build)

    sys.exit(0)
