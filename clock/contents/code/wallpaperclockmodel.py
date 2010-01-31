#!/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright (c) 2009 Petri Damstén <damu@iki.fi>
#    Copyright (c) 2007 Paolo Capriotti <p.capriotti@gmail.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details
#
#    You should have received a copy of the GNU Library General Public
#    License along with this program; if not, write to the
#    Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

#    C++ to python conversion by Petri Damstén <damu@iki.fi>

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *
from PyKDE4.kio import *
from PyKDE4.plasma import Plasma
from backgrounddelegate import BackgroundDelegate
from clockpackage import ClockPackage

class WallpaperClockFinder(QObject): # (QThread): TODO
    def __init__(self, parent = None):
        #QThread.__init__(self, parent) TODO
        QObject.__init__(self, parent)

    def run(self):
        dir = QDir()
        dir.setFilter(QDir.AllDirs | QDir.Hidden | QDir.Readable)
        paths = KGlobal.dirs().findDirs('data', 'plasma/clockwallpapers')

        while not paths.isEmpty():
            path = paths.takeLast()
            print '### doing', path
            dir.setPath(path)
            dirs = dir.entryInfoList()
            for cwp in dirs:
                if (cwp.fileName() == '.') or (cwp.fileName() == '..'):
                    continue
                print '   ### directory', cwp.fileName()
                package = ClockPackage(None, cwp.canonicalFilePath())
                self.emit(SIGNAL('newClockWallpaper(ClockPackage*)'), package)
        self.emit(SIGNAL('finished()'))


class WallpaperClockModel(QAbstractListModel):
    def __init__(self, parent):
        QAbstractListModel.__init__(self, parent)
        self.packages = []
        self.dirwatch = KDirWatch()
        self.progress = None
        self.connect(self.dirwatch, SIGNAL('deleted(QString)'), self.removeClockWallpaper)
        self.findAllBackgrounds()

    def removeClockWallpaper(self, path):
        index = self.indexOf(path)

        if index.isValid():
            beginRemoveRows(QModelIndex(), index.row(), index.row())
            self.packages.removeAt(index.row())
            endRemoveRows()

    def addClockWallpaper(self, package):
        if self.progress:
            self.progress.setLabelText(
                i18n('Finding clock wallpapers.') + '\n\n' +
                i18n('Adding "%1" wallpaper', package.metadata().name()))

        if not self.dirwatch.contains(package.path()):
            self.dirwatch.addDir(package.path())

        self.beginInsertRows(QModelIndex(), 0, 0)
        self.packages.insert(0, package)
        self.endInsertRows()

    def finderFinished(self):
        if self.progress:
            self.progress.close()
            self.progress = None
        if self.finder:
            self.finder = None

    def indexOf(self, path):
        info = QFileInfo(path)
        if info.isDir() and not path.endsWith('/'):
            path += '/'
        for i, p in enumerate(self.packages):
            if path == p.path():
                return self.index(i, 0)
        return QModelIndex()

    def contains(self, path):
        return self.indexOf(path).isValid()

    def rowCount(self, index):
        return len(self.packages)

    def data(self, index, role):
        if not index.isValid():
            return QVariant()

        if index.row() >= len(self.packages):
            return QVariant()

        b = self.package(index.row())
        if not b:
            return QVariant()

        if role == Qt.DisplayRole:
            title = b.metadata().name()
            if title.isEmpty():
                title = QFileInfo(b.path()).completeBaseName()
            return QVariant(unicode(title))

        elif role == Qt.DecorationRole or role == BackgroundDelegate.ScreenshotRole:
            return QPixmap(b.preview())

        elif role == BackgroundDelegate.AuthorRole:
            return QVariant(unicode(b.metadata().author()))

        elif role == BackgroundDelegate.ResolutionRole:
            size = b.size()
            if size.isValid():
                return QVariant(u'%dx%d' % (size.width(), size.height()))
            return QVariant()

        elif role == BackgroundDelegate.PathRole:
            return QVariant(unicode(b.path()))
        else:
            return QVariant()

    def package(self, index):
        return self.packages[index]

    def findAllBackgrounds(self):
        self.progress = KProgressDialog()
        self.progress.setAllowCancel(False)
        self.progress.setModal(True)
        self.progress.setLabelText(i18n('Finding clock wallpapers.'))
        self.progress.progressBar().setRange(0, 0)

        self.finder = WallpaperClockFinder(self)
        self.connect(self.finder, SIGNAL('newClockWallpaper(ClockPackage*)'), self.addClockWallpaper)
        self.connect(self.finder, SIGNAL('finished()'), self.finderFinished)
        #self.finder.start() # TODO
        self.finder.run()
