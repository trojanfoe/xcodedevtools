#!/usr/bin/env python
from __future__ import print_function

"""Copy dylibs into the build folder.

Usage: copy_dylibs.py [dylib ... dylib]

If additional dylibs are specified on the command line, they will be copied into the app bundle.

Copyright (c)2019,2021 Andy Duplain <trojanfoe@gmail.com>

"""

import sys, os, traceback, shutil, subprocess, re

# Any dependencies outside of these directories needs copying and fixing
good_dirs = [ '/System/', '/usr/lib/', '@rpath/' ]

# Turn on for more output
debug = False

frameworks_dir = None

# Module and library install_name changes:
# {
#    dylib_path : [ old_name, new_name ], ..., [old_name, new_name]
#    ...
# }
install_names = {}

# List of dylibs copied
copied_dylibs = set()

def is_file_good(file):
	for dir in good_dirs:
		if file.startswith(dir):
			return True
	return False

def copy_dylib(src):
	global copied_dylibs

	(dylib_path, dylib_filename) = os.path.split(src)
	dest = os.path.join(frameworks_dir, dylib_filename)

	if not os.path.exists(dest):
		if debug:
			print("Copying {0} into bundle".format(src))
		shutil.copyfile(src, dest)
		os.chmod(dest, 0o644)
		copied_dylibs.add(dest)
		copy_dependencies(dest)

def copy_dependencies(file):
	global install_names

	(file_path, file_filename) = os.path.split(file)
	print("Examining {0}".format(file_filename))
	found = 0
	pipe = subprocess.Popen(['otool', '-L', file], stdout=subprocess.PIPE)
	while True:
		line = pipe.stdout.readline().decode("utf-8")
		if line == '':
			break
		# 	/opt/local/lib/libz.1.dylib (compatibility version 1.0.0, current version 1.2.8)
		m = re.match(r'\s*(\S+)\s*\(compatibility version .+\)$', line)
		if m:
			dep = m.group(1)
			if not is_file_good(dep):
				(dep_path, dep_filename) = os.path.split(dep)
				dest = os.path.join(frameworks_dir, dep_filename)

				if dep_filename != file_filename:
					print(" ...found external dependency {0}".format(dep))
					found += 1

				list = []
				if file in install_names:
					list = install_names[file]
				list.append([dep, '@rpath/' + dep_filename])
				install_names[file] = list

				copy_dylib(dep)

	if found == 0:
		print("... no external dependencies found")

def change_install_names():
	for dylib in install_names.keys():
		(dylib_path, dylib_filename) = os.path.split(dylib)
		list = install_names[dylib]
		for install_name in list:
			old_name = install_name[0]
			new_name = install_name[1]
			if debug:
				print("{0}: old={1} new={2}".format(dylib, old_name, new_name))
			(old_name_path, old_name_filename) = os.path.split(old_name)
			if dylib_filename == old_name_filename:
				cmdline = ['install_name_tool', '-id', new_name, dylib]
			else:
				cmdline = ['install_name_tool', '-change', old_name, new_name, dylib]
			if debug:
				print("Running: " + " ".join(cmdline))
			exitcode = subprocess.call(cmdline)
			if exitcode != 0:
				raise RuntimeError("Failed to change '{0}' to '{1}' in '{2}".format(old_name, new_name, dylib))

def main(args):
	global frameworks_dir

	# Only work during builds
	action = 'build'
	if 'ACTION' in os.environ:
		action = os.environ['ACTION']
	if action != 'build':
		return 0

	# Set-up output directories within app bundle
	build_dir = os.environ['TARGET_BUILD_DIR']
	frameworks_path = os.environ['FRAMEWORKS_FOLDER_PATH']
	frameworks_dir = os.path.join(build_dir, frameworks_path)

	executable_path = os.environ['EXECUTABLE_PATH']
	executable_file = os.path.join(build_dir, executable_path)

	if os.path.exists(frameworks_dir):
		# Process existing .dylib files in Frameworks directory first as Xcode might have copied them and they might need attention
		for file in os.listdir(frameworks_dir):
			if file.endswith(".dylib"):
				copy_dependencies(os.path.join(frameworks_dir, file))
	else:
		os.makedirs(frameworks_dir)

	# Copy additional dylibs
	if len(args) > 1:
		for arg in args[1:]:
			copy_dylib(arg)

	# Process main executable
	copy_dependencies(executable_file)

	change_install_names()

	if debug:
		print("This is what your executable looks like now:")
		pipe = subprocess.Popen(['otool', '-L', executable_file], stdout=subprocess.PIPE)
		while True:
			line = pipe.stdout.readline().decode("utf-8")
			if line == '':
				break
			print(line, end='')

	print("\nRemember to add '--deep' to your 'Other Code Signing Flags'")

if __name__ == "__main__":
	exitcode = 99
	try:
		exitcode = main(sys.argv)
	except Exception as e:
		print(traceback.format_exc())
	sys.exit(exitcode)
