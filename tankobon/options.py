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


Parse the user options and return a nice object
with all the fields classified.
"""

from pathlib import Path
from xdg import BaseDirectory

import argparse

import logging

import configparser


from .transform import WorkMode


class ActionFlag(argparse.Action):
    """
    Option that allows to enable and disable it.
    This allows to use the default value as stored configuration and
    to override it from command line

    If no default value is given, it works as a store_true action

    Developed from:
    https://stackoverflow.com/a/20422915
    """

    _Negate = '--no-'
    """Prefix used for the negate form of the options"""

    # noinspection PyShadowingBuiltins
    def __init__(self, option_strings, dest, default=None, required=False, help=None):
        """
        Create a Flag Action with enable/disable options.

        This action will create an option to enable it and
        other to disable it.

        Only the first option is considered to select the default value.
        If no default value is given and the option starts with
        --no-
        it works as a store_false, for any other option is a store_true.
        Any short option is considered as a store_true and the negation
        is added: -b ==> --no-b

        Args:
            option_strings: Array with the options
            dest: Name of the attribute in the namespace
            default: Initial value of the flag.
                     Use None to select it from the first option
            required: This flag is mandatory
            help: Help string
        """
        assert(len(option_strings) > 0)
        opts = []
        for opt in option_strings:
            if opt.startswith(self._Negate):
                # Negative option => Add the positive version
                opts.append('--' + opt[len(self._Negate):])
                opts.append(opt)
                act = False

            elif opt.startswith('--'):
                # Long positive option => Add the negative
                opts.append(opt)
                opts.append(self._Negate + opt[2:])
                act = True

            elif opt.startswith('-'):
                # Short option, consider it always positive,
                # Add a negative version so -b ==> --no-b
                opts.append(opt)
                opts.append(self._Negate + opt[1:])
                act = True
            else:
                # No command line arguments accepted
                raise ValueError('Flags cannot be cmd line arguments')

            if default is None:
                default = act

        super().__init__(
            opts, dest, nargs=0, const=None, default=default,
            type=None, choices=None, required=required,
            help=help, metavar=None
        )

    def __call__(self, parser, namespace, values, option_strings=None):
        assert(option_strings is not None)
        is_negative = option_strings.startswith(self._Negate)
        setattr(namespace, self.dest, not is_negative)


class OptDict:
    """
    Group options in a single container.

    This base class has just the mapping and representation logic.
    The options can be referred as attributes or dict keys

    Internal Attributes:
        _map: Store the option <=> ArgParse relation.
    """

    def __init__(self):
        super().__init__()
        self._map = {}

    def __repr__(self):
        s = [
            f'{key}={getattr(self, key)}' for key in vars(self)
            if not key.startswith('_')
        ]
        return '{}({})'.format(type(self).__name__, ', '.join(s))

    def __getitem__(self, item):
        """
        Work as a dictionary of options

        Args:
            Any of the attributes

        Returns:
            The attribute value
        """
        return self.__dict__[item]

    def store(self, config):
        """
        Store this element in an ini file

        Args:
            config: The ConfigParser object
        """
        raise NotImplementedError

    def load(self, config):
        """
        Read from an ini file

        Args:
            config: a ConfigParser object
        """
        raise NotImplementedError

    def _classify(self, args):
        """
        Create a sub namespace with the options of this group.

        Args:
            args: a Namespace from argparse
        """
        args = vars(args)
        for key, label in self._map.items():
            if key in args:
                self.__dict__[label] = args[key]


class OptGroup(OptDict):
    """
    Create an option group with all the common options
    for volumes and chapters

    Internal Attributes:
        _name: Full name of the level for the help strings

    Attributes:
        prefix: Initial string for the options
        label: String to use as series name at this level
        roman: Flag to select arabic or roman formats
        first: Specify the number of the first element instead of 1
        flat: Element with no sub-elements or start counting in each container.
        template: Format used for this level
        upper: String used to tag the parent numbers at this level
               So at chapter level this is the 'V' that goes with volume.
        wide: Number of digits to use
        special: suffix to add to the special volumes/chapters (Out of numeration)
        bonus: suffix to add to the bonus chapters
        normalize: Remove unnecessary fractional parts from the numbers
    """

    def __init__(self, name: str, prefix: str = None, **kwargs):
        """
        Create a default options group

        Args:
            name: Full name for the help strings
            prefix: Identifier of the level (equal to name if omitted)
            **kwargs: Any other attribute to set its initial value
        """
        super().__init__()

        self._name = name

        if prefix is None:
            prefix = name
        self.prefix = prefix

        # The label cannot be a fixed value
        self.label = None

        # Default Values
        self.roman = False
        self.first = 1
        self.flat = False
        # Default template:
        # If the element has no parent:
        # 'Series name Vol 01'
        # If it has a parent:
        #  'Series name Vol 01 Cap 01'
        self.template = '%l%_%t%u %p%n%s'
        self.upper = None
        self.wide = -1  # Auto
        self.force = False
        self.special = ' Special'
        self.bonus = 'Bonus'
        self.normalize = False

        # Inherit any user given value
        self.__dict__.update(kwargs)

    def store(self, config):
        """
        Store this element in an ini file

        Args:
            config: The ConfigParser object
        """
        config[self._name] = {
            'roman': self.roman,
            'first': self.first,
            'flat': self.flat,
            'template': self.template,
            'prefix': self.prefix,
            'upper': self.upper,
            'wide': self.wide,
            'force': self.force,
            'special': self.special,
            'bonus': self.bonus,
            'normalize': self.normalize
        }

    def load(self, config):
        """
        Read from an ini file

        Args:
            config: a ConfigParser object
        """
        if self._name not in config:
            return
        sub = config[self._name]
        self.roman = sub.getboolean('roman', vars=self)
        self.first = sub.getint('first', vars=self)
        self.flat = sub.getboolean('flat', vars=self)
        self.template = sub.get('template', vars=self)
        self.prefix = sub.get('prefix', vars=self)
        self.upper = sub.get('upper', vars=self)
        self.wide = sub.getint('wide', vars=self)
        self.force = sub.getfloat('force', vars=self)
        self.special = sub.get('special', vars=self)
        self.bonus = sub.get('bonus', vars=self)
        self.normalize = sub.getboolean('normalize', vars=self)

    def add_group(self, is_bottom: bool, parser: argparse.ArgumentParser, tag=None):
        """
        Add The options to an argument parser

        Args:
            is_bottom: True for the lowest level element options
            parser: The ArgumentParser
            tag: The initial label (use prefix if omitted)
        """
        if tag is None:
            tag = self.prefix.strip().lower()

        # This is just to shorten the expressions
        name = self._name

        group = parser.add_argument_group(
            title=f'{name} Options',
            description=f'Options to control the input and output of {name} level'
        )

        g = group.add_argument(
            f'--{tag}-normalize', action=ActionFlag, default=self.normalize,
            help=f'Remove unnecessary fractional parts in {name} numbers'
        )
        self._map[g.dest] = 'normalize'

        # Search for roman numerals in the input?
        g = group.add_argument(
            f'--{tag}-roman', action=ActionFlag, default=self.roman,
            help=f'Search for roman numerals in {name} names'
        )
        self._map[g.dest] = 'roman'

        # Number of the first element
        g = group.add_argument(
            f'--{tag}-first', type=int, default=self.first,
            metavar='N', help=f'Number of the first {name}'
        )
        self._map[g.dest] = 'first'

        # Is a flat element: This depends of volumes/chapters...
        if is_bottom:
            h = f'Flat {name}, elements restarts the count in each container'
        else:
            h = f'Flat {name}, with no sub levels'
        g = group.add_argument(
            f'--{tag}-flat', action=ActionFlag, default=self.flat, help=h
        )
        self._map[g.dest] = 'flat'
        # Add the opposite, so it is possible to overwrite

        # Output name template
        g = group.add_argument(
            f'--{tag}-template', default=self.template,
            metavar='TPL', help=f'Template for {name} output names'
        )
        self._map[g.dest] = 'template'

        # Level memo letter to use
        g = group.add_argument(
            f'--{tag}-prefix', default=self.prefix, metavar='TAG',
            help=f'Prefix of the {name} level (default: %(default)s)'
        )
        self._map[g.dest] = 'prefix'

        # Parent level memo (if any)
        g = group.add_argument(
            f'--{tag}-upper', default=self.upper, metavar='TAG',
            help=f'Prefix for the {name} parent level (default: %(default)s)'
        )
        self._map[g.dest] = 'upper'

        # Number of digits in the output
        g = group.add_argument(
            f'--{tag}-wide', type=int, default=self.wide, metavar='W',
            help=f'Digits in the {name} numbers (default: auto)'
        )
        self._map[g.dest] = 'wide'

        # Force usage of decimal
        g = group.add_argument(
            f'--{tag}-float', action='store_true',
            help=f'Force to use decimal value in the {name} numbers (default: False)'
        )
        self._map[g.dest] = 'force'

        # Label to use
        g = group.add_argument(
            f'--{tag}-label', metavar='TXT',
            help=f'Label to use for {name} (default: series name)'
        )
        self._map[g.dest] = 'label'

        # Special name
        g = group.add_argument(
            f'--{tag}-special', default=self.special, metavar='TXT',
            help=f'Additional text for {name} numbered items out of the sequence'
        )
        self._map[g.dest] = 'special'

        # Bonus name
        g = group.add_argument(
            f'--{tag}-bonus', default=self.bonus, metavar='TXT',
            help=f'Text for the number in the {name} bonus entries'
        )
        self._map[g.dest] = 'bonus'


_Description = """
Sort Manga series to obtain uniform volume/chapter tree.
Identify the numbers from the directory names, even if they are
in roman numerals."""

_Epilog = """
Notice that by default the tool just report, as in a dry run.
Label syntax:
    %l: Label
    %m: Real name
    %n: Number, using the level wide
    %r: Number in roman numerals
    %p: Prefix
    %s: Suffix text, only if no bonus (i.e. has a valid number)
    %u: Parent (upper) number
    %R: Parent Number in roman numerals
    %t: Parent prefix
    %_: Blank space only if parent is valid
    %%: Literal %
"""


class Options(OptDict):
    """
    Full set of options.

    Add the program general options and the capacity to read and write
    to a configuration file.

    Use the XDG convention to store the default options file.

    Attributes:
        name: Full name that the series shall have
        root: Series directory
        action: Can be one of
                - report: Pretty print of the structure found
                - dryrun: Echo the mv commands, but keep the folders intact
                - enable: Move the folders to the new names
        single: There is just one volume, with chapters
        log: Log level, one of 'debug', 'info', 'quiet'
        volume: Options for the volume level
        chapter: Options for the chapter level
    """
    Config = 'config.ini'
    Label = "GENERAL"

    @classmethod
    def get_ini(cls, prog: str, store=False):
        """
        Select the best ini file for the program

        Args:
            prog: Name of the xdg section
            store: Is this file to write the options?

        Returns:
            The config file or None
        """
        if store:
            d = Path(BaseDirectory.save_config_path(prog))
            f = d / cls.Config
            return f.open('wt')

        d = BaseDirectory.load_first_config(prog)
        if d is None:
            return None
        f = Path(d) / cls.Config
        if f.is_file():
            return f.open('r')
        else:
            return None

    def __init__(self, prog: str = None, args=None):
        """
        Parse the options in a nice object...

        Args:
            prog: Program identifier for xdg
            args: Command line args (sys.argv by default)
        """
        super().__init__()

        # noinspection PyTypeChecker
        parser = argparse.ArgumentParser(
            description=_Description,
            epilog=_Epilog,
            formatter_class=argparse.RawDescriptionHelpFormatter
        )
        # General options
        self.name = None
        self.root = None
        self.action = WorkMode.REPORT
        self.glob = '*'
        self.single = False
        self.log = 'info'
        self.hoax = []
        self.renumber = 'asis'

        self.volume = OptGroup('Volume', 'vol ')
        self.volume.add_group(False, parser)

        self.chapter = OptGroup('Chapter', 'c', upper='v', special=' oMake')
        self.chapter.add_group(True, parser, tag='ch')

        self.add_group(parser)

        args = parser.parse_args(args=args)

        if args.config:
            ini = args.config
        else:
            ini = self.get_ini(prog)

        if ini:
            # Read the configuration before processing the command line
            # so command line has precedence over stored values
            config = configparser.ConfigParser()
            config.read_file(ini)
            self.load(config)
            ini.close()

        self._classify(args)

        # Store the configuration if required
        if args.store is not None:
            config = configparser.ConfigParser()

            self.store(config)

            if args.store == '':
                # Use the xdg specification
                args.store = self.get_ini(prog, True)
            config.write(args.store)

        if not self.root:
            raise ValueError('Root cannot be empty')

        if not self.root.is_dir():
            raise ValueError(f'Root is not a folder: {self.root}')

        if self.volume.label is None:
            self.volume.label = self.name

        if self.chapter.label is None:
            self.chapter.label = self.name

    def load(self, config):
        """
        Read from an ini file

        Args:
             config: a ConfigParser object
        """
        self.volume.load(config)
        self.chapter.load(config)
        if self.Label not in config:
            return
        sub = config[self.Label]
        self.glob = sub.get('glob', vars=self)
        self.single = sub.getboolean('single', vars=self)
        self.action = WorkMode(sub.get('action', vars=self))
        self.log = sub.get('log', vars=self)
        self.hoax = [int(s) for s in sub.get('hoax', vars=self).split()]
        self.renumber = sub.get('renumber', 'asis')

    def store(self, config):
        """
        Write to an ini file

        Args:
            config: a ConfigParser object
        """
        config[self.Label] = {
            'glob': self.glob,
            'single': self.single,
            'action': self.action.value,
            'log': self.log,
            'hoax': ' '.join(str(n) for n in self.hoax),
            'renumber': self.renumber,
        }
        self.volume.store(config)
        self.chapter.store(config)

    def add_group(self, parser):
        """
        General options

        Args:
            parser: An ArgParse object
        """
        g = parser.add_argument('name', help='Name of the series')
        self._map[g.dest] = 'name'

        g = parser.add_argument(
            'root', type=Path, nargs='?', default='.',
            help='Root directory of the series'
        )
        self._map[g.dest] = 'root'

        # Config and store are special arguments, only relevant
        # for the parser itself
        parser.add_argument(
            '--config', type=argparse.FileType('r'),
            help='Read default configuration from given file'
        )

        parser.add_argument(
            '--store', type=argparse.FileType('w'), nargs='?',
            help='Write the config (optional, give a file)'
        )

        g = parser.add_argument(
            f'--glob', default=self.glob,
            help=f'Glob expression to select folders (default %(default)s)'
        )
        self._map[g.dest] = 'glob'

        g = parser.add_argument(
            '--single', action=ActionFlag, default=self.single,
            help='The series has just one volume'
        )
        self._map[g.dest] = 'single'

        g = parser.add_argument(
            '--action', choices=[act.value for act in WorkMode],
            type=WorkMode,
            default=self.action,
            help='Working mode of the program. Dry run prints the mv commands'
        )
        self._map[g.dest] = 'action'

        # Add some alias to --action
        parser.add_argument(
            '--report', action='store_const', dest='action', const=WorkMode.REPORT,
            help='Just report the structure found. Equal to --action=report'
        )
        parser.add_argument(
            '--dry-run', action='store_const', dest='action', const=WorkMode.DRY_RUN,
            help='Echo the mv actions. Equal to --action=dryrun'
        )
        parser.add_argument(
            '--enable', action='store_const', dest='action', const=WorkMode.ENABLE,
            help='Move the directories to the new names. Equal to --action=enable'
        )

        g = parser.add_argument(
            '--log', choices=['debug', 'info', 'quiet'],
            default=self.log, help="Select log level [%(default)s]"
        )
        self._map[g.dest] = 'log'

        g = parser.add_argument(
            '--hoax', type=int, action='append', default=self.hoax,
            help='Numbers to ignore from all the levels'
        )
        self._map[g.dest] = 'hoax'

        g = parser.add_argument(
            '--renumber', choices=['asis', 'flat', 'continuous'],
            default='asis', help='Change the chapter numeration schema'
        )
        self._map[g.dest] = 'renumber'

    def _classify(self, args):
        """
        Get the options from the parser

        Args:
            args: Return value from parse arguments.
        """
        super()._classify(args)

        levels = {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'quiet': logging.CRITICAL
        }

        self.log = levels[args.log]

        self.volume._classify(args)
        self.chapter._classify(args)
