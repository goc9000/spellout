# gui/TreeEditor.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

from PyQt4.Qt import QGraphicsItem, SIGNAL
from PyQt4.QtGui import QDialog

from gui.widgets.WindowUtils import WindowUtils
from gui.templates.Ui_TreeEditor import Ui_TreeEditor

from graphics.TreeRenderer import TreeRenderer

from structures.tree.Tree import Tree
from structures.tree.PlaceholderNode import PlaceholderNode


class TreeEditor(QDialog, Ui_TreeEditor, WindowUtils):
    was_accepted = False
    
    _tree = None
    _selected_node = None
    _disable_panel_update = False
    
    def __init__(self, parent):
        QDialog.__init__(self, parent)

        self.initUi()
        self.set_tree(None)
    
    def initUi(self):
        self.setupUi(self)
        self._setup_icons_using_property()

    def get_tree(self):
        return self._tree.clone() if self._tree is not None else None

    def set_tree(self, tree):
        tree = tree.clone() if tree is not None else Tree(PlaceholderNode())
        
        self._tree = tree
        self._selected_node = tree.root
    
        self._update_tree_display()
    
    def show(self):
        self.was_accepted = False
        QDialog.show(self)
    
    def accept(self):
        try:
            self._tree.check()
        except RuntimeError as e:
            self._show_error_messagebox(e)
            return
        
        self.was_accepted = True
        QDialog.accept(self)
    
    def _update_tree_display(self):
        select_node = self._selected_node

        scene = TreeRenderer(self._tree, scale=2).get_tree_scene()
        self.tree_display.setScene(scene)
        
        self.connect(scene, SIGNAL('selectionChanged()'), self._on_node_selected)
        
        for item in scene.items():
            if item.data(0).toPyObject() == 'node':
                item.setFlags(QGraphicsItem.ItemIsSelectable)
                if item.data(1).toPyObject() == select_node:
                    item.setSelected(True)
    
    def _on_node_selected(self):
        node = None
        for item in self.tree_display.scene().selectedItems():
            node = item.data(1).toPyObject()
        
        self._selected_node = node
        
        if not self._disable_panel_update:
            self.current_editor.set_node(node if not isinstance(node, PlaceholderNode) else None)

            self.current_label.setEnabled(node is not None)
            self.current_editor.setEnabled(node is not None)
            self.add_left_button.setEnabled(node is not None and node.left is None)
            self.add_right_button.setEnabled(node is not None and node.right is None)
            self.delete_current_button.setEnabled(node is not None)
        
    def _on_clicked_add_left(self):
        new_node = PlaceholderNode()
        self._selected_node.set_child(0, new_node)
        self._selected_node = new_node
        self._update_tree_display()
    
    def _on_clicked_add_right(self):
        new_node = PlaceholderNode()
        self._selected_node.set_child(1, new_node)
        self._selected_node = new_node
        self._update_tree_display()
    
    def _on_clicked_delete_current(self):
        parent, side = self._tree.locate_node(self._selected_node)
    
        if parent is not None:
            parent.set_child(side, None)
            self._selected_node = parent
        else:
            self._tree.root = PlaceholderNode()
            self._selected_node = self._tree.root
        
        self._update_tree_display()

    def _on_edited_current(self, _):
        try:
            new_node = self.current_editor.get_node()
        except RuntimeError:
            return

        if new_node is None:
            new_node = PlaceholderNode()

        new_node.left = self._selected_node.left
        new_node.right = self._selected_node.right

        parent, side = self._tree.locate_node(self._selected_node)
        
        if parent is not None:
            parent.set_child(side, new_node)
        else:
            self._tree.root = new_node
        
        self._selected_node = new_node
    
        self._disable_panel_update = True
        self._update_tree_display()
        self._disable_panel_update = False
    