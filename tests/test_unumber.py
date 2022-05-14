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
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

from tankobon import UNumber

import pytest


@pytest.fixture
def probes():
    probes = {
        1: 'I', 4: 'IV', 5: 'V', 9: 'IX',
        10: 'X', 12: 'XII', 14: 'XIV', 19: 'XIX', 48: 'XLVIII',
        50: 'L', 67: 'LXVII', 89: 'LXXXIX',
        100: 'C', 194: 'CXCIV', 468: 'CDLXVIII',
        500: 'D', 793: 'DCCXCIII',
        1000: 'M', 4999: 'MMMMCMXCIX'
    }
    return probes


def test_from_roman(probes):
    """
    Convert roman numbers to decimal
    """
    for v in probes:
        assert v == UNumber.from_roman(probes[v])


def test_to_roman(probes):
    """
    Convert Decimal numbers to roman
    """
    for v in probes:
        assert UNumber.to_roman(v) == probes[v]


def test_roman_special():
    """
    Special cases of roman numbers like IIII for 4.
    """
    assert UNumber.from_roman('IIII') == 4
    assert UNumber.from_roman('VIIII') == 9


def test_exhaustive():
    """
    Test the transformation of all the numbers from 1 to 4999

    note: This is different to the previous test, where pre-known
          pairs are tested. Here only implementation errors are
          detected, not design errors like swapping D and L in the definition.
    """
    for n in range(1, 5000):
        c = UNumber(n)
        r = f'{c:r}'
        v = UNumber(r)
        assert c == v


def test_extract_numbers():
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
        assert values == num


def test_is_normal():
    """
    Check if a UNumber has decimal part
    """
    assert UNumber(14).is_normal()
    assert not UNumber(14.5).is_normal()


def test_accessors():
    """
    Check the modification of the number content
    """
    un = UNumber('3.14')

    assert un.whole == 3
    assert un.decimal == 14

    # Try to change the values
    un.whole = 5
    assert int(un) == 5
    assert float(un) == pytest.approx(5.14)
    un.decimal = 33
    assert float(un) == pytest.approx(5.33)
    assert not un.is_normal()
    un.decimal = None
    assert un.is_normal()
