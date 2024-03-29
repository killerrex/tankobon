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


Structure to represent
- A Root Node (Series)
  - With 1 or mode Volumes
    - With 0 or more chapters
"""

from __future__ import annotations

from typing import Optional
from pathlib import Path
import logging
import re
from functools import total_ordering

from .options import OptGroup, Options
from .transform import Transform
from .unumber import UNumber

_logger = logging.getLogger('tankobon')


class Error(Exception):
    """
    Base Exception for this node
    """
    pass


class CannotChooseError(Error):
    """
    Raised when algorithm cannot choose a single number from all the candidates

    Args:
        name: Original file/folder name
    """
    def __init__(self, name):
        super().__init__(name)
        self.name = name


class Base:
    """
    Common tools for all the nodes, including root.

    This is really an abstract class, with the minimum set of methods
    any element must have.

    Attributes:
        _name: Original name of the Element
        _number: Associated number in the collection.
        _hoaxes: List of numbers present in this level name not related
                 with the real number
        _glob: Pattern to select folders for the sub-elements
    """

    def __init__(self, name: str, pattern='*'):
        """
        Create a base object.

        Args:
            name: Original name of the file/folder
        """
        super().__init__()
        self._name = name
        self._number: Optional[UNumber] = None
        self._hoaxes = []
        self._glob = pattern

    def normalize(self):
        """
        Assure the number does not end in .0 even if the original was X.0
        """
        if self._number is None:
            return
        self._number.normalize()

    def path(self) -> Path:
        """
        Get the current real path to this element.

        Returns:
            Base implementation uses the element name as path.
        """
        raise NotImplementedError

    def _listdir(self):
        """
        List all the folders inside this element.

        Returns:
            List with all the subdirectories names
        """
        path = self.path()

        if not path.is_dir():
            return []

        children = [s.name for s in path.glob(self._glob) if s.is_dir()]
        return sorted(children)

    def spurious(self):
        """
        List of numbers that all this element children will inherit.

        Any number present in a children's name just as repetition
        of the parent's numbers is considered spurious.

        Returns:
            hoaxes, level-related
        """
        if self._number:
            level = [int(self._number)]
        else:
            level = []
        return self._hoaxes[:], level

    def wide(self, level=0) -> int:
        """
        Wide to represent all the numbers for the level required.

        Args:
            level: Number of sub-levels to dive.

        Returns:
            Default value is the number of digits for this number
        """
        if self._number is None:
            return 0
        else:
            return len(str(int(self._number)))

    def skip(self):
        """
        Check if this element must not be in nested representations.

        Returns:
            Any element with a valid number is represented.
        """
        return self._number is None

    def is_normal(self):
        """
        Identify a node as normal.

        The nodes can be either normal (i.e. is a whole number) or
        special (extra chapters, oMakes)

        Returns:
            True if it ia a normal one
        """
        return self._number and self._number.is_normal()

    def __int__(self):
        """
        Representation of this element as an integer number.

        Returns:
            The integer part of the number or 0 for specials
        """
        if self._number:
            return int(self._number)
        else:
            return 0

    def __hash__(self):
        """
        Allow to use this element as tag in dicts.

        Returns:
            A hash based only on the name and the number
        """
        return hash(self._number) ^ hash(self._name)


@total_ordering
class Node(Base):
    """
    Common class to all the nodes.

    This class creates the common functions to scan strings,
    formatting and the minimum API required.

    Attributes:
        _parent: Node where this element is nested.
        _option: OptGroup object with the user options for this level.
        _extra: Label to add for the special chapters, or None
    """

    def __init__(self, parent: Base, name, expected, opt: OptGroup):
        """
        Extract the number from the name.

        Args:
            parent: Base object where this element is nested
            name: Current name of the object
            expected: List of number candidates
            opt: User options for this level

        Raises:
            AssertionError: The parent is not a Base object.
        """
        super().__init__(name)
        self._parent = parent
        self._option = opt
        self._extra = None
        self._parse_number(expected)

    def spurious(self):
        """
        List of numbers that can be in the name not for ordering.

        Get the list of numbers that a child may have in the name
        because they are part of the parent's name, so they can be
        discarded

        Returns:
            hoaxes, level related
        """
        hoax, top = super().spurious()
        if self._parent is not None:
            dh, dt = self._parent.spurious()
            hoax.extend(dh)
            top.extend(dt)
        return hoax, top

    def _rm_spurious(self, numbers, greedy=False):
        """
        Remove the spurious numbers from the list.

        Args:
            numbers: List of all the numbers found in this element's name.
            greedy: Try to remove numbers even if only 1 left

        Returns:
            A list of numbers, original is untouched.
        """
        # Avoid modifying entry and assure is mutable
        numbers = list(numbers)

        if self._parent is None:
            return numbers

        hoax, spurious = self._parent.spurious()
        _logger.debug(
            "\tNumbers: %s {%s:%s}",
            str(numbers),
            str(hoax),
            str(spurious)
        )

        # Process hoaxes first, always in not-greedy mode
        for n in hoax:
            # Remove hoaxes only if there is still too many elements
            if len(numbers) == 1:
                break
            if n in numbers:
                numbers.remove(n)
                _logger.debug("\tRemove hoax: %d", n)

        # Remove any spurious value (just once each one)
        for n in spurious:
            if not greedy and len(numbers) == 1:
                break
            if n in numbers:
                numbers.remove(n)
                _logger.debug("\tRemove spurious: %d", n)

        return numbers

    def _guess(self, expected, numbers) -> (UNumber, list):
        """
        Decide the best number of a set as value for the Element.

        Decide the best number of a set considering
        the values found so far...

        Args:
            expected: Numbers expected for this level (i.e. chapter's numbers)
            numbers: Numbers found in the element's name.

        Returns:
            The best candidate, the hoaxes found

        Raises:
            CannotChooseError: Too many options left, cannot decide.
        """
        if len(numbers) == 0:
            # Oh, is a special element...
            return None, []

        # Filter based on the expected ones
        guess = [x for x in numbers if x in expected]
        _logger.debug("\tGuesses from expected: %s", str(guess))

        if not guess:
            # An entry with no numbers in the expected?
            # This maybe a special element with a spurious number
            numbers = self._rm_spurious(numbers, True)

            if len(numbers) == 0:
                # Oh, is a special element...
                return None, []

            # Ok, just pick the first element
            _logger.debug("\tJust pick the first one: %s", str(numbers))
            return numbers[0], numbers[1:]

        if len(guess) == 1:
            _logger.debug("\tJust one guess: %s", str(guess))
            numbers.remove(guess[0])
            return guess[0], numbers

        # Several candidates and numbers...
        raise CannotChooseError(self._name)

    def _parse_number(self, expected):
        """
        Scan the name and determine this Volume/Chapter number.

        Args:
            expected: List of candidate numbers
        """
        _logger.debug("Name: %s", self._name)

        # Isolate all the numbers from the name
        numbers = UNumber.extract_numbers(self._name, self._option.roman)

        if expected is None:
            # This is a non-numbered item, but with a number in the name...
            self._hoaxes.extend(numbers)
            self._number = None
            return

        # Remove any spurious value
        numbers = self._rm_spurious(numbers)
        # Decide from the expected values
        number, hoax = self._guess(expected, numbers)
        self._hoaxes.extend(hoax)

        if number is None:
            # This is a bonus number, use the 'bonus' label
            _logger.debug("  Bonus {}".format(type(self).__name__))
            self._extra = self._option.bonus
            return

        self._number = number
        if self._option.normalize:
            self.normalize()

        # The intermediate chapters are never expected...
        if not self._number.is_normal():
            return
        n = int(self._number)
        try:
            expected.remove(n)
        except ValueError:
            # Ok, this shall be a special one
            _logger.info("%s: Special as %s not in %s", self.path(), n, str(expected))
            self._extra = self._option.special

    def __eq__(self, other: Node):
        """
        Check equality.

        2 nodes are equal when they have the same number and special flag.

        Args:
            other: The other NestedNode

        Raises:
            AssertionError: The other is not a Node instance
        """
        if not isinstance(other, Node):
            return NotImplemented

        def check(a, b):
            return (a is None and b is None) or a == b

        return (
            check(self._number, other._number) and
            check(self._extra, other._extra)
        )

    def __lt__(self, other: Node):
        """
        Order the Nodes by number.

        If both numbers are equal, use special to order.

        Args:
            other: The other NestedNode

        Raises:
            AssertionError: The other is not a Node instance
        """
        if not isinstance(other, Node):
            return NotImplemented

        if self._number is None:
            return False
        if other._number is None:
            return True

        if self._number == other._number:
            if self._extra is None:
                return True
            if other._extra is None:
                return False
            else:
                return self._extra < other._extra
        else:
            return self._number < other._number

    def path(self):
        """
        Build the full path to this element recursively up to the root.

        Returns:
            The nested path to this element
        """
        return self._parent.path() / self._name

    def wide(self, level=0):
        """
        Wide for the elements of the given level

        Args:
            level: The index in the nested structure

        Returns:
            The selected wide for the level
        """
        if level == 0 and self._option.wide >= 0:
            return self._option.wide
        # 0 means just the needed chars
        if self._parent is None:
            return 0
        return self._parent.wide(level + 1)

    def __format__(self, format_spec):
        """
        Scan the format line and return the formatted string.

        Format specification:
        %l: Label
        %m: Real name
        %n: Number, using the level wide
        %r: Number in roman numerals
        %p: Prefix (Only if the level has number)
        %s: Suffix text, only if no bonus (i.e. has a valid number)
        %u: Parent (upper) number
        %R: Parent Number in roman numerals
        %t: Parent prefix
        %_: Blank space only if parent is valid
        %%: Literal %

        Args:
            format_spec: A format string with the desired codes

        Returns:
            The formatted string

        Raises:
            ValueError: Unknown format spec (% + something not listed)
        """
        # If the format is empty, use the default template
        if not format_spec:
            format_spec = self._option.template

        # Split using re
        res = []
        for part in re.split(r'(%[lmnrpsuRt_%])', format_spec):
            if part == '%l':
                part = self._option.label

            elif part == '%m':
                part = self._name

            elif part == '%n':
                if self._number:
                    if self._option.force:
                        part = '{:0{w}f}'.format(self._number, w=self.wide())
                    else:
                        part = '{:0{w}d}'.format(self._number, w=self.wide())
                else:
                    part = self._extra

            elif part == '%r':
                if self._number:
                    part = f'{self._number:r}'
                else:
                    part = self._extra

            elif part == '%p':
                if self._number:
                    part = self._option.prefix
                else:
                    continue

            elif part == '%u':
                if self._parent is None or self._parent.skip():
                    continue
                part = '{:%n}'.format(self._parent)

            elif part == '%R':
                if self._parent is None or self._parent.skip():
                    continue
                part = '{:%r}'.format(self._parent)

            elif part == '%t':
                if self._parent is None or self._parent.skip():
                    continue
                part = self._option.upper

            elif part == '%_':
                if self._parent is None or self._parent.skip():
                    continue
                part = ' '

            elif part == '%s':
                # Add the extra suffix only if no bonus...
                if self._number is None or self._extra is None:
                    continue
                part = self._extra

            elif part == '%%':
                part = '%'

            elif part.startswith('%'):
                raise ValueError(
                    "Unknown format code {} for Node".format(part[1:])
                )
            else:
                # Nothing to do for raw strings
                pass
            if part is None:
                continue
            res.append(part)
        res = ''.join(res)
        # Remove any trailing blanks
        return res.rstrip()

    def __repr__(self):
        return f"<{type(self).__name__} {self._number}>"

    def __str__(self):
        if self._parent:
            return f"{self._parent!s}:{type(self).__name__} {self._number}>"
        else:
            return f"{type(self).__name__} {self._number}"

    def transform(self):
        """
        Create a transform object to the new names.

        Returns:
            The transform of the node.
        """
        return Transform(self._name, format(self))

    def force(self, whole=None, decimal=...):
        """
        Change the internal numbering to the given values

        Args:
            whole: Change the whole number.
            decimal: Change the decimal Use None for no decimal
        """
        if self._number is None:
            self._number = UNumber('0')
        if whole is not None:
            self._number.whole = whole
        if decimal is not Ellipsis:
            self._number.decimal = decimal


class Chapter(Node):
    """
    One chapter inside a volume
    """
    pass


class Volume(Node):
    """
    One complete Tankobon

    Attributes:
        _nodes: List of child nodes
    """

    def __init__(self, parent, name, expected, opt):
        super().__init__(parent, name, expected, opt)
        self._nodes = []

    def populate(self, last, opts):
        """
        Search the directory for chapters.

        List all the directories of the Volume folder
        and try to fit them in the chapter order

        Args:
            last: Last chapter found
            opts: Options for the chapters

        Returns:
            Biggest index of the sub-nodes

        Raises:
            EmptyFolderError: A volume cannot be empty
        """

        if last is None:
            last = opts.first

        chapters = self._listdir()
        if not chapters:
            _logger.info("Empty folder: %s", self._name)
            return last

        numbers = [last + k for k in range(len(chapters))]
        # Update the last element expected
        last = numbers[-1]

        self._nodes = [Chapter(self, c, numbers, opts) for c in chapters]

        # Remove any last numbers not found if we have found special chapters
        for c in self._nodes:
            if c.is_normal():
                continue
            # We know it must be the last element...
            if numbers[-1] == last:
                del numbers[-1]
                last -= 1

        if numbers:
            _logger.info("Volume %d Missing: %s", int(self), str(numbers))

        self._nodes.sort()

        # Prevent several special chapters to collapse to the same name
        seen = {}
        for c in self._nodes:
            # This only happens with the special ones
            if c._number is not None:
                continue
            txt = format(self)
            if txt in seen:
                n = seen[txt] + 1
                c._extra += f" {n}"
            else:
                n = 1
            seen[txt] = n

        if opts.flat:
            return None

        if self._nodes:
            return self.last() + 1
        else:
            return 1

    def last(self):
        """
        Last chapter of the volume
        """
        if self._nodes:
            return max(int(c) for c in self._nodes)
        else:
            return 0

    def __iter__(self):
        """
        Iterate through the elements

        Returns:
            Iterator in the list of child nodes
        """
        return iter(self._nodes)

    def transform(self):
        """
        Return the transformation of this volume
        """
        nest = [node.transform() for node in self._nodes]
        return Transform(self._name, format(self), nest)

    def renumber(self, n0):
        """
        Convert to a continuous numeration

        Args:
            n0: Value of the last chapter. Set it to 0 to reset the count

        Returns:
            Chapter number of the last chapter in this volume
        """
        n = n0
        for chapter in self._nodes:
            if chapter.skip():
                continue
            # Do not increment the counter in special chapters, so they get the
            # same relative position
            if chapter.is_normal():
                n += 1
            chapter.force(whole=n)
        return n


class Series(Base):
    """
    Group of volumes that form a complete collection.

    Attributes:
        _nodes: List of child nodes (Volumes)
        _wides: List of the selected wide for each level
    """

    def __init__(self, opts: Options):
        """
        Create the full series element

        Args:
            opts: Options for the whole collection.
        """
        super().__init__(opts.root.name, pattern=opts.glob)
        self.origin = opts.root.parent
        self._virtual = opts.single

        self._nodes: list[Volume] = []
        self._wides = [0, 0, 0]
        # Search for a number in the old title...
        self._hoaxes = UNumber.extract_numbers(self._name, False)
        # Add any user defined hoax
        self._hoaxes.extend(opts.hoax)
        # Launch the recursive process
        self._populate(opts)
        # change the numeration if needed
        if opts.renumber != 'asis':
            self.renumber(opts.renumber == 'flat')

    def path(self) -> Path:
        if self._virtual:
            return self.origin
        else:
            return self.origin / self._name

    def _populate(self, opts):
        if self._virtual:
            self._populate_single(opts)
        else:
            self._populate_multi(opts)

    def _populate_multi(self, opts: Options):
        """
        Scan the directory

        Args:
            opts: The program options
        """
        nodes = self._listdir()
        expected = [opts.volume.first + x for x in range(len(nodes))]
        # Biggest expected value give the volume optimum width
        # but use always at least 2 chars
        self._wides[1] = max(2, len(str(expected[-1])))

        children = [Volume(self, v, expected, opts.volume) for v in nodes]
        # Reorder as the final numeric order might be different to the alphabetical order
        children.sort()

        # Do not search for chapters in flat mode
        if opts.volume.flat:
            self._nodes = children
            return

        # Now sub-populate
        nxt = None
        ch_wide = 0
        for vol in children:
            try:
                nxt = vol.populate(nxt, opts.chapter)
            except ValueError as err:
                _logger.info("Ignore: %s: %s", str(vol), str(err))
                continue
            self._nodes.append(vol)

            # Get the best wide
            ch_wide = max(ch_wide, len(str(vol.last())))

        if len(self._nodes) != len(children):
            # Some Volume missing, report
            _logger.error('Missing Volumes {}'.format(expected))

        # This last element gives us the optimum wide for chapters
        # but use always at least 2 chars
        self._wides[2] = max(2, ch_wide)

    def _populate_single(self, opts: Options):
        """
        Scan the directory for a single book

        Args:
            opts: The program options
        """
        # Not really used as at volume level there is no number to write
        self._wides[1] = 2
        # As a single book, no bonus or extra for volume level
        opts.volume.bonus = None
        opts.volume.special = None
        nodes = self._listdir()
        if len(nodes) != 1:
            # Assume we are already inside the volume
            vol = Volume(self, opts.root.resolve().name, None, opts.volume)
        else:
            vol = Volume(self, nodes[0], None, opts.volume)
        self._nodes = [vol]

        # Do not search for chapters in flat mode... this is a bit silly in single mode
        if opts.volume.flat:
            return

        # Now sub-populate
        try:
            vol.populate(None, opts.chapter)
        except ValueError as err:
            _logger.info("Ignore: %s: %s", str(vol), str(err))

        # This last element gives us the optimum wide for chapters
        # but use always at least 2 chars
        self._wides[2] = max(2, len(str(vol.last())))

    def wide(self, level=0):
        """
        Returns:
             the optimum wide for the desired level

        Args:
            level: Depth level requesting the value
        """
        return self._wides[level]

    def transform(self):
        """
        Returns:
             the full transformation of all the volumes.
        """
        nest = [node.transform() for node in self._nodes]
        if self._virtual:
            if len(nest) != 1:
                raise ValueError("Virtual series can be only single")
            return nest[0]
        else:
            return Transform(self._name, None, nest)

    def skip(self):
        """
        Skip always the series...

        Returns:
             Always true, the top node is always skip.
        """
        return True

    def renumber(self, flat):
        n = 0
        for vol in self._nodes:
            # Restart all the volumes at chapter 1
            m = vol.renumber(n)
            if not flat:
                n = m
