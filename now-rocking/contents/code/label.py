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
from PyQt4.QtCore import QSizeF
from PyQt4.QtGui  import QGraphicsWidget
from PyQt4.QtGui  import QPainter
from PyQt4.QtGui  import QApplication
from PyQt4.QtGui  import QSizePolicy
from PyQt4.QtGui  import QFontMetricsF
from PyKDE4.plasma import Plasma
from fader import Fader

class Label(Fader, QGraphicsWidget):
    def __init__(self, parent = None):
        QGraphicsWidget.__init__(self, parent)
        Fader.__init__(self)
        self._text = ''
        self._tight = False
        self._color = Plasma.Theme.defaultTheme().color(Plasma.Theme.TextColor)
        self._align = Qt.AlignHCenter
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)

    def setText(self, text):
        #print '** Label.setText', self._text, text
        if self._text == text:
            return
        if self.isVisible():
            self.saveFadeStart()
        self._text = text
        if self.isVisible():
            self.startFade(Fader.Slow)
        self.updateGeometry()

    def text(self):
        return self._text

    def setFont(self, font):
        QGraphicsWidget.setFont(self, font)
        self.updateGeometry()
        self.update()

    def setColor(self, color):
        self._color = color
        self.update()

    def setAlign(self, align):
        self._align = align
        self.update()

    def setTight(self, tight):
        self._tight = tight
        self.updateGeometry()
        self.update()

    def sizeHint(self, which, constraint):
        hint = QGraphicsWidget.sizeHint(self, which, constraint)
        if which == Qt.PreferredSize or which == Qt.MinimumSize:
            txt = self._text
            if txt == '':
                txt = u'Äg'
            fm = QFontMetricsF(self.font())
            hint.setWidth(fm.width(txt))
            if not self._tight:
                hint.setHeight(fm.boundingRect(txt).height())
            else:
                hint.setHeight(fm.tightBoundingRect(txt).height())
        #print '** Label.sizeHint', hint, self._text, which, Qt.PreferredSize
        return hint

    def paint(self, painter, option, widget = None):
        #print '** Label.paint', self._text, self.contentsRect()
        if self._text != '':
            painter.setPen(self._color)
            painter.setFont(self.font())
            painter.drawText(self.contentsRect(), self._align | Qt.AlignVCenter, self._text)
            #painter.drawRect(self.contentsRect())
