# structures/Session.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
#
# This file is part of spellout.
#
# Licensed under the GPL-3

import os

from algorithm.Setup import Setup
from algorithm.SpelloutAlgorithm import SpelloutAlgorithm


class Session:
    filename = None

    setup = None
    algorithm = None

    def __init__(self):
        self.setup = Setup()
        self.algorithm = SpelloutAlgorithm()

    def name(self):
        if self.filename is None:
            return 'untitled'

        _, filename = os.path.split(self.filename)
        name, _ = os.path.splitext(filename)

        return name

    def to_json_obj(self):
        obj = {
            'setup': self.setup.to_json_obj(),
            'algorithm': self.algorithm.to_json_obj()
        }

        return obj

    @staticmethod
    def from_json_obj(data):
        session = Session()
        session.setup = Setup.from_json_obj(data['setup'])
        session.algorithm = SpelloutAlgorithm.from_json_obj(data['algorithm'])

        return session
