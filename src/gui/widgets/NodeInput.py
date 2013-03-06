# gui/widgets/NodeInput.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

import re

from PyQt4.QtGui import QLineEdit

from structures.tree.TreeNode import TreeNode


class NodeInput(QLineEdit):
    def __init__(self, *args):
        QLineEdit.__init__(self, *args)

    def get_node(self):
        text = unicode(self.text()).strip()
        if text == '':
            return None

        node = TreeNode.from_name(text)
        if node is None:
            raise RuntimeError("'{0}' does not represent a valid node".format(text))

        return node

    def get_nodes(self):
        text = unicode(self.text())
        text = re.sub(r'[ \t,;]+', ' ', text).strip()
        if text == '':
            return []

        nodes = []
        for node_text in text.split(' '):
            node = TreeNode.from_name(node_text)
            if node is None:
                raise RuntimeError("'{0}' does not represent a valid node".format(node_text))

            nodes.append(node)

        return nodes

    def set_node(self, node):
        self.setText(node.name() if node is not None else '')

    def set_nodes(self, nodes):
        self.setText(' '.join((node.name() for node in nodes)))
