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
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import QTimer
from PyQt4.QtCore import QSizeF
from PyQt4.QtGui  import QPainter
from PyKDE4.plasma import Plasma
from fader import Fader
from image import ImagePainter

class ButtonHelper():
    def __init__(self):
        self.hover = False
        self.setAcceptHoverEvents(True)
        self.elementString = 'normal'
        self.connect(self.nativeWidget(), SIGNAL('sliderPressed()'), self.checkState)
        self.connect(self.nativeWidget(), SIGNAL('sliderReleased()'), self.checkState)

    def paint(self, painter, option, widget = None):
        if self.state() != self.element():
            QTimer.singleShot(0, self.checkState)
        ImagePainter.paint(self, painter, option, widget)

    def checkState(self):
        self.setElement(self.state())

    def state(self):
        if isinstance(self, Plasma.PushButton):
            isDown = self.nativeWidget().isDown()
        else:
            isDown = self.nativeWidget().isSliderDown()
        if not self.nativeWidget().isEnabled():
            self.hover = False
            return 'disabled'
        elif isDown:
            if self.hover:
                return 'down-hover'
            else:
                return 'down'
        else:
            if self.hover:
                return 'normal-hover'
            else:
                return 'normal'

    def setImage(self, img):
        ImagePainter.setImage(self, img)
        self.img.setContainsMultipleImages(True)

    def hoverEnterEvent(self, event):
        self.hover = True
        self.checkState()

    def hoverLeaveEvent(self, event):
        self.hover = False
        self.checkState()

class Button(ButtonHelper, ImagePainter, Plasma.PushButton):
    def __init__(self, parent = None):
        Plasma.PushButton.__init__(self, parent)
        ImagePainter.__init__(self)
        ButtonHelper.__init__(self)

