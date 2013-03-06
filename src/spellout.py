#!/usr/bin/python

# spellout.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

import sys

from app.SpelloutApp import SpelloutApp
from gui.Gui import Gui


def main():
    try:
        app = SpelloutApp()
        if len(sys.argv) > 1:
            app.load_session(sys.argv[1])

        gui = Gui(app)
        gui.run_blocking()
    except RuntimeError as e:
        sys.stderr.write(unicode(e) + '\n')


if __name__ == "__main__":
    main()
