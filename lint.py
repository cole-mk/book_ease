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


# the pylint score required to pass
MINIMUM_SCORE = 10
# files to ignore
ignore_list = ['__init__.py', 'book_ease.py']
# Get a list of python source files in the git repo.
file_to_be_linted = subprocess.check_output(["git", "ls-files", "*.py"])

FAILURE = False
results = []
for file_ in file_to_be_linted.decode().split('\n'):
    # Split always gives an extra blank line after the last file.
    if not file_:
        continue
    if file_ .split("/")[-1] in ignore_list:
        continue
    # Lint the source file.
    run = lint.Run([file_], do_exit=False)
    # Get and assess the score.
    score = run.linter.stats.global_note
    # Store the results for printing at the end of the script.
    results.append(['Success', score, file_])
    if score < MINIMUM_SCORE:
        # Store a failed exit state for the script.
        FAILURE = True
        # Set the message in the second column of the previously appended row.
        results[len(results)-1][0] = 'Failure'

# Uutput a summary of the results.

PART_ONE = """\n\n
Summary of Results:
——————————————————
Overall:"""

PART_TWO = """
——————————————————
Individual:\n
Status  Score File
——————  ————— ————"""

print(PART_ONE)
print('Failure' if FAILURE else 'Success')
print(PART_TWO)
for result in results:
    print(result[0], f"{result[1]:05.2f}", result[2])

if FAILURE:
    sys.exit(1)
