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

class BackgroundFinder(QObject):
    def __init__(self, structureParent, container, paths, eventLoop):
        QObject.__init__(self, None)
        self.structureParent = structureParent
        self.container = container
        self.paths = paths
        self.eventLoop = eventLoop
        self._papersFound = []

    def start(self):
        progress = KProgressDialog()
        progress.setAllowCancel(False)
        progress.setModal(True)
        progress.setLabelText(i18n('Finding images for the wallpaper slideshow.'))
        progress.progressBar().setRange(0, 0)

        suffixes = set(['png', 'jpeg', 'jpg', 'svg', 'svgz'])
        dir = QDir()
        dir.setFilter(QDir.AllDirs | QDir.Files | QDir.Hidden | QDir.Readable)

        count = 0
        allCount = 0
        setLabel = True

        if not self.paths.isEmpty():
            path = self.paths.takeLast()
            # print 'doing', path
            dir.setPath(path)
            files = dir.entryInfoList()
            for wp in files:
                if wp.isDir():
                    # print 'directory', wp.fileName(),
                    # validPackages.self.contains(wp.fileName())
                    name = wp.fileName()

                    if (name == '.') or (name == '..'):
                        # do nothing
                        pass
                    elif QFile.exists(wp.filePath() + '/metadata.desktop'):
                        structure = Plasma.Wallpaper.packageStructure(self.structureParent)
                        pkg = Plasma.Package(wp.filePath(), structure)

                        if pkg.isValid() and (self.container or \
                            not self.container.contains(pkg.path())):
                            if setLabel:
                                progress.setLabelText(
                                        i18n('Finding images for the wallpaper slideshow.') +
                                             '\n\n' +
                                        i18n('Adding wallpaper self.package in %1', name))
                            count += 1
                            self._papersFound.append(pkg.path())
                            # print 'gots a', wp.filePath()
                        else:
                            self.paths.append(wp.filePath())
                    else:
                        self.paths.append(wp.filePath())
                elif wp.suffix().toLower() in suffixes and \
                     (not self.container or wp.filePath() not in self.container):
                    # print 'adding', wp.filePath(), setLabel
                    if setLabel:
                        progress.setLabelText(
                                i18n('Finding images for the wallpaper slideshow.') + '\n\n' +
                                i18n('Adding image %1', wp.filePath()))
                        setLabel = False

                    # print '     adding image file', wp.filePath()
                    count += 1
                    self._papersFound.append(wp.filePath())

                allCount += 1
                if allCount % 10 == 0:
                    self.eventLoop.processEvents(QEventLoop.ExcludeUserInputEvents)
                    if progress.isVisible() and count % 10:
                        setLabel = True
        self.emit(SIGNAL('finished()'))

    def papersFound(self):
        return self._papersFound


class BackgroundListModel(QAbstractListModel):
    def __init__(self, ratio, listener, parent):
        QAbstractListModel.__init__(self, parent)
        self.listener = listener
        self.structureParent = listener
        self.ratio = ratio
        self.size = QSize(0, 0)
        self.resizeMethod = Plasma.Wallpaper.ScaledResize
        self.dirwatch = KDirWatch()
        self.packages = []
        self.sizeCache = {}
        self.previews = {}
        self.previewJobs = {}
        self.connect(self.dirwatch, SIGNAL('deleted(QString)'), self.removeBackground)

    def removeBackground(self, path):
        index = self.indexOf(path)

        if index.isValid():
            beginRemoveRows(QModelIndex(), index.row(), index.row())
            package = self.packages.at(index.row())
            self.packages.removeAt(index.row())
            endRemoveRows()

    def reload(self):
        self.reload(QStringList())

    def reload(self, selected):
        dirs = KGlobal.dirs().findDirs('wallpaper', '')

        if len(self.packages) > 0:
            self.beginRemoveRows(QModelIndex(), 0, len(self.packages) - 1)
            self.packages = []
            self.endRemoveRows()

        tmp = []
        for file in selected:
            if not self.contains(file) and QFile.exists(file):
                tmp.append(Plasma.Package(file,
                                          Plasma.Wallpaper.packageStructure(self.structureParent)))

        backgrounds = self.findAllBackgrounds(self.structureParent, self, dirs)
        for background in backgrounds:
            package = Plasma.Package(background,
                                     Plasma.Wallpaper.packageStructure(self.structureParent))
            tmp.append(package)
            package = None

        # add new files to dirwatch
        for b in tmp:
            if not self.dirwatch.contains(b.path()):
                self.dirwatch.addFile(b.path())

        if len(tmp) > 0:
            self.beginInsertRows(QModelIndex(), 0, len(tmp) - 1)
            self.packages = tmp
            self.endInsertRows()

    def addBackground(self, path):
        if not self.contains(path):
            if not self.dirwatch.contains(path):
                self.dirwatch.addFile(path)

            self.beginInsertRows(QModelIndex(), 0, 0)
            structure = Plasma.Wallpaper.packageStructure(self.structureParent)
            pkg = Plasma.Package(path, structure)
            self.packages.insert(0, pkg)
            self.endInsertRows()

    def indexOf(self, path):
        info = QFileInfo(path)
        if info.isDir() and not path.endsWith('/'):
            path += '/'
        for i, p in enumerate(self.packages):
            print path, p.path(), p.filePath('preferred')
            if path == p.path() or path == p.filePath('preferred'):
                return self.index(i, 0)
        return QModelIndex()

    def contains(self, path):
        return self.indexOf(path).isValid()

    def rowCount(self, index):
        return len(self.packages)

    def bestSize(self, package):
        if package in self.sizeCache:
            return self.sizeCache[package]

        image = package.filePath('preferred')
        if image.isEmpty():
            return QSize()

        info = KFileMetaInfo(image, QString(), KFileMetaInfo.TechnicalInfo)
        size = QSize(info.item('http://freedesktop.org/standards/xesam/1.0/core#width').
                            value().toInt()[0],
                     info.item('http://freedesktop.org/standards/xesam/1.0/core#height').
                            value().toInt()[0])

        # backup solution if strigi does not work
        if (size.width() == 0) or (size.height() == 0):
            print 'fall back to QImage, check your strigi'
            size = QImage(image).size()

        self.sizeCache[package] = size
        return size

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
                title = QFileInfo(b.filePath('preferred')).completeBaseName()
            return QVariant(unicode(title))

        elif role == Qt.DecorationRole or role == BackgroundDelegate.ScreenshotRole:
            if b in self.previews:
                return self.previews[b]
            file = KUrl(b.filePath('preferred'))
            if file.isValid():
                self.previewJobs[file.prettyUrl()] = QPersistentModelIndex(index)
                l = KUrl.List([file])
                job = KIO.filePreview(l, BackgroundDelegate.SCREENSHOT_SIZE, \
                                      BackgroundDelegate.SCREENSHOT_SIZE)
                self.connect(job, SIGNAL('gotPreview(const KFileItem &, const QPixmap &)'),
                             self.showPreview)
                self.connect(job, SIGNAL('failed(const KFileItem &)'), self.previewFailed)

            pix = QPixmap(BackgroundDelegate.SCREENSHOT_SIZE, BackgroundDelegate.SCREENSHOT_SIZE)
            pix.fill(Qt.transparent)
            self.previews[b] = pix
            return pix

        elif role == BackgroundDelegate.AuthorRole:
            return QVariant(unicode(b.metadata().author()))

        elif role == BackgroundDelegate.ResolutionRole:
            size = self.bestSize(b)
            if size.isValid():
                return QVariant(u'%dx%d' % (size.width(), size.height()))
            return QVariant()

        elif role == BackgroundDelegate.PathRole:
            if b.structure().contentsPrefix().isEmpty():
                return QVariant(unicode(b.filePath('preferred')))
            else:
                return QVariant(unicode(b.path()))
        else:
            return QVariant()

    def showPreview(self, item, preview):
        if item.url().prettyUrl() not in self.previewJobs:
            return
        index = self.previewJobs[item.url().prettyUrl()]
        if not index.isValid():
            return
        del self.previewJobs[item.url().prettyUrl()]

        b = self.package(index.row())
        if b == None:
            return

        self.previews[b] = preview
        self.emit(SIGNAL('dataChanged(const QModelIndex&, const QModelIndex&)'), \
                QModelIndex(index), QModelIndex(index))

    def previewFailed(self, item):
        del self.previewJobs[item.url().prettyUrl()]

    def package(self, index):
        return self.packages[index]

    def findAllBackgrounds(self, structureParent, container, p):
        # TODO: put this in a thread so that it can run in the background without blocking
        localEventLoop = QEventLoop()
        finder = BackgroundFinder(structureParent, container, p, localEventLoop)

        self.connect(finder, SIGNAL('finished()'), localEventLoop, SLOT('quit()'))
        QTimer.singleShot(0, finder.start)
        localEventLoop.exec_()
        return finder.papersFound()

    def setWallpaperSize(self, size):
        self.size = size

    def setResizeMethod(self, resizeMethod):
        self.resizeMethod = resizeMethod
