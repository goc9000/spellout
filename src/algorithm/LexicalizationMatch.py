#!/usr/bin/python

# algorithm/LexicalizationMatch.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3


class LexicalizationMatch():
    lexicon_entry = None
    extras = None
    moved = None

    def __init__(self, lexicon_entry, extras, moved=None):
        self.lexicon_entry = lexicon_entry
        self.extras = extras
        self.moved = moved

    def description(self):
        text = self.lexicon_entry.name

        if self.moved is None:
            if self.extras > 0:
                text += " ({0} extras)".format(self.extras)
        else:
            text += u' (moving {0}'.format(self.moved.name())
            if self.extras > 0:
                text += ", {0} extras".format(self.extras)
            text += ')'

        return text
