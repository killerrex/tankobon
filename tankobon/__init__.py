#!/usr/bin/env python3
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
import logging

from .unumber import UNumber
from .options import OptGroup, Options
from .transform import Transform
from .nestable import Chapter, Volume, Series, Error


class Main:
    """
    Tankobon object transformation
    """
    _Log_Format = '%(levelname)s:%(message)s'

    def __init__(self, prog='Tankobon', args=None):
        """
        Create a new application object

        Args:
            prog: Program name
            args: Command line (default: sys.argv)
        """
        super().__init__()

        self.opt = Options(prog, args=args)
        logging.basicConfig(level=self.opt.log, format=self._Log_Format)

        self.target = Series(self.opt)
        # Get the transform
        self.tree = self.target.transform()

    def exec(self):
        """
        Perform the required actions.

        Returns:
            System exit status
        """

        if self.opt.action == 'report':
            self.tree.pretty()
        elif self.opt.action == 'dryrun':
            self.tree.run(True)
        elif self.opt.action == 'enable':
            try:
                self.tree.run(False)
            except Error as er:
                print(str(er))
                return 1
        else:
            raise RuntimeError('Unknown action {}'.format(self.opt.action))

        return 0


__all__ = [
    UNumber, OptGroup, Options, Transform, Chapter, Volume, Series,
    Main
]
