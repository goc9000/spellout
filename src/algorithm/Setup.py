# algorithm/Setup.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
#
# This file is part of spellout.
#
# Licensed under the GPL-3

from structures.tree.FeatureNode import FeatureNode
from structures.tree.TreeNode import TreeNode
from structures.LexiconEntry import LexiconEntry


class Setup:
    initial_node = None
    external_merges = None
    lexicon = None

    def __init__(self):
        self.external_merges = []
        self.lexicon = []

    def clone(self):
        dupe = Setup()
        dupe.initial_node = self.initial_node.clone() if self.initial_node is not None else None
        dupe.external_merges = [item.clone() for item in self.external_merges]
        dupe.lexicon = [item.clone() for item in self.lexicon]

        return dupe

    def check(self):
        if self.initial_node is None:
            raise RuntimeError("You must provide an initial node for the algorithm to start")

        if not isinstance(self.initial_node, FeatureNode):
            raise RuntimeError("Initial node must be a feature node")

        if len(self.external_merges) == 0:
            raise RuntimeError("You must specify at least one node to externally merge")

        if not all([isinstance(node, FeatureNode) for node in self.external_merges]):
            raise RuntimeError("Only feature nodes may be externally merged")

        if len(self.lexicon) == 0:
            raise RuntimeError("The lexicon is empty")

    def to_json_obj(self):
        obj = {
            'initial_node': self.initial_node.to_json_obj() if self.initial_node is not None else None,
            'external_merges': [item.to_json_obj() for item in self.external_merges],
            'lexicon': [item.to_json_obj() for item in self.lexicon]
        }

        return obj

    @staticmethod
    def from_json_obj(data):
        setup = Setup()
        setup.initial_node = TreeNode.from_json_obj(data['initial_node'])
        setup.external_merges = [TreeNode.from_json_obj(obj) for obj in data['external_merges']]
        setup.lexicon = [LexiconEntry.from_json_obj(obj) for obj in data['lexicon']]

        return setup
