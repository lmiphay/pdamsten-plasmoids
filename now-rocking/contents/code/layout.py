#   -*- coding: utf-8 -*-
#
#   Copyright (C) 2009 Petri Damstén <damu@iki.fi>
#
#   This program is free software; you can redistribute it and/or modify
#   it under the terms of the GNU Library General Public License as
#   published by the Free Software Foundation; either version 2, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details
#
#   You should have received a copy of the GNU Library General Public
#   License along with this program; if not, write to the
#   Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

from PyQt4.QtCore import Qt
from PyQt4.QtCore import QRectF
from PyQt4.QtCore import QSizeF
from PyQt4.QtGui  import QGraphicsLayout

class Layout(QGraphicsLayout):
    def __init__(self, parent = None):
        QGraphicsLayout.__init__(self, parent)
        self.items = []

    def setGeometry(self, rect):
        QGraphicsLayout.setGeometry(self, rect)
        self.repositionItems()

    def itemAt(self, index):
        return self.items[index][0]

    def removeAt(self, index):
        del self.items[index]
        self.repositionItems()

    def addItem(self, item, pos):
        self.items.append((item, pos))
        self.repositionItems()

    def count(self):
        return len(self.items)

    def sizeHint(self, which, constraint):
        # We don't have preferred size
        if which == Qt.PreferredSize:
            return QSizeF(1, 1)
        else:
            return QSizeF(-1, -1)

    def repositionItems(self):
        rect = self.geometry()
        #print '***', type(self), rect
        for item in self.items:
            pos = item[1]
            item = item[0]
            #print pos
            ix = rect.x() + pos[0][0] * rect.width() + pos[0][1]
            iy = rect.y() + pos[1][0] * rect.height() + pos[1][1]
            if pos[2][0] != -1: # Same as height
                iw = rect.x() + pos[2][0] * rect.width() + pos[2][1] - ix
            else:
                iw = rect.y() + pos[3][0] * rect.height() + pos[3][1] - iy
            if pos[3][0] != -1:
                ih = rect.y() + pos[3][0] * rect.height() + pos[3][1] - iy
            else:
                ih = rect.x() + pos[2][0] * rect.width() + pos[2][1] - ix
            #print '** ', ix, iy, iw, ih
            item.setGeometry(QRectF(ix, iy, iw, ih))
            #print type(item), item.geometry()
