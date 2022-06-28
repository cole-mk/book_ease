# -*- coding: utf-8 -*-
#
#  lint.py
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
"""run pylint on all .py files in the repository"""
import subprocess
import sys
from pylint import lint
from pylint.lint import Run


# The pylint score required to pass
minimum_score = 10

# get a list of python source files in the git repo
file_to_be_linted = subprocess.check_output(["git", "ls-files", "*.py"])

failure = False
for file_ in file_to_be_linted.decode().split('\n'):
    # split always gives an extra blank line after the last file
    if not file_:
        continue
    # lint the source file
    run = lint.Run([file_], do_exit=False)
    # get and assess the score
    score = run.linter.stats.global_note
    if score < minimum_score:
        failure = True

if failure:
    sys.exit(1)

