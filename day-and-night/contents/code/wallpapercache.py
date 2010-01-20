#   -*- coding: utf-8 -*-
#
#   Copyright (c) 2010 by Petri Damstén <damu@iki.fi>
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

import sys
from PyQt4.QtCore import *
from PyKDE4.plasma import Plasma
from PyQt4.QtGui import *

class WallpaperCache(QObject):
    Path, Dirty, Pixmap, Color, Method, Data = range(6)
    All = -sys.maxint - 1

    def __init__(self, wallpaper):
        QObject.__init__(self, wallpaper)
        self.cache = {}
        self.wallpaper = wallpaper
        self.rendering = None
        self._size = None

    def checkId(self, id):
        if id not in self.cache.keys():
            self.cache[id] = ['', True, None, QColor(Qt.black), Plasma.Wallpaper.ScaledResize, None]

    def initId(self, id, path, color, method, data = None):
        self.checkId(id)
        self.cache[id][self.Path] = path
        self.cache[id][self.Color] = color
        self.cache[id][self.Method] = method
        self.cache[id][self.Data] = data

    def setValue(self, id, type, value):
        if id != self.All:
            self.checkId(id)
            self.cache[id][type] = value
        else:
            for id in self.cache.keys():
                self.cache[id][type] = value

    def value(self, id, type):
        self.checkId(id)
        return self.cache[id][type]

    def isDirty(self, id):
        return self.value(id, self.Dirty)

    def setDirty(self, id):
        self.setValue(id, self.Dirty, True)
        self.render()

    def data(self, id):
        return self.value(id, self.Data)

    def setData(self, id, data):
        self.setValue(id, self.Data, data)

    def pixmap(self, id):
        pixmap = self.value(id, self.Pixmap)
        if pixmap == None:
            self.cache[id][self.Dirty] = True
            self.render()
        return pixmap

    def setPixmap(self, id, pixmap):
        self.setValue(id, self.Pixmap, pixmap)
        self.cache[id][self.Dirty] = False

    def path(self, id):
        return self.value(id, self.Path)

    def setPath(self, id, path):
        self.setValue(id, self.Path, path)
        self.setDirty(id)

    def color(self, id):
        return self.value(id, self.Color)

    def setColor(self, id, color):
        self.setValue(id, self.Color, color)
        self.setDirty(id)

    def method(self, id):
        return self.value(id, self.Method)

    def setMethod(self, id, method):
        self.setValue(id, self.Method, method)
        self.setDirty(id)

    def size(self):
        return self._size

    def ratio(self):
        if self._size == None or self._size.isEmpty() or self._size.height() == 0:
            return 1.0
        else:
            return self._size.width() / float(self._size.height())

    def checkGeometry(self):
        if self._size != self.wallpaper.boundingRect().size().toSize():
            self._size = self.wallpaper.boundingRect().size().toSize()
            self.setDirty(self.All)
            return True
        return False

    def init(self):
        self.disconnect(self.wallpaper.wallpaper, SIGNAL('renderCompleted(const QImage&)'), \
                        self.renderCompleted)
        self.connect(self.wallpaper.wallpaper, SIGNAL('renderCompleted(const QImage&)'), \
                     self.renderCompleted)
        self.checkGeometry()

    def render(self):
        if self.rendering != None:
            return
        if self._size == None:
            return
        for id in self.cache.keys():
            if self.cache[id][self.Dirty] and self.cache[id][self.Path] != '':
                self.rendering = id
                package = Plasma.Package(self.cache[id][self.Path], \
                                         self.wallpaper.packageStructure(self.wallpaper.wallpaper))
                path = package.filePath('preferred')
                if path.isEmpty():
                    path = self.cache[id][self.Path]
                self.wallpaper.render(path, self._size, self.cache[id][self.Method], \
                                      self.cache[id][self.Color])
                return
        self.emit(SIGNAL('renderingsCompleted()'))

    def renderCompleted(self, image):
        self.cache[self.rendering][self.Dirty] = False
        self.cache[self.rendering][self.Pixmap] = QPixmap(image)
        self.rendering = None
        self.render()
