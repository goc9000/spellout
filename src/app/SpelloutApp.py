#!/usr/bin/python

# app/SpelloutApp.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

import json

from structures.Session import Session


class SpelloutApp():
    session = None

    def __init__(self):
        self.session = Session()

    def load_session(self, filename):
        with open(filename, "r") as f:
            obj = json.load(f)

        self.session = Session.from_json_obj(obj)
        self.session.filename = filename

    def save_session(self, filename=None):
        if filename is None:
            if self.session.filename is None:
                raise RuntimeError("No filename specified for saving session")
            filename = self.session.filename

        with open(filename, "wt+") as f:
            json.dump(self.session.to_json_obj(), f, indent=4)

        self.session.filename = filename

    def can_go_forward(self):
        return (not self.session.algorithm.started()) or self.session.algorithm.can_go_forward()

    def go_forward(self, alternative=None):
        if self.session.algorithm.started():
            self.session.algorithm.go_forward(alternative)
        else:
            self.restart_algorithm()

    def can_go_back(self):
        return self.session.algorithm.can_go_back()

    def go_back(self):
        self.session.algorithm.go_back()

    def can_go_to_end(self):
        return self.can_go_forward()

    def go_to_end(self):
        while self.can_go_forward():
            self.go_forward(None)

    def do_full_run(self, only_successful=False):
        self.restart_algorithm()
        self.go_to_end()

        while only_successful and not self.session.algorithm.success():
            self.next_possibility(True)

        return True

    def has_next_possibility(self):
        return self.session.algorithm.last_choice() is not None

    def has_last_choice(self):
        return self.session.algorithm.last_choice() is not None

    def next_possibility(self, only_successful=False):
        while True:
            last_choice = self.session.algorithm.last_choice()
            if not self.go_to_last_choice():
                return False

            n_choices = len(self.session.algorithm.alternatives())
            if last_choice == n_choices - 1:
                continue

            self.go_forward(last_choice + 1)
            self.go_to_end()

            if only_successful and not self.session.algorithm.success():
                continue

            return True

    def go_to_last_choice(self):
        if not self.has_last_choice():
            return False

        self.go_back()
        while not self.session.algorithm.in_choice_state():
            self.go_back()

        return True

    def restart_algorithm(self):
        self.session.algorithm.start(self.session.setup['initial_node'],
                                     self.session.setup['external_merges'],
                                     self.session.setup['lexicon'])
