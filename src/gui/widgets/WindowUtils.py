# gui/widgets/WindowUtils.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

import inspect

from PyQt4 import QtGui
from PyQt4.QtCore import QObject
from PyQt4.QtGui import QDesktopWidget, QMessageBox, QStyle


class WindowUtils():
    def __init__(self):
        pass

    def center_on_screen(self):
        desktop = QDesktopWidget().screenGeometry()
        self.move((desktop.width() / 2) - (self.frameSize().width() / 2),
                  (desktop.height() / 2) - (self.frameSize().height() / 2))

    def _show_error_messagebox(self, error, title='Error'):
        QMessageBox.critical(self, title, unicode(error))

    def _show_info_messagebox(self, message, title='Note'):
        QMessageBox.information(self, title, unicode(message))

    def _setup_icons_using_property(self):
        for name, item in inspect.getmembers(self, lambda x: not callable(x)):
            if isinstance(item, QObject):
                icon_name = item.property('standardIcon').toPyObject()
                if icon_name is not None and hasattr(QStyle, str(icon_name)):
                    icon = QtGui.qApp.style().standardIcon(getattr(QStyle, str(icon_name)))
                    item.setIcon(icon)

    def do_icon_test(self):
        ICONS = [
            'SP_ArrowBack',
            'SP_ArrowDown',
            'SP_ArrowForward',
            'SP_ArrowLeft',
            'SP_ArrowRight',
            'SP_ArrowUp',
            'SP_BrowserReload',
            'SP_BrowserStop',
            'SP_CommandLink',
            'SP_ComputerIcon',
            'SP_DesktopIcon',
            'SP_DialogApplyButton',
            'SP_DialogCancelButton',
            'SP_DialogCloseButton',
            'SP_DialogDiscardButton',
            'SP_DialogHelpButton',
            'SP_DialogNoButton',
            'SP_DialogOkButton',
            'SP_DialogOpenButton',
            'SP_DialogResetButton',
            'SP_DialogSaveButton',
            'SP_DialogYesButton',
            'SP_DirClosedIcon',
            'SP_DirHomeIcon',
            'SP_DirIcon',
            'SP_DirLinkIcon',
            'SP_DirOpenIcon',
            'SP_DockWidgetCloseButton',
            'SP_DriveCDIcon',
            'SP_DriveDVDIcon',
            'SP_DriveFDIcon',
            'SP_DriveHDIcon',
            'SP_DriveNetIcon',
            'SP_FileDialogBack',
            'SP_FileDialogContentsView',
            'SP_FileDialogDetailedView',
            'SP_FileDialogEnd',
            'SP_FileDialogInfoView',
            'SP_FileDialogListView',
            'SP_FileDialogNewFolder',
            'SP_FileDialogStart',
            'SP_FileDialogToParent',
            'SP_FileIcon',
            'SP_FileLinkIcon',
            'SP_MediaPause',
            'SP_MediaPlay',
            'SP_MediaSeekBackward',
            'SP_MediaSeekForward',
            'SP_MediaSkipBackward',
            'SP_MediaSkipForward',
            'SP_MediaStop',
            'SP_MediaVolume',
            'SP_MediaVolumeMuted',
            'SP_MessageBoxCritical',
            'SP_MessageBoxInformation',
            'SP_MessageBoxQuestion',
            'SP_MessageBoxWarning',
            'SP_TitleBarCloseButton',
            'SP_TitleBarContextHelpButton',
            'SP_TitleBarMaxButton',
            'SP_TitleBarMenuButton',
            'SP_TitleBarMinButton',
            'SP_TitleBarNormalButton',
            'SP_TitleBarShadeButton',
            'SP_TitleBarUnshadeButton',
            'SP_ToolBarHorizontalExtensionButton',
            'SP_ToolBarVerticalExtensionButton',
            'SP_TrashIcon',
            'SP_VistaShield'
        ]

        ICON = QtGui.qApp.style().standardIcon

        menu = self.menuBar().addMenu('Icon Test')
        for icon in ICONS:
            entry = menu.addAction(icon)
            entry.setIcon(ICON(eval('QStyle.{0}'.format(icon))))
            menu.addAction(entry)
