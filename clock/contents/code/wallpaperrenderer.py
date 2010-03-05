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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.plasma import Plasma

class WallpaperRenderer(QThread):
    def __init__(self, parent):
        QThread.__init__(self, parent)
        self.mutex = QMutex()
        self.condition = QWaitCondition()
        self.abort = False
        self.currentToken = 0

    def __dtor__(self):
        print 'WallpaperRenderer.__dtor__'
        try:
            self.mutex.lock()
            self.abort = True
            self.condition.wakeOne()
        finally:
            self.mutex.unlock()
        self.wait()

    def render(self, fileName, size, method, color):
        try:
            self.mutex.lock()
            self.fileName = fileName
            self.color = color
            self.method = method
            self.size = size
            self.restart = True
            self.currentToken += 1
            token = self.currentToken
        finally:
            self.mutex.unlock()

        if not self.isRunning():
            print 'WallpaperRenderer starting...'
            self.start()
        else:
            print 'WallpaperRenderer waking up...'
            self.condition.wakeOne()
        return token

    def run(self):
        print 'WallpaperRenderer.run'
        while True:
            try:
                self.mutex.lock()
                if not self.restart and not self.abort:
                    print 'WAIT'
                    self.condition.wait(self.mutex)
                if self.abort:
                    print 'ABORT'
                    return
                self.restart = False
                print 'cont'

                # load all parameters in nonshared variables
                token = self.currentToken
                fileName = self.fileName
                color = QColor(self.color)
                size = self.size
                ratio = float(self.size.width()) / self.size.height()
                method = self.method
            finally:
                self.mutex.unlock()

            print 'xx0'
            result = QImage(size, QImage.Format_ARGB32_Premultiplied)
            result.fill(color.rgba())

            if fileName.isEmpty() or not QFile.exists(fileName):
                print 'xxxxxxxxxx'
                self.emit(SIGNAL('renderCompleted(const QImage&)'), result)
                continue

            print 'xx1'
            pos = QPoint(0, 0)
            tiled = False
            scalable = fileName.endsWith(QLatin1String('svg')) or fileName.endsWith(QLatin1String('svgz'))
            scaledSize = QSize()
            img = QImage()

            # set image size
            imgSize = QSize()

            print 'xx'
            if scalable:
                # scalable: image can be of any size
                imgSize = size
            else:
                # otherwise, use the natural size of the loaded image
                img = QImage(fileName)
                imgSize = img.size()
                # print 'loaded with', imgSize, ratio

            print 'xx2'
            # if any of them is zero we may self.run into a div-by-zero below.
            if imgSize.width() < 1:
                imgSize.setWidth(1)

            if imgSize.height() < 1:
                imgSize.setHeight(1)

            print 'xx3'
            if ratio < 1:
                ratio = 1

            print 'xx4'
            # set self.render parameters according to resize mode
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

            # print token, scalable, scaledSize, imgSize
            if scalable:
                # tiling is ignored for scalable wallpapers
                svg = QSvgRenderer(fileName)
                if self.restart:
                    continue
                svg.self.render(p)
            else:
                if scaledSize != imgSize:
                    img = img.scaled(scaledSize, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)

                if self.restart:
                    continue

                if tiled:
                    for x in range(pos.x(), size.width(), scaledSize.width()):
                        for y in range(pos.y(), size.height(), scaledSize.height()):
                            p.drawImage(QPoint(x, y), img)
                            if self.restart:
                                continue
                else:
                    p.drawImage(pos, img)
            p.end()

            # signal we're done
            print 'DONE'
            self.emit(SIGNAL('renderCompleted(const QImage&)'), result)