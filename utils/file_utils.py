from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import (
         bytes, dict, int, list, object, range, str,
         ascii, chr, hex, input, next, oct, pow, round,
         super, filter, map, zip)
import collections
from functools import partial
from io import open
import six

try:
    from typing import (Any, Callable, Dict, Iterator, List, Sequence, Tuple, Union)
except ImportError:
    pass

"""
A set of functions used to read files
"""

def is_iterable(obj):
    # type: (Any) -> bool
    """
    Returns True if obj is a non-string iterable
    """
    if isinstance(obj, six.string_types) or isinstance(obj, collections.Iterable) is False:
        return False
    else:
        return True

def is_callable(obj):
    # type: (Any) -> bool
    """
    Returns True if obj is callable
    """
    return six.callable(obj)

def is_sequence(obj):
    # type: (Any) -> bool
    """
    Returns True if obj is a sequence
    """
    return is_iterable(obj) and isinstance(obj, collections.Sequence)

def is_dict(obj):
    # type: (Any) -> bool
    """
    Returns True if obj is a collections.Mapping type
    """
    return isinstance(obj, collections.Mapping)

def get_clean_path(path_string, check_for_file=False):
    # type: (Union[str, Path], Optional[bool]) -> str
    """
    Returns a trimmed, normalized, and expanded path string from the provided one
    """
    return_filename = path.expanduser(path.expandvars(path.normpath(str(path_string).strip()))) # type: str
    # Replace double leading slashes with a single slash
    if str(path_string).startswith('//'):
        return_filename = return_filename[1:]
    if check_for_file is True and return_filename.exists() is False:
        raise OSError('The provided filename does not exist!\nProvided filename: {0}'.format(str(path_string)))
    return return_filename

def clean_file_record(raw_record):
    # type: (str) -> str
    """
    Removes NUL values from the raw_record
    """
    return raw_record.replace('\x00', '')

def __value_matches__(matching_obj, value):
    # type: (Union[collections.Sequence, Any], Any) -> bool
    """
    Returns True if value is in matching_obj (if matching_obj is a sequence),
    or if value is equal to matching_obj (if matching_obj is a single item)
    """
    if is_iterable(matching_obj) and is_iterable(value):
        return len([i for i in matching_obj if i in value]) > 0
    elif is_iterable(matching_obj) and not is_iterable(value):
        return value in matching_obj
    elif is_iterable(value) and not is_iterable(matching_obj):
        return matching_obj in value
    else:
        return value == matching_obj

def __dict_matches__(matching_dict, dict_obj):
    # type: (dict, dict) -> bool
    """
    Returns True if dict_obj contains all of the keys in matching_dict,
    and each value of dict_obj returns True when passed to __value_matches__
    """
    type_error_msg = 'The provided object was not a {0}!'
    if is_dict(dict_obj) is False:
        raise AttributeError(type_error_msg.format('dictionary'))
    match_results = [k in dict_obj and __value_matches__(dict_obj[k], v) for k, v in matching_dict.items()]
    return len(match_results) > 0 and all(match_results)

def __get_match_function__(match_criteria):
    # type: (Union[collections.Callable, dict, list]) -> collections.Callable
    """
    Returns a partial function that expects a single parameter (record) to be passed to it
    for a truth test.
    If match_criteria is None, then the returned function will always return True.
    If match_criteria is a function, it must return True or False, when passed a record.
    If match_criteria is a dictionary, the returned function will match on keys and values.
    If match_criteria is a list, the returned function will match on values only.
    """
    if match_criteria is None:
        m_func = lambda v: True
    if is_callable(match_criteria):
        m_func = match_criteria
    elif isinstance(match_criteria, dict):
        m_func = partial(__dict_matches__, match_criteria)
    else:
        m_func = partial(__value_matches__, match_criteria)

    return m_func

def read_file(filename, mode='rt', encoding='utf-8'):
    # type: (Union[str, Sequence[str]], str, str) -> Iterator[List[str]]
    """
    Returns an iterator for filename, which can be a string referencing a single file
    or a list of filenames. Each line is cleansed before returning it.
    """
    if is_iterable(filename):
        for file_name in filename:
            for file_record in read_file(filename=file_name, mode=mode, encoding=encoding):
                yield file_record
    else:
        try:
            for file_record in open(filename, mode=mode, encoding=encoding):
                yield clean_file_record(file_record)

        except IOError as io_e:
            print('{0} could not be opened!\nError details: {1}'.format(filename, io_e))
            raise

def read_json_file(filename, filter_key_list=None, key_func=None, value_func=None, value_check_func=None):
    """
    TODO: Make this like read_delimited_file
    Returns a dictionary from the provided filename.
    If an iterable is passed as the filter_key_list, the only keys that are in that list are returned.
    If key_func is passed, then keys will only be returned if they match values in the filter_key_list that
    have also been passed to key_func. Note that the original values in filter_key_list are returned as the key,
    and not the return value of key_func.
    If value_func is provided, every value is passed to it before the dictionary is returned.
    If value_check_func is provided, values are added to the returned dictionary only if
    value_check_func returns True.
    """
    return_dict = {}
    do_nothing_func = lambda v: v
    return_true = lambda v: True

    k_func = key_func if is_callable(key_func) else do_nothing_func
    v_func = value_func if is_callable(value_func) else do_nothing_func
    vc_func = value_check_func if is_callable(value_check_func) else return_true

    if is_iterable(filename):
        for file_name in filename:
            return_dict.update(read_json_file(file_name, filter_key_list, key_func, value_func))
    else:
        filter_dict = dict((k_func(k), k) for k in get_iterable(filter_key_list))
        decoder = json.JSONDecoder()
        file_content = ' '.join([l.replace('\n', '').replace('\r', '') for l in read_file(get_clean_path(filename))])
        try:
            file_dict = decoder.decode(file_content)
        except json.decoder.JSONDecodeError:
            # Python JSON requires double quotes for strings. This safely parses JSON strings even
            # if they are single-quoted, but might choke on some strings that aren't correct for Python
            try:
                file_dict = ast.literal_eval(file_content)
            except:
                raise

        return_dict = dict(
            (filter_dict[k_func(search_field_name)], value_func(match_values))
            for search_field_name, match_values in file_dict.items()
            if vc_func(match_values) is True and k_func(search_field_name) in filter_dict
        )

    return return_dict

def read_delimited_file(filename, mode='rt', encoding='utf-8', delimiter=',', field_names=None):
    # type: (str, str, str, str, Optional[Sequence[str]]) -> Iterator[List[str]]
    """
    Returns an iterator for filename, which can be a string referencing a single file
    or a list of filenames. Each line is cleansed, then split by delimiter. If field_names
    is provided, then the returned iterator will produce a dict, otherwise it will be a list.
    If field_names is provided and the file has a header row, the header row will not be
    in the returned records.
    """
    check_header = False
    first_line = None
    if field_names is not None:
        if is_sequence(field_names):
            first_line = delimiter.join(field_names)
            check_header = True
        else:
            raise AttributeError('Field names must be a sequence!')

    for file_record in read_file(filename=filename, mode=mode, encoding=encoding):
        if check_header is True:
            check_header = False
            if file_record.startswith(first_line) is True:
                continue

        file_record = file_record.split(delimiter)
        if field_names is not None:
            file_record = dict(zip(field_names, file_record))

        yield file_record

def get_matching_records(match_criteria, record_iterator):
    # type: (Callable, Iterator[Union[Dict[str: Any], List[Any]]) -> Iterator[Union[Dict[str: Any], List[Any]]
    """
    Returns all records from record_iterator that match the provided match_criteria.
    See the doc for __get_match_function__ for more detail
    """
    match_func = __get_match_function__(match_criteria)
    for record in record_iterator:
        if match_func(record) is True:
            yield record