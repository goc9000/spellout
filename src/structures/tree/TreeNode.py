# structures/tree/TreeNode.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

from collections import deque

import re


class TreeNode:
    left = None
    right = None

    def __init__(self, left=None, right=None):
        self.left = left
        self.right = right
    
    def children(self):
        return [child for child in (self.left, self.right) if child is not None]
    
    def get_child(self, side):
        return self.left if side == 0 else self.right
    
    def set_child(self, side, value):
        if side == 0:
            self.left = value
        else:
            self.right = value
    
    def bfs(self):
        q = deque()
        q.appendleft(self)
        
        while len(q) > 0:
            head = q.popleft()
            yield head
            
            for child in head.children():
                q.append(child)
    
    def locate_child(self, node):
        if node == self:
            return None, 0
            
        for parent in self.bfs():
            if parent.left == node:
                return parent, 0
            elif parent.right == node:
                return parent, 1
        
        return None, None

    def signature(self):
        my_sig = self.own_signature()
        if my_sig is None:
            return
        
        sig = [my_sig]
        
        for sub_node in (self.left, self.right):
            if sub_node is not None:
                sub_sig = sub_node.signature()
                if sub_sig is not None:
                    if sub_sig[0] == my_sig:
                        sig.extend(sub_sig[1:])
                    else:
                        sig.append(sub_sig)
        
        return tuple(sig)
    
    def subtree_size(self):
        return 1 + sum((child.subtree_size() for child in self.children()))
    
    def own_signature(self):
        raise RuntimeError("own_signature() must be overridden in descendants of TreeNode")
    
    def name(self):
        raise RuntimeError("name() must be overridden in descendants of TreeNode")
    
    def clone(self):
        raise RuntimeError("clone() must be overridden in descendants of TreeNode")
    
    def to_json_obj(self, nodes_to_ids=None):
        obj = dict()
        self._fill_json_obj(obj, nodes_to_ids)
        
        if nodes_to_ids is not None and self in nodes_to_ids:
            obj['id'] = nodes_to_ids[self]

        if self.left is not None:
            obj['left'] = self.left.to_json_obj(nodes_to_ids)
        if self.right is not None:
            obj['right'] = self.right.to_json_obj(nodes_to_ids)
        
        return obj
    
    def _on_cloned_from(self, _):
        return self

    def _fill_json_obj(self, obj, nodes_to_ids):
        raise RuntimeError("_fill_json_obj() must be overridden in descendants of TreeNode")
    
    def _finalize_from_json_obj(self, obj, ids_to_nodes):
        pass
    
    @staticmethod
    def from_name(name, connect_left=None, connect_right=None):
        from structures.tree.FeatureNode import FeatureNode
        from structures.tree.PhrasalNode import PhrasalNode

        match = re.match(r'^([a-z]+?)(P([0-9]+)?)?$', name, re.I)
        if not match:
            return None

        feat_str, p_str, deg_str = match.groups()
        
        feature = feat_str.capitalize()
        
        if p_str is None:
            return FeatureNode(feature, connect_left, connect_right)
        
        degree = int(deg_str) if deg_str is not None else 0
        
        return PhrasalNode(feature, degree, connect_left, connect_right)

    @staticmethod
    def from_json_obj(obj):
        from structures.tree.FeatureNode import FeatureNode
        from structures.tree.PhrasalNode import PhrasalNode
        from structures.tree.TraceNode import TraceNode
        from structures.tree.PlaceholderNode import PlaceholderNode

        if obj is None:
            return None
        
        if obj['type'] == 'FeatureNode':
            node = FeatureNode._from_json_obj(obj)
        elif obj['type'] == 'PhrasalNode':
            node = PhrasalNode._from_json_obj(obj)
        elif obj['type'] == 'TraceNode':
            node = TraceNode._from_json_obj(obj)
        elif obj['type'] == 'PlaceholderNode':
            node = PlaceholderNode._from_json_obj(obj)
        else:
            raise RuntimeError("Unsupported node type '{0}'".format(obj['type']))

        node.left = node.right = None
        if 'left' in obj:
            node.left = TreeNode.from_json_obj(obj['left'])
        if 'right' in obj:
            node.right = TreeNode.from_json_obj(obj['right'])
        
        return node
