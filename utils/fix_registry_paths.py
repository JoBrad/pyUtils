#!/usr/bin/env python
# -*- coding: utf-8 -*-
import const
import futils as fu
import io
from pathlib import Path
import sys
from typing import (List, Union)

"""
Fixes corrupted Registry Paths, related to a bug in Windows Insider editions which replaces
the drive in non-system Drive Program Files/Program Files (x86) paths to the system drive.
This script will look for these paths, and update them.
NOTE: This hasn't really been tested, except on one laptop.
"""
INPUT_FILE = Path('~/Desktop/hkcr.reg').expanduser()
OUTPUT_FILE = INPUT_FILE.with_name('{0}_replaced{1}'.format(INPUT_FILE.stem, INPUT_FILE.suffix))

d_program_file_paths = ['{0}\\\\'.format(str(p).replace('\\', '\\\\')) for p in fu.get_unique_paths('D:/Program Files', 'C:/Program Files')] + [str(p).replace('\\', '\\\\') for p in fu.get_unique_paths('D:/Program Files (x86)', 'C:/Program Files (x86)')]
incorrect_program_paths = ['C{0}'.format(p[1:]) for p in d_program_file_paths]

path_replacements = [p for p in zip(incorrect_program_paths, d_program_file_paths)]

# get_path_part_count = lambda p: len(fu.get_path_parts(p))

made_changes = False

class RegFile_Section():
    __header_string__ = 'Windows Registry Editor'

    def __init__(self, section_text:List[str]):
        """
        Returns a RegFile_Section object for the section_text
        """
        self.name = None # type: str
        self.type = None # type: str
        self.content = [] # type: List[str]
        self.text = [] # type: List[str]

        content = [str(t) for t in section_text]
        if content[0].startswith(self.__header_string__):
            self.type = 'HEADER'
            self.content = content
        else:
            self.type = 'SECTION'
            self.name = content[0].strip().lstrip('[').rstrip(']')
            self.content = content[1:]

        self.text = ''.join(content)

    def __repr__(self):
        """
        Returns the raw text of the object
        """
        return self.text

    def __contains__(self, text):
        """
        Returns true if this object contains text
        """
        return text in repr(self)

class RegFile():
    def __init__(self, filename):
        """
        Returns an iterator for the filename
        """
        self.header = None
        self.filename = str(Path(filename))

    def __repr__(self):
        """
        Returns a description of the object
        """
        return 'RegFile <{0}>'.format(self.filename)

    def __get_next_section__(self, file_obj):
        """
        Returns the next file section, as a RegFile_Section object,
        or None, if at the end of the file.
        """
        return_strings = [] # type: List[str]
        found_header_or_eof = False # type: bool
        while found_header_or_eof is False:
            current_position = file_obj.tell()
            this_line = file_obj.readline() # type:Union[str, None]
            if len(this_line) == 0:
                found_header_or_eof = True
            elif this_line.startswith('[') and this_line.strip().endswith(']') and len(return_strings) > 0:
                file_obj.seek(current_position, io.SEEK_SET)
                found_header_or_eof = True
            else:
                return_strings.append(this_line)

        if len(return_strings) > 0:
            return RegFile_Section(return_strings)
        else:
            return None

    def __iter__(self):
        yield from self.sections()

    def sections(self):
        """
        Returns an iterator of the file's sections
        """
        with open(self.filename, 'rt', encoding='utf-16') as in_file:
            try:
                while True:
                    yield self.__get_next_section__(in_file)
            except EOFError:
                pass

in_file = RegFile(INPUT_FILE)

def parse_sections(input_file, output_filename):
    made_changes = False
    with open(output_filename, 'wt', encoding='utf-16', newline='\n') as out_file:
        for section in input_file.sections():
            if section is not None:
                file_record = section.text
                if 'C:\\\\Program Files' in section:
                    found_record = [i for i, p in enumerate(incorrect_program_paths) if p in section]
                    if len(found_record) > 0:
                        made_changes = True
                        for replacement_index in found_record:
                            incorrect_path, replacement_path = path_replacements[replacement_index]
                            file_record = file_record.replace(incorrect_path, replacement_path)
                            print('Changed {0} to {1}'.format(incorrect_path, replacement_path))

                        out_file.write(file_record)

                elif section.type == 'HEADER':
                    out_file.write(file_record)

            else:
                break
    return made_changes

made_changes = parse_sections(in_file, OUTPUT_FILE)

if made_changes is False:
    Path(OUTPUT_FILE).unlink()
    print('No changes made.')
print('All done!')
