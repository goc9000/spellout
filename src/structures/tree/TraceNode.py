# structures/tree/TraceNode.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

from structures.tree.TreeNode import TreeNode


class TraceNode(TreeNode):
    of_node = None
    
    def __init__(self, of_node):
        TreeNode.__init__(self, None, None)
        self.of_node = of_node
    
    def subtree_size(self):
        return 0
    
    def clone(self):
        return TraceNode(None)._on_cloned_from(self)
    
    def own_signature(self):
        return None
    
    def name(self):
        return "t{0}".format(self.of_node.name())
    
    def _fill_json_obj(self, obj, nodes_to_ids):
        if nodes_to_ids is None:
            raise RuntimeError("Cannot JSON-ize TraceNode without nodes_to_ids map")
        
        obj['type'] = 'TraceNode'
        obj['of_node'] = nodes_to_ids[self.of_node]
    
    def _finalize_from_json_obj(self, obj, ids_to_nodes):
        self.of_node = ids_to_nodes[obj['of_node']]
    
    @staticmethod
    def _from_json_obj(obj):
        if obj['type'] != 'TraceNode':
            raise RuntimeError("Expected type=TraceNode in JSON object")

        return TraceNode(None)
