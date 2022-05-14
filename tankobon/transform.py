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


Transform objects store the mapping between the old and new names,
and the correct order to rename them.
"""

from pathlib import Path
from enum import Enum

import logging

_logger = logging.getLogger('tankobon')


class WorkMode(Enum):
    # Just describe what it is found
    REPORT = 'report'
    # Show the bash commands but do nothing
    DRY_RUN = 'dry-run'
    # Really perform the renaming
    ENABLE = 'enable'


class Transform:
    """
    Create a nested transformation object
    A transform is the rename action of
    a file or a directory.

    Attributes:
        _old: Original name of the file/directory
        _new: New name of the file/directory
        _nested: For directories, transform of the contents.
    """
    _Tab = '    '

    def __init__(self, old: str, new: str = None, nested=None):
        """
        Create a transform from old to new.
        Use nested argument for directory transforms

        Args:
            old: Old name
            new: New name. Set it to None to use the same name, but move the folder.
            nested: list of Transform objects or None
        """
        super().__init__()

        self._old = old
        self._new = new

        self._nested = []
        if nested is None:
            return
        for obj in nested:
            assert(isinstance(obj, Transform))
            self._nested.append(obj)

    @property
    def old(self) -> str:
        """
        Existing name
        """
        return self._old

    @property
    def new(self) -> str:
        """
        New name
        """
        return self._new

    def _two_cols(self, tabs=''):
        """
        Get a two columns transform schema

        Return:
            [old], [new]
        """
        old = [f'{tabs}{self._old}']
        if self._new is None:
            new = list(old)
        else:
            new = [f'{tabs}{self._new}']

        # Now the nested ones...
        tabs += self._Tab
        for sub in self._nested:
            s_old, s_new = sub._two_cols(tabs)
            old.extend(s_old)
            new.extend(s_new)
        return old, new

    def pretty(self, tabs='', as_log=False):
        """
        Write the transform schema in a nice format.

        It can write to the info logger level or the stdout.

        Args:
            tabs: String to add to each line as tabs for alignment
            as_log: Use the log as output
        """
        # Obtain the info as 2 columns
        old, new = self._two_cols(tabs)

        c = max(len(s) for s in old)
        for o, n in zip(old, new):
            txt = f'{o:<{c}s} ==> {n}'

            if as_log:
                _logger.info(txt)
            else:
                print(txt)

    def run(self, dry: bool, path: Path = None):
        """
        Rename the files and directories.

        Args:
            dry: Just simulate the execution
            path: Base path to apply this transform
        """
        if not path:
            path = Path.cwd()

        old = path / self._old

        # First move all the child
        for sub in self._nested:
            sub.run(dry, old)

        # Check if this is the top node
        if self._new is None:
            # This is the root
            return

        new = path / self._new

        # Now transform this element
        try:
            r = new.resolve(strict=True)
            is_same = old.samefile(r)
        except FileNotFoundError:
            is_same = False
        if is_same:
            _logger.debug("Same folders: '%s' '%s';", old, new)
        elif dry:
            _logger.info("mv '%s' '%s';", old, new)
        else:
            _logger.debug("mv '%s' '%s';", old, new)
            old.replace(new)

    def __eq__(self, other):
        """
        Check if this transform is equal to other

        Two transforms are equal iff both have equal
        old and new names and the nested ones are also
        equal and defined in the same order

        Args:
            other: A Transform object

        Returns:
            True if both transforms are equivalent
        """
        if not isinstance(other, Transform):
            return NotImplemented
        if self._old != other._old:
            return False
        if self._new != other._new:
            return False
        if len(self._nested) != len(other._nested):
            return False
        for a, b in zip(self._nested, other._nested):
            if a != b:
                return False
        return True

    def __repr__(self):
        """
        Simple representation
        """
        name = type(self).__name__
        if len(self._nested) == 0:
            extra = ', ...'
        else:
            extra = ''

        return f'{name}({self._old!r}, {self._new!r}{extra})'

    def __call__(self, action: WorkMode, *args, **kwargs):
        """
        Realize the transformation (or report about it)

        Args:
            action: Work mode
            *args: Extra arguments to run or pretty
            **kwargs: Extra arguments to run or pretty
        """
        if action is WorkMode.REPORT:
            self.pretty(*args, **kwargs)
        elif action is WorkMode.DRY_RUN:
            self.run(True, *args, **kwargs)
        elif action is WorkMode.ENABLE:
            self.run(False, *args, **kwargs)
        else:
            raise RuntimeError(f'Unknown action {action}')
