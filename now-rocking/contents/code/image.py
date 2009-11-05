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

from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from PyKDE4.plasma import Plasma
from fader import Fader

class ImagePainter(Fader):
    def __init__(self):
        Fader.__init__(self)
        self.img = QPixmap()
        self.cache = {}
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
            p = self.boundingRect().topLeft()
            s = self.boundingRect().size().toSize()
            pixmap = self.scaledPixmap(s.width(), s.height())
            p.setX(p.x() + ((s.width() - pixmap.width()) / 2.0))
            p.setY(p.y() + ((s.height() - pixmap.height()) / 2.0))
            painter.drawPixmap(p, pixmap)
        elif isinstance(self.img, Plasma.Svg):
            #print type(self), self.svgElement(), self.boundingRect(), self.imageSize()
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
        if not isinstance(img, QPixmap) and self.imgPath == img:
            return
        if self.isVisible():
            self.saveFadeStart()
        if isinstance(img, QPixmap):
            self.imgPath = ''
            self.img = img
        else:
            self.imgPath = img
            if self.imgPath.find('.svg') > -1:
                self.img = Plasma.Svg(self)
                self.img.setImagePath(self.imgPath)
            else:
                self.img = QPixmap(self.imgPath)
        self.cache = {}
        if self.isVisible():
            self.startFade(Fader.Slow)
        self.setPreferredSize(QSizeF(self.imageSize()))

    def image(self):
        return self.imgPath

    def scaledPixmap(self, w, h):
        key = '%dx%d' % (w, h)
        if key in self.cache:
            return self.cache[key]
        if isinstance(self.img, QPixmap):
            pixmap = self.img
        elif isinstance(self.img, Plasma.Svg):
            pixmap = self.img.pixmap()
        else:
            return QPixmap()
        #if pixmap.height() > 750:
        #    trans = Qt.FastTransformation
        #else:
        trans = Qt.SmoothTransformation
        self.cache[key] = pixmap.scaled(QSize(w, h), self.aspectRatioMode, trans)
        return self.cache[key]

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
        self.cache = {}
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
        if event.button() == Qt.LeftButton:
            event.accept()
        else:
            QGraphicsWidget.mousePressEvent(self, event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.emit(SIGNAL('clicked()'))
        else:
            QGraphicsWidget.mouseReleaseEvent(self, event)
