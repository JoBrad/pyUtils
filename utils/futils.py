#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement)
from builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, open, pow, round, super, filter, map, zip)
from collections import Sequence
import os
from operator import getitem
from pathlib import (Path, PurePath, PurePosixPath, PureWindowsPath)
import platform
from typing import (Dict, Iterable, List, Match, Pattern, Set, Sequence, Tuple, Union)
import psutil

"""
Provides several utilities for working with files
"""

PATH_LIKE = Union[Path, str]
PATH_LIKE_ITERABLE = Iterable[PATH_LIKE]
DIRECTORY_PAIRING = Tuple[PATH_LIKE, PATH_LIKE]
STR_ITERABLE = Iterable[str]
STR_TUPLE = Tuple[str]
STR_TUPLE_ITERABLE = Iterable[STR_TUPLE]

def get_clean_path(path_string:PATH_LIKE, check_for_file:bool=False) -> Path:
    """
    Returns a trimmed, normalized, and expanded path string from the provided one
    """
    return_filename = Path(path_string).expanduser()
    # Replace double leading slashes with a single slash
    if str(path_string).startswith('//'):
        return_filename = Path('/{0}'.format(str(return_filename)))
    if check_for_file is True and return_filename.exists() is False:
        raise OSError('The provided filename does not exist!\nProvided filename: {0}'.format(str(path_string)))

    return return_filename

def get_path_parts(file_path:Union[PATH_LIKE, PATH_LIKE_ITERABLE], as_posix=True) -> Union[STR_TUPLE, STR_TUPLE_ITERABLE]:
    """
    Returns a tuple or list of tuples of the parts in the provided file_path.
    Unless otherwise set, paths will be returned as Posix paths.
    """
    return_parts = []
    if is_iterable(file_path):
        for this_path in file_path:
            return_parts.append(get_path_parts(this_path))
    else:
        this_path = get_clean_path(file_path)
        if as_posix is True and '/' not in str(this_path):
            this_path = this_path.as_posix()
            if this_path.startswith('/'):
                return_parts.append('/')
            return_parts += [p for p in this_path.split('/') if len(p) > 0]
        else:
            return_parts = this_path.parts
    return tuple(return_parts)

def get_path_from_path_parts(*path_parts:Tuple) -> Path:
    """
    Returns a Path object by concatenating all of the provided items together
    with the path separator.
    """
    if len(path_parts) == 1 and is_iterable(path_parts[0]):
        path_parts = path_parts[0]
    return get_clean_path('/'.join(path_parts))

def get_drives() -> List[str]:
    """
    Returns all mounted drives
    """
    return [d for d in psutil.disk_partitions(all=True)]

def is_iterable(obj:any) -> bool:
    """
    Returns True if the value is a non-string iterable.
    """
    return not isinstance(obj, str) and isinstance(obj, Iterable)

def swap_dirs_if_needed(file_path:PATH_LIKE, alternate_directory_pairings:List[DIRECTORY_PAIRING], check_exists:bool=True) -> PATH_LIKE:
    """
    If the provided file_path exists, it is returned, without modification.
    alternate_directory_pairings should be an iterable containing two Tuples, one for each
    directory to be evaluated against the other.
    If the provided file_path does not exist, starts with either of the provided directory
    pairings, and exists in the other provided directory pairing, then the path is updated to
    that other directory.
    In all other cases, the provided file_path is returned without any changes.
    """
    get_path_part_count = lambda p: len(get_path_parts(p))

    if Path(file_path).exists():
        return file_path
    else:
        return_path = get_clean_path(file_path).as_posix()
        path_alternates = []
        # Only support 2 pairings, for now
        for dir_one, dir_two, *_ in alternate_directory_pairings:
            # We want to sort by the length of the paths, and only include existing paths
            dir_pairs = [Path(p) for p in sorted([dir_one, dir_two], key=get_path_part_count, reverse=True)]
            # dir_pairs = [get_path_from_path_parts(path_part) for path_part in sorted([path_parts for path_parts in get_path_parts([dir_one, dir_two])], key=len, reverse=True)]
            if any([p.exists() and return_path.startswith(p.as_posix()) for p in dir_pairs]):
                path_alternates.append((dir_pairs[0].as_posix(), dir_pairs[1].as_posix(), dir_pairs[0].exists()))
                path_alternates.append((dir_pairs[1].as_posix(), dir_pairs[0].as_posix(), dir_pairs[1].exists()))

        for this_dir, other_dir, this_dir_exists in path_alternates:
            if return_path.startswith(other_dir) and this_dir_exists:
                rest_of_path = return_path[len(str(other_dir)):]
                new_path = Path('{0}/{1}'.format(this_dir, rest_of_path))
                if check_exists is True and new_path.exists():
                    return_path = new_path
                else:
                    return_path = new_path
                break

        return return_path

def get_files(directory:PATH_LIKE, file_mask:str=None, recursive=True, exclusion_list:List[PATH_LIKE]=None) -> PATH_LIKE_ITERABLE:
    """
    Returns files in the given directory or list of directories. The list can be
    optionally filtered by a glob string (file_mask) or exclusion_list.
    """
    return_file_list = []

    if is_iterable(directory):
        for this_directory in directory:
            return_file_list += get_files(this_directory, file_mask, recursive, exclusion_list)
    else:
        mask_prefix = '**' if recursive is True else '*'
        if file_mask is None:
            file_mask = '*'

        provided_path = Path(directory)

        return_file_list = provided_path.glob('{0}/{1}'.format(mask_prefix, file_mask))

        if exclusion_list is not None:
            for exclude_pattern in exclusion_list:
                return_file_list = [f for f in return_file_list if exclude_pattern not in str(f)]

    return return_file_list

def get_dirs(directory:PATH_LIKE, recursive=False, include_symlinks=False) -> PATH_LIKE_ITERABLE:
    """
    Returns a list of child directories for the provided path or paths.
    Does not include symlinks by default.
    """
    return_list = []
    if is_iterable(directory):
        for this_dir in directory:
            return_list += get_dirs(this_dir, recursive)
    else:
        provided_path = Path(directory)
        if recursive is True:
            glob = '**/*'
        else:
            glob = '*'

        if provided_path.is_dir():
            return_list = [c for c in provided_path.glob(glob) if c.is_dir()]
            if include_symlinks is False:
                return_list = [c for c in return_list if c.is_symlink() is False]

    return return_list

def get_unique_paths(first_path:PATH_LIKE, second_path:PATH_LIKE) -> Path:
    """
    Yields a iterator of all paths in the first path that are not in the second path.
    Is only as recursive as it needs to be.
    """
    first_path_children = {p.name:p for p in get_dirs(first_path)} # type: Dict[str, Path]
    second_path_children = {p.name:p for p in get_dirs(second_path)} # type: Dict[str, Path]
    for f_path, f_path_obj in first_path_children.items():
        if f_path in second_path_children:
            yield from get_unique_paths(f_path_obj, second_path_children[f_path])
        else:
            yield f_path_obj

def safe_move(source_filename:PATH_LIKE, destination_filename:PATH_LIKE, force:bool=False) -> Path:
    """
    Renames source_filename to destination_filename, and returns a Path
    object that represents the final file.
    If destination_filename only contains a filename(no directory), then the directory of the source_filename will be used.
    If destination_filename only contains a directory(no filename), then the filename of the source_filename will be used.
    If a file with the same name as destination_filename exists, then the destination_filename
    will be appended with numbers to make the final filename unique, unless force is True.
    """
    if force is True:
        do_overwrite = True
    else:
        do_overwrite = False

    input_filename = get_clean_path(source_filename, check_for_file=True)
    output_filename = Path(destination_filename)

    if str(output_filename.parent) == '.' and output_filename.name == destination_filename:
        output_filename = Path.joinpath(input_filename.parent, output_filename.name)
    if output_filename.is_dir() is True:
        output_filename = Path.joinpath(output_filename.parent, input_filename.name)

    if output_filename.exists() is True:
        if output_filename.samefile(input_filename):
            return input_filename
        elif do_overwrite is False:
            output_filename = get_unique_filename(output_filename)

    input_filename.rename(output_filename)
    return output_filename

def get_directory_name(full_path:[Path, str]) -> Path:
    """
    Returns the name of the parent directory of the provided path.
    """
    provided_path = get_clean_path(full_path)
    return provided_path.parent

def change_path_drive(directory:[Path, str], new_drive:str) -> Path:
    """
    Returns path_obj as a Path object, with its drive replaced
    with new_drive
    """
    valid_drives = [d.mountpoint.strip('\\/').upper() for d in get_drives()]
    provided_path = Path(directory)
    provided_drive = Path('{0}:'.format(str(new_drive))).drive.upper()
    if provided_drive == '' or provided_drive not in valid_drives:
        raise AttributeError('The provided value for new_drive is invalid!')

    _, *remaining_parts = provided_path.parts
    try:
        return Path('/'.join([provided_drive] + remaining_parts))
    except OSError:
        return provided_path

def get_unique_filename(new_filename:PATH_LIKE) -> Path:
    """
    Appends a numeric to the provided filename to make it unique,
    if it already exists.
    """
    original_filename = get_clean_path(new_filename)

    base_file_name = str(Path.joinpath(original_filename.parent, original_filename.stem))
    file_suffix = original_filename.suffix
    new_file_path = original_filename

    append_value = 0
    while new_file_path.exists():
        append_value += 1
        new_file_path = Path('{0} {1}{2}'.format(base_file_name, str(append_value), file_suffix))

    return new_file_path