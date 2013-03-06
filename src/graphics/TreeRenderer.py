# graphics/TreeRenderer.py
#
# (C) Copyright 2013  Cristian Dinu <goc9000@gmail.com>
# 
# This file is part of spellout.
#
# Licensed under the GPL-3

from PyQt4.Qt import QSize, QRectF, QLineF, QTextDocument, QPainter, QImage, QGraphicsScene

from structures.tree.PhrasalNode import PhrasalNode
from structures.tree.FeatureNode import FeatureNode
from structures.tree.TraceNode import TraceNode
from structures.tree.PlaceholderNode import PlaceholderNode


# Note: this class is not thread-safe
class TreeRenderer():
    font_size = None
    node_v_spacing = 16
    node_h_spacing = 24

    _tree = None
    _doc = None
    _last_font_size = None
    
    def __init__(self, tree=None, **kwargs):
        self._tree = tree

        self._doc = QTextDocument()
        self._doc.setUndoRedoEnabled(False)
        self._doc.setUseDesignMetrics(True)
        self._doc.setDocumentMargin(0)
        self.font_size = self._doc.defaultFont().pointSize()

        if 'scale' in kwargs:
            self.scale(kwargs['scale'])

    def set_tree(self, tree):
        self._tree = tree

    def scale(self, factor):
        self.font_size *= factor
        self.node_h_spacing *= factor
        self.node_v_spacing *= factor
    
    def get_tree_size(self):
        if self._get_tree() is None:
            return QSize(0, 0)
        
        left_width, right_width, height = self._get_subtree_spans(self._get_tree().root)
        
        return QSize(left_width + right_width, height)
    
    def get_tree_layout(self):
        layout = dict()

        if self._get_tree() is not None:
            self._layout_node_rec(self._get_tree().root, 0, 0, layout)
        
        return layout
    
    def render_tree(self, painter):
        if self._get_tree() is None:
            return

        scene = self.get_tree_scene()
        scene.render(painter)
    
    def get_tree_image(self):
        size = self.get_tree_size()

        img = QImage(size, QImage.Format_ARGB32_Premultiplied)
        img.fill(0)

        if self._get_tree() is not None:
            painter = QPainter(img)
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setRenderHint(QPainter.TextAntialiasing)
            self.render_tree(painter)

        return img
    
    def get_tree_scene(self):
        scene = QGraphicsScene()
    
        if self._get_tree() is None:
            return scene
        
        layout = self.get_tree_layout()
        
        font = self._setup_doc('').defaultFont()

        for x, y, html, node in self._iter_rendered_nodes(layout):
            item = scene.addText('', font)
            item.document().setUndoRedoEnabled(False)
            item.document().setUseDesignMetrics(True)
            item.document().setDocumentMargin(0)
            item.setHtml(html)
            item.setPos(x, y)
            item.setData(0, 'node')
            item.setData(1, node)
            
        for x1, y1, x2, y2, from_node, to_node in self._iter_rendered_branches(layout):
            item = scene.addLine(QLineF(x1, y1, x2, y2))
            item.setData(0, 'edge')
            item.setData(1, (from_node, to_node))
        
        return scene

    def _get_tree(self):
        # Note: do not replace by a simple attribute access - this is overridden in AlgorithmTreeRender
        return self._tree
    
    def _iter_rendered_nodes(self, layout):
        for node, rect in layout.items():
            left_deco, center_html, right_deco = self._get_node_html(node)
            html = left_deco + center_html + right_deco
            
            yield (rect.x(), rect.y(), html, node)
    
    def _iter_rendered_branches(self, layout):
        for node, rect in layout.items():
            my_left, _, _ = self._get_node_spans(node)
            
            for child in node.children():
                child_left, _, _ = self._get_node_spans(child)
                
                x1, y1 = (rect.x() + my_left, rect.y() + rect.height())
                x2, y2 = (layout[child].x() + child_left, layout[child].y())
                
                yield (x1, y1, x2, y2, node, child)
    
    def _layout_node_rec(self, node, x, y, layout):
        my_left, my_right, my_height = self._get_node_spans(node)
    
        n_children = len(node.children())
    
        if n_children == 0:
            layout[node] = QRectF(x, y, my_left+my_right, my_height)
        elif n_children == 1:
            child = node.left if node.left is not None else node.right
            child_left, _, _ = self._get_subtree_spans(child)
            
            center_x = x + max(my_left, child_left)
            subtree_y = y + my_height + self.node_v_spacing
            
            layout[node] = QRectF(center_x - my_left, y, my_left+my_right, my_height)
            self._layout_node_rec(child, center_x - child_left, subtree_y, layout)
        else:
            l_left, l_right, _ = self._get_subtree_spans(node.left)
            
            subtree_left = l_left + l_right + self.node_h_spacing / 2.0
            center_x = x + max(my_left, subtree_left)
            subtree_y = y + my_height + self.node_v_spacing
    
            layout[node] = QRectF(center_x - my_left, y, my_left+my_right, my_height)
            self._layout_node_rec(node.left, center_x - subtree_left, subtree_y, layout)
            self._layout_node_rec(node.right, center_x + self.node_h_spacing / 2.0, subtree_y, layout)
    
    def _get_subtree_spans(self, node):
        my_left, my_right, my_height = self._get_node_spans(node)
        
        n_children = len(node.children())
        
        if n_children == 0:
            return my_left, my_right, my_height
        elif n_children == 1:
            child = node.left if node.left is not None else node.right
            child_left, child_right, child_height = self._get_subtree_spans(child)
            
            left = max(my_left, child_left)
            right = max(my_right, child_right)
            height = my_height + self.node_v_spacing + child_height
        
            return left, right, height
        else:
            l_left, l_right, l_height = self._get_subtree_spans(node.left)
            r_left, r_right, r_height = self._get_subtree_spans(node.right)
            
            left = max(my_left, l_left + l_right + self.node_h_spacing / 2.0)
            right = max(my_right, r_left + r_right + self.node_h_spacing / 2.0)
            height = my_height + self.node_v_spacing + max(l_height, r_height)
            
            return left, right, height

    def _get_node_spans(self, node):
        left_deco, center_html, right_deco = self._get_node_html(node)
        
        left_deco_size = self._measure_html(left_deco)
        right_deco_size = self._measure_html(right_deco)
        center_html_size = self._measure_html(center_html)
        
        left_span = left_deco_size.width() + center_html_size.width() / 2.0
        right_span = right_deco_size.width() + center_html_size.width() / 2.0
        height = max(left_deco_size.height(), center_html_size.height(), right_deco_size.height())
        
        return left_span, right_span, height

    def _get_node_html(self, node):
        left_decoration = ''
        right_decoration = ''
        
        if isinstance(node, PhrasalNode):
            central_html = node.feature + "P" + ('<sub>{0}</sub>'.format(node.degree) if node.degree > 0 else '')
        elif isinstance(node, FeatureNode):
            central_html = node.feature
        elif isinstance(node, TraceNode):
            if node.of_node is None:
                ref_html = "?"
            else:
                _, ref_html, _ = self._get_node_html(node.of_node)
            central_html = "t<sub>" + ref_html + "</sub>"
        elif isinstance(node, PlaceholderNode):
            central_html = '...'
        else:
            raise RuntimeError("NIY")
        
        return left_decoration, central_html, right_decoration

    def _measure_html(self, html):
        return self._setup_doc(html).size()

    def _render_html(self, painter, x, y, html):
        doc = self._setup_doc(html)
        painter.save()
        painter.translate(x, y)
        doc.drawContents(painter)
        painter.restore()

    def _setup_doc(self, html):
        doc = self._doc
        
        if self.font_size != self._last_font_size:
            self._last_font_size = self.font_size
            font = doc.defaultFont()
            font.setPointSize(self.font_size)
            doc.setDefaultFont(font)
        
        doc.setHtml(html)
        
        return doc
        