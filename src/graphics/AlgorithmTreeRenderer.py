# graphics/AlgorithmTreeRenderer.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

import math

from graphics.TreeRenderer import TreeRenderer
from algorithm.SpelloutAlgorithm import HIGHLIGHT_DESTINATION, HIGHLIGHT_POINT, HIGHLIGHT_SOURCE

from PyQt4.QtGui import QColor, QPen, QBrush, QPainterPath
from PyQt4.QtCore import QPointF


class AlgorithmTreeRenderer(TreeRenderer):
    arrow_length = 16
    arrow_spacing = 4
    arrow_head_angle = 23
    arrow_inner_head_length = 4
    arrow_outer_head_length = 8
    arrow_angle = 20

    _algorithm = None

    _cached_node_info = None

    def __init__(self, algorithm=None, **kwargs):
        TreeRenderer.__init__(self, **kwargs)
        self._algorithm = algorithm

    def _get_tree(self):
        tree = self._algorithm.tree()

        self._update_cached_node_info(tree)

        return tree

    def _update_cached_node_info(self, tree):
        if tree is None:
            self._cached_node_info = dict()
            return

        self._cached_node_info = dict((node, dict()) for node in tree.bfs())

        for node in tree.bfs():
            for side in (0, 1):
                child = node.get_child(side)
                if child is not None:
                    self._cached_node_info[child]['parent'] = node
                    self._cached_node_info[child]['side'] = side

        for node, lexicon_entry in self._algorithm.lexicalizations().items():
            self._cached_node_info[node]['lexicalization'] = lexicon_entry

        for node, destination in self._algorithm.pending_moves().items():
            self._cached_node_info[node]['move_to'] = destination

    def get_tree_scene(self):
        scene = TreeRenderer.get_tree_scene(self)

        self._add_node_highlights(scene)

        return scene

    def _add_node_highlights(self, scene):
        initial_rect = scene.sceneRect()

        highlights = self._algorithm.highlighted_nodes()

        items = list(scene.items())
        for item in items:
            if item.data(0).toPyObject() == 'node':
                node = item.data(1).toPyObject()
                if node not in highlights:
                    continue

                if highlights[node] == HIGHLIGHT_DESTINATION:
                    angle, away, color = [180 - self.arrow_angle, False, QColor(192, 0, 0)]
                elif highlights[node] == HIGHLIGHT_SOURCE:
                    angle, away, color = [180 - self.arrow_angle, True, QColor(0, 128, 0)]
                elif highlights[node] == HIGHLIGHT_POINT:
                    angle, away, color = [180, False, QColor(0, 0, 255)]
                else:
                    continue

                target = QPointF(item.x() - 1, item.y() + item.boundingRect().height() / 2.0)

                scene.addPath(self._compute_arrow_path(target, angle, away), QPen(color), QBrush(color))

        scene.setSceneRect(initial_rect)

    def _compute_arrow_path(self, target, angle_deg, away):
        def move_from_point(origin, angle_deg, distance):
            return QPointF(origin.x() + math.cos(math.radians(angle_deg)) * distance,
                           origin.y() - math.sin(math.radians(angle_deg)) * distance)

        path = QPainterPath()

        base_pt = move_from_point(target, angle_deg, self.arrow_spacing + (0 if away else self.arrow_length))
        shaft_angle = angle_deg if away else angle_deg + 180

        attach_pt = move_from_point(base_pt, shaft_angle, self.arrow_length - self.arrow_inner_head_length)
        tip_pt = move_from_point(base_pt, shaft_angle, self.arrow_length)
        left_pt = move_from_point(tip_pt, shaft_angle + 180 + self.arrow_head_angle, self.arrow_outer_head_length)
        right_pt = move_from_point(tip_pt, shaft_angle + 180 - self.arrow_head_angle, self.arrow_outer_head_length)

        path.moveTo(base_pt)
        path.lineTo(attach_pt)
        path.lineTo(left_pt)
        path.lineTo(tip_pt)
        path.lineTo(right_pt)
        path.lineTo(attach_pt)

        return path

    def _get_node_html(self, node):
        left_decoration, central_html, right_decoration = TreeRenderer._get_node_html(self, node)

        node_info = self._cached_node_info[node]

        if 'lexicalization' in node_info and node_info['lexicalization'] is not None:
            entry = node_info['lexicalization']

            overridden = False
            if 'parent' in node_info:
                parent_info = self._cached_node_info[node_info['parent']]
                if 'lexicalization' in parent_info and parent_info['lexicalization'] is not None:
                    overridden = True

            side = node_info['side'] if 'side' in node_info else 1

            decoration = [u'{0} &larr;', u'&rarr; {0}'][side].format(entry.name)
            if overridden:
                decoration = '(' + decoration + ')'

            if side == 0:
                left_decoration = decoration + ' ' + left_decoration
            else:
                right_decoration = right_decoration + ' ' + decoration

        if 'move_to' in node_info:
            _, html, _ = self._get_node_html(node_info['move_to'])
            right_decoration = u'<sub>&lt;{0}&gt;</sub>'.format(html) + right_decoration

        return left_decoration, central_html, right_decoration
