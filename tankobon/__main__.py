"""
Tankobon Organiser

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

import logging

from . import Tankobon


class Main(Tankobon):
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
        super().__init__(prog, args)
        logging.basicConfig(level=self.opt.log, format=self._Log_Format)


if __name__ == '__main__':
    Main().exec()
