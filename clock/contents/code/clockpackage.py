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
from PyKDE4.plasma import Plasma
from helpers import *
import re

# Use Plasma.PackageStructure here although it does not get installed like other package structures

class ClockPackage(Plasma.PackageStructure):
    def __init__(self, parent = None, path = None):
        Plasma.PackageStructure.__init__(self, parent, 'ClockWallpaper')
        self.setContentsPrefix(QString())
        self.setDefaultPackageRoot('plasma/clockwallpapers/')
        self.setServicePrefix('plasma-clockwallpaper')
        self._metadata = Plasma.PackageMetadata()
        if path:
            self.setPath(path)

    def installPackage(self, archivePath, packageRoot):
        name = os.path.splitext(os.path.basename(archivePath))[0]
        packageDir = os.path.join(U(packageRoot), U(name))

        if not os.path.exists(packageDir):
            KStandardDirs.makeDir(packageDir)
            if not os.path.exists(packageDir)():
                return False

        zip = KZip(archivePath)
        if zip.open(QIODevice.ReadOnly):
            zipDir = zip.directory()
            zipDir.copyTo(packageDir)
        else:
            return False

    def uninstallPackage(self, packageName, packageRoot):
        packageDir = os.path.join(U(packageRoot), U(packageName))
        self.job = KIO.del_(KUrl(packageDir))
        return self.job.exec_()

    """
    def createNewWidgetBrowser(self, parent = None):
        pass
    """

    def preview(self):
        # TODO
        return QPixmap()

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
                'refreshhourinterval': 60, 'hourimages': 24}
        for i in a:
            dict[i[0]] = i[1]

        self._metadata.setPluginName(os.path.basename(U(self.path()).rstrip('/')))
        if dict['name'] == '':
            dict['name'] = self._metadata.pluginName()

        self._metadata.setName(dict['name'])
        self.width = I(dict['width'])
        self.height = I(dict['height'])
        self._metadata.setAuthor(dict['author'])
        self._metadata.setEmail(dict['email'])
        self._metadata.setDescription(dict['description'])
        self._metadata.setWebsite(dict['homepageURL'])
        self._metadata.setRemoteLocation(KUrl(dict['downloadURL']))
        self.refreshHourInterval = dict['refreshhourinterval']
        self.hourImages = dict['hourimages']
