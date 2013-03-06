# gui/MainWindow.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
#
# This file is part of spellout.
#
# Licensed under the GPL-3

from PyQt4 import QtGui
from PyQt4.QtCore import QObject, SIGNAL
from PyQt4.QtGui import QMainWindow, QFileDialog, QStyle, QListWidgetItem

from algorithm.Setup import Setup
from algorithm.SpelloutAlgorithm import MSG_NOTE, MSG_ERROR, MSG_WARNING
from graphics.AlgorithmTreeRenderer import AlgorithmTreeRenderer

from gui.widgets.WindowUtils import WindowUtils
from gui.templates.Ui_MainWindow import Ui_MainWindow


class MainWindow(QMainWindow, Ui_MainWindow, WindowUtils):
    _gui = None
    _app = None

    def __init__(self, gui, app):
        QMainWindow.__init__(self)

        self._gui = gui
        self._app = app
        self._init_ui()
        self.center_on_screen()

    def _init_ui(self):
        self.setupUi(self)
        self._setup_icons_using_property()

        self.advanced_box.setVisible(self.advanced_button.isChecked())

        self._update_all_from_session()

    def setup(self, setup):
        self.initial_node_editor.set_node(setup.initial_node)
        self.external_merges_editor.set_nodes(setup.external_merges)
        self.lexicon_table.set_lexicon(setup.lexicon)

    def get_setup(self):
        setup = Setup()
        setup.initial_node = self.initial_node_editor.get_node()
        setup.external_merges = self.external_merges_editor.get_nodes()
        setup.lexicon = self.lexicon_table.get_lexicon()

        return setup

    def _commit_setup(self):
        try:
            self._app.session.setup = self.get_setup()
            return True
        except Exception as e:
            self._show_error_messagebox(e)
            return False

    def _update_all_from_session(self):
        self.setup(self._app.session.setup)
        self._update_title()
        self._update_algorithm_status()

    def _update_title(self):
        self.setWindowTitle("Spellout - [{0}]".format(self._app.session.name()))

    def _update_algorithm_status(self):
        scene = AlgorithmTreeRenderer(self._app.session.algorithm).get_tree_scene()
        self.tree_display.setScene(scene)

        self.log_listview.clear()
        for severity, text in self._app.session.algorithm.log():
            item = QListWidgetItem(self._get_icon_for_severity(severity), text)
            self.log_listview.addItem(item)
        self.log_listview.scrollToBottom()

        self._update_controls()

    def _get_icon_for_severity(self, severity):
        ICON = QtGui.qApp.style().standardIcon

        if severity == MSG_NOTE:
            return ICON(QStyle.SP_MessageBoxInformation)
        elif severity == MSG_WARNING:
            return ICON(QStyle.SP_MessageBoxWarning)
        elif severity == MSG_ERROR:
            return ICON(QStyle.SP_MessageBoxCritical)
        else:
            return ICON(QStyle.SP_MessageBoxInformation)

    def _update_controls(self):
        self._update_alternatives()

        self.forward_button.setEnabled(self._app.can_go_forward())
        self.forward_action.setEnabled(self._app.can_go_forward())
        self.back_button.setEnabled(self._app.can_go_back())
        self.back_action.setEnabled(self._app.can_go_back())
        self.go_to_end_button.setEnabled(self._app.can_go_to_end())
        self.go_to_end_action.setEnabled(self._app.can_go_to_end())
        self.next_possibility_button.setEnabled(self._app.has_next_possibility())
        self.next_possibility_action.setEnabled(self._app.has_next_possibility())

    def _update_alternatives(self):
        self.alternatives_combo.clear()
        self.alternatives_combo.addItem('Choose alternative...', None)
        self.alternatives_menu.clear()

        alternatives = self._app.session.algorithm.alternatives()

        self.alternatives_combo.setEnabled(len(alternatives) > 1)
        self.alternatives_menu.setEnabled(len(alternatives) > 1)

        if len(alternatives) > 1:
            for i, alt in enumerate(alternatives):
                text, value = alt

                self.alternatives_combo.addItem(text, value)

                action = self.alternatives_menu.addAction("&{0}. {1}".format(i + 1, text))
                QObject.connect(action, SIGNAL("activated()"), lambda: self._on_clicked_alternative(value))

    def _on_alternative_selected_in_combo(self, index):
        if index <= 0:
            return

        value = self.alternatives_combo.itemData(index)
        if value is not None:
            value = value.toPyObject()

        self._on_clicked_alternative(value)

    def _on_clicked_open(self):
        filename = unicode(QFileDialog.getOpenFileName(self, "Open Session",
                                                       filter="Sessions [*.json] (*.json)"))
        if filename == '':
            return

        try:
            self._app.load_session(filename)
            self._update_all_from_session()
        except Exception as e:
            self._show_error_messagebox(u"Error loading session:\n{0}".format(unicode(e)))

    def _on_clicked_save(self):
        self._on_clicked_save_function(False)

    def _on_clicked_save_as(self):
        self._on_clicked_save_function(True)

    def _on_clicked_save_function(self, save_as):
        if not self._commit_setup():
            return

        if save_as or (self._app.session.filename is None):
            filename = unicode(QFileDialog.getSaveFileName(
                self, "Save Session", self._app.session.name() + ".json", "Sessions [*.json] (*.json)"))
            if filename == '':
                return
        else:
            filename = None

        try:
            self._app.save_session(filename)
            self._update_title()
        except Exception as e:
            import sys
            import traceback

            traceback.print_exc(file=sys.stderr)
            self._show_error_messagebox(u"Error saving session:\n{0}".format(unicode(e)))

    def _on_toggled_advanced(self, active):
        self.advanced_box.setVisible(active)

    def _on_toggled_only_successful(self, active):
        for item in [self.only_successful_action, self.only_successful_checkbox]:
            if item.isChecked() != active:
                item.setChecked(active)

    def _on_clicked_full_run(self):
        self._do_algorithm_action(lambda: self._app.do_full_run(self.only_successful_checkbox.isChecked()))

    def _on_clicked_next_possibility(self):
        if not self._do_algorithm_action(lambda: self._app.next_possibility(self.only_successful_checkbox.isChecked())):
            self._show_info_messagebox("There are no more possibilities")

    def _on_clicked_restart(self):
        self._do_algorithm_action(lambda: self._app.restart_algorithm())

    def _on_clicked_back(self):
        self._do_algorithm_action(lambda: self._app.go_back())

    def _on_clicked_forward(self):
        self._do_algorithm_action(lambda: self._app.go_forward())

    def _on_clicked_alternative(self, value):
        self._do_algorithm_action(lambda: self._app.go_forward(value))

    def _on_clicked_go_to_end(self):
        self._do_algorithm_action(lambda: self._app.go_to_end())

    def _do_algorithm_action(self, action):
        try:
            self._commit_setup()
            result = action()
            self._update_algorithm_status()

            return result
        except Exception as e:
            self._show_error_messagebox(u"Error running algorithm:\n{0}".format(unicode(e)))

            return e
