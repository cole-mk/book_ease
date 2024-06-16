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
import re
from datetime import datetime
from pathlib import Path
from typing import Literal


class BEPath():
    """
    Wraper for pathlib.Path.
    Mostly implements the pathlib.Path interface plus a number of convenience
    functions for collecting data from pathlib objects.

    Note: isinstance(BEPath(), Path) will return False.
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

    def __getattr__(self, attr):
        return getattr(self._path, attr)

    @property
    def timestamp_formatted(self) -> str:
        """Get a formatted timestamp as a string"""
        return datetime.fromtimestamp(self.stat().st_ctime).strftime("%y/%m/%d  %H:%M")

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
