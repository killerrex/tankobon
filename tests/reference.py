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


This module contains test helpers for the tankobon tool
"""
import tankobon


class LevelFmt:
    """
    Clumsy object to group level properties
    """
    def __init__(self, wide, tag):
        super().__init__()
        self.wide = wide
        self.tag = tag


class Reference:
    """
    Generator of transforms
    """
    _Layout = {
        'nominal': {
            'volumes': [1, 2, 3],
            'chapters': [
                [1, 2, 3, 4],
                [5, 6, 7, 7.2, 8, 9],
                [10, 11, 12, 13, 'oMake']
            ],
            'labels': ['nominal', 'Nom', 'Nom']
        },
        'num1': {
            'volumes': [1, 2, 3],
            'chapters': [
                [1, 2, 3],
                [4, 5, 6, 7, 8],
                [9, 10, 11, 12, 13]
            ],
            'labels': ['Num 1 in title', 'Num 1 in title', 'Num 1 in title']
        },
        'miss': {
            'volumes': [2, 3],
            'chapters': [
                [4, 5, 6],
                [7, 8, 9, 10]
            ],
            'labels': ['Miss vol 1', 'Miss Vol 1', 'Miss vol 1']
        },
        'flatvol': {
            'volumes': [1, 2, 3],
            'chapters': [[], [], []],
            'labels': ['No Chapters', 'No Chapter']
        },
        'reset': {
            'volumes': [1, 2, 3],
            'chapters': [
                [1, 2, 3, 4],
                [1, 2, 3],
                [1, 2, 3, 4, 5]
            ],
            'labels': ['Reset Count', 'Reset', 'Reset']
        },
        'single': {
            'volumes': [None],
            'chapters': [[1, 2, 3]],
            'labels': [None, 'Single Vol', 'Single']
        }

    }

    def __init__(self, labels, volumes, chapters):
        """
        Create a new transform generator from the
        reference defined in the arguments
        Args:
            labels: ['series', 'volumen', 'chapter']
            volumes: [n]
            chapters: [[c1,...]...]
        """
        super().__init__()
        if isinstance(labels, str):
            labels = [labels]*3
        assert(len(labels) > 0)

        self.labels = labels
        while len(self.labels) < 3:
            self.labels.append(labels[0])

        self.volumes = volumes
        assert(len(volumes) == len(chapters))
        self.chapters = chapters

    def __call__(self, name, vfmt, cfmt, extra):
        """
        Create a fake transform with the given specs for
        Args:
            name: Series name
            vfmt: LevelFmt with wide and tag for the volume
            cfmt: LevelFmt with wide and tag for the Chapter
            extra: Label for the extra chapter

        Returns:
            A Transform object
        """
        assert(isinstance(vfmt, LevelFmt))

        old_d = {'wv': 2, 'tv': ['v', 'v'], 'wc': 2, 'wf': 4, 'tc': 'c'}
        new_d = {'wv': vfmt.wide, 'tv': vfmt.tag}
        if cfmt is not None:
            new_d['wc'] = cfmt.wide
            new_d['wf'] = cfmt.wide + 2
            new_d['tc'] = cfmt.tag

        res = []
        for v, cha in zip(self.volumes, self.chapters):
            # First the childs
            nested = []

            if v is None:
                v_block = ''
            else:
                v_block = ' {tv[1]}{v:0{wv}d}'
            for c in cha:
                n = c
                if isinstance(c, int):
                    fmt = ' {tc}{c:0{wc}d}'
                elif isinstance(c, float):
                    fmt = ' {tc}{c:0{wf}.1f}'
                else:
                    fmt = ' {c}'
                    n = extra
                fmt = '{}' + v_block + fmt

                old_d['v'] = v
                old_d['c'] = c
                new_d['v'] = v
                new_d['c'] = n

                old = fmt.format(self.labels[2], **old_d)
                new = fmt.format(name, **new_d)
                nested.append(tankobon.Transform(old, new))

            if v is None:
                old = self.labels[1]
                new = name
            else:
                old = '{} {tv[0]}{:02d}'.format(self.labels[1], v, **old_d)
                new = '{} {tv[0]}{:0{wv}d}'.format(name, v, **new_d)
            res.append(tankobon.Transform(old, new, nested=nested))
        if self.labels[0] is None:
            return res[0]
        else:
            return tankobon.Transform(self.labels[0], None, res)

    @classmethod
    def generate(cls, mode):
        """
        Create a default reference
        Args:
            mode: one of 'nominal', 'num1'

        Returns:
            The new Reference
        """

        values = cls._Layout[mode]

        return cls(**values)
