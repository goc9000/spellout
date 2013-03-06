# structures/tree/PlaceholderNode.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

from structures.tree.TreeNode import TreeNode


class PlaceholderNode(TreeNode):
    def __init__(self, left=None, right=None):
        TreeNode.__init__(self, left, right)
    
    def clone(self):
        return PlaceholderNode()._on_cloned_from(self)
    
    def own_signature(self):
        return '...'
    
    def name(self):
        return '...'
    
    def _fill_json_obj(self, obj, nodes_to_ids):
        obj['type'] = 'PlaceholderNode'

    @staticmethod
    def _from_json_obj(obj):
        if obj['type'] != 'PlaceholderNode':
            raise RuntimeError("Expected type=PlaceholderNode in JSON object")

        return PlaceholderNode()
