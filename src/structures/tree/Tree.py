# structures/tree/Tree.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
#
# This file is part of spellout.
#
# Licensed under the GPL-3

from structures.tree.TreeNode import TreeNode
from structures.tree.PhrasalNode import PhrasalNode
from structures.tree.TraceNode import TraceNode
from structures.tree.PlaceholderNode import PlaceholderNode

from collections import deque


class Tree:
    root = None

    def __init__(self, root_node):
        self.root = root_node

    def clone(self):
        mapping = {}

        for node in self.root.bfs():
            mapping[node] = node.clone()

        for old_node, new_node in mapping.iteritems():
            if old_node.left is not None:
                new_node.left = mapping[old_node.left]
            if old_node.right is not None:
                new_node.right = mapping[old_node.right]
            if isinstance(new_node, TraceNode):
                new_node.of_node = mapping[old_node.of_node]

        return Tree(mapping[self.root])

    def bfs(self):
        return self.root.bfs()

    def locate_node(self, node):
        return self.root.locate_child(node)

    def check(self):
        for node in self.root.bfs():
            if isinstance(node, PhrasalNode):
                if len(node.children()) == 0:
                    raise RuntimeError("Phrasal node {0} must have at least one child".format(node.name()))

            if isinstance(node, PlaceholderNode):
                raise RuntimeError("Some nodes are still not filled in")

    def to_json_obj(self):
        nodes_to_ids = dict(((node, i + 1) for i, node in enumerate(self.root.bfs())))

        obj = {
            'root': self.root.to_json_obj(nodes_to_ids)
        }

        return obj

    @staticmethod
    def from_json_obj(obj):
        def bfs_json_tree(root):
            q = deque()
            q.appendleft(root)

            while len(q) > 0:
                head = q.popleft()
                yield head

                for key in ('left', 'right'):
                    if (key in head) and (head[key] is not None):
                        q.append(head[key])

        if obj is None:
            return None

        root = TreeNode.from_json_obj(obj['root'])

        ids_to_nodes = dict()
        for node, json_node in zip(root.bfs(), bfs_json_tree(obj['root'])):
            if 'id' in json_node:
                ids_to_nodes[json_node['id']] = node

        for node, json_node in zip(root.bfs(), bfs_json_tree(obj['root'])):
            node._finalize_from_json_obj(json_node, ids_to_nodes)

        tree = Tree(root)

        return tree
