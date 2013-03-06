# algorithm/SpelloutAlgorithm.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
#
# This file is part of spellout.
#
# Licensed under the GPL-3

import copy

from algorithm.Setup import Setup
from structures.tree.Tree import Tree
from structures.tree.TreeNode import TreeNode
from structures.tree.PhrasalNode import PhrasalNode
from structures.tree.TraceNode import TraceNode
from structures.LexiconEntry import LexiconEntry
from algorithm.LexicalizationMatch import LexicalizationMatch


MSG_NOTE = 'i'
MSG_WARNING = '!'
MSG_ERROR = 'E'

HIGHLIGHT_DESTINATION = '>'
HIGHLIGHT_SOURCE = '<'
HIGHLIGHT_POINT = '*'


class SpelloutAlgorithm():
    _setup = None

    _state = None
    _external_merge_round = 0

    _tree = None
    _log = None
    _highlighted_nodes = None
    _lexicalizations = None
    _pending_moves = None
    _last_choice = None

    _undo_info = None

    _tree_clone = None
    _node_clones = None

    def __init__(self):
        self._state = self._state_not_started
        self._log = []
        self._highlighted_nodes = {}
        self._lexicalizations = {}
        self._pending_moves = {}
        self._undo_info = []

    def started(self):
        return self._state != self._state_not_started

    def tree(self):
        return self._tree_clone

    def highlighted_nodes(self):
        return dict((self._node_clones[node], highlight) for node, highlight in self._highlighted_nodes.items())

    def lexicalizations(self):
        return dict((self._node_clones[node], lexicon_entry) for node, lexicon_entry in self._lexicalizations.items())

    def pending_moves(self):
        return dict((self._node_clones[node], self._node_clones[destination])
                    for node, destination in self._pending_moves.items())

    def log(self):
        return [message for message in self._log]

    def alternatives(self):
        if self._state == self._state_list_matches:
            node = self._first_nonlexicalized_node()

            return [(match.description(), index) for index, match in enumerate(self._matches_for_node(node))]

        return [('Default', None)]

    def last_choice(self):
        return self._last_choice

    def in_choice_state(self):
        return self._state == self._state_list_matches and len(self.alternatives()) > 1

    def success(self):
        return self._state == self._state_success

    def start(self, setup):
        setup.check()
        self._setup = setup.clone()

        self._switch_state(self._state_just_started, {})

    def can_go_forward(self):
        return self._state not in [self._state_not_started, self._state_failure, self._state_success]

    def go_forward(self, alternative=None):
        if not self.can_go_forward():
            raise RuntimeError("The algorithm cannot go forward from this point")

        self._new_undo_point()
        next_state, state_entry_args = self._get_next_state(alternative)

        self._switch_state(next_state, state_entry_args)

    def can_go_back(self):
        return len(self._undo_info) > 0

    def go_back(self):
        actions = self._undo_info.pop()

        while len(actions) > 0:
            action, args = actions.pop()
            action(*args)

    def spellout(self):
        parts = []
        self._spellout_rec(self._tree.root, parts)

        return parts

    def to_json_obj(self):
        REF = self._references_to_json
        MAT = self._materialize_to_json

        obj = {
            'setup': self._setup.to_json_obj(),
            'state': REF(self._state),
            'external_merge_round': self._external_merge_round,
            'tree': MAT(self._tree),
            'log': MAT(self._log),
            'last_choice': self._last_choice,
            'highlights': REF(self._highlighted_nodes),
            'lexicalizations': REF(self._lexicalizations),
            'pending_moves': REF(self._pending_moves),
            'undo_info': REF(self._undo_info)
        }

        return obj

    @staticmethod
    def from_json_obj(data):
        algorithm = SpelloutAlgorithm()
        algorithm._load_from_json_obj(data)

        return algorithm

    def _get_state_name(self, state):
        return state.__name__[len('_state_'):] if state is not None else None

    def _get_next_state(self, alternative):
        next_state = None
        state_entry_args = {}

        if self._state == self._state_just_started:
            next_state = self._state_begin_merge_round
        elif self._state == self._state_begin_merge_round or self._state == self._state_moved_node:
            if self._any_to_move():
                next_state = self._state_announce_move
            elif not self._is_final_round():
                next_state = self._state_announce_external_merge
            elif self._any_to_lexicalize():
                next_state = self._state_announce_lexicalization
            else:
                next_state = self._state_lexicalization_done
        elif self._state == self._state_announce_move:
            next_state = self._state_moved_node
        elif self._state == self._state_announce_external_merge:
            next_state = self._state_merged_node
        elif self._state == self._state_merged_node or self._state == self._state_lexicalized_node:
            next_state = self._state_announce_lexicalization if self._any_to_lexicalize()\
                else self._state_lexicalization_done
        elif self._state == self._state_announce_lexicalization:
            next_state = self._state_list_matches
        elif self._state == self._state_list_matches:
            node = self._first_nonlexicalized_node()
            if len(self._matches_for_node(node)) == 0 and not self._children_are_lexicalized(node):
                state_entry_args['error_text'] = "Children are not lexicalized either, lexicalization failed"
                next_state = self._state_failure
            else:
                state_entry_args['alternative'] = alternative
                next_state = self._state_lexicalized_node
        elif self._state == self._state_lexicalization_done:
            next_state = self._state_end_merge_round
        elif self._state == self._state_end_merge_round:
            next_state = self._state_success if self._is_final_round() else self._state_begin_merge_round

        if next_state is None:
            next_state = self._state_failure
            state_entry_args['error_text'] = "Don't know how to proceed from this point"

        return next_state, state_entry_args

    def _state_not_started(self, **_):
        raise RuntimeError("This should never be executed")

    def _state_just_started(self, **_):
        self._tree = Tree(self._setup.initial_node)
        self._update_tree_clone()

        self._external_merge_round = 0
        self._log = []
        self._highlighted_nodes = {}
        self._lexicalizations = {}
        self._pending_moves = {}
        self._log_note("Algorithm started.")
        self._log_note("Initial tree consists of node {0}".format(self._setup.initial_node.name()))
        self._undo_info = []
        self._last_choice = None

    def _state_begin_merge_round(self, **_):
        self._increment_round_counter()
        self._clear_highlighting()
        self._log_note(u"Beginning of {0}".format(self._current_round_name()))

    def _state_announce_move(self, **_):
        node = self._first_node_to_move()
        destination = self._pending_moves[node]
        self._highlight_nodes({node: HIGHLIGHT_SOURCE, destination: HIGHLIGHT_DESTINATION})
        self._log_note(u"About to move node {0}".format(node.name()))

    def _state_moved_node(self, **_):
        node = self._first_node_to_move()
        self._do_node_move(node)
        self._highlight_nodes({node: HIGHLIGHT_DESTINATION})
        self._log_note(u"Moved node {0}".format(node.name()))

    def _state_announce_external_merge(self, **_):
        node = self._setup.external_merges[self._external_merge_round - 1]
        self._highlight_nodes({self._tree.root: HIGHLIGHT_DESTINATION})
        self._log_note(u"About to perform external merge of node {0}".format(node.name()))

    def _state_merged_node(self, **_):
        node = self._setup.external_merges[self._external_merge_round - 1]
        merged_node = self._do_external_merge(node)
        self._highlight_nodes({merged_node: HIGHLIGHT_POINT})
        self._log_note(u"Merged node {0}".format(node.name()))

    def _state_announce_lexicalization(self, **_):
        node = self._first_nonlexicalized_node()
        self._highlight_nodes({node: HIGHLIGHT_POINT})
        self._log_note(u"About to lexicalize node {0}".format(node.name()))

    def _state_list_matches(self, **_):
        node = self._first_nonlexicalized_node()
        self._highlight_nodes({node: HIGHLIGHT_POINT})

        matches = self._matches_for_node(node)
        if len(matches) > 0:
            self._log_note(u"Matches: {0}".format(', '.join(match.description() for match in matches)))
        else:
            self._log_warning("No matches for this node")

    def _state_lexicalized_node(self, **kwargs):
        node = self._first_nonlexicalized_node()
        self._highlight_nodes({node: HIGHLIGHT_POINT})

        matches = self._matches_for_node(node)
        if len(matches) == 0:
            self._do_lexicalization(node, None)
            self._log_note("OK, since children are lexicalized")
        else:
            alternative = kwargs['alternative'] if kwargs['alternative'] is not None else 0
            if alternative < 0 or alternative >= len(matches):
                raise RuntimeError("Invalid alternative index {0}".format(alternative))

            self._do_lexicalization(node, matches[alternative])
            if len(matches) > 1:
                self._set_last_choice(alternative)

            self._log_note(u"Lexicalized node {0} using item {1}".format(node.name(),
                                                                         matches[alternative].lexicon_entry.name))

    def _state_lexicalization_done(self, **_):
        self._clear_highlighting()
        self._log_note("All nodes lexicalized")

    def _state_end_merge_round(self, **_):
        self._clear_highlighting()
        self._log_note("End of {0}".format(self._current_round_name()))

    def _state_success(self, **_):
        self._clear_highlighting()
        self._log_note("Algorithm completed successfully")

        spellout = self.spellout()
        self._log_note(u"Spell-out: {0} (/{1}/)".format(
            u'+'.join(item.name for item in spellout),
            u' '.join(item.phonological_content for item in spellout)
        ))

    def _state_failure(self, **kwargs):
        self._log_error(u"FAILURE: " + kwargs['error_text'])

    def _current_round_name(self):
        if self._is_final_round():
            return "final cleanup round"
        else:
            return "external merge round no.{0}".format(self._external_merge_round)

    def _is_final_round(self):
        return self._external_merge_round == len(self._setup.external_merges) + 1

    def _any_to_move(self):
        return len(self._pending_moves) > 0

    def _any_to_lexicalize(self):
        return self._first_nonlexicalized_node() is not None

    def _first_nonlexicalized_node(self):
        for node in reversed(list(self._tree.bfs())):
            if not (isinstance(node, TraceNode) or self._node_is_lexicalized(node)):
                # Special: the root does not need to be lexicalized in the final cycle
                if node == self._tree.root and self._is_final_round():
                    return None

                return node

        return None

    def _first_node_to_move(self):
        for node in reversed(list(self._tree.bfs())):
            if node in self._pending_moves:
                return node

        return None

    def _node_is_lexicalized(self, node):
        return node in self._lexicalizations

    def _children_are_lexicalized(self, node):
        return len(node.children()) > 0 and all(self._node_is_lexicalized(child) for child in node.children())

    def _spellout_rec(self, node, parts):
        if self._node_is_lexicalized(node) and self._lexicalizations[node] is not None:
            parts.append(self._lexicalizations[node])
            return

        for child in node.children():
            self._spellout_rec(child, parts)

    def _matches_for_node(self, node):
        matches = self._matches_without_movement(node)
        matches.extend(self._matches_with_one_movement(node))

        return matches

    def _accessible_lexicon(self):
        for item in self._setup.lexicon:
            if item.conceptual_content is None or item.conceptual_content == self._setup.conceptual_series:
                yield item

    def _matches_without_movement(self, node):
        matches = []

        node_sig = node.signature()
        for item in self._accessible_lexicon():
            item_tree_size = item.tree.root.subtree_size()

            for start_node in item.tree.bfs():
                if start_node.signature() == node_sig:
                    matches.append(LexicalizationMatch(item, item_tree_size - start_node.subtree_size()))

        matches.sort(key=lambda x: x.extras)

        return matches

    def _matches_with_one_movement(self, node):
        matches = []

        for parent in node.bfs():
            for side in (0, 1):
                if parent.get_child(side) is not None:
                    temp = parent.get_child(side)
                    parent.set_child(side, None)
                    for m in self._matches_without_movement(node):
                        m.moved = temp
                        matches.append(m)
                    parent.set_child(side, temp)

        return matches

    def _switch_state(self, next_state, state_entry_args):
        next_state(**state_entry_args)

        prev_state = self._state
        self._state = next_state
        self._add_undo_action(self._undo_switch_state, prev_state)

    def _clear_highlighting(self):
        self._highlight_nodes({})

    def _highlight_nodes(self, highlight_now):
        removed = set(self._highlighted_nodes.keys()) - set(highlight_now.keys())

        for item in removed:
            prev_value = self._highlighted_nodes[item]
            self._add_undo_action(self._undo_highlight_node, item, prev_value)
            del self._highlighted_nodes[item]

        for item in highlight_now:
            if item in self._highlighted_nodes and self._highlighted_nodes[item] == highlight_now[item]:
                continue

            prev_value = self._highlighted_nodes.get(item)
            self._highlighted_nodes[item] = highlight_now[item]
            self._add_undo_action(self._undo_highlight_node, item, prev_value)

    def _increment_round_counter(self):
        self._external_merge_round += 1
        self._add_undo_action(self._undo_increment_round_counter)

    def _do_external_merge(self, merged_node):
        merged_node = merged_node.clone()
        self._tree.root = PhrasalNode(merged_node.feature, 0, merged_node, self._tree.root)
        self._update_tree_clone()

        self._add_undo_action(self._undo_external_merge)

        return merged_node

    def _do_node_move(self, node):
        if not node in self._pending_moves:
            raise RuntimeError(u"Node {0} is not marked for moving!".format(node.name()))
        src_parent, src_side = self._tree.locate_node(node)
        if src_parent is None:
            raise RuntimeError(u"Cannot move root node {0}!".format(node.name()))

        destination = self._pending_moves[node]
        self._add_undo_action(self._undo_node_move, node, destination, src_parent, src_side)

        src_parent.set_child(src_side, TraceNode(node))

        dest_parent, dest_side = self._tree.locate_node(destination)
        if destination.degree == 0:
            destination.degree = 1

        phrasal = PhrasalNode(destination.feature, destination.degree + 1)
        phrasal.right = destination
        phrasal.left = node

        if dest_parent is None:
            self._tree.root = phrasal
        else:
            dest_parent.set_child(dest_side, phrasal)

        self._update_tree_clone()

        del self._pending_moves[node]

    def _do_lexicalization(self, node, match):
        undo_moved_node = None
        undo_prev_destination = None

        if match is not None:
            self._lexicalizations[node] = match.lexicon_entry

            if match.moved is not None:
                undo_moved_node = match.moved
                undo_prev_destination = self._pending_moves.get(match.moved)
                self._pending_moves[match.moved] = node
        else:
            self._lexicalizations[node] = None

        self._add_undo_action(self._undo_lexicalization, node, undo_moved_node, undo_prev_destination)

    def _set_last_choice(self, choice):
        prev_choice = self._last_choice
        self._last_choice = choice
        self._add_undo_action(self._undo_set_last_choice, prev_choice)

    def _log_message(self, kind, message):
        self._log.append((kind, message))
        self._add_undo_action(self._undo_log_message)

    def _log_note(self, message):
        self._log_message(MSG_NOTE, message)

    def _log_warning(self, message):
        self._log_message(MSG_WARNING, message)

    def _log_error(self, message):
        self._log_message(MSG_ERROR, message)

    def _new_undo_point(self):
        self._undo_info.append([])

    def _add_undo_action(self, action, *args):
        if len(self._undo_info) > 0:
            self._undo_info[-1].append((action, args))

    def _undo_switch_state(self, prev_state):
        self._state = prev_state

    def _undo_set_last_choice(self, prev_choice):
        self._last_choice = prev_choice

    def _undo_highlight_node(self, node, prev_value):
        if prev_value is None:
            del self._highlighted_nodes[node]
        else:
            self._highlighted_nodes[node] = prev_value

    def _undo_increment_round_counter(self):
        self._external_merge_round -= 1

    def _undo_external_merge(self):
        self._tree.root = self._tree.root.right
        self._update_tree_clone()

    def _undo_lexicalization(self, node, moved_node, prev_destination):
        del self._lexicalizations[node]

        if moved_node is not None:
            if prev_destination is not None:
                self._pending_moves[moved_node] = prev_destination
            else:
                del self._pending_moves[moved_node]

    def _undo_node_move(self, node, destination, src_parent, src_side):
        phrasal, _ = self._tree.locate_node(destination)
        ph_parent, ph_side = self._tree.locate_node(phrasal)

        if ph_parent is None:
            self._tree.root = destination
        else:
            ph_parent.set_child(ph_side, destination)

        destination.degree -= 1
        if destination.degree == 1:
            destination.degree = 0

        src_parent.set_child(src_side, node)

        self._pending_moves[node] = destination

        self._update_tree_clone()

    def _undo_log_message(self):
        self._log.pop()

    def _update_tree_clone(self):
        if self._tree is not None:
            self._tree_clone = self._tree.clone()
            self._node_clones = dict(zip(self._tree.bfs(), self._tree_clone.bfs()))
        else:
            self._tree_clone = None
            self._node_clones = {}

    def _load_from_json_obj(self, data):
        REF = self._references_from_json

        self._setup = Setup.from_json_obj(data['setup'])

        self._tree = Tree.from_json_obj(data['tree'])
        self._log = copy.deepcopy(data['log'])

        self._state = REF(data['state'])
        self._last_choice = data['last_choice']
        self._external_merge_round = data['external_merge_round']
        self._lexicalizations = REF(data['lexicalizations'])
        self._pending_moves = REF(data['pending_moves'])
        self._highlights = REF(data['highlights'])
        self._undo_info = REF(data['undo_info'])

        self._update_tree_clone()

    def _materialize_to_json(self, value):
        if isinstance(value, list) or isinstance(value, tuple) or isinstance(value, set):
            return [self._materialize_to_json(item) for item in value]
        elif hasattr(value, 'to_json_obj'):
            return value.to_json_obj()
        else:
            return value

    def _references_to_json(self, value):
        if isinstance(value, list) or isinstance(value, tuple) or isinstance(value, set):
            return [self._references_to_json(item) for item in value]
        elif isinstance(value, dict):
            return dict((self._references_to_json(key), self._references_to_json(val))
                        for key, val in value.items())
        elif isinstance(value, TreeNode):
            for node_idx, node in enumerate(self._tree.bfs()):
                if value == node:
                    return '@node:{0}'.format(node_idx + 1)

            raise RuntimeError("Tried to refer to node not in tree")
        elif isinstance(value, LexiconEntry):
            return '@lexicon:{0}'.format(self._setup.lexicon.index(value))
        elif callable(value):
            if value.__name__.startswith('_state_'):
                return '@state:' + self._get_state_name(value)
            else:
                return '@action:' + value.__name__
        else:
            return value

    def _references_from_json(self, data):
        if data is None:
            return None
        elif isinstance(data, basestring):
            if data.startswith('@state:'):
                name = data[len('@state:'):]
                if not hasattr(self, '_state_' + name):
                    raise RuntimeError("No such state: '{0}'".format(name))

                return getattr(self, '_state_' + name)
            elif data.startswith('@action:'):
                name = data[len('@action:'):]
                if not hasattr(self, name) or not callable(getattr(self, name)):
                    raise RuntimeError("No such action: '{0}'".format(name))

                return getattr(self, name)
            elif data.startswith('@node:'):
                index = int(data[len('@node:'):])
                all_nodes = list(self._tree.bfs())
                if index < 1 or index > len(all_nodes):
                    raise RuntimeError("Invalid node ID: {0}".format(index))

                return all_nodes[index - 1]
            elif data.startswith('@lexicon:'):
                index = int(data[len('@lexicon:'):])
                if index < 0 or index >= len(self._setup.lexicon):
                    raise RuntimeError("Invalid lexicon item index: {0}".format(index))

                return self._setup.lexicon[index]
        elif isinstance(data, dict):
            return dict((self._references_from_json(key), self._references_from_json(val))
                        for key, val in data.items())
        elif isinstance(data, list):
            return [self._references_from_json(item) for item in data]

        return data
