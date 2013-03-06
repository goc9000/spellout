# structures/Session.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

import os

from algorithm.SpelloutAlgorithm import SpelloutAlgorithm
from structures.tree.TreeNode import TreeNode
from structures.LexiconEntry import LexiconEntry


class Session:
    filename = None

    setup = None
    algorithm = None

    def __init__(self):
        self.setup = {
            'initial_node': None,
            'external_merges': [],
            'lexicon': []
        }
        self.algorithm = SpelloutAlgorithm()

    def name(self):
        if self.filename is None:
            return 'untitled'

        _, filename = os.path.split(self.filename)
        name, _ = os.path.splitext(filename)

        return name

    def to_json_obj(self):
        obj = {
            'initial_node': self.setup['initial_node'].to_json_obj() if self.setup['initial_node'] is not None
            else None,
            'external_merges': [item.to_json_obj() for item in self.setup['external_merges']],
            'lexicon': [item.to_json_obj() for item in self.setup['lexicon']],
            'algorithm': self.algorithm.to_json_obj()
        }

        return obj

    @staticmethod
    def from_json_obj(data):
        session = Session()

        session.setup = {
            'initial_node': TreeNode.from_json_obj(data['initial_node']),
            'external_merges': [TreeNode.from_json_obj(obj) for obj in data['external_merges']],
            'lexicon': [LexiconEntry.from_json_obj(obj) for obj in data['lexicon']]
        }
        session.algorithm = SpelloutAlgorithm.from_json_obj(data['algorithm'])

        return session
