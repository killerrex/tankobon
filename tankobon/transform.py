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


Transform objects store the mapping between the old and new names,
and the correct order to rename them.
"""
import os
import shutil

import logging
_logger = logging.getLogger('tankobon')


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

    def __init__(self, old, new, nested=None):
        """
        Create a transform from old to new.
        Use nested argument for directory transforms

        Args:
            old: Old name
            new: New name
            nested: list of Transform objects or None
        """
        super().__init__()

        self._old = old
        self._new = new
        self._nested = nested or []

    def _two_cols(self, tabs=''):
        """
        Get a two columns transform schema

        Return:
            [old], [new]
        """
        old = ['{}{}'.format(tabs, self._old)]
        if self._new is None:
            new = [old[0]]
        else:
            new = ['{}{}'.format(tabs, self._new)]

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
        # Obtain the info as a 2 columns
        old, new = self._two_cols(tabs)

        c = max(len(s) for s in old)
        for o, n in zip(old, new):
            txt = o.ljust(c) + ' ==> ' + n

            if as_log:
                _logger.info(txt)
            else:
                print(txt)

    def run(self, dry, path=None):
        """
        Rename the files and directories.

        Args:
            dry: Just simulate the execution
            path: Base path to apply this transform
        """
        if path:
            old = os.path.join(path, self._old)
        else:
            old = self._old

        # First move all the child
        for sub in self._nested:
            sub.run(dry, old)

        # Check if this is the top node
        if self._new is None:
            # This is the root
            return

        new = os.path.join(path, self._new)

        # Now transform this element
        if dry:
            _logger.info("mv '%s' '%s';", old, new)
        else:
            _logger.debug("mv '%s' '%s';", old, new)
            shutil.move(old, new)

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
            return "{}({}, {})".format(name, self._old, self._new)
        else:
            return "{}({}, {}, ...)".format(name, self._old, self._new)
