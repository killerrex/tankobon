# coding=utf-8

"""
Tankobon Organiser Module

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

from .unumber import UNumber
from .options import OptGroup, Options
from .transform import Transform
from .nestable import Chapter, Volume, Series, Error


class Tankobon:
    """
    Tankobon object transformation
    """

    def __init__(self, prog='Tankobon', args=None):
        """
        Create a new application object

        Args:
            prog: Program name
            args: Command line (default: sys.argv)
        """
        super().__init__()

        self.opt = Options(prog, args=args)
        self._target = None
        self._tree = None

    @property
    def target(self) -> Series:
        if self._target is None:
            self._target = Series(self.opt)
        return self._target

    @property
    def tree(self) -> Transform:
        if self._tree is None:
            self._tree = self.target.transform()
        return self._tree

    def exec(self):
        """
        Perform the required actions.

        Returns:
            System exit status
        """
        tree = self.tree

        try:
            tree(self.opt.action)
        except Error as er:
            print(str(er))
            return 1
        return 0


__all__ = [
    'UNumber', 'OptGroup', 'Options', 'Transform', 'Chapter', 'Volume', 'Series', 'Tankobon'
]
