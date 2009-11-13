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
from config import ConfigPage
from helpers import *

MAX=1000000000
MIN=-1000000000

class AnalogMeter(Applet):
    def __init__(self, parent, args = None):
        Applet.__init__(self, parent)
        self.cfg = {}
        self.halfSecondSource = False

    def init(self):
        # To find ui files from package dir
        UiHelper.applet = self.applet

        self.setAspectRatioMode(Plasma.Square)
        cg = self.config()
        self.cfg['header'] = U(cg.readEntry('header', '{value:1.1f} {unit}'))
        self.cfg['font'] = QFont()
        self.cfg['font'].fromString(
                U(cg.readEntry('font', 'Sans Serif,8,-1,5,50,0,0,0,0,0')))
        self.cfg['fontcolor'] = QColor(U(cg.readEntry('fontcolor', '#000000')))
        self.cfg['interval'] = I(cg.readEntry('interval', '60000'))
        self.cfg['min'] = F(cg.readEntry('min', '0.0'))
        self.cfg['max'] = F(cg.readEntry('max', '100.0'))
        self.cfg['autorange'] = cg.readEntry('autorange', 'true').toBool()
        try:
            self.cfg['source'] = eval(U(cg.readEntry('source', '')))
            check(isinstance(self.cfg['source'], dict))
        except:
            self.cfg['source'] = None

        self.smengine = self.applet.dataEngine('systemmonitor')
        self.allSystemmonitorSources = self.smengine.sources()
        self.activeSystemmonitorSources = self.parseSystemmonitorSources()
        self.createMeter()
        self.connect(self.smengine, SIGNAL('sourceAdded(const QString&)'), self.sourceAdded)
        self.connect(self.smengine, SIGNAL('sourceRemoved(const QString&)'), self.sourceRemoved)

    def sourceAdded(self, name):
        self.allSystemmonitorSources.append(name)
        if name in self.activeSystemmonitorSources:
            self.connectSystemMonitorSource(name)

    def connectSystemMonitorSource(self, name):
        if name in self.allSystemmonitorSources:
            # Hack for correctly update 'systemmonitor' dataengine
            self.halfSecondSource = True
            self.smengine.connectSource(name, self, 500)

    def sourceRemoved(self, name):
        self.allSystemmonitorSources.removeAll(name)

    def parseSystemmonitorSources(self):
        result = []
        if self.cfg['source'] and self.cfg['source']['dataengine'] == 'systemmonitor':
            result.append(self.cfg['source']['source'])
        return result

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
        self.meter.setLabelColor(1, self.cfg['fontcolor'])
        self.meter.setLabelAlignment(1, Qt.AlignCenter)
        self.meter.setLabelFont(1, self.cfg['font'])
        if self.cfg['autorange']:
            self.meter.setMinimum(MAX)
            self.meter.setMaximum(MIN)
        else:
            self.meter.setMinimum(self.cfg['min'])
            self.meter.setMaximum(self.cfg['max'])
        layout.addItem(self.meter)
        c = self.cfg['source']
        self.valueName = QString(c['value'])
        self.minName = QString(c['min'])
        self.maxName = QString(c['max'])
        self.unitName = QString(c['unit'])
        if c['dataengine'] == 'systemmonitor':
            self.connectSystemMonitorSource(c['source'])
        else:
            self.dataEngine(c['dataengine']).connectSource(c['source'], self, self.cfg['interval'])

    @pyqtSignature("dataUpdated(const QString &, const Plasma::DataEngine::Data &)")
    def dataUpdated(self, sourceName, data):
        #print data
        if self.valueName in data:
            # Hack for correctly update 'systemmonitor' dataengine ---------------------
            if self.halfSecondSource:
                self.halfSecondSource = False
                c = self.cfg['source']
                #self.dataEngine(c['dataengine']).disconnectSource(c['source'], self)
                self.dataEngine(c['dataengine']).connectSource(c['source'], \
                                self, self.cfg['interval'])
            # --------------------------------------------------------------------------
            if self.cfg['autorange'] and F(data[self.minName]) != F(data[self.maxName]):
                if self.meter.minimum() != F(data[self.minName]):
                    self.meter.setMinimum(F(data[self.minName]))
                if self.meter.maximum() != F(data[self.maxName]):
                    self.meter.setMaximum(F(data[self.maxName]))
            elif self.cfg['autorange']:
                if self.meter.minimum() > F(data[self.valueName]):
                    self.meter.setMinimum(F(data[self.valueName]))
                if self.meter.maximum() < F(data[self.valueName]):
                    self.meter.setMaximum(F(data[self.valueName]))
                print self.meter.minimum(), self.meter.maximum()

            self.meter.setValue(F(data[self.valueName]))
            try:
                s = self.cfg['header'].format(value = F(data[self.valueName]),
                                             max = F(data[self.maxName]),
                                             min = F(data[self.minName]),
                                             unit = U(data[self.unitName]),
                                             name = self.cfg['source']['name'])
            except:
                s = i18n('error')
            self.meter.setLabel(1, s)

    @pyqtSignature("configAccepted()")
    def configAccepted(self):
        cg = self.config()
        self.cfg = self.configPage.data()
        cg.writeEntry('header', self.cfg['header'])
        cg.writeEntry('autorange', self.cfg['autorange'])
        cg.writeEntry('min', self.cfg['min'])
        cg.writeEntry('max', self.cfg['max'])
        cg.writeEntry('font', U(self.cfg['font']))
        cg.writeEntry('fontcolor', U(self.cfg['fontcolor']))
        cg.writeEntry('source', repr(self.cfg['source']))
        cg.writeEntry('interval', repr(self.cfg['interval']))
        self.activeSystemmonitorSources = self.parseSystemmonitorSources()
        self.createMeter()

    def showConfigurationInterface(self):
        if isKDEVersion(4,3,74):
            Applet.showConfigurationInterface(self)
            return

        # KDE 4.3
        cfgId = QString('%1settings%2script').arg(self.applet.id()).arg(self.applet.name())
        if KConfigDialog.showDialog(cfgId):
            return
        self.nullManager = KConfigSkeleton()
        self.dlg = KConfigDialog(None, cfgId, self.nullManager)
        self.dlg.setFaceType(KPageDialog.Auto)
        self.dlg.setWindowTitle(i18nc('@title:window', '%1 Settings', self.applet.name()))
        self.dlg.setAttribute(Qt.WA_DeleteOnClose, True)
        self.dlg.showButton(KDialog.Apply, False)
        self.connect(self.dlg, SIGNAL('finished()'), self.nullManager, SLOT('deleteLater()'))

        self.createConfigurationInterface(self.dlg)
        self.dlg.show()

    def createConfigurationInterface(self, dlg):
        # KDE 4.4
        self.configPage = ConfigPage(None, self.applet)
        self.configPage.setData(self.cfg)
        dlg.addPage(self.configPage, i18n('General'), 'applications-utilities')

        self.connect(dlg, SIGNAL('applyClicked()'), self, SLOT('configAccepted()'))
        self.connect(dlg, SIGNAL('okClicked()'), self, SLOT('configAccepted()'))

    def constraintsEvent(self, constraints):
        if constraints & Plasma.FormFactorConstraint:
            self.setBackgroundHints(Plasma.Applet.NoBackground)

def CreateApplet(parent):
    return AnalogMeter(parent)

