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

class WallpaperRenderer(QThread):
    def __init__(self, parent = None):
        QThread.__init__(self, parent)
        self.abort = False
        self.restart = False

    def __del__(self):
        # abort computation
        lock = QMutexLocker(self.mutex)
        self.abort = True
        self.condition.wakeOne()
        lock.unlock()
        self.wait()

    def setSize(self, size):
        lock = QMutexLocker(self.mutex)
        self.size = size

    def render(self, file, size, method, color):
        lock = QMutexLocker(self.mutex)
        self.file = file
        self.color = color
        self.method = method
        self.size = size
        self.restart = True
        self.currentToken += 1
        token = self.currentToken

        if not isRunning():
            self.start()
        else:
            self.condition.wakeOne()
        return token

    def run(self):
        file = QString()
        color = QColor()
        size = QSize()
        method = Wallpaper.ResizeMethod()

        while True: 
            lock = QMutexLocker(self.mutex)
            if not self.restart and not self.abort:
                self.condition.wait(self.mutex)
            if self.abort:
                return
            self.restart = False

            # load all parameters in nonshared variables
            token = self.currentToken
            file = self.file
            color = self.color
            size = self.size
            ratio = self.size.width() / qreal(self.size.height())
            method = self.method
            lock.unlock()

            result = QImage(size, QImage.Format_ARGB32_Premultiplied)
            result.fill(color.rgba())

            if file.isEmpty() or not QFile.exists(file):
                self.emit(SIGNAL('done()'), token, result, file, size, method, color)
                break

            pos = QPoint(0, 0)
            tiled = False
            scalable = file.endsWith(QLatin1String('svg')) or file.endsWith(QLatin1String('svgz'))
            scaledSize = QSize()
            img = QImage()

            # set image size
            imgSize = QSize()

            if scalable:
                # scalable: image can be of any size
                imgSize = size
            else:
                # otherwise, use the natural size of the loaded image
                img = QImage(file)
                imgSize = img.size()
                # print 'loaded with', imgSize, ratio

            # if any of them is zero we may self.run into a div-by-zero below.
            if imgSize.width() < 1:
                imgSize.setWidth(1)

            if imgSize.height() < 1:
                imgSize.setHeight(1)

            if ratio < 1:
                ratio = 1

            # set self.render parameters according to resize mode
            if method == Wallpaper.ScaledResize:
                scaledSize = size
            elif method == Wallpaper.CenteredResize:
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
                elif method == Wallpaper.MaxpectResize:
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

                elif method == Wallpaper.ScaledAndCroppedResize:
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

                elif method == Wallpaper.TiledResize:
                    scaledSize = imgSize
                    tiled = True

                elif method == Wallpaper.CenterTiledResize:
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
                svg = QSvgRenderer(file)
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

            # signal we're done
            self.emit(SIGNAL('done()'), token, result, file, size, method, color)
            break
