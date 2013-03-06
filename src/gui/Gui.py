# gui/Gui.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

import sys

from PyQt4.QtGui import QApplication

from gui.MainWindow import MainWindow


class Gui():
    main_window = None

    _app = None
    _qapp = None

    def __init__(self, app):
        self._app = app
        self._qapp = QApplication(sys.argv)
        self.main_window = MainWindow(self, app)

    def run_blocking(self):
        self.main_window.show()
        self._qapp.exec_()
        self._qapp.deleteLater()
