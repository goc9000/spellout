# gui/widgets/LexiconTable.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
#
# This file is part of spellout.
#
# Licensed under the GPL-3

from PyQt4.Qt import Qt, QModelIndex, SIGNAL
from PyQt4.QtGui import QTableView, QItemDelegate, QHeaderView
from PyQt4.QtCore import QAbstractTableModel, QVariant, pyqtSignal

from gui.TreeEditor import TreeEditor

from graphics.TreeRenderer import TreeRenderer

from structures.LexiconEntry import LexiconEntry


COL_NAME, COL_PHONO, COL_CONCEPT, COL_TREE = range(4)
COLUMN_NAMES = ['Name', 'Phono', 'Concept', 'Tree']
COLUMN_WIDTHS = [56, 56, 64]


class LexiconTable(QTableView):
    changed = pyqtSignal()

    def __init__(self, parent):
        QTableView.__init__(self, parent)

        model = LexiconTableModel(self)
        self.setModel(model)

        item_delegate = LexiconTableItemDelegate(self)
        self.setItemDelegate(item_delegate)

        for col, width in enumerate(COLUMN_WIDTHS):
            self.setColumnWidth(col, width)
        self.horizontalHeader().setStretchLastSection(True)

        self.verticalHeader().setVisible(False)
        self.verticalHeader().setResizeMode(QHeaderView.ResizeToContents)

        self.connect(model, SIGNAL("dataChanged(QModelIndex,QModelIndex)"), self._on_change)
        self.connect(model, SIGNAL("modelReset()"), self._on_change)
        self.connect(model, SIGNAL("rowsInserted(QModelIndex,int,int)"), self._on_change)
        self.connect(model, SIGNAL("rowsRemoved(QModelIndex,int,int)"), self._on_change)
        self.connect(model, SIGNAL("rowsMoved(QModelIndex,int,int,QModelIndex,int)"), self._on_change)

        self.setSelectionBehavior(self.SelectRows)

    def set_lexicon(self, lexicon):
        self.model().set_lexicon(lexicon)

    def get_lexicon(self):
        return self.model().get_lexicon()

    def valid_commands(self):
        row = self.currentIndex().row()
        count = self.model().rowCount(0)

        commands = {
            'delete': 0 <= row < count - 1,
            'clear': row == count - 1,
            'move_up': row > 0 and row != count - 1,
            'move_down': 0 <= row < count - 2
        }

        return commands

    def delete_current_item(self):
        self.model().delete_item(self.currentIndex().row())

    def clear_new_row(self):
        self.model().clear_new_row()

    def move_current_item_up(self):
        self.model().move_item(self.currentIndex().row(), self.currentIndex().row() - 1)

    def move_current_item_down(self):
        self.model().move_item(self.currentIndex().row(), self.currentIndex().row() + 1)

    def _on_change(self):
        self.changed.emit()


class LexiconTableItemDelegate(QItemDelegate):
    def __init__(self, parent=None):
        QItemDelegate.__init__(self, parent)

    def createEditor(self, parent, option, index):
        if index.column() == COL_TREE:
            editor = TreeEditor(self.parent())

            return editor

        editor = QItemDelegate.createEditor(self, parent, option, index)
        editor.setAlignment(Qt.AlignHCenter | Qt.AlignTop)

        return editor

    def setEditorData(self, editor, index):
        if index.column() == COL_TREE:
            tree = index.model().data(index, Qt.EditRole).toPyObject()
            editor.set_tree(tree)
            return

        return QItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        if index.column() == COL_TREE:
            if editor.was_accepted:
                model.setData(index, QVariant(editor.get_tree()), Qt.EditRole)
            return

        return QItemDelegate.setModelData(self, editor, model, index)

    def updateEditorGeometry(self, editor, option, index):
        if index.column() == COL_TREE:
            abs_table_pos = self.parent().mapToGlobal(self.parent().pos())
            editor.move(abs_table_pos.x() + option.rect.x(), abs_table_pos.y() + option.rect.y())
            return

        return QItemDelegate.updateEditorGeometry(self, editor, option, index)

    def sizeHint(self, option, index):
        if index.column() == COL_TREE:
            return index.data(Qt.DecorationRole).toPyObject().size()
        else:
            return QItemDelegate.sizeHint(self, option, index)


class LexiconTableModel(QAbstractTableModel):
    _parent = None
    _lexicon = None
    _new_entry = None
    _tree_pic_cache = None

    def __init__(self, parent):
        QAbstractTableModel.__init__(self, parent)
        self._lexicon = []
        self._new_entry = LexiconEntry(None, None, None, None)
        self._parent = parent
        self._refresh_tree_pic_cache()

    def set_lexicon(self, lexicon):
        self.beginResetModel()
        self._lexicon = [entry.clone() for entry in lexicon]
        self._new_entry = LexiconEntry(None, None, None, None)
        self._refresh_tree_pic_cache()
        self.endResetModel()

    def get_lexicon(self):
        return [entry.clone() for entry in self._lexicon]

    def clear_new_row(self):
        self._new_entry = LexiconEntry(None, None, None, None)
        self._refresh_tree_pic_cache()
        self.dataChanged.emit(self.createIndex(self.rowCount(0) - 1, 0),
                              self.createIndex(self.rowCount(0), self.columnCount(0)))

    def delete_item(self, row):
        self.beginRemoveRows(QModelIndex(), row, row)
        self._lexicon.pop(row)
        self._tree_pic_cache.pop(row)
        self.endRemoveRows()

    def move_item(self, from_row, to_row):
        if to_row == from_row:
            return

        # Note: we can't use begin/endMoveRows due to a severe bug in PyQt
        self.beginRemoveRows(QModelIndex(), from_row, from_row)
        item = self._lexicon.pop(from_row)
        image = self._tree_pic_cache.pop(from_row)
        self.endRemoveRows()
        self.beginInsertRows(QModelIndex(), to_row, to_row)
        self._lexicon.insert(to_row, item)
        self._tree_pic_cache.insert(to_row, image)
        self.endInsertRows()
        self._parent.setCurrentIndex(self.createIndex(to_row, 0))

    def rowCount(self, parent):
        return len(self._lexicon) + 1

    def columnCount(self, parent):
        return len(COLUMN_NAMES)

    def flags(self, index):
        return Qt.ItemIsEnabled | Qt.ItemIsEditable

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        entry = self.entry_at_row(index.row())

        if role == Qt.DisplayRole or role == Qt.EditRole:
            if index.column() == COL_NAME:
                return QVariant(entry.name)
            if index.column() == COL_PHONO:
                if role == Qt.DisplayRole:
                    if entry.phonological_content is not None:
                        return QVariant('/' + entry.phonological_content + '/')
                else:
                    return QVariant(entry.phonological_content)
            if index.column() == COL_CONCEPT:
                return QVariant(entry.conceptual_content)
            if index.column() == COL_TREE and role == Qt.EditRole:
                return QVariant(entry.tree)
        elif role == Qt.TextAlignmentRole:
            return Qt.AlignHCenter
        elif role == Qt.DecorationRole:
            if index.column() == COL_TREE:
                return QVariant(self._tree_pic_cache[index.row()])

        return QVariant()

    def setData(self, index, value_variant, role):
        if not index.isValid() or role != Qt.EditRole:
            return False

        entry = self.entry_at_row(index.row())
        value = value_variant.toPyObject()

        if index.column() == COL_NAME:
            if value == '' and entry != self._new_entry:
                return False
            entry.name = unicode(value) if value != '' else None
        elif index.column() == COL_PHONO:
            entry.phonological_content = unicode(value) if value != '' else None
        elif index.column() == COL_CONCEPT:
            entry.conceptual_content = unicode(value) if value != '' else None
        elif index.column() == COL_TREE:
            entry.tree = value
            self._refresh_tree_pic_cache(index.row())
        else:
            return False

        self.dataChanged.emit(index, index)

        self._commit_new_entry()

        return True

    def headerData(self, col, orientation, role):
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return QVariant(COLUMN_NAMES[col])
        else:
            return QVariant()

    def entry_at_row(self, row):
        return self._lexicon[row] if row < len(self._lexicon) else self._new_entry

    def _refresh_tree_pic_cache(self, row=None):
        if row is None:
            self._tree_pic_cache = [TreeRenderer(self.entry_at_row(row).tree).get_tree_image()
                                    for row in xrange(len(self._lexicon) + 1)]
        else:
            self._tree_pic_cache[row] = TreeRenderer(self.entry_at_row(row).tree).get_tree_image()

    def _commit_new_entry(self):
        if not self._new_entry.is_complete():
            return

        self.beginInsertRows(QModelIndex(), len(self._lexicon), len(self._lexicon))
        self._lexicon.append(self._new_entry)
        self._new_entry = LexiconEntry(None, None, None, None)
        self._tree_pic_cache.append(TreeRenderer(None).get_tree_image())
        self.endInsertRows()
