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

from PyQt4.QtCore import *
from PyKDE4.plasma import Plasma
from PyQt4.QtGui import *

class WallpaperCache(QObject):
    Path, Dirty, Pixmap, Data = range(4)

    def __init__(self, wallpaper):
        QObject.__init__(self, wallpaper)
        self.cache = {}
        self.wallpaper = wallpaper
        self.rendering = None
        self._size = None
        self._method = None
        self._color = None

    def checkId(self, id):
        if id not in self.cache.keys():
            self.cache[id] = ['', True, None, None]

    def isDirty(self, id):
        self.checkId(id)
        return self.cache[id][self.Dirty]

    def setDirty(self, id):
        self.checkId(id)
        self.cache[id][self.Dirty] = True
        self.render()

    def setAllDirty(self):
        for id in self.cache.keys():
            if self.cache[id][self.Pixmap]:
                self.cache[id][self.Dirty] = True
        self.render()

    def data(self, id):
        self.checkId(id)
        return self.cache[id][self.Data]

    def setData(self, id, data):
        self.checkId(id)
        self.cache[id][self.Data] = data

    def pixmap(self, id):
        self.checkId(id)
        pixmap = self.cache[id][self.Pixmap]
        if pixmap == None:
            self.cache[id][self.Dirty] = True
            self.render()
        return pixmap

    def setPixmap(self, id, pixmap):
        self.checkId(id)
        self.cache[id][self.Pixmap] = pixmap
        self.cache[id][self.Dirty] = False

    def setPath(self, id, path, preAdd = False):
        self.checkId(id)
        self.cache[id][self.Path] = path
        if preAdd:
            self.cache[id][self.Dirty] = False
        else:
            self.cache[id][self.Dirty] = True
            self.render()

    def path(self, id):
        self.checkId(id)
        return self.cache[id][self.Path]

    def color(self):
        return self._color

    def setColor(self, color):
        self._color = color
        self.setAllDirty()

    def method(self):
        return self._method

    def setMethod(self, method):
        self._method = method
        self.setAllDirty()

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
            self.setAllDirty()
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
        if self._size == None or self._method == None or self._color == None:
            return
        for id in self.cache.keys():
            if self.cache[id][self.Dirty] and self.cache[id][self.Path] != '':
                self.rendering = id
                package = Plasma.Package(self.cache[id][self.Path], \
                                         self.wallpaper.packageStructure(self.wallpaper.wallpaper))
                path = package.filePath('preferred')
                if path.isEmpty():
                    path = self.cache[id][self.Path]
                self.wallpaper.render(path, self._size, self._method, self._color)
                return
        self.emit(SIGNAL('renderingsCompleted()'))

    def renderCompleted(self, image):
        self.cache[self.rendering][self.Dirty] = False
        self.cache[self.rendering][self.Pixmap] = QPixmap(image)
        self.rendering = None
        self.render()
