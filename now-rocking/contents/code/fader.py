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
from PyQt4.QtCore import SLOT
from PyQt4.QtCore import pyqtSignature
from PyQt4.QtCore import QObject
from PyQt4.QtCore import QTimeLine
from PyQt4.QtCore import QSize
from PyQt4.QtCore import QPoint
from PyQt4.QtGui  import QPixmap
from PyQt4.QtGui  import QPainter
from PyQt4.QtGui  import QColor
from PyQt4.QtGui  import QStyleOptionGraphicsItem
from PyKDE4.plasma import Plasma
from PyQt4.QtCore import QPointF
import traceback

# Fader cannot be QObject
class FaderHelper(QObject):
    def __init__(self, fader):
        self.fader = fader

    def valueChanged(self, value):
        self.fader.valueChanged(value)

    def fadingFinished(self):
        self.fader.fadingFinished()

class Fader():
    Fast = 250
    Medium = 500
    Slow = 1000

    timeline = QTimeLine()
    timeline.setDirection(QTimeLine.Forward)

    def __init__(self):
        self.originalPaint = self.paint
        self.paint = self.faderPaint

        self.helper = FaderHelper(self)
        self.old = QPixmap()
        self.new = QPixmap()
        self.fadeValue = 0.0
        self.animate = False
        self.enabled = True
        self.hideAfterFade = False
        self.fadeChildren = True
        self.connect(Fader.timeline, SIGNAL('valueChanged(qreal)'), self.helper.valueChanged)
        self.connect(Fader.timeline, SIGNAL('finished()'), self.helper.fadingFinished)

    def faderPaint(self, painter, option, widget = None):
        #print self.animate, type(self), self.fadeValue
        if self.animate:
            # Some glitches on small fade values??
            if self.fadeValue < 0.1:
                temp = self.old
            else:
                temp = Plasma.PaintUtils.transition(self.old, self.new, self.fadeValue)
            painter.drawPixmap(QPoint(0, 0), temp)
        else:
            self.originalPaint(painter, option, widget)

    def fadeIn(self, ms):
        Fader.timeline.stop()
        if not self.enabled:
            self.show()
            return
        self.show()
        self.new = self.currentPixmap()
        self.old = QPixmap(self.new.size())
        self.old.fill(Qt.transparent)
        self.hideAfterFade = False
        self.fade(ms)

    def fadeOut(self, ms):
        self.setItemAndChildsVisible(self, False)
        Fader.timeline.stop()
        if not self.enabled:
            self.hide()
            return
        self.show()
        self.old = self.currentPixmap()
        self.new = QPixmap(self.old.size())
        self.new.fill(Qt.transparent)
        self.hideAfterFade = True
        self.fade(ms)

    def saveFadeStart(self):
        #print 'saveFadeStart'
        Fader.timeline.stop()
        if not self.enabled:
            return
        self.old = self.currentPixmap()

    def startFade(self, ms):
        #print self.__class__.__name__, 'startFade'
        #traceback.print_stack()
        Fader.timeline.stop()
        if not self.enabled:
            self.update()
            return
        self.show()
        self.new = self.currentPixmap()
        self.hideAfterFade = False
        self.fade(ms)

    def fade(self, ms):
        self.animate = True
        Fader.timeline.setDuration(ms)
        Fader.timeline.setFrameRange(0, ms / 50)
        Fader.timeline.start()

    def setFadeEnabled(self, enabled):
        self.enabled = enabled

    def setFadeChildren(self, paint):
        self.fadeChildren = paint

    def paintChilds(self, item, painter):
        option = QStyleOptionGraphicsItem()
        for child in item.childItems():
            painter.save()
            pos = child.scenePos()
            pos = self.mapFromScene(pos)
            painter.translate(pos)
            if isinstance(child, Fader):
                child.originalPaint(painter, option, None)
            else:
                child.paint(painter, option, None)
            painter.restore()
            self.paintChilds(child, painter)

    def currentPixmap(self):
        option = QStyleOptionGraphicsItem()
        pixmap = QPixmap(self.boundingRect().size().toSize() + QSize(1, 1))
        pixmap.fill(Qt.transparent)
        painter = QPainter(pixmap)
        self.originalPaint(painter, option, None)
        if self.fadeChildren:
            self.paintChilds(self, painter)
        return pixmap

    def valueChanged(self, value):
        if self.animate:
            self.fadeValue = value
            self.update()

    def setItemAndChildsVisible(self, item, visible):
        item.setVisible(visible)
        if self.fadeChildren:
            for child in item.childItems():
                self.setItemAndChildsVisible(child, visible)

    def fadingFinished(self):
        if self.animate:
            self.animate = False
            self.setItemAndChildsVisible(self, not self.hideAfterFade)
