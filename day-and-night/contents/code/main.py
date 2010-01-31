#   -*- coding: utf-8 -*-
#
#   Copyright (c) 2009-2010 by Petri Damstén <damu@iki.fi>
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
from PyQt4 import uic
from PyKDE4.plasma import Plasma
from PyKDE4.plasmascript import Wallpaper
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *
from PyKDE4.kio import *
from PyKDE4.knewstuff import *

from wallpapermodel import WallpaperModel
from backgrounddelegate import BackgroundDelegate
from wallpapercache import WallpaperCache


class DayAndNight(Wallpaper):
    UpdateInterval = 1.0 # minutes
    Day, Twilight, Night = range(3)
    DayAngle, NightAngle = (50.0 / 60.0, -6.0)

    def __init__(self, parent, args = None):
        Wallpaper.__init__(self, parent)
        self.usersWallpapers = None
        self.wallpaperModel = None
        self.elevation = None
        self.lastTimeOfDay = None
        self.newStuffDialog = None
        self.fileDialog = None
        self.widget = None
        self.source = ''
        self.ui = None
        self.cache = WallpaperCache(self)
        self.connect(self.cache, SIGNAL('renderingsCompleted()'), self.renderingsCompleted)

    def init(self, config):
        self.cache.init()

        method = Plasma.Wallpaper.ResizeMethod(config.readEntry('resizemethod', \
                Plasma.Wallpaper.ScaledResize).toInt()[0])
        dayColor = QColor(config.readEntry('wallpapercolor', QColor(56, 111, 150)))
        nightColor = QColor(config.readEntry('nightwallpapercolor', QColor(0, 0, 0)))
        dayPath = self.checkIfEmpty(config.readEntry('daywallpaper', '').toString())
        nightPath = self.checkIfEmpty(config.readEntry('nightwallpaper', '').toString())

        self.cache.initId(self.Day, [WallpaperCache.FromDisk, dayPath, dayColor, method])
        self.cache.initId(self.Night, [WallpaperCache.FromDisk, nightPath, nightColor, method])

        self.usersWallpapers = config.readEntry('userswallpapers', []).toStringList()
        self.longitude = config.readEntry('longitude', 100.0).toDouble()[0]
        self.latitude = config.readEntry('latitude', 100.0).toDouble()[0]
        if self.latitude > 90.0 or self.longitude > 90.0:
            engine = self.dataEngine('geolocation')
            engine.connectSource('location', self)
        else:
            self.longitudeLatitudeEditingFinished()

    def save(self, config):
        # For some reason QStrings must be converted to python strings before writing?
        config.writeEntry('resizemethod',
                int(self.cache.operationParam(self.Day, WallpaperCache.Method)))
        config.writeEntry('wallpapercolor', \
                self.cache.operationParam(self.Day, WallpaperCache.Color))
        config.writeEntry('nightwallpapercolor', \
                self.cache.operationParam(self.Night, WallpaperCache.Color))
        config.writeEntry('daywallpaper',
                unicode(self.cache.operationParam(self.Day, WallpaperCache.Path)))
        config.writeEntry('nightwallpaper',
                unicode(self.cache.operationParam(self.Night, WallpaperCache.Path)))
        config.writeEntry('userswallpapers', [unicode(x) for x in self.usersWallpapers])
        config.writeEntry('longitude', float(self.longitude))
        config.writeEntry('latitude', float(self.latitude))

    @pyqtSignature('dataUpdated(const QString&, const Plasma::DataEngine::Data&)')
    def dataUpdated(self, sourceName, data):
        if QString(u'Corrected Elevation') in data:
            self.elevation = data[QString(u'Corrected Elevation')]
            # DEBUG self.elevation = -3.0
            timeOfDay = self.timeOfDay()
            if timeOfDay == self.Twilight or timeOfDay != self.lastTimeOfDay:
                self.lastTimeOfDay = timeOfDay
                if timeOfDay == self.Twilight:
                    nightAngle = abs(self.NightAngle)
                    n = 1.0 - (self.elevation + nightAngle) / (nightAngle + self.DayAngle)
                    self.cache.setOperation(self.Twilight, \
                            [WallpaperCache.Transition, (self.Day, self.Night), n])
                else:
                    self.update(self.boundingRect())
        else:
            try:
                self.latitude = float(data[QString(u'latitude')])
                self.longitude = float(data[QString(u'longitude')])
            except:
                self.latitude = 0.0
                self.longitude = 0.0
                if self.ui:
                    self.ui.latitudeEdit.setText(str(self.latitude))
                    self.ui.longitudeEdit.setText(str(self.longitude))

                self.longitudeLatitudeEditingFinished()

    def checkIfEmpty(self, wallpaper):
        if wallpaper.isEmpty():
            wallpaper = Plasma.Theme.defaultTheme().wallpaperPath()
            index = wallpaper.indexOf('/contents/images/')
            if index > -1: # We have file from package -> get path to package
                wallpaper = wallpaper.left(index)
        return wallpaper

    def checkGeometry(self):
        if self.cache.checkGeometry() and self.wallpaperModel:
            self.wallpaperModel.setWallpaperSize(self.cache.size())

    def renderingsCompleted(self):
        self.update(self.boundingRect())

    def timeOfDay(self):
        if self.elevation:
            if self.elevation > self.DayAngle:
                return self.Day
            elif self.elevation > self.NightAngle:
                return self.Twilight
            else:
                return self.Night
        return None

    def paint(self, painter, exposedRect):
        self.checkGeometry()
        pixmap = None

        # get pixmap
        timeOfDay = self.timeOfDay()
        if timeOfDay == self.Twilight:
            pixmap = self.cache.pixmap(self.Twilight)
        if timeOfDay == self.Day or (timeOfDay == self.Twilight and pixmap == None):
            pixmap = self.cache.pixmap(self.Day)
        if timeOfDay == self.Night or (timeOfDay == self.Twilight and pixmap == None):
            pixmap = self.cache.pixmap(self.Night)

        # paint
        if pixmap:
            if painter.worldMatrix() == QMatrix():
                # draw the background untransformed when possible; (saves lots of per-pixel-math)
                painter.resetTransform()

            # blit the background (saves all the per-pixel-products that blending does)
            painter.setCompositionMode(QPainter.CompositionMode_Source)

            # for pixmaps we draw only the exposed part (untransformed since the
            # bitmapBackground already has the size of the viewport)
            painter.drawPixmap(exposedRect, pixmap,
                               exposedRect.translated(-self.boundingRect().topLeft()))
        else:
            painter.fillRect(exposedRect, self.cache.operationParam(self.Day, WallpaperCache.Color))

    # Url dropped
    #----------------------------------------------------------------------------------------------

    def urlDropped(self, url):
        if url.isLocalFile():
            self.setWallpaperPath(url.toLocalFile())
        else:
            wallpaperPath = KGlobal.dirs().locateLocal('wallpaper', url.fileName())
            if not wallpaperPath.isEmpty():
                job = KIO.file_copy(url, KUrl(wallpaperPath))
                self.connect(job, SIGNAL('result(KJob*)'), self.wallpaperRetrieved)

    def wallpaperRetrieved(self, job):
        self.setWallpaperPath(job.destUrl().toLocalFile())

    def setWallpaperPath(self, path):
        if self.elevation > (self.NightAngle + self.DayAngle) / 2.0:
            self.cache.setPath(self.Day, path)
        else:
            self.cache.setPath(self.Night, path)

        if not self.usersWallpapers.contains(path):
            self.usersWallpapers.append(path)

    # Configuration dialog
    #----------------------------------------------------------------------------------------------

    def createConfigurationInterface(self, parent):
        self.widget = QWidget(parent)
        self.connect(self.widget, SIGNAL('destroyed(QObject*)'), self.configWidgetDestroyed)
        self.ui = uic.loadUi(self.package().filePath('ui', 'config.ui'), self.widget)
        self.dayCombo = self.ui.dayCombo

        self.ui.positioningCombo.setCurrentIndex(
                self.cache.operationParam(self.Day, WallpaperCache.Method))
        self.connect(self.ui.positioningCombo, SIGNAL('currentIndexChanged(int)'), \
                     self.resizeChanged)

        self.ui.latitudeEdit.setText(str(self.latitude))
        self.connect(self.ui.latitudeEdit, SIGNAL('textChanged(const QString&)'), \
                     self.latitudeChanged)
        self.connect(self.ui.latitudeEdit, SIGNAL('editingFinished()'), \
                self.longitudeLatitudeEditingFinished)

        self.ui.longitudeEdit.setText(str(self.longitude))
        self.connect(self.ui.longitudeEdit, SIGNAL('textChanged(const QString&)'), \
                     self.longitudeChanged)
        self.connect(self.ui.longitudeEdit, SIGNAL('editingFinished()'), \
                self.longitudeLatitudeEditingFinished)

        self.wallpaperModel = WallpaperModel(self.cache.ratio(), self.wallpaper, self)
        self.wallpaperModel.setResizeMethod( \
                self.cache.operationParam(self.Day, WallpaperCache.Method))
        self.wallpaperModel.setWallpaperSize(self.cache.size())
        self.wallpaperModel.addBackgrounds(self.usersWallpapers)
        delegate = BackgroundDelegate(self.cache.ratio(), self)

        self.ui.dayColorButton.setColor(
                self.cache.operationParam(self.Day, WallpaperCache.Color))
        self.connect(self.ui.dayColorButton, SIGNAL('changed(const QColor&)'), \
                     self.dayColorChanged)

        self.ui.dayCombo.setModel(self.wallpaperModel)
        self.ui.dayCombo.setItemDelegate(delegate)
        self.connect(self.ui.dayCombo, SIGNAL('currentIndexChanged(int)'), \
                     self.dayWallpaperChanged)
        index = self.wallpaperModel.indexOf( \
                self.cache.operationParam(self.Day, WallpaperCache.Path))
        if index.isValid():
            self.ui.dayCombo.setCurrentIndex(index.row())

        self.ui.nightColorButton.setColor(
                self.cache.operationParam(self.Night, WallpaperCache.Color))
        self.connect(self.ui.nightColorButton, SIGNAL('changed(const QColor&)'), \
                     self.nightColorChanged)

        self.ui.nightCombo.setModel(self.wallpaperModel)
        self.ui.nightCombo.setItemDelegate(delegate)
        self.connect(self.ui.nightCombo, SIGNAL('currentIndexChanged(int)'), \
                     self.nightWallpaperChanged)
        index = self.wallpaperModel.indexOf(\
                self.cache.operationParam(self.Night, WallpaperCache.Path))
        if index.isValid():
            self.ui.nightCombo.setCurrentIndex(index.row())

        self.ui.openButton.setIcon(KIcon('document-open'));
        self.connect(self.ui.openButton, SIGNAL('clicked()'), self.showFileDialog)

        self.ui.getNewButton.setIcon(KIcon('get-hot-new-stuff'));
        self.connect(self.ui.getNewButton, SIGNAL('clicked()'), self.getNewWallpaper)
        return self.widget

    def configWidgetDestroyed(self):
        self.widget = None
        self.wallpaperModel = None
        self.ui = None

    def resizeChanged(self, index):
        self.settingsChanged(True)
        self.cache.setOperationParam(self.Day, WallpaperCache.Method, index)
        self.cache.setOperationParam(self.Night, WallpaperCache.Method, index)

    def dayColorChanged(self, color):
        self.settingsChanged(True)
        self.cache.setOperationParam(self.Day, WallpaperCache.Color, color)

    def nightColorChanged(self, color):
        self.settingsChanged(True)
        self.cache.setOperationParam(self.Night, WallpaperCache.Color, color)

    def latitudeChanged(self, txt):
        self.latitude = float(txt)

    def longitudeChanged(self, txt):
        self.longitude = float(txt)

    def longitudeLatitudeEditingFinished(self):
        engine = self.dataEngine('time')
        if self.source != '':
            engine.disconnectSource(self.source, self)
        self.source = 'Local|Solar|Latitude=%f|Longitude=%f' % (self.latitude, self.longitude)
        engine.connectSource(self.source, self, int(self.UpdateInterval * 60 * 1000))

    def dayWallpaperChanged(self, row):
        self.settingsChanged(True)
        path = self.wallpaperModel.data(self.wallpaperModel.index(row, 0), \
                                        BackgroundDelegate.PathRole).toString()
        self.cache.setOperationParam(self.Day, WallpaperCache.Path, path)

    def nightWallpaperChanged(self, row):
        self.settingsChanged(True)
        path = self.wallpaperModel.data(self.wallpaperModel.index(row, 0),
                                        BackgroundDelegate.PathRole).toString()
        self.cache.setOperationParam(self.Night, WallpaperCache.Path, path)

    # GHNS

    def getNewWallpaper(self):
        if not self.newStuffDialog:
            self.newStuffDialog = KNS3.DownloadDialog('wallpaper.knsrc', self.widget)
            self.connect(self.newStuffDialog, SIGNAL('accepted()'), self.newStuffFinished)
        self.newStuffDialog.show()

    def newStuffFinished(self):
        for entry in self.newStuffDialog.changedEntries():
            for wallpaper in entry.installedFiles():
                self.wallpaperModel.addBackground(wallpaper)

    # Open file

    def showFileDialog(self):
        if not self.fileDialog:
            self.fileDialog = KFileDialog(KUrl(), '*.png *.jpeg *.jpg *.xcf *.svg *.svgz', \
                    self.widget)
            self.fileDialog.setOperationMode(KFileDialog.Opening)
            self.fileDialog.setInlinePreviewShown(True)
            self.fileDialog.setCaption(i18n('Select Wallpaper Image File'))
            self.fileDialog.setModal(False)
            self.connect(self.fileDialog, SIGNAL('okClicked()'), self.wallpaperBrowseCompleted)
            self.connect(self.fileDialog, SIGNAL('destroyed(QObject*)'), self.fileDialogFinished)

        self.fileDialog.show()
        self.fileDialog.raise_()
        self.fileDialog.activateWindow()

    def fileDialogFinished(self):
        self.fileDialog = None

    def wallpaperBrowseCompleted(self):
        info = QFileInfo(self.fileDialog.selectedFile())
        # the full file path, so it isn't broken when dealing with symlinks
        wallpaper = info.canonicalFilePath()
        if wallpaper.isEmpty():
            return
        if not self.wallpaperModel.contains(wallpaper):
            self.wallpaperModel.addBackground(wallpaper)
        if not self.usersWallpapers.contains(wallpaper):
            self.usersWallpapers.append(wallpaper)


def CreateWallpaper(parent):
    return DayAndNight(parent)
