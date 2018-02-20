# -*- coding: utf-8 -*-
#
# Copyright (c), 2018, SISSA (International School for Advanced Studies).
# All rights reserved.
# This file is distributed under the terms of the MIT License.
# See the file 'LICENSE' in the root directory of the present
# distribution, or http://opensource.org/licenses/MIT.
#
# @author Davide Brunato <brunato@sissa.it>
#

from .exceptions import ElementPathValueError


class ElementPathContext:
    _parent_map = None

    def __init__(self, root=None, node=None, position=0, size=0, values=None):
        self.root = root
        self.node = node
        self.position = position
        self.size = size
        self.values = {} if values is None else values

    def __repr__(self):
        return '%s(root=%r, node=%r, position=%r, size=%r)' % (
            self.__class__.__name__, self.root, self.node, self.position, self.size
        )

    def copy(self):
        return ElementPathContext(
            self.root, self.node, self.position, self.size, self.values.copy()
        )

    @property
    def parent_map(self):
        if self._parent_map is None:
            self._parent_map = {child: elem for elem in self.root.iter() for child in elem}
        return self._parent_map

    def iter_descendants(self):
        if self.node is None:
            self.size, self.position = 1, 0
            yield self
            self.node = self.root

        yield self
        elem = self.node
        if len(elem):
            self.size = len(elem)
            for self.position, self.node in enumerate(elem):
                for descendant in self.iter_descendants():
                    yield descendant

    def iter_children(self):
        if self.node is None:
            self.size, self.position, self.node = 1, 0, self.root
            yield self
        else:
            elem = self.node
            self.size = len(elem)
            for self.position, self.node in enumerate(elem):
                yield self

    def get_ancestors(self, elem):
        parent_map = self.parent_map
        ancestors = []
        while True:
            try:
                p = parent_map[elem]
            except KeyError:
                break
            else:
                if p in parent_map[elem]:
                    raise ElementPathValueError("context root is not a tree, circularity found at node %r." % p)
                ancestors.append(p)
        return ancestors
