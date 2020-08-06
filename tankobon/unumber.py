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


Universal representation of a number.
It handles also roman numerals
"""

import sys
import re
from functools import total_ordering


@total_ordering
class UNumber:
    """
    Represent a number used in numeration of a chapter/volume...

    The roman numerals are limited to the range [1-4999]
    Special representations like IIII=4 or VIIII=9 are read correctly,
    but not used to print them (so 4=IV)

    Attributes:
        _value: Integer part
        _dec: Decimal part (integer number) or None for whole numbers.
    """

    # Mapping for roman numbers
    _R_VALUES = {
        'I': 1, 'V': 5, 'X': 10, 'L': 50,
        'C': 100, 'D': 500, 'M': 1000
    }
    _R_INV = (
        ('', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX'),
        ('', 'X', 'XX', 'XXX', 'XL', 'L', 'LX', 'LXX', 'LXXX', 'XC'),
        ('', 'C', 'CC', 'CCC', 'CD', 'D', 'DC', 'DCC', 'DCCC', 'CM'),
        ('', 'M', 'MM', 'MMM', 'MMMM')
    )

    # TODO: Improve this RE
    _R_Match = re.compile(r"[IVXLCDM]+")
    _A_Match = re.compile(r"\d+(?:\.\d+)?")

    @classmethod
    def from_roman(cls, txt: str):
        """
        Transform a roman number in decimal.

        Args:
            txt: Input text, only with IVXLCDM characters.

        Returns:
            The decimal number

        Examples:
            >>> UNumber.from_roman('XIX')
            19
            >>> UNumber.from_roman('MMMMCMXCIX')
            4999

        Raises:
            ValueError: The string is not a valid roman numeral
        """

        value = 0
        highest = 0
        for c in reversed(txt.upper()):
            if c not in cls._R_VALUES:
                raise ValueError(f'Invalid roman character [{c}] in {txt}')

            v = cls._R_VALUES[c]
            if v >= highest:
                # The position is bigger than the last bigger value:
                # Changing from V to X or C or ...
                value += v
                highest = v
                continue

            # This is subtractive value, only I, X, C and it must be
            # 5 or 10 times smaller, so the valid sets are:
            # I only with V, X; X only with L, C; C only with D, M
            if v not in (1, 10, 100) or highest // v > 10:
                raise ValueError(f'Invalid roman numeral in {txt} ({c} out of order)')
            value -= v
        return value

    @classmethod
    def to_roman(cls, value: int):
        """
        Write the number in canonical roman form.

        Only numbers between 1 and 4999 are valid.

        Args:
            value: The number to transform

        Returns:
            A string with the number in romans

        Examples:
            >>> UNumber.to_roman(19)
            'XIX'
            >>> UNumber.to_roman(4999)
            'MMMMCMXCIX'

        Raises:
            ValueError: The number is out of the valid range
        """
        if not 0 < value < 5000:
            raise ValueError("Out of valid range [1,4999]")

        res = []
        scale = 0
        while value > 0:
            value, n = divmod(value, 10)
            res.append(cls._R_INV[scale][n])
            scale += 1
        return ''.join(reversed(res))

    @classmethod
    def extract_numbers(cls, txt: str, roman=False):
        """
        Parse the name for valid numbers.

        Args:
            txt: Text to scan
            roman: Search for roman numerals

        Returns:
            A list with the numbers found.
        """
        if roman:
            pattern = cls._R_Match
        else:
            pattern = cls._A_Match

        return [cls(s) for s in pattern.findall(txt)]

    # Add slots to avoid adding new attributes
    __slots__ = ('_value', '_dec')

    def __init__(self, txt):
        """
        Store a number for a volume/chapter.

        Use the decimal point as special release marker.

        Args:
            txt: The numeric string to analyse. It can be also a number
        """

        if not isinstance(txt, str):
            # TODO: Improve the the format applied to different numbers
            txt = str(txt)

        if '.' in txt:
            a, b = txt.split('.', 1)
            self._value = int(a)
            self._dec = int(b)
        elif txt.isdigit():
            self._value = int(txt)
            self._dec = None
        else:
            self._value = self.from_roman(txt)
            self._dec = None

    def __str__(self):
        """
        String representation. Add a decimal part only if is not None (0 will output n.0)
        """
        if self._dec is None:
            return str(self._value)
        else:
            return f"{self._value}.{self._dec}"

    def __repr__(self):
        return f"{type(self).__name__}({self})"

    def __format__(self, format_spec: str):
        """
        Format the number following a specification

        The valid format specifications are:
        - Same as d for arabic format
        - Using f instead of d => force the usage of decimals
        - 'r' for roman format.

        Args:
            format_spec: String with the format specification.

        Returns:
            the formatted string
        """
        if format_spec == 'r':
            # no decimals for roman numbers
            return self.to_roman(self._value)

        if format_spec.endswith('f'):
            # User wants to use float format
            if self._dec is None:
                dec = 0
            else:
                dec = self._dec
            # Get first a float
            f = float(f'{self._value}.{dec}')
            return format(f, format_spec)

        # Ok, normal decimal
        s = format(self._value, format_spec)

        if self._dec is None:
            return s
        else:
            return f"{s}.{self._dec}"

    def __int__(self):
        """
        Select only the whole part of the number

        Returns:
            the Integer part
        """
        return self._value

    def __float__(self):
        """
        Use the float format to include the decimal part

        Returns:
            The number as a floating value
        """
        return float(str(self))

    def __eq__(self, other):
        """
        Compare with other UNumber, float or int

        Args:
            other: Comparison element. Can be also an integer or float

        Returns:
            True if both are equal
        """
        if isinstance(other, UNumber):
            return self._value == other._value and self._dec == other._dec
        elif self._dec:
            # Comparing floating point numbers is always problematic
            # As we compare simple numbers like 1.35, use the system eps
            # as criteria
            return abs(float(self) - other) <= sys.float_info.epsilon
        else:
            return int(self) == other

    def __hash__(self):
        return hash(self._value) ^ hash(self._dec)

    def _tuple(self):
        """
        Create a Tuple with the Integer, decimal

        Returns:
            The tuple representation
        """
        if self._dec:
            return self._value, self._dec
        else:
            return self._value, 0

    def __lt__(self, other):
        """
        Set a total ordering in the numerations.

        The natural order is the tuple representation
        where the None for the decimal is 0

        Args:
            other: An UNumber

        Returns:
            True if this UNumber is smaller in the tuple sense.
        """
        if not isinstance(other, UNumber):
            other = UNumber(other)

        return self._tuple() < other._tuple()

    def is_normal(self):
        """
        Check if this is a special number.

        Returns:
            True if this is a normal number, not an special.
        """
        return self._dec is None
