from __future__ import (absolute_import, division, print_function, unicode_literals)
from builtins import (
         bytes, dict, int, list, object, range, str,
         ascii, chr, hex, input, next, oct, pow, round,
         super, filter, map, zip)
import collections
from datetime import datetime
import os
import re
from functools import partial
from io import open
import six

"""
Saves records which are in the export file but not in the tracker file
in a new file.
"""

TRACKER_FILE = os.path.join(os.path.dirname(__file__), 'tracker.csv')
TRACKER_FIELDS = 'merchant_name,merchant_location,city,state,merchant_postal,merchant_id,merchant_number,last_four_card,transaction_date,transaction_amount,Key,Previously sent'.split(',')

EXPORT_FILE = os.path.join(os.path.dirname(__file__), 'bk_download.csv')
EXPORT_FIELDS = 'posted_status,who_the,transaction_date,fuck_cares,merchant_name,payment_category,transaction_amount'.split(',')

MMDDYYYY_PATTERN = re.compile('(?P<month>1[0-2]|0[1-9])([\\-\\/])?(?P<day>[0-2][0-9]|3[0-1])([\\-\\/])?(?P<year>201\\d)')
YYYYMMDD_PATTERN = re.compile('(?P<year>201\\d)([\\-\\/])?(?P<month>1[0-2]|0[1-9])([\\-\\/])?(?P<day>[0-2][0-9]|3[0-1])')

def is_str(obj):
    # type: (Any) -> bool
    """
    Returns True if obj is a string
    """
    return isinstance(obj, six.string_types)

def get_str(string):
    # type: (str) -> str
    """
    Makes sure the provided obj is a string, and returns it
    """
    if is_str(string):
        return str(string)
    else:
        raise AttributeError('The provided value is not a string!')

def is_iterable(obj):
    # type: (Any) -> bool
    """
    Returns True if obj is a non-string iterable
    """
    if is_str(obj) is True or isinstance(obj, collections.Iterable) is False:
        return False
    else:
        return True

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

def get_stripped_string(string):
    # type: (Union[str, collections.Iterable]) -> Union[str, list]
    """
    Returns the provided string as lower case and with only alphanumeric characters.
    If provided a list, then the result will be a list where the same operation has
    been applied.
    """
    if is_str(string):
        return ''.join([char for char in get_str(string).lower() if char.isalnum()])
    elif is_iterable(string):
        return [get_stripped_string(s_val) for s_val in string]
    else:
        raise AttributeError('The provided value is not a string or iterable of strings!')

def get_matching_str_from_iterable(string, iterable):
    """
    Returns string from iterable, after cleansing string and iterable's
    keys. If not found, None is returned.
    """
    match_dict = dict(zip([k for k in iterable], get_stripped_string(iterable)))
    compare_string = get_stripped_string(string)
    if compare_string in match_dict:
        return_val = match_dict[compare_string]
    else:
        return_val = None
    return return_val

def clean_file_record(raw_record_string):
    # type: (str) -> str
    """
    Performs some basic cleansing of the provided string, and returns it
    """
    return raw_record_string.replace('\x00', '')

def get_record_values_matching_keys(record, keys):
    """
    Returns key/value pairs from record whose keys are in keys. If no
    keys match, the returned dict is empty.
    The keys in the returned dict will match the keys in keys
    """
    return_dict = {}
    for key in keys:
        if is_dict(keys):
            matching_field = get_matching_str_from_iterable(keys[key], record)
        else:
            matching_field = get_matching_str_from_iterable(key, record)
        if matching_field is not None:
            return_dict[key] = record[matching_field]
    return return_dict

def fields_match(record_set, matching_fields, record):
    """
    Returns True if record is in record_set, based on matching_fields.
    If matching_fields is a dict, then the keys should be fields in record_set,
    whose values are corresponding fields in record. If the field names are the same,
    then a list can be used.
    In either case, cleansed versions of the fields are compared instead of the raw
    provided values.
    """
    record_values = get_record_values_matching_keys(record, matching_fields)

    if len(record_values) > 0:
        for r in record_set:
            match_tests = [v == r[get_stripped_string(k)] for k, v in record_values.items()]
            if len(match_tests) == len(record_values) and False not in match_tests:
                return True
    return False

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
        if file_record.startswith('\ufeff'):
            file_record = file_record[1:]
        if check_header is True:
            check_header = False
            if file_record.startswith(first_line) is True:
                continue

        file_record = file_record.split(delimiter)
        if field_names is not None:
            file_record = dict(zip(field_names, file_record))

        yield file_record

def parse_transaction_record(txn_record):
    """
    Converts some fields in the transaction record to float or date
    """
    return_record = {}
    for field_name, field_value in txn_record.items():
        compare_field_name = get_stripped_string(field_name)
        if compare_field_name == get_stripped_string('transaction_amount'):
            field_value = float(field_value)

        if compare_field_name == get_stripped_string('transaction_date'):
            date_value = MMDDYYYY_PATTERN.search(field_value) or YYYYMMDD_PATTERN.search(field_value)
            if date_value is not None:
                field_value = datetime(year=int(date_value['year']), month=int(date_value['month']), day=int(date_value['day']))

        return_record[compare_field_name] = field_value

    return return_record


matching_fields = [
    'transaction_amount',
    'merchant_name',
    'merchant_id'
]

submitted_records = [parse_transaction_record(r) for r in read_delimited_file(TRACKER_FILE, field_names=TRACKER_FIELDS)]

records_match = partial(fields_match, submitted_records, matching_fields)

stored_records = [parse_transaction_record(r) for r in read_delimited_file(EXPORT_FILE, field_names=EXPORT_FIELDS)]
new_records = []
for r in stored_records:
    if r[get_stripped_string('transaction_amount')] < 0 and records_match(r) is False:
        new_records.append(r)

for r in new_records:
        print(r)