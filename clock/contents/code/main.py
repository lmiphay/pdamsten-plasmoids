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

from wallpaperclockmodel import WallpaperClockModel
from backgrounddelegate import BackgroundDelegate
from wallpapercache import WallpaperCache
from clockpackage import ClockPackage
from helpers import *


class Clock(Wallpaper):
    UpdateInterval = 1.0 # minutes
    Current, Next, Background, BackgroundHour, \
            Zodiac, Moon, Month, WeekDay, Day, Hour, Minute, AmPm  = range(12)

    def __init__(self, parent, args = None):
        Wallpaper.__init__(self, parent)
        self.usersWallpapers = None
        self.wallpaperModel = None
        self.newStuffDialog = None
        self.fileDialog = None
        self.widget = None
        self.source = ''
        self.cache = WallpaperCache(self)
        self.connect(self.cache, SIGNAL('renderingsCompleted()'), self.renderingsCompleted)

    def init(self, config):
        print '### init'
        self.cache.init()

        self.method = Plasma.Wallpaper.ResizeMethod(config.readEntry('resizemethod', \
                Plasma.Wallpaper.ScaledResize).toInt()[0])
        self.color = QColor(config.readEntry('wallpapercolor', QColor(56, 111, 150)))
        self.package = ClockPackage(self,
                self.checkIfEmpty(config.readEntry('clockwallpaper', '').toString()))
        self.cache.initId(self.Current, [WallpaperCache.Manual])
        self.cache.initId(self.Next, [WallpaperCache.Combine, [self.BackgroundHour, self.Minute]])
        self.cache.initId(self.BackgroundHour, [WallpaperCache.Combine, \
                [self.Background, self.Zodiac, self.Moon, self.Month, self.WeekDay, \
                 self.Day, self.Hour, self.AmPm]])
        engine = self.dataEngine('time')
        engine.connectSource(self.source, self, int(self.UpdateInterval * 60 * 1000))

    def save(self, config):
        print '### save'
        # For some reason QStrings must be converted to python strings before writing?
        config.writeEntry('resizemethod', self.method)
        config.writeEntry('wallpapercolor', self.color)
        config.writeEntry('clockwallpaper', self.package.path())

    @pyqtSignature('dataUpdated(const QString&, const Plasma::DataEngine::Data&)')
    def dataUpdated(self, sourceName, data):
        print '### dataUpdated'
        if self.cache.pixmap(self.Next) != None:
            self.cache.setPixmap(self.Current, self.cache.pixmap(self.Next))
            self.update(self.boundingRect())

        now = QDateTime(data[QString('Date')], data[QString('Time')])
        next = now.addSecs(60)
        self.updateImages(now, next)

    def updateImages(self, now, next):
        path = self.package.path()
        self.cache.setOperation(self.Background, [WallpaperCache.FromDisk, \
                path + 'bg.jpg', self.color, self.method])
        """
        self.cache.setOperation(self.Zodiac, [WallpaperCache.FromDisk, \
                path + 'zodiac%s.png', Qt.transparent, self.method])
        self.cache.setOperation(self.Moon, [WallpaperCache.FromDisk, \
                path + 'moonphase%d.png', Qt.transparent, self.method])
        """
        self.cache.setOperation(self.Month, [WallpaperCache.FromDisk, \
                path + 'month%d.png' % next.date().month(), Qt.transparent, self.method])
        self.cache.setOperation(self.WeekDay, [WallpaperCache.FromDisk, \
                path + 'weekday%d.png' % next.date().dayOfWeek(), Qt.transparent, self.method])
        self.cache.setOperation(self.Day, [WallpaperCache.FromDisk, \
                path + 'day%d.png' % next.date().day(), Qt.transparent, self.method])
        # TODO 12 min update
        self.cache.setOperation(self.Hour, [WallpaperCache.FromDisk, \
                path + 'hour%d.png' % next.time().hour(), Qt.transparent, self.method])
        """
        self.cache.setOperation(self.AmPm, [WallpaperCache.FromDisk, \
                path + '%s.png', Qt.transparent, self.method])
        """
        self.cache.setOperation(self.Minute, [WallpaperCache.FromDisk,
                path + 'minute%d.png' % next.time().minute(), Qt.transparent, self.method])

    def checkIfEmpty(self, wallpaper):
        print '### checkIfEmpty'
        if wallpaper.isEmpty():
            paths = KGlobal.dirs().findDirs('data', 'plasma/clockwallpapers')
            dir = QDir()
            dir.setFilter(QDir.AllDirs | QDir.Hidden | QDir.Readable)
            for path in paths:
                dir.setPath(path)
                dirs = dir.entryInfoList()
                for cwp in dirs:
                    print cwp.fileName()
                    if (cwp.fileName() == '.') or (cwp.fileName() == '..'):
                        continue
                    wallpaper = cwp.canonicalFilePath()
                    break
        return U(wallpaper)

    def checkGeometry(self):
        print '### checkGeometry'
        # TODO update
        if self.cache.checkGeometry() and self.wallpaperModel:
            self.wallpaperModel.setWallpaperSize(self.cache.size())

    def renderingsCompleted(self):
        print '### renderingsCompleted'
        if self.cache.pixmap(self.Current) == None:
            # On start
            self.cache.setPixmap(self.Current, self.cache.pixmap(self.Next))
            self.update(self.boundingRect())

    def paint(self, painter, exposedRect):
        print '### paint'
        self.checkGeometry()

        # get pixmap
        pixmap = self.cache.pixmap(self.Current)

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
            painter.fillRect(exposedRect, self.color)

    def installPackage(self, localPath):
        print '### installPackage', localPath
        package = ClockPackage(self)
        packageRoot = KStandardDirs.locateLocal("data", package.defaultPackageRoot())
        ClockPackage.installPackage(localPath, packageRoot)
        if self.wallpaperModel:
            name = os.path.splitext(os.path.basename(U(localPath)))[0]
            package.setPath(os.path.join(U(packageRoot), U(name)))
            self.wallpaperModel.addClockWallpaper(package)

    # Url dropped
    #----------------------------------------------------------------------------------------------
    def urlDropped(self, url):
        print '### urlDropped', url
        if url.isLocalFile():
            self.installPackage(url.toLocalFile())
        else:
            self.tmpFile = KTemporaryFile()
            if self.tmpFile.open():
                job = KIO.file_copy(url, KUrl(self.tmpFile.fileName()))
                self.connect(job, SIGNAL('result(KJob*)'), self.wallpaperRetrieved)

    def wallpaperRetrieved(self, job):
        self.installPackage(job.destUrl().toLocalFile())
        self.tmpFile = None

    # Configuration dialog
    #----------------------------------------------------------------------------------------------

    def createConfigurationInterface(self, parent):
        self.widget = QWidget(parent)
        self.connect(self.widget, SIGNAL('destroyed(QObject*)'), self.configWidgetDestroyed)
        self.ui = uic.loadUi(self.package().filePath('ui', 'config.ui'), self.widget)

        self.ui.positioningCombo.setCurrentIndex(
                self.cache.operationParam(self.Current, WallpaperCache.Method))
        self.connect(self.ui.positioningCombo, SIGNAL('currentIndexChanged(int)'), \
                     self.resizeChanged)

        self.wallpaperModel = WallpaperClockModel(self)
        delegate = BackgroundDelegate(self.cache.ratio(), self)

        self.ui.colorButton.setColor(
                self.cache.operationParam(self.Current, WallpaperCache.Color))
        self.connect(self.ui.colorButton, SIGNAL('changed(const QColor&)'), \
                     self.colorChanged)

        self.ui.clockWallpaperView.setModel(self.wallpaperModel)
        self.ui.clockWallpaperView.setItemDelegate(delegate)
        self.connect(self.ui.clockWallpaperView.selectionModel(),
                     SIGNAL('currentChanged(const QModelIndex&, const QModelIndex&)'),
                     self.wallpaperChanged)
        index = self.wallpaperModel.indexOf( \
                self.cache.operationParam(self.Current, WallpaperCache.Path))
        if index.isValid():
            self.ui.clockWallpaperView.setCurrentIndex(index)

        self.ui.openButton.setIcon(KIcon('document-open'));
        self.connect(self.ui.openButton, SIGNAL('clicked()'), self.showFileDialog)

        self.ui.getNewButton.setIcon(KIcon('get-hot-new-stuff'));
        self.connect(self.ui.getNewButton, SIGNAL('clicked()'), self.getNewWallpaper)

        self.ui.uninstallButton.setIcon(KIcon('edit-delete'));
        self.connect(self.ui.uninstallButton, SIGNAL('clicked()'), self.uninstall)
        return self.widget

    def configWidgetDestroyed(self):
        self.widget = None
        self.wallpaperModel = None
        self.ui = None

    def resizeChanged(self, index):
        self.settingsChanged(True)
        self.method = index
        self.cache.setAllDirty()

    def colorChanged(self, color):
        self.settingsChanged(True)
        self.color = color
        self.cache.setAllDirty()

    def wallpaperChanged(self, index):
        self.settingsChanged(True)
        self.package.setPath(
                self.wallpaperModel.data(index, BackgroundDelegate.PathRole).toString())
        # TODO free all images
        self.updateImages(QDateTime(), QDateTime.currentDateTime())

    # Uninstall
    def uninstall(self):
        index = self.ui.clockWallpaperView.currentIndex()
        if index.isValid():
            package = self.wallpaperModel.package(index.row())
            if KMessageBox.warningYesNo(self.widget, \
                    i18n('Are you sure you want to uninstall "%1"- clock wallpaper', \
                         package.metadata().name())) == KMessageBox.Yes:
                packageRoot = KStandardDirs.locateLocal("data", package.defaultPackageRoot())
                ClockPackage.uninstallPackage(package.metadata().pluginName(), packageRoot)

    # New wallpaper from website

    def getNewWallpaper(self):
        # TODO
        pass

    def newStuffFinished(self):
        # TODO
        self.wallpaperModel.addBackground(wallpaper)
        pass

    # Open file

    def showFileDialog(self):
        if not self.fileDialog:
            self.fileDialog = KFileDialog(KUrl(), '*.wcz *.zip', self.widget)
            self.fileDialog.setOperationMode(KFileDialog.Opening)
            self.fileDialog.setInlinePreviewShown(True)
            self.fileDialog.setCaption(i18n('Select Clock Wallpaper File'))
            self.fileDialog.setModal(False)
            self.connect(self.fileDialog, SIGNAL('okClicked()'), self.wallpaperBrowseCompleted)
            self.connect(self.fileDialog, SIGNAL('destroyed(QObject*)'), self.fileDialogFinished)

        self.fileDialog.show()
        self.fileDialog.raise_()
        self.fileDialog.activateWindow()

    def fileDialogFinished(self):
        self.fileDialog = None

    def wallpaperBrowseCompleted(self):
        name = self.fileDialog.selectedFile()
        self.installPackage(name)


def CreateWallpaper(parent):
    return Clock(parent)
