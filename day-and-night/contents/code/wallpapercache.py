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
    All = -sys.maxint - 1                           # id
    Operation, Dirty, Pixmap, Data = range(4)       # id properties
    FromDisk, Transition = range(2)                 # operations
    OperationId = 0
    Path, Color, Method = range(1, 4)               # FromDisk operation
    Pixmaps, Amount = range(1, 3)                   # Transition operation

    def __init__(self, wallpaper):
        QObject.__init__(self, wallpaper)
        self.cache = {}
        self.wallpaper = wallpaper
        self.rendering = None
        self._size = None
        self.dirtyTimer = QTimer(self)
        self.dirtyTimer.setInterval(0)
        self.dirtyTimer.setSingleShot(True)
        self.connect(self.dirtyTimer, SIGNAL('timeout()'), self.checkDirtyPixmaps)

    def checkId(self, id):
        if id not in self.cache.keys():
            self.cache[id] = [None, True, None, None]

    def initId(self, id, operation, data = None):
        self.checkId(id)
        self.cache[id][self.Operation] = operation
        self.cache[id][self.Dirty] = False
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
        #print '### setDirty', id
        self.setValue(id, self.Dirty, True)
        for key in self.cache.keys():
            if self.cache[key][self.Operation][self.OperationId] == self.Transition and \
               id in self.cache[key][self.Operation][self.Pixmaps]:
                #print '   ### And setDirty', key
                self.cache[key][self.Dirty] = True
        self.dirtyTimer.start()

    def data(self, id):
        return self.value(id, self.Data)

    def setData(self, id, data):
        self.setValue(id, self.Data, data)

    def pixmap(self, id):
        pixmap = self.value(id, self.Pixmap)
        if pixmap == None:
            self.cache[id][self.Dirty] = True
            self.dirtyTimer.start()
        return pixmap

    def setPixmap(self, id, pixmap):
        self.setValue(id, self.Pixmap, pixmap)
        self.cache[id][self.Dirty] = False

    def operation(self, id):
        return self.value(id, self.Operation)

    def setOperation(self, id, operation):
        self.setValue(id, self.Operation, operation)
        self.setDirty(id)

    def operationParam(self, id, param):
        return self.value(id, self.Operation)[param]

    def setOperationParam(self, id, param, value):
        #print '### setOperationParam', id
        self.value(id, self.Operation)[param] = value
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

    def doOperation(self, operation):
        #print '### doOperation', self.rendering, operation[self.OperationId]
        if operation == None:
            self.cache[self.rendering][self.Dirty] = False
            return True

        elif operation[self.OperationId] == self.FromDisk:
            package = Plasma.Package(operation[self.Path], \
                                     self.wallpaper.packageStructure(self.wallpaper.wallpaper))
            path = package.filePath('preferred')
            if path.isEmpty():
                path = operation[self.Path]
            self.wallpaper.render(path, self._size, operation[self.Method], operation[self.Color])
            return False

        elif operation[self.OperationId] == self.Transition:
            pix1 = self.pixmap(operation[self.Pixmaps][0])
            pix2 = self.pixmap(operation[self.Pixmaps][1])
            if pix1 and not self.isDirty(operation[self.Pixmaps][0]) and \
               pix2 and not self.isDirty(operation[self.Pixmaps][1]):
                self.setPixmap(self.rendering,
                               Plasma.PaintUtils.transition(pix1, pix2, operation[self.Amount]))
            return True

        return True

    def renderCompleted(self, image):
        #print '### renderCompleted', self.rendering
        self.setPixmap(self.rendering, QPixmap(image))
        self.rendering = None
        self.dirtyTimer.start()

    def checkDirtyPixmaps(self):
        #print '### checkDirtyPixmaps', self.rendering
        if self.rendering != None:
            return
        if self._size == None:
            return

        while True:
            dirty = False
            for id in self.cache.keys():
                #print '### ID', id, self.cache[id][self.Dirty]
                if self.cache[id][self.Dirty]:
                    dirty = True
                    self.rendering = id
                    if not self.doOperation(self.cache[id][self.Operation]):
                        return
            if dirty == False: # Handling dirty might set other pixmaps dirty
                self.rendering = None
                break
        self.emit(SIGNAL('renderingsCompleted()'))
