#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import (absolute_import, division, generators, nested_scopes, print_function, unicode_literals, with_statement)
from builtins import (bytes, dict, int, list, object, range, str, ascii, chr, hex, input, next, oct, open, pow, round, super, filter, map, zip)
from enum import IntFlag

from ctypes import (c_int, WINFUNCTYPE, windll)
from ctypes.wintypes import HWND, LPCSTR, UINT
"""
Exposes some Windows functions as Python functions
"""

prototype = WINFUNCTYPE(c_int, HWND, LPCSTR, LPCSTR, UINT)
paramflags = (1, "hwnd", 0), (1, "text", "Sample message"), (1, "caption", None), (1, "flags", 0x00000000)
MessageBoxW = prototype(("MessageBoxA", windll.user32), paramflags)


class MB_OPTIONS(IntFlag):
    MB_ABORTRETRYIGNORE = 0x00000002 # Abort, Retry, and Ignore (Deprecated)
    MB_CANCELTRYCONTINUE = 0x00000006 # Cancel, Try Again, Continue
    MB_HELP = 0x00004000 # Adds a help button
    MB_OK = 0x00000000 # OK Button
    MB_OKCANCEL = 0x00000001 # OK, Cancel buttons
    MB_RETRYCANCEL = 0x00000005 # Retry, Cancel buttons
    MB_YESNO = 0x00000004 # Yes, No buttons
    MB_YESNOCANCEL = 0x00000003 # Yes, No, Cancel buttons
    MB_ICONEXCLAMATION = 0x00000030 # exclamation-point icon
    MB_ICONWARNING = 0x00000030 # exclamation-point icon
    MB_ICONINFORMATION = 0x00000040 # lowercase letter i in a circle
    MB_ICONASTERISK = 0x00000040 # lowercase letter i in a circle
    MB_ICONQUESTION = 0x00000020 # question-mark icon (Deprecated)
    MB_ICONSTOP = 0x00000010 # stop-sign icon
    MB_ICONERROR = 0x00000010 # stop-sign icon
    MB_ICONHAND = 0x00000010 # stop-sign icon
    MB_DEFBUTTON1 = 0x00000000 # First button is default
    MB_DEFBUTTON2 = 0x00000100 # Second button is default
    MB_DEFBUTTON3 = 0x00000200 # Third button is default
    MB_DEFBUTTON4 = 0x00000300 # Fourth button is default
    MB_APPLMODAL = 0x00000000 # Application-level modal
    MB_SYSTEMMODAL = 0x00001000 # Modal for serious, system-level issues
    MB_TASKMODAL = 0x00002000 # Like modal, but for a window without a parent handle
    MB_DEFAULT_DESKTOP_ONLY = 0x00020000 # Desktop of the interactive window station
    MB_RIGHT = 0x00080000 # Right-justified text
    MB_RTLREADING = 0x00100000 # Uses Right to left reading order
    MB_SETFOREGROUND = 0x00010000 # The message box becomes the foreground window
    MB_TOPMOST = 0x00040000 # The message box is created with the WS_EX_TOPMOST window style
    MB_SERVICE_NOTIFICATION = 0x00200000 # Displays a message box on the current active desktop, even if there is no user logged on to the computer.

def MessageBox(parent_window_handle=None, message:str='Dialog message', title:str='Dialog title', options:MB_OPTIONS=MB_OPTIONS.MB_OK) -> int:
    """
    Displays a message box
    """
    return MessageBoxW(parent_window_handle, bytes(message, encoding='utf-8'), bytes(title, encoding='utf-8'), options)