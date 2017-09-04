#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement)
from builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, open, pow, round, super, filter, map, zip)
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import (Dict, Set, List, Tuple, Sequence, Union, Pattern, Match)
import os
import sys

import ctypes
from utils import futils
from utils.windows import (MessageBox, MB_OPTIONS)
import winshell

"""
Fixes broken shortcuts in the Start Menu
"""
PATH_TYPE = Path
PATH_OR_STR_TYPE = Union[PATH_TYPE, str]
PATH_PAIRING = Tuple[PATH_OR_STR_TYPE, PATH_OR_STR_TYPE]
PATH_SEQ_TYPE = Sequence[PATH_TYPE]
SHORTCUT_TYPE = winshell.Shortcut

INPUT_PATH = Path('~/Desktop/Programs').expanduser()

def is_admin():
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except:
        return False

def get_updated_path(input_path:PATH_OR_STR_TYPE, path_pairing:List[PATH_PAIRING]) -> PATH_TYPE:
    """
    Checks whether the current path is valid. If it isn't, then the
    same path, but on the D drive will be tried.
    The returned value will only be different if the provided path is
    invalid AND the updated path is valid. Otherwise the provided path
    is returned.
    """
    return_path = Path(input_path)
    new_path = futils.swap_dirs_if_needed(return_path, path_pairing)
    if return_path.parent != new_path.parent:
        return new_path
    else:
        return input_path

def update_link(link_file:PATH_OR_STR_TYPE):
    """
    Updates the provided link, if required
    """
    shortcut = winshell.shortcut(str(link_file))
    shortcut_path = Path(shortcut.path)
    working_directory = shortcut.working_directory
    icon_path, icon_index = shortcut.icon_location
    drive_pairing = [('C:','D:')]

    if shortcut_path.drive == 'C:' and 'Program Files' in str(shortcut_path) and shortcut_path.exists() is False:
        if '%' not in str(shortcut_path):
            shortcut_path = str(get_updated_path(shortcut_path, drive_pairing))
        if len(working_directory) > 0 and not '%' in working_directory:
            working_directory = str(get_updated_path(working_directory, drive_pairing))
        if len(icon_path) > 0 and not '%' in icon_path:
            icon_path = str(get_updated_path(icon_path, drive_pairing))

        if shortcut_path != shortcut.path or working_directory != shortcut.working_directory or icon_path != shortcut.icon_location[0]:
            shortcut.path = shortcut_path
            shortcut.working_directory = working_directory
            shortcut.icon_location = (icon_path, icon_index)
            if DO_MAKE_CHANGES is True:
                print('Updating shortcut: {0}'.format(link_file))
                shortcut.write()
            else:
                print('Shortcut that needs updating: {0}'.format(link_file))


# if not is_admin():
#     window_options = MB_OPTIONS.MB_OK | MB_OPTIONS.MB_ICONINFORMATION | MB_OPTIONS.MB_SYSTEMMODAL
#     MessageBox(None, 'Running in preview mode. To make changes, re-run this script as admin.', 'Preview mode only!', window_options)
#     DO_MAKE_CHANGES = False
# else:
DO_MAKE_CHANGES = True

for shortcut_file in futils.get_files(INPUT_PATH, '*.lnk'):
    update_link(shortcut_file)

print('All done!')