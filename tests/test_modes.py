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

import unittest

from tankobon import Tankobon

from tests.reference import Reference, LevelFmt


class TestWorkModesCase(unittest.TestCase):

    def test_nominal(self):
        # Prepare the arguments
        args = ['Normal Series', 'nominal']

        app = Tankobon(args=args)

        print("Transform:")
        app.tree.pretty(as_log=False)

        # Create the expected tree
        vol = LevelFmt(2, ['vol ', 'v'])
        cha = LevelFmt(2, 'c')

        nominal = Reference.generate('nominal')
        expected = nominal(args[0], vol, cha, 'Bonus')
        print("Expected transform:")
        expected.pretty(as_log=False)

        self.assertEqual(app.tree, expected)

    def test_num_in_title(self):
        # Prepare the arguments
        args = ['Number 1', 'Num 1 in title']

        app = Tankobon(args=args)

        print("Transform:")
        app.tree.pretty(as_log=False)

        # Create the expected tree
        vol = LevelFmt(2, ['vol ', 'v'])
        cha = LevelFmt(2, 'c')
        num1 = Reference.generate('num1')
        expected = num1(args[0], vol, cha, 'Bonus')
        print("Expected transform:")
        expected.pretty(as_log=False)

        self.assertEqual(app.tree, expected)

    def test_miss_volume(self):
        # Prepare the arguments
        args = [
            'Miss First', 'Miss vol 1',
            '--vol-first=2', '--ch-first=4'
        ]

        app = Tankobon(args=args)

        print("Transform:")
        app.tree.pretty(as_log=False)

        # Create the expected tree
        vol = LevelFmt(2, ['vol ', 'v'])
        cha = LevelFmt(2, 'c')
        num1 = Reference.generate('miss')
        expected = num1(args[0], vol, cha, 'Bonus')
        print("Expected transform:")
        expected.pretty(as_log=False)

        self.assertEqual(app.tree, expected)

    def test_no_chapters(self):
        # Prepare the arguments
        args = [
            'Flat Volume', 'No Chapters', '--vol-flat'
        ]

        app = Tankobon(args=args)

        print("Transform:")
        app.tree.pretty(as_log=False)

        # Create the expected tree
        vol = LevelFmt(2, ['vol ', 'v'])
        cha = None
        num1 = Reference.generate('flatvol')
        expected = num1(args[0], vol, cha, 'Bonus')
        print("Expected transform:")
        expected.pretty(as_log=False)

        self.assertEqual(app.tree, expected)

    def test_reset_count(self):
        # Prepare the arguments
        args = [
            'Start At 1', 'Reset Count', '--ch-flat'
        ]

        app = Tankobon(args=args)

        print("Transform:")
        app.tree.pretty(as_log=False)

        # Create the expected tree
        vol = LevelFmt(2, ['vol ', 'v'])
        cha = LevelFmt(2, 'c')
        num1 = Reference.generate('reset')
        expected = num1(args[0], vol, cha, 'Bonus')
        print("Expected transform:")
        expected.pretty(as_log=False)

        self.assertEqual(app.tree, expected)

    def test_single_col(self):
        # Prepare the arguments
        args = [
            'Just One', 'Single Vol', '--single'
        ]

        app = Tankobon(args=args)

        print("Transform:")
        app.tree.pretty(as_log=False)

        # Create the expected tree
        vol = LevelFmt(2, ['vol ', 'v'])
        cha = LevelFmt(2, 'c')
        num1 = Reference.generate('single')
        expected = num1(args[0], vol, cha, 'Bonus')
        print("Expected transform:")
        expected.pretty(as_log=False)

        self.assertEqual(app.tree, expected)


if __name__ == '__main__':
    unittest.main()
