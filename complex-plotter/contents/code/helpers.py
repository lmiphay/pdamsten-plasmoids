#   -*- coding: utf-8 -*-
#
#   Copyright (C) 2009 Petri Damstén <damu@iki.fi>
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

from PyQt4 import uic
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.kdeui import *
from PyKDE4.kio import *

def check(b):
    if not b:
        raise ValueError('Check failed.')

def U(s):
    # For some reason in Arch Linux & Gentoo data map is QString => QString
    # and in kubuntu (and C++ plasma) QString => QVariant
    if isinstance(s, QVariant):
        return unicode(s.toString())
    elif isinstance(s, QString):
        return unicode(s)
    elif isinstance(s, QFont):
        return unicode(s.toString())
    elif isinstance(s, QColor):
        return unicode(s.name())
    elif isinstance(s, QLineEdit) or isinstance(s, KLineEdit) or \
         isinstance(s, QStandardItem) or isinstance(s, QListWidgetItem) or \
         isinstance(s, KUrlComboRequester):
        return unicode(s.text())
    elif isinstance(s, KColorCombo):
        return unicode(s.color().name())
    else:
        return unicode(s)

def F(f):
    if isinstance(f, QVariant) or isinstance(f, QString):
        return float(f.toDouble()[0])
    elif isinstance(f, QLineEdit) or isinstance(f, KLineEdit):
        return float(f.text().toDouble()[0])
    else:
        return float(f)

def I(i):
    if isinstance(i, QVariant) or isinstance(i, QString):
        return int(i.toInt()[0])
    else:
        return int(i)

class UiHelper():
    applet = None

    def __init__(self, uifile):
        if QDir.isAbsolutePath(uifile) or QFile.exists(uifile):
            self.ui = uic.loadUi(uifile)
        else:
            self.ui = uic.loadUi(self.applet.package().filePath('ui', uifile))
        self.addChildrenAsMembers(self.ui)

    def addChildrenAsMembers(self, widget):
        for w in widget.children():
            if w.inherits('QWidget'):
                try:
                    self.__dict__[str(w.objectName())] = self.ui.findChild(\
                            globals()[w.metaObject().className()], w.objectName())
                    self.addChildrenAsMembers(self.__dict__[str(w.objectName())])
                except:
                    print 'Not using ' + w.metaObject().className() + ':' + str(w.objectName()) + \
                          ' as child.'
