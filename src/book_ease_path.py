#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
#  book_ease_path.py
#
#  This file is part of book_ease.
#
#  Copyright 2021 mark cole <mark@capstonedistribution.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.

"""
This module provides a convenience class for dealing with the file system.
It wraps a pathlib.Path object with extra functions.
"""

import stat
import re
from datetime import datetime
from pathlib import Path
from typing import Literal
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    import os


class BEPath(type(Path())):
    """
    Wraper for pathlib.Path.
    Adds a number of convenience methods for collecting data from pathlib objects.
    """

    # strings that start with a period.
    dot_file_regex = re.compile(r"^[\.]")

    # build compiled regexes for matching list of media suffixes.
    audio_file_types = ('.flac', '.opus', '.loss', '.aiff', '.ogg', '.m4b', '.mp3', '.wav')
    f_type_re = []
    for i in audio_file_types:
        i = '.*.\\' + i.strip() + '$'
        f_type_re.append(re.compile(i))

    def __init__(self, *args, **kwargs):
        self._path = Path(*args, **kwargs)
        self._stat_result: os.stat_result | None = None

    def update_stat(self):
        """
        Update the internal os.stat_result.
        Note: os.stat_result is not intended to be long lived, so
        this method needs to be called before using stat results.
        """
        self._stat_result = self.stat()

    @property
    def perm_usr(self) -> str:
        """The user permission for this file as a string. ie 'r--x' or 'rw--'"""
        perm  = 'r' if self._stat_result.st_mode & stat.S_IRUSR else '--'
        perm += 'w' if self._stat_result.st_mode & stat.S_IWUSR else '--'
        perm += 'x' if self._stat_result.st_mode & stat.S_IXUSR else '--'
        return perm

    @property
    def perm_grp(self) -> str:
        """The user permission for this file as a string. ie 'r--x' or 'rw--'"""
        perm  = 'r' if self._stat_result.st_mode & stat.S_IRGRP else '--'
        perm += 'w' if self._stat_result.st_mode & stat.S_IWGRP else '--'
        perm += 'x' if self._stat_result.st_mode & stat.S_IXGRP else '--'
        return perm

    @property
    def perm_oth(self) -> str:
        """The user permission for this file as a string. ie 'r--x' or 'rw--'"""
        perm  = 'r' if self._stat_result.st_mode & stat.S_IROTH else '--'
        perm += 'w' if self._stat_result.st_mode & stat.S_IWOTH else '--'
        perm += 'x' if self._stat_result.st_mode & stat.S_IXOTH else '--'
        return perm

    @property
    def timestamp_formatted(self) -> str:
        """Get a formatted timestamp as a string"""
        return datetime.fromtimestamp(self.stat().st_ctime).strftime("%y/%m/%d  %H:%M")

    @property
    def file_type(self) -> str:
        """
        Get the file type formatted as a string.
        ie 'Audio File', etc.
        """
        if self.is_dir():
            return 'Directory'
        elif self.is_media_file():
            return 'Audio File'
        elif self.is_file():
            return 'File'

    @property
    def size_formatted(self) -> tuple[str, Literal['b', 'kb', 'mb', 'gb', 'tb']]:
        """
        convert file size to string with appropriate units
        This includes generating a units suffix thats returned with the formatted size as a tuple.
        """
        units = 'b'
        size = self.stat().st_size
        length = len(f"{size:.0f}")
        if length <= 3:
            val = str(size)
        elif length <= 6:
            val = f"{size / 10e+2:.1f}"
            units = 'kb'
        elif length <= 9:
            val = f"{size / 10e+5:.1f}"
            units = 'mb'
        elif length <= 12:
            val = f"{size / 10e+8:.1f}"
            units = 'gb'
        else:
            val = f"{size / 10e+11:.1f}"
            units = 'tb'
        return (val, units)

    def is_hidden_file(self) -> bool:
        """determine if the file refered to by self is a hidden file"""
        if self.dot_file_regex.match(self.name):
            return True
        return False

    def is_media_file(self) -> bool:
        """Determine if the current file is a media file"""
        for regex in self.f_type_re:
            if regex.match(self.name):
                return True
        return False
