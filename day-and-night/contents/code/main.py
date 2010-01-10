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
from PyKDE4.kio import *
from PyKDE4.knewstuff import *

from backgroundlistmodel import BackgroundListModel
from backgrounddelegate import BackgroundDelegate

class DayAndNight(Wallpaper):
    UpdateInterval = 1.0 # minutes
    NoRendering, Day, Twilight, Night = (0, 1, 2, 4)
    DayAngle, NightAngle = (50.0 / 60.0, -6.0)

    def __init__(self, parent, args = None):
        Wallpaper.__init__(self, parent)
        self.firstPaint = True
        self.dayPixmap = None
        self.nightPixmap = None
        self.method = None
        self.color = None
        self.dayWallpaper = None
        self.nightWallpaper = None
        self.usersWallpapers = None
        self.wallpaperModel = None
        self.elevation = None
        self.rendering = self.NoRendering
        self.lastTimeOfDay = None
        self.newStuffDialog = None
        self.fileDialog = None
        self.widget = None
        self.source = ''

    def init(self, config):
        print '### init',
        self.connect(self, SIGNAL('urlDropped(KUrl)'), self.fileDropped)

        self.checkGeometry()
        print self.size

        self.method = Plasma.Wallpaper.ResizeMethod(config.readEntry('resizemethod', \
                Plasma.Wallpaper.ScaledResize).toInt()[0])
        self.color = QColor(config.readEntry('wallpapercolor', QColor(56, 111, 150)))
        self.dayWallpaper = self.checkIfEmpty(config.readEntry('daywallpaper', \
                '').toString())
        self.nightWallpaper = self.checkIfEmpty(config.readEntry('nightwallpaper', \
                '').toString())
        self.usersWallpapers = config.readEntry('userswallpapers', []).toStringList()
        self.longitude = config.readEntry('longitude', 100.0).toDouble()[0]
        self.latitude = config.readEntry('latitude', 100.0).toDouble()[0]
        if self.latitude > 90.0 or self.longitude > 90.0:
            engine = self.dataEngine('geolocation')
            engine.connectSource('location', self)
        else:
            self.longitudeLatitudeEditingFinished()

    def save(self, config):
        print '### save'
        # For some reason QStrings must be converted to python strings before writing?
        config.writeEntry('resizemethod', int(self.method))
        config.writeEntry('wallpapercolor', self.color)
        config.writeEntry('daywallpaper', unicode(self.dayWallpaper))
        config.writeEntry('nightwallpaper', unicode(self.nightWallpaper))
        config.writeEntry('userswallpapers', [unicode(x) for x in self.usersWallpapers])
        config.writeEntry('longitude', float(self.longitude))
        config.writeEntry('latitude', float(self.latitude))

    @pyqtSignature('dataUpdated(const QString&, const Plasma::DataEngine::Data&)')
    def dataUpdated(self, sourceName, data):
        print '### dataUpdated',
        if QString(u'Corrected Elevation') in data:
            self.elevation = data[QString(u'Corrected Elevation')]
            print self.elevation
            # DEBUG self.elevation = -3.0
            timeOfDay = self.timeOfDay()
            if timeOfDay == self.Twilight or timeOfDay != self.lastTimeOfDay:
                self.lastTimeOfDay = timeOfDay
                self.update(self.boundingRect())
        else:
            try:
                print data[QString(u'latitude')], data[QString(u'longitude')]
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
        self.size = self.boundingRect().size().toSize()
        if self.wallpaperModel:
            self.wallpaperModel.setWallpaperSize(self.size)

    def timeOfDay(self):
        if self.elevation > self.DayAngle:
            return self.Day
        elif self.elevation > self.NightAngle:
            return self.Twilight
        else:
            return self.Night

    def paint(self, painter, exposedRect):
        print '### paint'
        day = False
        night = False
        pixmap = None

        if self.elevation != None:
            timeOfDay = self.timeOfDay()
            if timeOfDay == self.Day:
                if self.dayPixmap:
                    pixmap = self.dayPixmap
                else:
                    day = True
            elif timeOfDay == self.Twilight:
                if self.nightPixmap and self.dayPixmap:
                    nightAngle = abs(self.NightAngle)
                    n = (self.elevation + nightAngle) / (nightAngle + self.DayAngle)
                    pixmap = Plasma.PaintUtils.transition(self.nightPixmap, self.dayPixmap, n)
                else:
                    if not self.nightPixmap:
                        night = True
                    if not self.dayPixmap:
                        day = True
            else: # Night
                if self.nightPixmap:
                    pixmap = self.nightPixmap
                else:
                    night = True

        if day or night or not self.elevation:
            if self.firstPaint:
                painter.fillRect(exposedRect, self.color)
            if day and not self.rendering & self.Day:
                self.rendering |= self.Day
                self.renderWallpaper(self.dayWallpaper)
            if night and not self.rendering & self.Night:
                self.rendering |= self.Night
                if not day:
                    self.renderWallpaper(self.nightWallpaper)
        else:
            if painter.worldMatrix() == QMatrix():
                # draw the background untransformed when possible; (saves lots of per-pixel-math)
                painter.resetTransform()

            # blit the background (saves all the per-pixel-products that blending does)
            painter.setCompositionMode(QPainter.CompositionMode_Source)

            # for pixmaps we draw only the exposed part (untransformed since the
            # bitmapBackground already has the size of the viewport)
            painter.drawPixmap(exposedRect, pixmap,
                            exposedRect.translated(-self.boundingRect().topLeft()))
        self.firstPaint = False

    def renderWallpaper(self, wallpaper):
        if wallpaper.isEmpty():
            return
        if self.size.isEmpty():
            return

        b = Plasma.Package(wallpaper, self.packageStructure(self.wallpaper))
        img = b.filePath('preferred')

        if img.isEmpty():
            img = wallpaper
        self.render(img, self.size, self.method, self.color)

    def fileDropped(self, url):
        # TODO TEST
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
            self.renderWallpaper(self.nightWallpaper)
        elif self.rendering & self.Day:
            self.renderWallpaper(self.dayWallpaper)
        else:
            self.update(self.boundingRect())

    def createConfigurationInterface(self, parent):
        print '### createConfigurationInterface '
        self.widget = QWidget(parent)
        self.connect(self.widget, SIGNAL('destroyed(QObject*)'), self.configWidgetDestroyed)
        self.ui = uic.loadUi(self.package().filePath('ui', 'config.ui'), self.widget)
        self.dayCombo = self.ui.dayCombo

        self.ui.positioningCombo.setCurrentIndex(self.method)
        self.connect(self.ui.positioningCombo, SIGNAL('currentIndexChanged(int)'), self.resizeChanged)

        self.ui.colorButton.setColor(self.color)
        self.connect(self.ui.colorButton, SIGNAL('changed(const QColor&)'), self.colorChanged)

        self.ui.latitudeEdit.setText(str(self.latitude))
        self.connect(self.ui.latitudeEdit, SIGNAL('textChanged(const QString&)'), self.latitudeChanged)
        self.connect(self.ui.latitudeEdit, SIGNAL('editingFinished()'), \
                self.longitudeLatitudeEditingFinished)

        self.ui.longitudeEdit.setText(str(self.longitude))
        self.connect(self.ui.longitudeEdit, SIGNAL('textChanged(const QString&)'), self.longitudeChanged)
        self.connect(self.ui.longitudeEdit, SIGNAL('editingFinished()'), \
                self.longitudeLatitudeEditingFinished)

        if self.size.isEmpty():
            ratio = 1.0
        else:
            ratio = self.size.width() / float(self.size.height())

        self.wallpaperModel = BackgroundListModel(ratio, self.wallpaper, self)
        self.wallpaperModel.setResizeMethod(self.method)
        self.wallpaperModel.setWallpaperSize(self.size)
        self.wallpaperModel.reload(self.usersWallpapers)
        delegate = BackgroundDelegate(ratio, self)

        self.ui.dayCombo.setModel(self.wallpaperModel)
        self.ui.dayCombo.setItemDelegate(delegate)
        index = self.wallpaperModel.indexOf(self.dayWallpaper)
        if index.isValid():
            self.ui.dayCombo.setCurrentIndex(index.row())
        self.connect(self.ui.dayCombo, SIGNAL('currentIndexChanged(int)'), self.dayWallpaperChanged)

        self.ui.nightCombo.setModel(self.wallpaperModel)
        self.ui.nightCombo.setItemDelegate(delegate)
        index = self.wallpaperModel.indexOf(self.nightWallpaper)
        if index.isValid():
            self.ui.nightCombo.setCurrentIndex(index.row())
        self.connect(self.ui.nightCombo, SIGNAL('currentIndexChanged(int)'), self.nightWallpaperChanged)

        self.ui.openButton.setIcon(KIcon('document-open'));
        self.connect(self.ui.openButton, SIGNAL('clicked()'), self.showFileDialog)

        self.ui.getNewButton.setIcon(KIcon('get-hot-new-stuff'));
        self.connect(self.ui.getNewButton, SIGNAL('clicked()'), self.getNewWallpaper)

        return self.widget

    def fullUpdate(self):
        self.settingsChanged(True)
        self.dayPixmap = None
        self.nightPixmap = None
        self.update(self.boundingRect())

    def configWidgetDestroyed(self):
        self.widget = None
        self.wallpaperModel = None
        self.ui = None

    def resizeChanged(self, index):
        self.method = index
        self.fullUpdate()

    def colorChanged(self, color):
        self.color = color
        self.fullUpdate()

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
        self.dayWallpaper = self.wallpaperModel.data(self.wallpaperModel.index(row, 0), \
                BackgroundDelegate.PathRole).toString()
        self.settingsChanged(True)
        self.dayPixmap = None
        if self.timeOfDay() != self.Night:
            self.update(self.boundingRect())

    def nightWallpaperChanged(self, row):
        self.nightWallpaper = self.wallpaperModel.data(self.wallpaperModel.index(row, 0), \
                BackgroundDelegate.PathRole).toString()
        self.settingsChanged(True)
        self.nightPixmap = None
        if self.timeOfDay() != self.Day:
            self.update(self.boundingRect())

    def getNewWallpaper(self):
        # TODO not yet in pykde4 bindings
        if not self.newStuffDialog:
            self.newStuffDialog = KNS3.DownloadDialog('wallpaper.knsrc', self.widget)
            self.connect(self.newStuffDialog, SIGNAL('accepted()'), self.newStuffFinished)
        self.newStuffDialog.show()

    def newStuffFinished(self):
        if self.newStuffDialog.changedEntries().size() > 0:
            self.wallpaperModel.reload()

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
