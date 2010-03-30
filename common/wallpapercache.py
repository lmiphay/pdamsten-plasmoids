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
from wallpaperrenderer import WallpaperRenderer, SingleImageJob, BlendJob, DummyJob, StackJob
from helpers import *

class WallpaperCache(QObject):
    All = -sys.maxint - 1                                       # id
    Operation, Dirty, Image, Color, Method, Data = range(6)     # id properties
    SingleImage, Blend, Stack, Manual = range(4)                # operations
    OperationId = 0
    Images = 1                                                  # SingleImage operation
    Images, Amount = range(1, 3)                                # Blend operation
    Images = 1                                                  # Stack operation
    ImageOperations = [Blend, Stack]
    TypesThatCauseDirtines = [Operation, Color, Method]

    def __init__(self, wallpaper):
        QObject.__init__(self, wallpaper)
        self.cache = {}
        self.wallpaper = wallpaper
        self.rendering = 0
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
            self.cache[id] = [[self.Manual], True, None, Qt.black, \
                              Plasma.Wallpaper.ScaledResize, None]
            return False
        return True

    def initId(self, id, operation, color = Qt.black, \
               method = Plasma.Wallpaper.ScaledResize, data = None):
        self.checkId(id)
        self.cache[id][self.Operation] = operation
        self.cache[id][self.Color] = color
        self.cache[id][self.Method] = method
        self.cache[id][self.Dirty] = False
        self.cache[id][self.Data] = data
        self.cache[id][self.Image] = None

    def value(self, id, type):
        self.checkId(id)
        return self.cache[id][type]

    def setValue(self, ids, type, value):
        #if isinstance(ids, int) and ids != self.All:
        #    print '### setValue', ids, type, value, self.cache[ids][type]
        if isinstance(ids, int):
            if ids != self.All:
                self.checkId(ids)
                if self.cache[ids][type] != value:
                    self.cache[ids][type] = value
                    if type in self.TypesThatCauseDirtines:
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
        #print '### setDirty', id, dirty
        r = self.setValue(id, self.Dirty, dirty)
        if dirty:
            for key in self.cache.keys():
                if self.operationParam(key, self.OperationId) in self.ImageOperations and \
                    id in self.operationParam(key, self.Images):
                    #print '   ### And setDirty', key
                    self.setDirty(key)
            self.dirtyTimer.start()
        return r

    def data(self, id):
        return self.value(id, self.Data)

    def setData(self, id, data):
        return self.setValue(id, self.Data, data)

    def color(self, id):
        return self.value(id, self.Color)

    def setColor(self, id, color):
        return self.setValue(id, self.Color, color)

    def method(self, id):
        return self.value(id, self.Method)

    def setMethod(self, id, method):
        return self.setValue(id, self.Method, method)

    def pixmap(self, id):
        #print '### pixmap', self.currentPixmapId, id
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
        #print '### setImage', id, self.currentPixmapId, self._size
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
        #print '### checkGeometry', self._size, self.wallpaper.boundingRect().size().toSize()
        if self._size != self.wallpaper.boundingRect().size().toSize():
            self._size = self.wallpaper.boundingRect().size().toSize()
            self.setDirty(self.All)
            return True
        return False

    def init(self):
        #print '### init'
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

        if operation[self.OperationId] == self.SingleImage:
            job = SingleImageJob(cacheId, self._size, self._img(operation[self.Images]), \
                                 QColor(self.color(cacheId)), self.method(cacheId))

        elif operation[self.OperationId] == self.Blend:
            job = BlendJob(cacheId, self._size, self._img(operation[self.Images][0]), \
                           self._img(operation[self.Images][1]), operation[self.Amount],
                           QColor(self.color(cacheId)), self.method(cacheId))

        elif operation[self.OperationId] == self.Stack:
            job = StackJob(cacheId, self._size, [self._img(x) for x in operation[self.Images]], \
                           QColor(self.color(cacheId)), self.method(cacheId))

        else:
            job = DummyJob(cacheId, self._size)

        self.setDirty(cacheId, False)
        self.rendering += 1
        #print '++++++++++++++++', self.rendering
        return job

    def doJob(self, cacheId):
        self.renderer.render(self._job(cacheId))

    def renderCompleted(self, jobId, image):
        #print '### renderCompleted', jobId, self.rendering, self.dirty(jobId), image.size()
        #image.save('/home/damu/test%d.png' % jobId)
        if image.isNull():
            image = None
        if not self.dirty(jobId):
            self.setImage(jobId, image)
        self.rendering -= 1
        #print '----------------', self.rendering
        self.dirtyTimer.start()

    def checkDirtyImages(self):
        #print '### checkDirtyImages', self.rendering
        if self.rendering > 0:
            return
        if self._size == None:
            return

        for id in self.cache.keys():
            #print '### ID', id, self.dirty(id)
            if self.dirty(id):
                self.doJob(id)
                #print '   ### Waiting... ', id, self.dirty(id)
                return
        self.dirtyTimer.stop()
        #print '### renderingsCompleted'
        self.emit(SIGNAL('renderingsCompleted()'))
