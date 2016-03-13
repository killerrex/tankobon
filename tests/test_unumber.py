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

from tankobon import UNumber


class TestUNumber(unittest.TestCase):
    probes = {
        1: 'I', 4: 'IV', 5: 'V', 9: 'IX',
        10: 'X', 12: 'XII', 14: 'XIV', 19: 'XIX', 48: 'XLVIII',
        50: 'L', 67: 'LXVII', 89: 'LXXXIX',
        100: 'C', 194: 'CXCIV', 468: 'CDLXVIII',
        500: 'D', 793: 'DCCXCIII',
        1000: 'M', 4999: 'MMMMCMXCIX'
    }

    def test_from_roman(self):
        """
        Convert roman numbers to decimal
        """
        for v in self.probes:
            self.assertEquals(v, UNumber.from_roman(self.probes[v]))

    def test_to_roman(self):
        """
        Convert Decimal numbers to roman
        """
        for v in self.probes:
            self.assertEquals(UNumber.to_roman(v), self.probes[v])

    def test_exhaustive(self):
        """
        Test the transformation of all the numbers from 1 to 4999

        note: This is different to the previous test, where pre-known
              pairs are tested. Here only implementation errors are
              detected, not design errors like D being 50 instead of 500.
        """
        for n in range(1, 5000):
            c = UNumber(n)
            r = '{:r}'.format(c)
            v = UNumber(r)
            self.assertEquals(c, v)

    def test_extract_numbers(self):
        """
        Read numbers from strings
        """
        lines = {
            (4, 5): 'Normal line 4 and 5',
            (4.5, 6): 'Line with 4.5 and 6',
            (10, 45): 'Roman X and XLV'
        }

        for num, txt in lines.items():
            roman = txt.startswith('Roman')
            num = [UNumber(x) for x in num]

            values = UNumber.extract_numbers(txt, roman)
            self.assertEquals(values, num)

    def test_is_normal(self):
        """
        Check if a UNumber has decimal part
        """
        self.assertTrue(UNumber(14).is_normal())
        self.assertFalse(UNumber(14.5).is_normal())
