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
from copy import copy
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.plasma import Plasma
from wallpaperrenderer import WallpaperRenderer, SingleImageJob, BlendJob, EmptyJob
from helpers import *

class WallpaperCache(QObject):
    All = -sys.maxint - 1                             # id
    Operation, Dirty, Image, Data = range(4)         # id properties
    FromDisk, Blend, Combine, Manual = range(4)  # operations
    OperationId = 0
    Path, Color, Method = range(1, 4)                 # FromDisk operation
    Images, Amount = range(1, 3)                     # Blend operation
    Images = 1                                       # Combine operation
    imageOperations = [Blend, Combine]

    def __init__(self, wallpaper):
        QObject.__init__(self, wallpaper)
        self.cache = {}
        self.wallpaper = wallpaper
        self.rendering = False
        self._size = None
        self.currentPixmap = None
        self.currentPixmapId = -1
        self.dirtyTimer = QTimer(self)
        self.dirtyTimer.setInterval(0)
        self.dirtyTimer.setSingleShot(True)
        self.connect(self.dirtyTimer, SIGNAL('timeout()'), self.checkDirtyImages)
        self.renderer = WallpaperRenderer(self)
        self.connect(self.renderer, SIGNAL('renderCompleted(int, const QImage&)'), \
                     self.renderCompleted, Qt.QueuedConnection)

    def checkId(self, id):
        if id not in self.cache.keys():
            self.cache[id] = [[self.Manual], True, None, None]
            return False
        return True

    def initId(self, id, operation, data = None):
        self.checkId(id)
        self.cache[id][self.Operation] = operation
        self.cache[id][self.Dirty] = False
        self.cache[id][self.Data] = data
        self.cache[id][self.Image] = None

    def value(self, id, type):
        self.checkId(id)
        return self.cache[id][type]

    def setValue(self, ids, type, value):
        #print '### setValue', ids, type, value
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
        print '### setDirty', id
        r = self.setValue(id, self.Dirty, dirty)
        if dirty:
            for key in self.cache.keys():
                if self.operationParam(key, self.OperationId) in self.imageOperations and \
                    id in self.operationParam(key, self.Images):
                    print '   ### And setDirty', key
                    self.setDirty(key)
            self.dirtyTimer.start()
        return r

    def data(self, id):
        return self.value(id, self.Data)

    def setData(self, id, data):
        return self.setValue(id, self.Data, data)

    def pixmap(self, id):
        print '### pixmap', self.currentPixmapId, id
        if self.currentPixmapId != id:
            img = self.image(id)
            if img:
                self.currentPixmapId = id
                self.currentPixmap = QPixmap(img)
            else:
                if self.operationParam(id, self.OperationId) != self.Manual:
                    self.setDirty(id)
        return self.currentPixmap

    def image(self, id):
        image = self.value(id, self.Image)
        return image

    def setImage(self, id, image):
        print '### setImage', id, self.currentPixmapId, self._size
        if id == self.currentPixmapId:
            self.currentPixmapId = -1
        self.setDirty(id, False)
        return self.setValue(id, self.Image, image)

    def operation(self, id):
        return self.value(id, self.Operation)

    def setOperation(self, id, operation):
        return self.setValue(id, self.Operation, operation)

    def operationParam(self, id, param):
        self.checkId(id)
        return self.value(id, self.Operation)[param]

    def setOperationParam(self, id, param, value):
        #print '### setOperationParam', id
        if isinstance(id, int):
            ids = [id]
        else:
            ids = id
        r = False
        for i in ids:
            v = copy(self.value(i, self.Operation))
            v[param] = value
            r |= self.setValue(id, self.Operation, v)
        return r

    def size(self):
        return self._size

    def ratio(self):
        if self._size == None or self._size.isEmpty() or self._size.height() == 0:
            return 1.0
        else:
            return self._size.width() / float(self._size.height())

    def checkGeometry(self):
        print '### checkGeometry', self._size, self.wallpaper.boundingRect().size().toSize()
        if self._size != self.wallpaper.boundingRect().size().toSize():
            self._size = self.wallpaper.boundingRect().size().toSize()
            self.setDirty(self.All)
            return True
        return False

    def init(self):
        print '### init'
        self.currentPixmapId = -1
        self.checkGeometry()

    def checkImages(self, ids):
        for id in ids:
            if self.image(id) == None or self.dirty(id):
                #print '   ### dirty', id
                return False
        return True

    def _img(self, img):
        if isinstance(img, int):
            if self.image(img) == None or self.dirty(img):
                return self._job(img)
            else:
                return self.image(img)

        if isinstance(img, QImage):
            return img

        if os.path.isdir(img):
            package = Plasma.Package(img, \
                                     self.wallpaper.packageStructure(self.wallpaper.wallpaper))
            img = package.filePath('preferred')

        return U(img)

    def _job(self, cacheId):
        operation = self.cache[cacheId][self.Operation]
        operationId = operation[self.OperationId]

        if operation[self.OperationId] == self.FromDisk:
            job = SingleImageJob(cacheId, self._size, self._img(operation[self.Path]), \
                                 QColor(operation[self.Color]), operation[self.Method])

        elif operation[self.OperationId] == self.Blend:
            job = BlendJob(cacheId, self._size, self._img(operation[self.Images][0]), \
                           self._img(operation[self.Images][1]), operation[self.Amount])

        else:
            job = EmptyJob(cacheId, self._size)

        return job

    def doJob(self, cacheId):
        self.renderer.render(self._job(cacheId))

    def doOperation(self, operation):
        #print '### doOperation', self.rendering, operation[self.OperationId],
        if operation[self.OperationId] == self.Manual:
            self.setDirty(self.rendering, False)
            if self.image(self.rendering) == None:
                self.setImage(self.rendering, QImage())
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
                self.setDirty(self.rendering, False)
                job = SingleImageJob(self.rendering, self._size, operation[self.Color],
                                     operation[self.Method], path)
                self.renderer.render(job)
                return False
            else:
                #print '   ### Does not exist'
                self.setImage(self.rendering, QImage())
                return True

        elif operation[self.OperationId] == self.Blend:
            #print operation[self.Images]
            if self.checkImages(operation[self.Images]):
                #print '   ### transition'
                self.setImage(self.rendering,
                        Plasma.PaintUtils.transition(self.image(operation[self.Images][0]), \
                        self.image(operation[self.Images][1]), operation[self.Amount]))
            return True

        elif operation[self.OperationId] == self.Combine:
            #print operation[self.Images]
            if self.checkImages(operation[self.Images]):
                #print '   ### combine'
                image = QImage(self._size)
                p = QPainter(image)
                p.resetTransform()
                p.setCompositionMode(QPainter.CompositionMode_SourceOver)
                for id in operation[self.Images]:
                    pix = self.image(id)
                    if not pix.isNull():
                        #print '      ### combine draw', id
                        p.drawImage(0, 0, pix)
                p.end()
                self.setImage(self.rendering, image)
            return True

        return True

    def renderCompleted(self, jobId, image):
        print '### renderCompleted', jobId, self.rendering, self.dirty(self.rendering)
        if not self.dirty(jobId):
            self.setImage(jobId, image)
        self.rendering = False
        self.dirtyTimer.start()

    def checkDirtyImages(self):
        print '### checkDirtyImages', self.rendering
        if self.rendering:
            return
        if self._size == None:
            return

        for id in self.cache.keys():
            print '### ID', id, self.dirty(id)
            if self.dirty(id):
                self.setDirty(id, False)
                self.rendering = True
                self.doJob(id)
                print '   ### Waiting... ', id, self.dirty(id)
                return
        self.dirtyTimer.stop()
        print '### renderingsCompleted'
        self.emit(SIGNAL('renderingsCompleted()'))
