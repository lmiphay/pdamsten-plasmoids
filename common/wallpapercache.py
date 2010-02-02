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

import sys, os
from PyQt4.QtCore import *
from PyKDE4.plasma import Plasma
from PyQt4.QtGui import *

class WallpaperCache(QObject):
    All = -sys.maxint - 1                             # id
    Operation, Dirty, Pixmap, Data = range(4)         # id properties
    FromDisk, Transition, Combine, Manual = range(4)  # operations
    OperationId = 0
    Path, Color, Method = range(1, 4)                 # FromDisk operation
    Pixmaps, Amount = range(1, 3)                     # Transition operation
    Pixmaps = 1                                       # Combine operation
    pixmapOperations = [Transition, Combine]

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
            self.cache[id] = [[self.Manual], True, None, None]

    def initId(self, id, operation, data = None):
        self.checkId(id)
        self.cache[id][self.Operation] = operation
        self.cache[id][self.Dirty] = False
        self.cache[id][self.Data] = data

    def value(self, id, type):
        self.checkId(id)
        return self.cache[id][type]

    def setValue(self, ids, type, value):
        if isinstance(ids, int):
            if ids != self.All:
                self.checkId(ids)
                if self.cache[ids][type] != value:
                    self.cache[ids][type] = value
                    if type == self.Operation:
                        self.setDirty(ids)
                    return True
                return False
            else:
                ids = self.cache.keys()
        r = False
        for id in ids:
            r |= self.setValue(id, type, value)
        return r

    def dirty(self, id):
        return self.value(id, self.Dirty)

    def setDirty(self, id, dirty = True):
        #print '### setDirty', id
        r = self.setValue(id, self.Dirty, dirty)
        if dirty:
            for key in self.cache.keys():
                if self.operationParam(key, self.OperationId) in self.pixmapOperations and \
                    id in self.operationParam(key, self.Pixmaps):
                    #print '   ### And setDirty', key
                    self.setDirty(key)
            self.dirtyTimer.start()
        return r

    def data(self, id):
        return self.value(id, self.Data)

    def setData(self, id, data):
        return self.setValue(id, self.Data, data)

    def pixmap(self, id):
        pixmap = self.value(id, self.Pixmap)
        if pixmap == None and self.operationParam(id, self.OperationId) != self.Manual:
            self.setDirty(id)
        return pixmap

    def setPixmap(self, id, pixmap):
        self.setDirty(id, False)
        return self.setValue(id, self.Pixmap, pixmap)

    def operation(self, id):
        return self.value(id, self.Operation)

    def setOperation(self, id, operation):
        return self.setValue(id, self.Operation, operation)

    def operationParam(self, id, param):
        self.checkId(id)
        return self.value(id, self.Operation)[param]

    def setOperationParam(self, id, param, value):
        #print '### setOperationParam', id
        v = self.value(id, self.Operation)
        v[param] = value
        return self.selValue(id, self.Operation, v)

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

    def checkPixmaps(self, ids):
        for id in ids:
            if self.pixmap(id) == None or self.dirty(id):
                #print '   ### dirty', id
                return False
        return True

    def doOperation(self, operation):
        #print '### doOperation', self.rendering, operation[self.OperationId],
        if operation[self.OperationId] == self.Manual:
            #print '*'
            self.setDirty(self.rendering, False)
            if self.pixmap(self.rendering) == None:
                self.setPixmap(self.rendering, QPixmap())
            return True

        elif operation[self.OperationId] == self.FromDisk:
            #print operation[self.Path]
            path = None
            if os.path.isdir(operation[self.Path]):
                package = Plasma.Package(operation[self.Path], \
                                     self.wallpaper.packageStructure(self.wallpaper.wallpaper))
                path = package.filePath('preferred')
            elif os.path.isfile(operation[self.Path]):
                path = operation[self.Path]
            if path:
                #print '   ### Rendering'
                self.wallpaper.render(path, self._size, operation[self.Method], \
                                      operation[self.Color])
                return False
            else:
                #print '   ### Does not exist'
                self.setPixmap(self.rendering, QPixmap())
                return True

        elif operation[self.OperationId] == self.Transition:
            #print operation[self.Pixmaps]
            if self.checkPixmaps(operation[self.Pixmaps]):
                #print '   ### transition'
                self.setPixmap(self.rendering,
                        Plasma.PaintUtils.transition(self.pixmap(operation[self.Pixmaps][0]), \
                        self.pixmap(operation[self.Pixmaps][1]), operation[self.Amount]))
            return True

        elif operation[self.OperationId] == self.Combine:
            #print operation[self.Pixmaps]
            if self.checkPixmaps(operation[self.Pixmaps]):
                #print '   ### combine'
                pixmap = QPixmap(self._size)
                p = QPainter(pixmap)
                p.resetTransform()
                p.setCompositionMode(QPainter.CompositionMode_SourceOver)
                for id in operation[self.Pixmaps]:
                    pix = self.pixmap(id)
                    if not pix.isNull():
                        #print '      ### combine draw', id
                        p.drawPixmap(0, 0, pix)
                p.end()
                self.setPixmap(self.rendering, pixmap)
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
        self.dirtyTimer.stop()
        self.emit(SIGNAL('renderingsCompleted()'))
