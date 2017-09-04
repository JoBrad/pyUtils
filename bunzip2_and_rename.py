#!/usr/bin/env python
from __future__ import (absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement)
from bz2 import decompress, BZ2File
import glob
import os
import re
import sys
"""
Decompresses bz2 files in a given path, and outputs the result to a file with the same name
as the source file, minus the .bz2 extension as well as a trailing timestamp, if it exists.
This script was made to work in Python 2.6+

Examples:
    some-random-filename.json.2017-05-09-09:00:06.bz2 -> some-random-filename.json
    SOME_OTHER_RANDOM_FILENAME_20170613_102515.TXT.2017-06-13-10:17:01.bz2 -> SOME_OTHER_RANDOM_FILENAME_20170613_102515.TXT
"""

TIMESTAMP_PATTERN = re.compile(r'(\.?\d\d\d\d\-\d\d\-\d\d\-\d\d[\-\:]\d\d[\-\:]\d\d$)')

def show_help():
    """
    Shows some help for the script
    """
    print('Decompresses and renames files to match their expected original name')
    print('Usage: bunzip_and_rename file_path')
    print('    file_path: Either a path to process for files, or a single file to process')


def get_files(dir_names):
    """
    Returns a set of files from the provide path, paths, glob, or globs
    """
    return_files = set()

    if isinstance(dir_names, str):
        dir_names = [dir_names]

    # Allow for multiple files to be processed
    for dir_name in dir_names:
        dir_files = set()
        # Expand ~ and any vars; correct slashes
        dir_name = os.path.expandvars(os.path.expanduser(os.path.normcase(os.path.normpath(dir_name))))

        # Is this just a filename?
        if os.path.dirname(dir_name) == '':
            dir_name = os.path.abspath(dir_name)

        # Check for glob patterns
        if any([g_char in dir_name for g_char in '?[].*']):
            dir_files.update(set(glob.glob(dir_name)))
        # Do we have a full path to a file?
        elif os.path.isfile(dir_name):
            dir_files.add(dir_name)
        else:
            # Assume this is a path where we should find files
            try:
                dir_files.update(set(os.path.join(os.path.normcase(dirpath), filename) for dirpath, _, filenames in os.walk(dir_name) for filename in filenames))
            except TypeError as te_err:
                print('Error trying to get files from {0}!\nError details: {1}'.format(dir_name, te_err))

        return_files.update(set([dir_file for dir_file in dir_files if dir_file.lower().endswith('.bz2')]))
    return return_files

if len(sys.argv) >= 1:
    DIR = sys.argv[1:]
    # Capture --help, -h, -help
    # I didn't want to support argparse and optparse, so I'm just doing this manually
    if len(DIR) == 1 and DIR[0].lower().lstrip('-') == 'h' or DIR[0].lower().lstrip('-') == 'help':
        show_help()
        sys.exit(0)
    else:
        FILES = get_files(DIR)
else:
    print('You must provide a path or file to decompress!')
    show_help()
    sys.exit(1)

if len(DIR) > 0:
    for compressed_filename in DIR:
        # Remove the .bz2 extension
        decompressed_filename = compressed_filename[:-4]

        # If a timestamp is appended to the remaining filename, clean it out
        decompressed_filename = TIMESTAMP_PATTERN.sub('', decompressed_filename)

        print('Decompressing {0} -> {1}'.format(compressed_filename, decompressed_filename))
        compressed_file = BZ2File(compressed_filename)
        with open(decompressed_filename, 'wb') as decompressed_file:
            decompressed_file.write(compressed_file.read())
        compressed_file.close()
else:
    print('No bz2 files were found!')