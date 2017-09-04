#!/usr/bin/env python
# -*- coding: utf-8 -*-
# from __future__ import (absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement)
# from builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, open, pow, round, super, filter, map, zip)
from functools import partial
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
import stat
from typing import (Dict, Set, List, Tuple, Sequence, Union, Pattern, Match, overload, Iterator)
from datetime import datetime as dt
from utils import futils
# from utils import dtutils

# MONTHS = dtutils.MONTHS
"""
Really raw WIP - this is a side thing that I've been doing on-demand, so it
has a lot of unused code, and basically is a mess.

Renames files in the provided directory using a date value in the file name,
or based on the attributes of the file.

Has only been tested in Windows, but the ultimate goal is for it to work across OS types.
"""

PATH_TYPE = Union[PurePosixPath, PureWindowsPath]
PATH_SEQ_TYPE = Sequence[PATH_TYPE]
PATTERN_TYPE = Pattern
MATCH_SEQ_TYPE = Sequence[Match]
STR_BOOL_TUPLE = Tuple[str, bool]
MATCH_STRING_TUPLE = Tuple[Match, str]

RE_IM = re.IGNORECASE + re.MULTILINE

INPUT_PATHS = [
    Path('INPUT PATH')
]

EXCLUDE_LIST = ['~', '.cache', '.git', '.idea', '.project', '.iml', '.vscode', 'desktop.ini'] # type: List[str]
DELETE_LIST = ['.DS_Store', 'Thumbs.db'] # type: List[str]

# TODO: Combine all of these data templates and patterns into another module
YEAR_TEMPLATE = '(?:20|19)[0-9][0-9]' # type: str
SHORT_YEAR_TEMPLATE = '[0-9][0-9]' # type: str
LONG_OR_SHORT_YEAR_TEMPLATE = '{year_pattern}|{short_year_pattern}'.format(
    year_pattern = YEAR_TEMPLATE,
    short_year_pattern = SHORT_YEAR_TEMPLATE
) # type: str
MONTH_TEMPLATE = '[1-9]|0[0-9]|1[0-2]' # type: str
DAY_TEMPLATE = '0[0-9]|[1-2][0-9]|3[0-1]|[1-9]' # type: str
DAY_YEAR_MONTH_TEMPLATE = '\\b(?P<day>{day_pattern}) ?(?P<year>{year_pattern}) ?(?P<month>{month_pattern})'.format(
    year_pattern = YEAR_TEMPLATE,
    month_pattern = MONTH_TEMPLATE,
    day_pattern = DAY_TEMPLATE
) # type: str
MONTH_AND_YEAR_TEMPLATE = '((?P<year1>{year_pattern})\\b\\s*(?P<month1>{month_pattern})|(?P<month2>{month_pattern})\\b\\s*(?P<year2>{year_pattern}))'.format(
    year_pattern = LONG_OR_SHORT_YEAR_TEMPLATE,
    month_pattern = MONTH_TEMPLATE
) # type: str
# Match month names to month numbers
MONTH_REPLACEMENT_TEMPLATES = {
    '(?:january|jan|01)': '01',
    '(?:february|feb|02)': '02',
    '(?:march|mar|03)': '03',
    '(?:april|apr|04)': '04',
    '(?:may|05)': '05',
    '(?:june|jun|06)': '06',
    '(?:july|jul|07)': '07',
    '(?:august|aug|08)': '08',
    '(?:september|sept|sep|09)': '09',
    '(?:october|oct|10)': '10',
    '(?:november|nov|11)': '11',
    '(?:december|dec|12)': '12'
} # type: Dict[str, str]
# August 2016 / Aug 2016 / 08 2016
M_YEAR_TEMPLATE = '\\b(?P<month>{month_pattern})\'(?P<year>{year_template})\\b' # type: str
# 2016 08 02
ISO_DATE_TEMPLATE = '\\b(?P<year>{year_pattern}) ?(?P<month>{month_pattern}) ?(?P<day>{day_pattern})\\b'.format(
    year_pattern = LONG_OR_SHORT_YEAR_TEMPLATE,
    month_pattern = MONTH_TEMPLATE,
    day_pattern = DAY_TEMPLATE
) # type: str
# 08 02 2016
US_DATE_TEMPLATE = '\\b(?P<month>{month_pattern}) ?(?P<day>{day_pattern}) ?(?P<year>{year_pattern})\\b'.format(
    month_pattern = MONTH_TEMPLATE,
    day_pattern = DAY_TEMPLATE,
    year_pattern = LONG_OR_SHORT_YEAR_TEMPLATE
) # type: str

# Patterns = compiled RegEx templates
MONTH_REPLACEMENT_PATTERNS = {
    re.compile(pattern='\\b({month_pattern})\\b'.format(month_pattern=k), flags=RE_IM): v
    for k, v in MONTH_REPLACEMENT_TEMPLATES.items()
} # type: Dict[PATTERN_TYPE, str]

# Apr'16
M_YEAR_PATTERNS = {
    re.compile(
        pattern=M_YEAR_TEMPLATE.format(
            month_pattern=k,
            year_template=LONG_OR_SHORT_YEAR_TEMPLATE
        ),
        flags=RE_IM
    ): v
    for k, v in MONTH_REPLACEMENT_TEMPLATES.items()
} # type: Dict[PATTERN_TYPE, str]

# MM dd yyyy
US_DATE_PATTERN = re.compile(
    pattern=US_DATE_TEMPLATE,
    flags=RE_IM
) # type: Pattern

# dd yyyy dd
DAY_YEAR_MONTH_PATTERN = re.compile(
    pattern=DAY_YEAR_MONTH_TEMPLATE,
    flags=RE_IM
) # type: Pattern

# yyyy MM dd
LONG_DATE_PATTERN = re.compile(
    pattern=ISO_DATE_TEMPLATE,
    flags=RE_IM
) # type: Pattern

# yyyy MM or MM yyyy
MONTH_YEAR_PATTERN = re.compile(
    pattern=MONTH_AND_YEAR_TEMPLATE,
    flags=RE_IM
) # type: Pattern

YEAR_PATTERN = re.compile(
    pattern='(?:\'?\\b(?P<year>{year_pattern}))\\b'.format(
        year_pattern = LONG_OR_SHORT_YEAR_TEMPLATE
    ),
    flags=RE_IM
) # type:PATTERN_TYPE

MONTH_PATTERN = re.compile(
    pattern='\\b(?P<month>{month_pattern})\\b'.format(
        month_pattern = MONTH_TEMPLATE
    ),
    flags=RE_IM
) # type: Pattern

WHITESPACE_PATTERN = re.compile('\s', RE_IM) # type: PATTERN_TYPE
SEPARATOR_PATTERN = re.compile(pattern='([ \\.\\,\\_\\-\\+])') # type: PATTERN_TYPE
BRACKET_PATTERN = re.compile(pattern='([\\(\\)\\[\\]\\{\\}])') # type: PATTERN_TYPE

format_year_string = lambda year_string: year_string if len(year_string.strip()) == 4 else '20{0}'.format(year_string.strip())
format_day_or_month_string = lambda day_or_month_string: day_or_month_string.strip().zfill(2)

def get_matches(input_string:str, search_pattern:Pattern) -> Iterator[Match]:
    """
    Moves from left to right, in input_string, yielding each match from search_pattern
    until there are no more matches, when None is returned
    """
    start_pos = 0 # type: int
    search_result = search_pattern.search(input_string, start_pos) # type: Match
    while search_result is not None:
        yield search_result # type: Match
        start_pos = search_result.span()[1]
        search_result = search_pattern.search(input_string, start_pos)

def match_patterns(input_string:str, search_patterns:Union[Dict[Pattern, str], List[Pattern]]) -> List[Pattern]:
    """
    Returns a List of all patterns in search_patterns that matched input_string. If none
    of the patterns matched, or if there was an error, an empty List is returned.
    """
    return {pattern: None if isinstance(search_patterns, List) else search_patterns[pattern] for pattern in search_patterns if pattern.search(str(input_string)) is not None} # type: Dict[Pattern, Union[str, None]]

@partial
def execute_on_matches(func:callable, input_string:str, search_patterns:Union[Dict[Pattern, str], List[Pattern]]) -> Tuple[str, bool]:
    """
    For each matching pattern in search_patterns, passes input_string and the result to func
    Returns Tuple[return_string, made_a_match] where return_string will be the result of func and True,
    or input_string with no changes, and False, if no matches were found in search_patterns
    """
    return_string = str(input_string) # type:str
    made_a_match = False # type: bool

    matching_patterns = match_patterns(input_string, search_patterns) # type: List[Pattern]
    if len(matching_patterns) > 0:
        for matching_pattern in matching_patterns: # type; Pattern
            made_a_match = True
            if isinstance(search_patterns, Dict):
                str_value = search_patterns[matching_pattern] # type: Union[None, str]
            else:
                str_value = None

            for match in get_matches(return_string, matching_pattern):
                return_string = func(return_string, (matching_pattern, str_value))

    return (return_string, made_a_match)

@partial
def execute_on_file_stem(func:callable, full_file_path:Union[str, Path], **kwargs) -> Tuple[Path, bool]:
    """
    Calls func(provided_file_stem, **kwargs), which should return Tuple[str, made_a_change],
    where str is the provided string, with any changes, and made_a_change is a boolean indicating
    whether changes were made.
    The returned string is returned as the stem of the provided full_file_path, as a Path object
    """
    try:
        file_obj, file_parent, filename, file_suffix = get_file_parts(full_file_path)
    except AttributeError:
        raise

    return_string, made_a_change = func(filename, **kwargs) # type: str, bool
    new_filename = '{0}{1}'.format(return_string, file_suffix) # type: str
    return (Path.joinpath(file_parent, new_filename), made_a_change)

def format_m_year_execute(input_string:str, match_pattern:Tuple[Pattern, str]) -> str:
    """
    Core of loop for format_m_year_strings
    """
    return_string = str(input_string) # type:str
    search_pattern, month_number = match_pattern # type: Pattern, str
    search_result = search_pattern.search(return_string) # type: Match
    string_to_replace, year = search_result.group(0), format_year_string(search_result.group('year')) # type: str, str
    return_string = replace_and_prepend(return_string, string_to_replace, '{0} {1} '.format(year, month_number))
    return return_string

def format_m_year_strings(input_string: str) -> Tuple[str, bool]:
    """
    Looks for a m'year value in the string. If it finds
    one, then it moves it to the front of the string
    Returns a tuple (return_string:str, made_a_match:bool)
    """
    return execute_on_matches(format_m_year_execute, input_string, M_YEAR_PATTERNS)

def format_month_string_execute(input_string:str, match_pattern:Tuple[Pattern, str]) -> str:
    """
    Core of loop for format_month_strings_with_numbers function
    """
    return_string = str(input_string) # type:str
    search_pattern, month_number = match_pattern # type: Match, str
    return search_pattern.sub(month_number, return_string)

def format_month_strings_with_numbers(input_string:str) -> Tuple[str, bool]:
    """
    Replaces month names with their padded numeric equivalent
    """
    return execute_on_matches(format_month_string_execute, input_string, MONTH_REPLACEMENT_PATTERNS)

def format_day_year_month_execute(input_string:str, match_pattern:Tuple[Pattern, None]) -> str:
    """
    Core of loop for format_day_year_month_date_string
    """
    return_string = str(input_string) # type:str
    search_result = match_pattern[0].search(return_string) # type: Match
    replacement_string = '{0} {1} {2}'.format(search_result.group('year'), search_result.group('month'), search_result.group('day')) # type: str
    return input_string.replace(search_result.group(0), replacement_string)

def format_day_year_month_date_string(input_string:str) -> Tuple[str, bool]:
    """
    Replaces dates with the format dd yyyy MM with yyyy MM dd format
    """
    return execute_on_matches(format_day_year_month_execute, input_string, [DAY_YEAR_MONTH_PATTERN])

def format_us_date_strings_execute(input_string:str, match_pattern:Tuple[Pattern, None]) -> str:
    """
    Core of loop for format_us_date_strings
    """
    return_string = str(input_string) # type:str
    search_result = match_pattern[0].search(return_string) # type: Match
    replacement_string = '{0} {1} {2}'.format(
        format_year_string(search_result.group('year')),
        format_day_or_month_string(search_result.group('month')),
        format_day_or_month_string(search_result.group('day'))
    ) # type: str
    return return_string.replace(search_result.group(0), replacement_string)

def format_us_date_strings(input_string:str) -> Tuple[str, bool]:
    """
    Re-arranges US-style date formats (MM-dd-yyyy) to yyyy-MM-dd style
    Un-padded month and day values are also matched.
    Years without a century value will be assumed to be after 2000.
    """
    return execute_on_matches(format_us_date_strings_execute, input_string, [US_DATE_PATTERN])

def format_year_month_execute(input_string:str, match_pattern:Tuple[Pattern, None]) -> str:
    """
    Core of loop for format_year_month_strings
    """
    return_string = str(input_string) # type:str
    search_result = match_pattern[0].search(return_string) # type: Match
    replacement_string = '{0} {1}'.format(
        format_year_string(search_result.group('year1') or search_result.group('year2')),
        format_day_or_month_string(search_result.group('month1') or search_result.group('month2'))
    ) # type: str
    return return_string.replace(search_result.group(0), replacement_string)

def format_year_month_strings(input_string:str) -> Tuple[str, bool]:
    """
    Formats MM yyyy date strings as yyyy MM
    """
    return execute_on_matches(format_year_month_execute, input_string, [MONTH_YEAR_PATTERN])

def remove_double_spaces(input_string:str) -> str:
    """
    Replaces double spaces with single spaces, in the provided string
    """
    return ' '.join(WHITESPACE_PATTERN.sub(' ', input_string).split())

def clean_up_name(input_string:str) -> Tuple[str, bool]:
    """
    Replaces .,_-+%20 with spaces
    Replaces unicode spaces with standard spaces
    Replaces double spaces with single spaces
    Removes trailing and leading spaces
    Removes ([{}])
    """
    filename = str(input_string).strip()
    # Replace separators with spaces
    new_filename = re.sub(SEPARATOR_PATTERN, ' ', filename)
    # Replace %20 with space
    new_filename = new_filename.replace('%20', ' ')
    # Replaces double spaces
    new_filename = remove_double_spaces(new_filename)
    # Remove brackets
    new_filename = re.sub(BRACKET_PATTERN, '', new_filename).strip()
    return (new_filename, new_filename.endswith(filename))

def fix_date_strings(input_string:str) -> Tuple[str, bool]:
    """
    Looks for several date formats in the provided string, and replaces
    them with a date with the most complete format that can be found,
    from the list below:
        yyyy MM dd
        yyyy MM
        yyyy
    Operational order
        * Replace mmm'yy or mmm'yyyy with yyyy MM
        * Replace dd yyyy MM with yyyy MM dd
        * Replace MM dd yyyy with yyyy MM dd

    Returns Tuple[return_string, made_a_match]
    If no changes were made, the provided string is returned, without any changes.
    """

    return_string = str(input_string).strip() # type:str
    made_a_match = False # type: bool
    date_funcs = (
        format_m_year_strings,
        format_month_strings_with_numbers,
        format_day_year_month_date_string,
        format_us_date_strings
    )

    # Only try these if we weren't able to find matches from date_funcs
    additional_date_patterns = [
        YEAR_PATTERN,
        MONTH_PATTERN
    ]

    for date_func in date_funcs:
        return_string, matched = date_func(return_string) # type: str, bool
        made_a_match = max(made_a_match, matched)

    if made_a_match is True:
        return (return_string, made_a_match)
    else:
        matching_patterns = match_patterns(return_string, additional_date_patterns)
        for matching_pattern in matching_patterns:
            if matching_pattern == YEAR_PATTERN:
                format_func = format_year_string
                group_name = 'year'
            else:
                format_func = format_day_or_month_string
                group_name = 0
            made_a_match = True
            for date_match in get_matches(return_string, matching_pattern): # type: Match
                return_string = return_string.replace(date_match.group(0), format_func(date_match.group(group_name)))
            break

        if made_a_match is False:
            return (input_string, made_a_match)
        else:
            return (return_string, made_a_match)

def replace_and_prepend(input_string:str, search_string: str, replacement_string:str=None, prepend_string:str=None) -> str:
    """
    If search_string is in input_string, it is replaced with replacement_string,
    the string is then trimmed, prepended with prepend_string, and returned.
    If search_string is not in input_string, the original string is returned.
    """
    return_string = input_string
    if prepend_string is None:
        prepend_string = ''

    if search_string in input_string:
        return remove_double_spaces('{0}{1}'.format(prepend_string, re.sub(search_string, replacement_string, return_string).strip()))
    else:
        return input_string

def get_best_date_string(input_string:str, start_pos:int=0) -> Match:
    """
    Returns the most complete date string found in input_string,
    starting at start_pos.
    If no match is found, then None is returned.
    """
    provided_string = str(input_string) # type: str
    date_patterns = [
        LONG_DATE_PATTERN,
        MONTH_YEAR_PATTERN,
        YEAR_PATTERN
    ]

    for date_pattern in match_patterns(provided_string, date_patterns):
        for search_result in get_matches(provided_string, date_pattern):
            yield search_result
        break

def add_file_date(file_name:str, full_file_path:Union[Path, str]) -> str:
    """
    Looks for the first, most complete date string in the stem of the provided
    file. If that date is missing a year and/or month value, then those
    values will be retrieved from either the parent folder name, or the file's
    modified timestamp. A day value will not be used unless it is already
    in the filename.
    Any date string retrieved from the filename will be moved to the
    begining of the string, in the format yyyy MM dd or yyyy MM.
    """
    file_path_obj = Path(full_file_path)
    if file_path_obj.is_file() is False:
        raise AttributeError('You must provide the file path to this function!')

    input_string = str(file_name)

    date_parts = ('year', 'month', 'day')
    file_name_date = {k: None for k in date_parts}
    string_to_replace = '' # type:str

    if YEAR_PATTERN.search(str(file_path_obj.parent)) is not None:
        file_name_date['year'] = YEAR_PATTERN.search(str(source_file.parent)).group('year')
    else:
        file_name_date['year'] = str(dt.fromtimestamp(source_file.stat().st_mtime).year)

    if MONTH_PATTERN.search(str(file_path_obj.parent)) is not None:
        file_name_date['month'] = MONTH_PATTERN.search(str(file_path_obj.parent)).group('month')
    else:
        file_name_date['month'] = str(dt.fromtimestamp(source_file.stat().st_mtime).month)

    # Get the best date we have
    for date_match in get_date_strings(input_string):
        string_to_replace = date_match.group(0)
        found_date_parts = [k.strip().lower() for k in date_match.groupdict().keys() if k.strip().lower() in date_parts]
        for date_part in found_date_parts:
            file_name_date[date_part] = date_match.groups(date_part)
        break

    best_date_string = '{0} {1} '.format(format_year_string(file_name_date['year']), format_day_or_month_string(file_name_date['month']))

    if file_name_date['day'] is not None:
        best_date_string = '{0}{1} '.format(best_date_string, format_day_or_month_string(file_name_date['day']))

    return_string = replace_and_prepend(input_string=input_string, search_string=string_to_replace, prepend_string=best_date_string)

def move_date_to_start_of_string(input_string:str) -> str:
    """
    Finds the best date string, and moves it to the begining of the string
    """
    try:
        best_date_strings = [date_string_match for date_string in get_best_date_string(input_string)]
        date_start_pos = best_date_strings[0].span()[0]
        date_end_pos = best_date_strings[len(best_date_strings) - 1].span()[1]
        date_string = input_string[date_start_pos:date_end_pos]
    except Exception as err:
        a = 1
        return input_string

    return replace_and_prepend(input_string=input_string, search_string=date_string, prepend_string=date_string)

def get_file_parts(file_obj:Union[str, Path]) -> Tuple[Path, Path, str, str]:
    """
    Returns Tuple[file_path_obj, file_parent_obj, file_stem, file_suffix]
    """
    source_file = futils.get_clean_path(file_obj)
    if source_file.parent == '.' or source_file.is_file() is False:
        raise AttributeError('You must provide a complete file path to this function!')

    return (source_file, source_file.parent, source_file.stem, source_file.suffix)

def apply_renaming_rules(filename:Union[PATH_TYPE, str], **kwargs:Dict[str, bool]) -> PATH_TYPE:
    """
    Applies some basic renaming rules to the file, and renames it, if neccesary
    Available options:
        * clean_names:  Removes junk from the file name
        * fix_dates:    Re-formats dates in the file name to yyyy MM dd format
        * add_file_date Adds the year and/or month to the file date, if it is not present
                        This is done by using dates from the parent folder name or the
                        file's modified_timestamp
        * move_date:    Moves dates to the begining of the filename.

    TODO: Properly handle date ranges, for move_date
    TODO: Properly handle all calls to execute_on_file_stem
    """
    try:
        source_file, source_file_parent, source_file_stem, source_file_suffix = get_file_parts(filename)
    except AttributeError:
        raise

    if len(kwargs) == 0:
        return source_file

    func_list = []
    options = [o.strip().lower() for o in kwargs.keys()]
    # We need to apply these in this order
    if 'clean_names' in options:
        func_list.append(clean_up_name)
    if 'fix_dates' in options:
        func_list.append(fix_date_strings)
    if 'add_file_date' in options:
        func_list.append(add_file_date)
    if 'move_date' in options:
        func_list.append(move_date_to_start_of_string)

    for func in func_list:
        execute_on_file_stem(func, source_file_stem)

    # Logic:
    #   * Clean up filename
    #   * Fix dates in the filename
    #   * Try renaming:
    #       * If the filename contains a date range, then move it to the begining of the file, and stop
    #       * If the filename contains a full date, then move it to the begining of the file, and stop
    #       * If the filename contains year month only, then move it to the begining of the file, and stop
    #       * If the filename only contains a month, then
    #           * Get the year from the parent folder name, or from the file's created timestamp
    #           * Prepend the year, and move the month just after it, and stop
    #       * If the filename only contains a year, then move it to the begining of the file, and stop

    new_file_stem = clean_up_name(source_file_stem)

    # Try to fix dates
    new_file_stem, found_match = fix_date_strings(new_file_stem)

    date_parts = ('year', 'month', 'day')
    file_name_date = {}
    # Get the best date we have
    for date_match in get_date_strings(new_file_stem):
        for date_part in date_parts:
            if date_part in date_match.groupdict():
                file_name_date[date_part] = date_match.groups(date_part)
        if 'year' not in file_name_date:
            file_name_date['year'] = backup_file_year
        break

    # We should have a good date now
    file_prefix = ' '.join(file_name_date[d] for d in date_parts)

    new_file_stem, found_match = move_year_month_to_string_start(new_file_stem)

    # In this case, we should use some other value for the year
    if found_match is False:
        new_file_stem, found_match = replace_month(new_file_stem)
        if found_match:
            if YEAR_PATTERN.search(str(filename.parent)) is not None:
                file_year = YEAR_PATTERN.search(str(filename.parent)).group(0)
            else:
                file_year = dt.fromtimestamp(filename.stat().st_mtime).year
            new_file_stem = '{0} {1}'.format(file_year, new_file_stem)

    if found_match is True and new_file_stem != source_file_stem:
        destination_file = futils.get_unique_filename(source_file.with_name('{0}{1}'.format(new_file_stem, file_suffix)))
        destination_file = futils.safe_move(source_file, destination_file.name)
    else:
        destination_file = source_file

    return destination_file

def get_files(directory:Union[PurePosixPath, PureWindowsPath]) -> Sequence[str]:
    """
    Returns a list of the full path for each file in the given directory
    """
    # return_file_list = [Path(f) for f in directory.glob('**/*') if f.is_file() and not bool(f.stat().st_file_attributes & stat.FILE_ATTRIBUTE_HIDDEN) and len(f.suffix) > 0]
    return_file_list = [Path(f) for f in directory.glob('**/*') if f.is_file()]
    for exclude_pattern in EXCLUDE_LIST:
        return_file_list = [f for f in return_file_list if exclude_pattern not in str(f)]

    return return_file_list

def process_files(input_directory:PATH_TYPE) -> PATH_SEQ_TYPE:
    """
    Processes files in the provided directory
    """
    processed_files = []
    for this_file in get_files(input_directory):
        if this_file.name in DELETE_LIST:
            this_file.unlink()
            processed_files.append((this_file, 'Deleted'))
        else:
            processed_files.append((this_file, apply_renaming_rules(this_file)))
    return processed_files

# for input_directory in INPUT_PATHS:
#     processed_files = process_files(input_directory)
#     for original_file, new_file in processed_files:
#         if str(original_file) != str(new_file):
#             print('Renamed {0}\nto\t{1}\n'.format(str(original_file), str(new_file)))

test_strings = [
    'CLIENT Weekly Performance Report 6 9 14 to 6 15 14',
    '2014 03 27 CLIENT Monthly Reporting Sample',
    'Rev Share \'14'
]
for test_string in test_strings:
    a, matched = fix_date_strings(test_string)
    for date_match in get_date_strings(a):
        c = 1
