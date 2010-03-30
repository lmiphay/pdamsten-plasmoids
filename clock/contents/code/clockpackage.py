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

import os
from PyQt4.QtCore import *
from PyQt4.QtWebKit import *
from PyKDE4.plasma import Plasma
from helpers import *
import re

# Use Plasma.PackageStructure here although it does not get installed like other package structures
class GetNewDialog(KDialog):
    def __init__(self, parent, package):
        KDialog.__init__(self, parent)
        self.package = package

        self.setCaption(i18n('Get New Clock Wallpapers'))
        self.setButtons(KDialog.ButtonCode())

        self.widget = QWidget()
        self.verticalLayout = QVBoxLayout(self.widget)
        self.verticalLayout.setObjectName('verticalLayout')
        self.webView = QWebView(self.widget)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.webView.sizePolicy().hasHeightForWidth())
        self.webView.setSizePolicy(sizePolicy)
        self.verticalLayout.addWidget(self.webView)
        self.label = QLabel(self.widget)
        self.label.setFrameShape(QFrame.StyledPanel)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Minimum)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.hide()
        self.verticalLayout.addWidget(self.label)
        self.horizontalLayout = QHBoxLayout()
        self.backButton = KPushButton(self.widget)
        self.horizontalLayout.addWidget(self.backButton)
        self.progressBar = QProgressBar(self.widget)
        self.horizontalLayout.addWidget(self.progressBar)
        self.closeButton = KPushButton(self.widget)
        self.closeButton.setAutoDefault(True)
        self.closeButton.setDefault(True)
        self.horizontalLayout.addWidget(self.closeButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.backButton.setText(i18n('Back'))
        self.backButton.setIcon(KIcon('go-previous'));
        self.connect(self.backButton, SIGNAL('clicked()'), self.webView.back)
        self.closeButton.setText(i18n('Close'))
        self.closeButton.setIcon(KIcon('dialog-close'));
        self.connect(self.closeButton, SIGNAL('clicked()'), self.close)
        self.setMainWidget(self.widget)

        self.webView.load(KUrl('http://www.vladstudio.com/wallpaperclock/browse.php'))
        self.webView.page().setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
        self.connect(self.webView, SIGNAL('linkClicked(const QUrl&)'), self.linkClicked)
        self.connect(self.webView, SIGNAL('loadProgress(int)'),  self.progressBar.setValue)
        self.webView.show()

    def linkClicked(self, url):
        s = U(url.toString())
        self.label.hide()
        if not s.startswith('http://www.vladstudio.com/wallpaperclock/') and \
           not s.startswith('http://www.google.com/'):
            s = 'http://www.vladstudio.com/wallpaperclock/'
            self.message(i18n('No browsing outside clock wallpapers.'))
        if s.find('download.php') >= 0:
            self.tmpFile = KTemporaryFile()
            self.tmpFile.setSuffix('.wcz')
            if self.tmpFile.open():
                job = KIO.file_copy(KUrl(s), KUrl(self.tmpFile.fileName()), -1, \
                                    KIO.JobFlags(KIO.Overwrite | KIO.HideProgressInfo))
                self.connect(job, SIGNAL('result(KJob*)'), self.downloaded)
                self.connect(job, SIGNAL('percent(KJob*, unsigned long)'), self.progress)
        else:
            self.webView.load(KUrl(s))

    def message(self, msg):
        self.label.show()
        self.label.setText(msg)

    def progress(self, job, percent):
        self.progressBar.setValue(percent)

    def downloaded(self, job):
        if job.error() == 0:
            print job.metaData()
            packageRoot = KStandardDirs.locateLocal("data", self.package.defaultPackageRoot())
            if self.package.installPackage(job.destUrl().toLocalFile(), packageRoot):
                self.message(i18n('Package installed.'))
            else:
                self.message(i18n('Package install Failed.'))
            self.tmpFile = None
        else:
            self.message(job.errorString())


class ClockPackage(Plasma.PackageStructure):
    job = None
    def __init__(self, parent = None, path = None):
        Plasma.PackageStructure.__init__(self, parent, 'ClockWallpaper')
        self.setContentsPrefix(QString())
        self.setDefaultPackageRoot('plasma/clockwallpapers/')
        self.setServicePrefix('plasma-clockwallpaper')
        self._metadata = Plasma.PackageMetadata()
        self.width = 0
        self.height = 0
        self._preview = None
        self._hourImages = 24
        self.ampm = False
        self.dlg = None
        if path:
            self.setPath(path)

    @staticmethod
    def installPackage(archivePath, packageRoot):
        name = os.path.splitext(os.path.basename(U(archivePath)))[0]
        packageDir = os.path.join(U(packageRoot), U(name))

        if not os.path.exists(packageDir):
            KStandardDirs.makeDir(packageDir)
            if not os.path.exists(packageDir):
                print 'ERROR: Cannot make package dir:', packageDir
                return False

        zip = KZip(archivePath)
        if zip.open(QIODevice.ReadOnly):
            zipDir = zip.directory()
            zipDir.copyTo(packageDir)
        else:
            print 'ERROR: Cannot zip to dir:', archivePath, packageDir
            return False
        return True

    @staticmethod
    def uninstallPackage(packageName, packageRoot):
        packageDir = os.path.join(U(packageRoot), U(packageName))
        ClockPackage.job = KIO.del_(KUrl(packageDir))
        return ClockPackage.job.exec_()

    def createNewWidgetBrowser(self, parent = None):
        if not self.dlg:
            self.dlg = GetNewDialog(parent, self)
            self.connect(self.dlg, SIGNAL('finished()'), self.finished)
        self.dlg.show()

    def finished(self):
        self.dlg.deleteLater()
        self.dlg = None
        self.emit(SIGNAL('newWidgetBrowserFinished()'))

    def preview(self):
        return self._preview

    def hourImages(self):
        return self._hourImages

    def ampmEnabled(self):
        return self.ampm

    def size(self):
        return QSize(self.width, self.height)

    def metadata(self):
        return self._metadata

    def pathChanged(self):
        s = open(U(self.path()) + '/clock.ini').read()
        s = s.replace('\r', '\n').replace('\n\n', '\n')
        # SafeConfigParser / KConfig does not like mixed windows/unix line endings
        # SafeConfigParser does not seem to parse string with StringIO
        # KConfig cannot read config from string
        try:
            s = re.findall('(?ims)\[Settings\].*?^\[', s)[0]
        except:
            s = ''
        a = re.findall('(.*?)=(.*)', s)
        dict = {'name': '', 'width': 1920, 'height': 1200, 'author': '', 'email': '', \
                'description': '', 'homepageURL': '', 'downloadURL': '', \
                'refreshhourinterval': 60, 'hourimages': 24, 'ampm': 0}
        for i in a:
            dict[i[0]] = i[1]

        path = U(self.path())
        self._metadata.setPluginName(os.path.basename(path.rstrip('/')))
        if dict['name'] == '':
            dict['name'] = self._metadata.pluginName()

        self._preview = QImage()
        preview = os.path.join(path, 'preview100x75.jpg')
        if os.path.exists(preview):
            self._preview.load(preview)
        else:
            preview = os.path.join(path, 'preview200x150.jpg')
            if os.path.exists(preview):
                self._preview.load(preview)

        self._metadata.setName(dict['name'])
        self.width = I(dict['width'])
        self.height = I(dict['height'])
        self._metadata.setAuthor(dict['author'])
        self._metadata.setEmail(dict['email'])
        self._metadata.setDescription(dict['description'])
        self._metadata.setWebsite(dict['homepageURL'])
        self.refreshHourInterval = dict['refreshhourinterval']
        self._hourImages = dict['hourimages']
        self.ampm = (dict['ampmenabled'] == '1')
