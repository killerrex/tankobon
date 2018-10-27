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


Parse the user options and return a nice object
with all the fields classified.
"""

from xdg import BaseDirectory

import argparse
from collections import OrderedDict
import os

import logging

import configparser


class ActionFlag(argparse.Action):
    """
    Option that allows enable and disable it.
    This allows to use the default value as stored configuration
    but it can be override from command line

    If no default value is given, it works as an store_true action

    Developed from:
    http://stackoverflow.com/a/20422915
    """

    _Negate = '--no-'
    """Prefix used for the negate form of the options"""

    def __init__(self, option_strings, dest, default=None, required=False, help=None):
        """
        Create a Flag Action with enable/disable options.

        This action will create an option to enable it and
        other to disable it.

        Only the first option is considered to select the default value.
        If no default value is given and the option starts with
        --no-
        it works as a store_false, for any other option is a store_true.
        Any short option is consider as a store_true and the negation
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
            '{}={}'.format(key, getattr(self, key)) for key in vars(self)
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
        flat: Element with no subelements or start counting in each container.
        template: Format used for this level
        upper: String used to tag the parent numbers at this level
               So at chapter level this is the 'V' that goes with volume.
        wide: Number of digits to use
        special: suffix to add to the special volumes/chapters (Out of numeration)
        bonus: suffix to add to the bonus chapters
    """

    def __init__(self, name: str, prefix: str=None, **kwargs):
        """
        Create a default options group

        Args:
            name: Full name for the help strings
            prefix: Identifier of the level (equal to name if omitted)
            **kwargs: Any other attribute to set it's initial value
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
        # If has a parent
        #  'Series name Vol 01 Cap 01'
        self.template = '%l%_%t%u %p%n%s'
        self.upper = None
        self.wide = -1  # Auto
        self.special = ' Special'
        self.bonus = 'Bonus'

        # Inherit any user given value
        self.__dict__.update(kwargs)

    def store(self, config):
        """
        Store this element in an ini file

        Args:
            config: The ConfigParser object
        """
        d = OrderedDict()
        d['roman'] = self.roman
        d['first'] = self.first
        d['flat'] = self.flat
        d['template'] = self.template
        d['prefix'] = self.prefix
        d['upper'] = self.upper
        d['wide'] = self.wide
        d['special'] = self.special
        d['bonus'] = self.bonus
        config[self._name] = d

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
        self.special = sub.get('special', vars=self)
        self.bonus = sub.get('bonus', vars=self)

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
            title='{} Options'.format(name),
            description='Options to control the input and output of {} level'.format(name)
        )

        # Search for roman numerals in the input?
        g = group.add_argument(
            '--{}-roman'.format(tag), action=ActionFlag, default=self.roman,
            help='Search for roman numerals in {} names'.format(name)
        )
        self._map[g.dest] = 'roman'

        # Number of the first element
        g = group.add_argument(
            '--{}-first'.format(tag), type=int, default=self.first,
            metavar='N', help='Number of the first {}'.format(name)
        )
        self._map[g.dest] = 'first'

        # Is a flat element: This depends of volumes/chapters...
        if is_bottom:
            h = 'Flat {}, elements restarts the count in each container'
        else:
            h = 'Flat {}, with no sub levels'
        g = group.add_argument(
            '--{}-flat'.format(tag), action=ActionFlag, default=self.flat,
            help=h.format(name)
        )
        self._map[g.dest] = 'flat'
        # Add the opposite, so it is possible to overwrite

        # Output name template
        g = group.add_argument(
            '--{}-template'.format(tag), default=self.template,
            metavar='TPL', help='Template for {} output names'.format(name)
        )
        self._map[g.dest] = 'template'

        # Level memo letter to use
        g = group.add_argument(
            '--{}-prefix'.format(tag), default=self.prefix, metavar='TAG',
            help='Prefix of the {} level (default: %(default)s)'.format(name)
        )
        self._map[g.dest] = 'prefix'

        # Parent level memo (if any)
        g = group.add_argument(
            '--{}-upper'.format(tag), default=self.upper, metavar='TAG',
            help='Prefix for the {} parent level (default: %(default)s)'.format(name)
        )
        self._map[g.dest] = 'upper'

        # Number of digits in the output
        g = group.add_argument(
            '--{}-wide'.format(tag), type=int, default=self.wide, metavar='W',
            help='Digits in the {} numbers (default: auto)'.format(name)
        )
        self._map[g.dest] = 'wide'

        # Label to use
        g = group.add_argument(
            '--{}-label'.format(tag), metavar='TXT',
            help='Label to use for {} (default: series name)'.format(name)
        )
        self._map[g.dest] = 'label'

        # Special name
        g = group.add_argument(
            '--{}-special'.format(tag), default=self.special, metavar='TXT',
            help='Additional text for {} numbered items out of the sequence'.format(name)
        )
        self._map[g.dest] = 'special'

        # Special name
        g = group.add_argument(
            '--{}-bonus'.format(tag), default=self.bonus, metavar='TXT',
            help='Text for the number in the {} bonus entries'.format(name)
        )
        self._map[g.dest] = 'bonus'


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
            d = BaseDirectory.save_config_path(prog)
            f = os.path.join(d, cls.Config)
            return open(f, 'wt')

        d = BaseDirectory.load_first_config(prog)
        if d is None:
            return None
        f = os.path.join(d, cls.Config)
        if os.path.isfile(f):
            return open(f, 'r')
        else:
            return None

    def __init__(self, prog: str=None, args=None):
        """
        Parse the options in a nice object...

        Args:
            prog: Program identifier for xdg
            args: Command line args (sys.argv by default)
        """
        super().__init__()

        parser = argparse.ArgumentParser(
            formatter_class=argparse.RawDescriptionHelpFormatter,
            description="""
Sort Manga series to obtain uniform volume/chapter tree.
Identify the numbers from the directory names, even if they are
in roman numerals.""",
            epilog="""
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
""")
        # General options
        self.name = None
        self.root = None
        self.action = 'report'
        self.single = False
        self.log = 'info'
        self.hoax = []

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

        assert(os.path.isdir(self.root))

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
        self.single = sub.getboolen('single', vars=self)
        self.action = sub.getboolean('action', vars=self)
        self.log = sub.get('log', vars=self)
        self.hoax = [int(s) for s in sub.get('hoax', vars=self).split()]

    def store(self, config):
        """
        Write to an ini file

        Args:
            config: a ConfigParser object
        """
        d = OrderedDict()
        d['single'] = self.single
        d['action'] = self.action
        d['log'] = self.log
        d['hoax'] = ' '.join(str(n) for n in self.hoax)
        config[self.Label] = d
        self.volume.store(config)
        self.chapter.store(config)

    def add_group(self, parser):
        """
        General options

        Args:
            parser: An ArgParse object
        """
        g = parser.add_argument("name", help="Name of the series")
        self._map[g.dest] = 'name'

        g = parser.add_argument(
            "root", nargs='?', default=".",
            help="Root directory of the series"
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
            '--single', action=ActionFlag, default=self.single,
            help='The series has just one volume'
        )
        self._map[g.dest] = 'single'

        g = parser.add_argument(
            '--action', choices=['report', 'dryrun', 'enable'],
            default=self.action,
            help='Working mode of the program. Dry run prints the mv commands'
        )
        self._map[g.dest] = 'action'

        # Add some alias to --action
        parser.add_argument(
            '--report', action='store_const', dest='action', const='report',
            help='Just report the structure found. Equal to --action=report'
        )
        parser.add_argument(
            '--dry-run', action='store_const', dest='action', const='dryrun',
            help='Echo the mv actions. Equal to --action=dryrun'
        )
        parser.add_argument(
            '--enable', action='store_const', dest='action', const='enable',
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
