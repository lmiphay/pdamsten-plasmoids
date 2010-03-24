#!/bin/env python
# -*- coding: utf-8 -*-
#
#   Copyright (c) 2010 by Petri Damstén <damu@iki.fi>
#   Copyright (c) 2007 Paolo Capriotti <p.capriotti@gmail.com>
#   Copyright (c) 2009 Aaron Seigo <aseigo@kde.org>
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

# Converted from C++ WallpaperRenderThread to python by Petri Damstén

from copy import copy
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.plasma import Plasma

# TODO handle abort & restart better

class WallpaperRenderer(QThread):
    def __init__(self, parent):
        QThread.__init__(self, parent)
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.abort = False

    def __dtor__(self):
        #print 'WallpaperRenderer.__dtor__'
        try:
            self.mutex.lock()
            self.abort = True
            self.condition.wakeOne()
        finally:
            self.mutex.unlock()
        self.wait()

    def render(self, job):
        try:
            self.mutex.lock()
            self.job = job
            self.restart = True
        finally:
            self.mutex.unlock()

        if not self.isRunning():
            #print 'WallpaperRenderer starting...'
            self.start()
        else:
            #print 'WallpaperRenderer waking up...'
            self.condition.wakeOne()

    def run(self):
        #print 'WallpaperRenderer.run'
        self.setPriority(QThread.LowestPriority)
        while True:
            try:
                self.mutex.lock()
                if not self.restart and not self.abort:
                    #print 'WAIT'
                    self.condition.wait(self.mutex)
                if self.abort:
                    #print 'ABORT'
                    return
                self.restart = False

                job = copy(self.job)
            finally:
                self.mutex.unlock()

            self.emit(SIGNAL('renderCompleted(int, const QImage&)'), job.jobId, job.do())


class WallpaperJob():
    def __init__(self, jobId):
        self.jobId = jobId

    def do(self):
        pass

    def load(self, img, size = None, color = None, method = None):
        if isinstance(img, QImage):
            return img

        if isinstance(img, WallpaperJob):
            return img.do()

        if len(img) == 0 or not QFile.exists(img):
            image = QImage(size, QImage.Format_ARGB32_Premultiplied)
            image.fill(color.rgba())
        else:
            if img.endswith(u'svg') or img.endswith(u'svgz'):
                image = QImage(size, QImage.Format_ARGB32_Premultiplied)
                p = QPainter(image)
                svg = QSvgRenderer(fileName)
                svg.render(p)
            else:
                image = QImage(img)
        return image

    def scale(self, img, size, color, method):
        if img.size() == size:
            return img
        result = QImage(size, QImage.Format_ARGB32_Premultiplied)
        result.fill(color.rgba())

        pos = QPoint(0, 0)
        tiled = False
        scaledSize = QSize()
        ratio = float(size.width()) / size.height()

        # otherwise, use the natural size of the loaded image
        imgSize = img.size()

        # if any of them is zero we may run into a div-by-zero below.
        if imgSize.width() < 1:
            imgSize.setWidth(1)

        if imgSize.height() < 1:
            imgSize.setHeight(1)

        if ratio < 1:
            ratio = 1

        # set render parameters according to resize mode
        if method == Plasma.Wallpaper.ScaledResize:
            scaledSize = size

        elif method == Plasma.Wallpaper.CenteredResize:
            scaledSize = imgSize
            pos = QPoint((size.width() - scaledSize.width()) / 2,
                         (size.height() - scaledSize.height()) / 2)

            # If the picture is bigger than the screen, shrink it
            if (size.width() < imgSize.width()) and (imgSize.width() > imgSize.height()):
                width = size.width()
                height = width * scaledSize.height() / imgSize.width()
                scaledSize = QSize(width, height)
                pos = QPoint((size.width() - scaledSize.width()) / 2,
                             (size.height() - scaledSize.height()) / 2)
            elif size.height() < imgSize.height():
                height = size.height()
                width = height * imgSize.width() / imgSize.height()
                scaledSize = QSize(width, height)
                pos = QPoint((size.width() - scaledSize.width()) / 2,
                             (size.height() - scaledSize.height()) / 2)

        elif method == Plasma.Wallpaper.MaxpectResize:
            xratio = float(size.width()) / imgSize.width()
            yratio = float(size.height()) / imgSize.height()

            if xratio > yratio:
                height = size.height()
                width = height * imgSize.width() / imgSize.height()
                scaledSize = QSize(width, height)
            else:
                width = size.width()
                height = width * imgSize.height() / imgSize.width()
                scaledSize = QSize(width, height)

            pos = QPoint((size.width() - scaledSize.width()) / 2,
                         (size.height() - scaledSize.height()) / 2)

        elif method == Plasma.Wallpaper.ScaledAndCroppedResize:
            xratio = float(size.width()) / imgSize.width()
            yratio = float(size.height()) / imgSize.height()

            if xratio > yratio:
                width = size.width()
                height = width * imgSize.height() / imgSize.width()
                scaledSize = QSize(width, height)
            else:
                height = size.height()
                width = height * imgSize.width() / imgSize.height()
                scaledSize = QSize(width, height)

            pos = QPoint((size.width() - scaledSize.width()) / 2,
                         (size.height() - scaledSize.height()) / 2)

        elif method == Plasma.Wallpaper.TiledResize:
            scaledSize = imgSize
            tiled = True

        elif method == Plasma.Wallpaper.CenterTiledResize:
            scaledSize = imgSize
            pos = QPoint(-scaledSize.width() +
                         ((size.width() - scaledSize.width()) / 2) % scaledSize.width(),
                         -scaledSize.height() +
                         ((size.height() - scaledSize.height()) / 2) % scaledSize.height())
            tiled = True

        p = QPainter(result)

        if scaledSize != imgSize:
            img = img.scaled(scaledSize, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

        #if self.restart:
        #    return result

        if tiled:
            for x in range(pos.x(), size.width(), scaledSize.width()):
                for y in range(pos.y(), size.height(), scaledSize.height()):
                    p.drawImage(QPoint(x, y), img)
                    #if self.restart:
                    #    return result
        else:
            p.drawImage(pos, img)
        p.end()
        return result


class SingleImageJob(WallpaperJob):
    def __init__(self, jobId, size, color, method, img):
        WallpaperJob.__init__(self, jobId)
        self.img = img
        self.size = size
        self.color = color
        self.method = method

    def do(self):
        return self.scale(self.load(self.img, self.size, self.color, self.method),
                          self.size, self.color, self.method)


class BlendJob(WallpaperJob):
    def __init__(self, jobId, img1, img2, amount):
        WallpaperJob.__init__(self, jobId)
        self.img1 = img1
        self.img2 = img2
        self.amount = amount

    def do(self):
        if self.amount <= 0.0:
            return self.load(self.img1)
        if self.amount >= 1.0:
            return self.load(self.img2)

        image1 = QImage(self.load(self.img1))
        image2 = QImage(self.load(self.img2))

        color = QColor()
        color.setAlphaF(self.amount)

        p = QPainter()
        p.begin(image2)
        p.setCompositionMode(QPainter.CompositionMode_DestinationIn)
        p.fillRect(image2.rect(), color)
        p.end()

        p.begin(image1)
        p.setCompositionMode(QPainter.CompositionMode_Plus);
        p.drawImage(0, 0, image2)
        p.end()
        return image1
