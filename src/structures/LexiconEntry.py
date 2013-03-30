# structures/LexiconEntry.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
#
# This file is part of spellout.
#
# Licensed under the GPL-3

from structures.tree.Tree import Tree


class LexiconEntry:
    name = None
    phonological_content = None
    conceptual_content = None
    tree = None

    def __init__(self, name=None, phonological_content=None, conceptual_content=None, tree=None):
        self.name = name
        self.phonological_content = phonological_content
        self.conceptual_content = list(conceptual_content) if conceptual_content is not None else []
        self.tree = tree

    def clone(self):
        return LexiconEntry(self.name, self.phonological_content, self.conceptual_content,
                            self.tree.clone() if self.tree is not None else None)

    def is_complete(self):
        return self.name is not None and self.tree is not None

    def to_json_obj(self):
        obj = {'name': self.name,
               'phonological_content': self.phonological_content,
               'conceptual_content': list(self.conceptual_content),
               'tree': self.tree.to_json_obj()}

        return obj

    @staticmethod
    def from_json_obj(obj):
        return LexiconEntry(obj['name'], obj['phonological_content'], obj['conceptual_content'],
                            Tree.from_json_obj(obj['tree']))
