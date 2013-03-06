# structures/tree/FeatureNode.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

from structures.tree.TreeNode import TreeNode


class FeatureNode(TreeNode):
    feature = None
    
    def __init__(self, feature, left=None, right=None):
        TreeNode.__init__(self, left, right)
        self.feature = feature
    
    def clone(self):
        return FeatureNode(self.feature)._on_cloned_from(self)
    
    def own_signature(self):
        return self.feature
    
    def name(self):
        return self.feature

    def _fill_json_obj(self, obj, nodes_to_ids):
        obj['type'] = 'FeatureNode'
        obj['feature'] = self.feature
    
    @staticmethod
    def _from_json_obj(obj):
        if obj['type'] != 'FeatureNode':
            raise RuntimeError("Expected type=FeatureNode in JSON object")

        return FeatureNode(obj['feature'])
