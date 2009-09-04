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

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import uic
from PyKDE4.plasma import Plasma
from PyKDE4.plasmascript import Applet
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *
from config import ConfigDialog
from uihelper import UiHelper

class AnalogMeter(Applet):
    def __init__(self, parent, args = None):
        Applet.__init__(self, parent)
        self.cfg = {}

    def init(self):
        # To find ui files from package dir
        UiHelper.applet = self.applet
        # This trickers source list fill so they are ready when needed (e.g. config)
        self.applet.dataEngine('systemmonitor').sources()

        cg = self.config()
        self.cfg['header'] = unicode(cg.readEntry('header', '').toString())
        self.cfg['sourcename'] = cg.readEntry('sourcename', '').toString()
        self.cfg['interval'] = cg.readEntry('interval', 60000).toInt()[0]
        try:
            self.cfg['source'] = eval(unicode(cg.readEntry('source', '').toString()))
        except:
            self.cfg['source'] = None
        self.createMeter()

    def createMeter(self):
        layout = self.applet.layout()
        if layout is None:
            layout = QGraphicsLinearLayout(Qt.Vertical, self.applet)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
        while layout.count() > 0:
            item = layout.itemAt(0)
            layout.removeAt(0)
            del item
        if self.cfg['source'] == None:
            self.setConfigurationRequired(True, i18n('Source not configured'))
            return
        self.setConfigurationRequired(False, '')

        theme = Plasma.Theme.defaultTheme()
        self.meter = Plasma.Meter(self.applet)
        self.meter.setMeterType(Plasma.Meter.AnalogMeter)
        self.meter.setLabel(1, '')
        self.meter.setLabelColor(1, theme.color(Plasma.Theme.TextColor))
        self.meter.setLabelAlignment(1, Qt.AlignCenter)
        font = theme.font(Plasma.Theme.DefaultFont)
        font.setPointSize(8)
        self.meter.setLabelFont(1, font)
        layout.addItem(self.meter)
        print self.cfg['source'], self.cfg['interval']
        self.dataEngine(self.cfg['source'][0]).connectSource(
                self.cfg['source'][1], self, self.cfg['interval'])

    @pyqtSignature("dataUpdated(const QString &, const Plasma::DataEngine::Data &)")
    def dataUpdated(self, sourceName, data):
        print data
        valueName = self.cfg['source'][2]
        if data.has_key(valueName):
            self.meter.setValue(data[valueName].toDouble()[0])
            # TODO text

    @pyqtSignature("configAccepted()")
    def configAccepted(self):
        cg = self.config()
        self.cfg = self.dlg.data()
        cg.writeEntry('header', self.cfg['header'])
        cg.writeEntry('sourcename', self.cfg['sourcename'])
        cg.writeEntry('source', repr(self.cfg['source']))
        cg.writeEntry('interval', repr(self.cfg['interval']))
        self.createMeter()

    def configDialogId(self):
        return QString('%1settings%2script').arg(self.applet.id()).arg(self.applet.name())

    def showConfigurationInterface(self):
        if KConfigDialog.showDialog(self.configDialogId()):
            return
        self.dlg = ConfigDialog(None, self.configDialogId(), self.applet)
        self.connect(self.dlg, SIGNAL('applyClicked()'), self, SLOT('configAccepted()'))
        self.connect(self.dlg, SIGNAL('okClicked()'), self, SLOT('configAccepted()'))
        self.dlg.setData(self.cfg)
        self.dlg.show()

def CreateApplet(parent):
    return AnalogMeter(parent)

