#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement)
from builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, open, pow, round, super, filter, map, zip)
from pathlib import Path, PurePosixPath, PureWindowsPath
import os
import re
import shutil
from typing import (Dict, Set, List, Tuple, Sequence, Union, Pattern, Match)
import tempfile

import futils

def copy_file(input_file:Union[str, Path], new_file:Union[str, Path]) -> Path:
    """
    Copies input_file to new_file, returning a Path object representing the destination file.
    If the new_file already exists, it will not be overwritten.
    """
    source_file = futils.get_clean_path(input_file)
    destination_file = futils.get_clean_path(new_file)
    try:
        if source_file.exists() is False:
            raise OSError('The provided input file does not exist!\nProvided file: {0}'.format(str(input_file)))

        if destination_file.exists() is True:
            raise OSError('The destination file already exists!\nProvided file:{0}'.format(str(new_file)))

        shutil.copy2(str(source_file), str(destination_file))

    except OSError:
        raise

    return destination_file

def replace_in_file(filename:Union[Path, str], search_value:Union[str, Pattern], replacement_string:str, use_regex:bool=False):
    """
    Replaces search_value in filename, with replacement_string.
    If use_regex is True, or if search_value is a RegEx object, then RegEx will be used to find the values in the file
    """
    if use_regex is True or isinstance(search_value, Pattern):
        search_obj = re.compile(search_value)
        replace_value = lambda x: re.sub(search_obj, replacement_string, x)
    else:
        replace_value = lambda x: x.replace(search_value, replacement_string)

    try:
        provided_file = Path(filename)
        provided_filename = str(provided_file)
        if provided_file.exists() is False:
            raise OSError('The provided file cannot be found!\nProvided file: {0}'.format(str(filename)))
    except OSError:
        raise OSError('The provided file cannot be opened!\nProvided file: {0}'.format(str(filename)))

    temp_filename = futils.get_unique_filename(provided_file)
    # Save the original filename
    backup_file = futils.get_unique_filename('{0}.bak'.format(provided_filename))
    copy_file(provided_filename, str(backup_file))

    with open(provided_file, 'rt') as input_file:
        with open(temp_filename, 'wt') as temp_file:
            for input_string in input_file:
                temp_file.write(replace_value(input_string))

    shutil.move(temp_filename, provided_filename)

TEST_FILE = Path.joinpath(Path(__file__).parent, 'test_data', 'test_file.csv')
TEST_SEARCH_STRING = '532012'

replace_in_file(TEST_FILE, TEST_SEARCH_STRING, 'was replaced')