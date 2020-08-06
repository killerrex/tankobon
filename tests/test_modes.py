#!/usr/bin/env python3
# coding=utf-8

"""
This file is part of Tankobon Organiser

Copyright (C) 2016  Killerrex (killerrex@gmail.com)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import os
from tankobon import Tankobon

from tests.reference import Reference, LevelFmt


class ChDir:
    def __init__(self, where):
        self._where = where
        self._saved = None

    def __enter__(self):
        self._saved = os.getcwd()
        os.chdir(self._where)

    def __exit__(self, etype, value, traceback):
        os.chdir(self._saved)


def generic(root, name, args, vol, cha, show=False):
    # Prepare the arguments
    ref = Reference.generate(name)
    ref.deploy(root)

    with ChDir(root):
        app = Tankobon(args=args)
        tree = app.tree

    # Create the expected tree
    expected = ref(args[0], vol, cha, 'Bonus')

    if show:
        print("Transform:")
        tree.pretty(as_log=False)
        print("Expected transform:")
        expected.pretty(as_log=False)

    assert app.tree == expected


def test_nominal(tmp_path):
    # Prepare the arguments
    args = ['Normal Series', 'nominal']
    vol = LevelFmt(2, ['vol ', 'v'])
    cha = LevelFmt(2, 'c')

    generic(tmp_path, 'nominal', args, vol, cha)


def test_num_in_title(tmp_path):
    # Prepare the arguments
    args = ['Number 1', 'Num 1 in title']
    vol = LevelFmt(2, ['vol ', 'v'])
    cha = LevelFmt(2, 'c')

    generic(tmp_path, 'num1', args, vol, cha)


def test_miss_volume(tmp_path):
    # Prepare the arguments
    args = [
        'Miss First', 'Miss vol 1',
        '--vol-first=2', '--ch-first=4'
    ]
    vol = LevelFmt(2, ['vol ', 'v'])
    cha = LevelFmt(2, 'c')

    generic(tmp_path, 'miss', args, vol, cha)


def test_no_chapters(tmp_path):
    # Prepare the arguments
    args = [
        'Flat Volume', 'No Chapters', '--vol-flat'
    ]
    vol = LevelFmt(2, ['vol ', 'v'])
    cha = None

    generic(tmp_path, 'flatvol', args, vol, cha)


def test_reset_count(tmp_path):
    # Prepare the arguments
    args = [
        'Start At 1', 'Reset Count', '--ch-flat'
    ]
    vol = LevelFmt(2, ['vol ', 'v'])
    cha = LevelFmt(2, 'c')

    generic(tmp_path, 'reset', args, vol, cha)


def test_single_col(tmp_path):
    # Prepare the arguments
    args = [
        'Just One', 'Single Vol', '--single'
    ]
    vol = LevelFmt(2, ['vol ', 'v'])
    cha = LevelFmt(2, 'c')

    generic(tmp_path, 'single', args, vol, cha)
