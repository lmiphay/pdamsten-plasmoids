#   -*- coding: utf-8 -*-
#
#   Copyright (c) 2009 by Petri Damstén <damu@iki.fi>
#   Copyright (c) 2007 by Paolo Capriotti <p.capriotti@gmail.com>
#   Copyright (c) 2007 by Aaron Seigo <aseigo@kde.org>
#   Copyright (c) 2008 by Alexis Ménard <darktears31@gmail.com>
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

# Some parts of the code are converted to python from C++ Image wallpaper plugin (GPLv2+)

import os, sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.phonon import *
from PyQt4 import uic
from PyKDE4.plasma import Plasma
from PyKDE4.plasmascript import Wallpaper
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *

from backgroundlistmodel import BackgroundListModel
from backgrounddelegate import BackgroundDelegate

class DayAndNight(Wallpaper):
    NoRendering, Day, Twilight, Night = (0, 1, 2, 4)

    def __init__(self, parent, args = None):
        Wallpaper.__init__(self, parent)
        self.dayPixmap = None
        self.nightPixmap = None
        self.method = None
        self.color = None
        self.dayWallpaper = None
        self.nightWallpaper = None
        self.usersWallpapers = None
        self.dayModel = None
        self.nightModel = None
        self.elevation = None
        self.rendering = self.NoRendering
        self.lastTimeOfDay = None

    def init(self, config):
        print '### init',
        self.connect(self, SIGNAL('urlDropped(KUrl)'), self.fileDropped)

        self.checkGeometry()
        print self.size

        self.method = Plasma.Wallpaper.ResizeMethod(config.readEntry('resizemethod', \
                Plasma.Wallpaper.ScaledResize).toInt()[0])
        self.color = QColor(config.readEntry('wallpapercolor', QColor(56, 111, 150)))
        self.dayWallpaper = self.checkIfEmpty(config.readEntry('daywallpaper', \
                QString()).toString())
        self.nightWallpaper = self.checkIfEmpty(config.readEntry('nightwallpaper', \
                QString()).toString())
        self.usersWallpapers = config.readEntry("userswallpapers", QStringList()).toStringList()
        self.longitude = config.readEntry("longitude", 0.0).toDouble()[0]
        self.latitude = config.readEntry("latitude", 0.0).toDouble()[0]
        self.dataEngine('time').connectSource('Local|Solar|Latitude=%f|Longitude=%f' % \
                (self.latitude, self.longitude), self, 5 * 60 * 1000)

    def save(self, config):
        print '### save'
        config.writeEntry('resizemethod', self.method)
        config.writeEntry('wallpapercolor', self.color)
        config.writeEntry('daywallpaper',self.dayWallpaper)
        config.writeEntry('nightwallpaper',self.nightWallpaper)
        config.writeEntry("userswallpapers", self.usersWallpapers)
        config.writeEntry("longitude", self.longitude)
        config.writeEntry("latitude", self.latitude)

    @pyqtSignature('dataUpdated(const QString&, const Plasma::DataEngine::Data&)')
    def dataUpdated(self, sourceName, data):
        print '### dataUpdated',
        self.elevation = data[QString(u'Corrected Elevation')]
        print self.elevation
        timeOfDay = self.timeOfDay()
        if timeOfDay != self.lastTimeOfDay:
            self.lastTimeOfDay = timeOfDay
            self.update(self.boundingRect())

    def checkIfEmpty(self, wallpaper):
        if wallpaper.isEmpty():
            wallpaper = Plasma.Theme.defaultTheme().wallpaperPath()
            index = wallpaper.indexOf('/contents/images/')
            if index > -1: # We have file from package -> get path to package
                wallpaper = wallpaper.left(index)
        return wallpaper

    def checkGeometry(self):
        self.size = self.boundingRect().size().toSize()
        if self.dayModel:
            self.dayModel.setWallpaperSize(self.size)
        if self.nightModel:
            self.dayModel.setWallpaperSize(self.size)

    def timeOfDay(self):
        if self.elevation > 5.0 / 6.0:
            return self.Day
        elif self.elevation > -6.0:
            return self.Twilight
        else:
            return self.Night

    def paint(self, painter, exposedRect):
        print '### paint'
        day = False
        night = False

        if self.elevation:
            timeOfDay = self.timeOfDay()
            if timeOfDay == self.Day:
                if self.dayPixmap:
                    self.paintPixmap(painter, exposedRect, self.dayPixmap)
                else:
                    day = True
            elif timeOfDay == self.Twilight:
                if self.nightPixmap and self.dayPixmap:
                    self.paintPixmap(painter, exposedRect, self.dayPixmap)
                    # TODO faded night
                else:
                    if not self.nightPixmap:
                        night = True
                    if not self.dayPixmap:
                        day = True
            else: # Night
                if self.nightPixmap:
                    self.paintPixmap(painter, exposedRect, self.nightPixmap)
                else:
                    night = True

        if day or night or not self.elevation:
            painter.fillRect(exposedRect, self.color)
            if day and not self.rendering & self.Day:
                self.rendering |= self.Day
                self.renderWallpaper(self.dayWallpaper)
            if night and not self.rendering & self.Night:
                self.rendering |= self.Night
                if not day:
                    self.renderWallpaper(self.nightWallpaper)

    def paintPixmap(self, painter, exposedRect, pixmap):
        if painter.worldMatrix() == QMatrix():
            # draw the background untransformed when possible; (saves lots of per-pixel-math)
            painter.resetTransform()

        # blit the background (saves all the per-pixel-products that blending does)
        painter.setCompositionMode(QPainter.CompositionMode_Source)

        # for pixmaps we draw only the exposed part (untransformed since the
        # bitmapBackground already has the size of the viewport)
        painter.drawPixmap(exposedRect, pixmap,
                           exposedRect.translated(-self.boundingRect().topLeft()))

    def renderWallpaper(self, wallpaper):
        if wallpaper.isEmpty():
            return
        if self.size.isEmpty():
            return

        b = Plasma.Package(wallpaper, self.packageStructure(self.wallpaper))
        img = b.filePath('preferred')

        if img.isEmpty():
            img = wallpaper
        print img, self.rendering
        self.render(img, self.size, self.method, self.color)

    def fileDropped(self, url):
        # TODO TEST
        if url.isLocalFile():
            self.setWallpaperPath(url.toLocalFile())
        else:
            wallpaperPath = KGlobal.dirs().locateLocal("wallpaper", url.fileName())
            if not wallpaperPath.isEmpty():
                job = KIO.file_copy(url, KUrl(wallpaperPath))
                self.connect(job, SIGNAL('result(KJob*)'), self.wallpaperRetrieved)

    def wallpaperRetrieved(self, job):
        self.setWallpaperPath(job.destUrl().toLocalFile())

    def setWallpaperPath(self, path):
        if self.elevation > -3.0:
            self.dayWallpaper = path
            self.dayPixmap = None
        else:
            self.nightWallpaper = path
            self.nightPixmap = None
        self.update(self.boundingRect())

        if self.usersWallpapers.contains(path):
            self.usersWallpapers.append(path)

    def renderCompleted(self, image):
        print '### renderCompleted', image.size(), self.rendering
        if self.rendering & self.Day:
            self.dayPixmap = QPixmap(image)
            self.rendering &= ~self.Day
        elif self.rendering & self.Night:
            self.nightPixmap = QPixmap(image)
            self.rendering &= ~self.Night

        if self.rendering & self.Night:
            self.render(self.nightWallpaper, self.size, self.method, self.color)
        elif self.rendering & self.Day:
            self.render(self.dayWallpaper, self.size, self.method, self.color)
        else:
            self.update(self.boundingRect())

    def createConfigurationInterface(self, parent):
        print '### createConfigurationInterface '
        self.currentColor = self.color
        widget = QWidget(parent)
        ui = uic.loadUi(self.package().filePath('ui', 'config.ui'), widget)
        ui.positioningCombo.setCurrentIndex(self.method)

        model = BackgroundListModel(4/3, self.wallpaper, self) # TODO
        ui.dayCombo.setModel(model)
        model.setResizeMethod(self.method)
        model.setWallpaperSize(self.size) # TODO
        model.reload([]) # TODO
        delegate = BackgroundDelegate(4/3, self)
        ui.dayCombo.setItemDelegate(delegate)

        model = BackgroundListModel(4/3, self.wallpaper, self)
        ui.nightCombo.setModel(model)
        model.setResizeMethod(self.method)
        model.setWallpaperSize(self.size) # TODO
        model.reload([]) # TODO
        delegate = BackgroundDelegate(4/3, self)
        ui.nightCombo.setItemDelegate(delegate)

        self.connect(ui.positioningCombo, SIGNAL('currentIndexChanged(int)'), self.resizeChanged)
        return widget

    def resizeChanged(self, index):
        print '### resizeChanged'
        self.method = index
        self.settingsChanged(True)
        self.render(self.image, self.size, self.method, self.color)


def CreateWallpaper(parent):
    return DayAndNight(parent)

