# structures/tree/PhrasalNode.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

from structures.tree.TreeNode import TreeNode


class PhrasalNode(TreeNode):
    feature = None
    degree = None
    
    def __init__(self, feature, degree, left=None, right=None):
        TreeNode.__init__(self, left, right)
        self.feature = feature
        self.degree = degree

    def clone(self):
        return PhrasalNode(self.feature, self.degree)._on_cloned_from(self)

    def own_signature(self):
        return "{0}P".format(self.feature)

    def name(self):
        if self.degree == 0:
            return "{0}P".format(self.feature)
        else:
            return "{0}P{1}".format(self.feature, self.degree)

    def _fill_json_obj(self, obj, nodes_to_ids):
        obj['type'] = 'PhrasalNode'
        obj['feature'] = self.feature
        obj['degree'] = self.degree

    @staticmethod
    def _from_json_obj(obj):
        if obj['type'] != 'PhrasalNode':
            raise RuntimeError("Expected type=PhrasalNode in JSON object")

        return PhrasalNode(obj['feature'], int(obj['degree']))
