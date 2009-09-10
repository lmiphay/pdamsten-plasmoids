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

import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
from PyKDE4.plasma import Plasma
from PyKDE4.plasmascript import Applet
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *
from add import AddDialog
from helpers import *

class ConfigDialog(KConfigDialog, UiHelper):
    def __init__(self, parent, id, applet):
        UiHelper.__init__(self, 'config.ui')
        self.nullManager = KConfigSkeleton()
        KConfigDialog.__init__(self, parent, id, self.nullManager)

        self.applet = applet
        self.connect(self, SIGNAL('finished()'), self.nullManager, SLOT('deleteLater()'))
        self.setFaceType(KPageDialog.Auto)
        title = i18nc('@title:window', '%1 Settings', applet.name())
        self.setWindowTitle(title)
        self.setAttribute(Qt.WA_DeleteOnClose, True)
        self.addPage(self.ui, title, 'settings')

        palette = self.sourceEdit.palette()
        palette.setColor(QPalette.Disabled, QPalette.Text, \
                palette.color(QPalette.Active, QPalette.Text))
        self.sourceEdit.setPalette(palette)

        self.connect(self.configureButton, SIGNAL('clicked()'), self.configureClicked)
        self.connect(self.autorangeCheck, SIGNAL('stateChanged(int)'), self.enableItems)
        self.connect(self.headerEdit, SIGNAL('textChanged(const QString&)'), self.setExample)
        self.connect(self.fontRequester, SIGNAL('fontSelected(const QFont&)'), self.setExample)
        self.connect(self.fontColorButton, SIGNAL('changed(const QColor&)'), self.setExample)
        self.enableItems()

    def setData(self, data):
        self.headerEdit.setText(data['header'])
        if data['source']:
            self.sourceEdit.setText(data['source']['name'])
        self.source = data['source']
        self.fontRequester.setFont(data['font'])
        self.fontColorButton.setColor(data['fontcolor'])
        self.autorangeCheck.setChecked(data['autorange'])
        self.maxSpin.setValue(data['max'])
        self.minSpin.setValue(data['min'])
        interval = data['interval']
        a = [1000, 60, 60, 24]
        for i, m in enumerate(a):
            if interval % m != 0 or i == len(a) - 1 or interval == 0:
                self.intervalSpin.setValue(interval)
                self.intervalCombo.setCurrentIndex(i)
                break
            interval /= m
        self.enableItems()

    def data(self):
        data = {}
        data['header'] = unicode(self.headerEdit.text())
        data['source'] = self.source
        data['font'] = self.fontRequester.font()
        data['fontcolor'] = self.fontColorButton.color()
        a = [1, 1000, 60 * 1000, 60 * 60 * 1000, 24 * 60 * 60 * 1000]
        data['interval'] = self.intervalSpin.value() * a[self.intervalCombo.currentIndex()]
        data['autorange'] = self.autorangeCheck.isChecked()
        data['max'] = self.maxSpin.value()
        data['min'] = self.minSpin.value()
        return data

    def setExample(self):
            try:
                self.exampleTitleLabel.setText(i18n('e.g.: '))
                s = unicode(self.headerEdit.text())
                s = s.format(value = 31.2345, max = 100.0, min = 0.0, unit = u'°C',
                             name = u'CPU Temp')
            except:
                self.exampleTitleLabel.setText(i18n('error: '))
                (exception_type, value, exception_traceback) = sys.exc_info()
                s = unicode(value)
            self.exampleLabel.setText(s)
            palette = self.exampleLabel.palette()
            palette.setColor(QPalette.Active, QPalette.WindowText, self.fontColorButton.color())
            self.exampleLabel.setPalette(palette)
            self.exampleLabel.setFont(self.fontRequester.font())

    def configureClicked(self):
        dlg = AddDialog(self, self.applet)
        if dlg.exec_() == QDialog.Accepted:
            s = dlg.selected()
            if s is not None:
                self.sourceEdit.setText(s['name'])
                self.source = s

    def enableItems(self):
        self.minLabel.setEnabled(not self.autorangeCheck.isChecked())
        self.minSpin.setEnabled(not self.autorangeCheck.isChecked())
        self.maxLabel.setEnabled(not self.autorangeCheck.isChecked())
        self.maxSpin.setEnabled(not self.autorangeCheck.isChecked())
