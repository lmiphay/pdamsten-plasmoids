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
from PyQt4.QtCore import QPointF
from PyQt4.QtCore import QSizeF
from PyQt4.QtCore import QRectF
from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui  import QGraphicsWidget
from PyQt4.QtGui  import QPixmap
from PyQt4.QtGui  import QPainter
from PyQt4.QtGui  import QSizePolicy
from PyKDE4.plasma import Plasma
from fader import Fader

class ImagePainter(Fader):
    def __init__(self):
        Fader.__init__(self)
        self.img = QPixmap()
        self.scaledImg = QPixmap()
        self.elementString = ''
        self.prefix = ''
        self.imgPath = ''
        self.setMinimumSize(8, 8)
        self.aspectRatioMode = Qt.IgnoreAspectRatio
        self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)

    def paint(self, painter, option, widget = None):
        if isinstance(self.img, QPixmap):
            if self.img.isNull():
                return
            s = self.boundingRect().size().toSize()
            if s.width() != self.scaledImg.size().width() and \
               s.height() != self.scaledImg.size().height():
                self.scaledImg = self.img.scaled(s, self.aspectRatioMode, Qt.SmoothTransformation)
            p = self.boundingRect().topLeft()
            p.setX(p.x() + ((s.width() - self.scaledImg.size().width()) / 2.0))
            p.setY(p.y() + ((s.height() - self.scaledImg.size().height()) / 2.0))
            painter.drawPixmap(p, self.scaledImg)
        elif isinstance(self.img, Plasma.Svg):
            #print self.svgElement(), self.boundingRect(), self.imageSize()
            elem = self.svgElement()
            self.img.paint(painter, self.boundingRect(), elem)
            try:
                r = self.boundingRect()
                r.setWidth(r.width() * self.value() / (self.maximum() - self.minimum()))
                painter.setClipRect(r)
                self.img.paint(painter, self.boundingRect(), elem + '-bar')
            except:
                pass

    def setImage(self, img):
        if self.isVisible():
            self.saveFadeStart()
        if isinstance(img, QPixmap):
            self.imgPath = ''
            self.img = img
        else:
            self.imgPath = img
            if self.imgPath.indexOf('.svg') > -1:
                self.img = Plasma.Svg(self)
                self.img.setImagePath(self.imgPath)
            else:
                self.img = QPixmap(self.imgPath)
        self.scaledImg = QPixmap()
        if self.isVisible():
            self.startFade(Fader.Slow)
        self.setPreferredSize(QSizeF(self.imageSize()))

    def image(self):
        return self.imgPath

    def pixmap(self):
        if isinstance(self.img, QPixmap):
            return self.img
        elif isinstance(self.img, Plasma.Svg):
            return self.img.pixmap()
        return QPixmap()

    def setPrefix(self, prefix):
        if self.prefix == prefix:
            return
        if self.isVisible():
            self.saveFadeStart()
        self.prefix = prefix
        if self.isVisible():
            self.startFade(Fader.Fast)

    def setElement(self, element):
        if self.elementString == element:
            return
        if self.isVisible():
            self.saveFadeStart()
        self.elementString = element
        if self.isVisible():
            self.startFade(Fader.Fast)

    def element(self):
        return self.elementString

    def setAspectRatioMode(self, mode):
        self.aspectRatioMode = mode
        self.scaledImg = QPixmap()
        self.update()

    def svgElement(self):
        elem = self.prefix
        if self.elementString != '' and self.prefix != '':
            elem += '-'
        elem += self.elementString
        return elem

    def imageSize(self):
        if isinstance(self.img, QPixmap):
            return self.img.size()
        elif isinstance(self.img, Plasma.Svg):
            return self.img.elementSize(self.svgElement())

class Image(ImagePainter, QGraphicsWidget):
    def __init__(self, parent = None):
        QGraphicsWidget.__init__(self, parent)
        ImagePainter.__init__(self)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def mousePressEvent(self, event):
        event.accept()

    def mouseReleaseEvent(self, event):
        self.emit(SIGNAL('clicked()'))
