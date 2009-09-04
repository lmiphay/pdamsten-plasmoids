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
from PyQt4.QtGui  import QGraphicsWidget
from PyQt4.QtGui  import QPainter
from PyQt4.QtGui  import QColor
from PyQt4.QtGui  import QPen
from PyKDE4.plasma import Plasma
from fader import Fader

class Frame(Fader, QGraphicsWidget):
    def __init__(self, parent = None):
        QGraphicsWidget.__init__(self, parent)
        Fader.__init__(self)
        self.svg = Plasma.FrameSvg(self)

    def setSvg(self, img):
        self.svg.setImagePath(img)
        (left, top, right, bottom) = self.svg.getMargins()
        self.setContentsMargins(left, top, right, bottom)

    def paint(self, painter, option, widget = None):
        self.svg.paintFrame(painter)

    def resizeEvent(self, event):
        #print event.newSize()
        self.svg.resizeFrame(event.newSize())
