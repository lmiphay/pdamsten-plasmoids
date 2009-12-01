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
from config import DEFAULTCFG
from plotterwidget import ComplexPlotterWidget
from helpers import *

QWIDGETSIZE_MAX = 16777215

class ComplexPlotter(Applet):
    def __init__(self, parent, args = None):
        Applet.__init__(self, parent)
        self.cfg = {}
        self.halfSecondSource = {}
        self.keepAlive = False
        self.plotters = {}

    def init(self):
        # To find ui files from package dir
        UiHelper.applet = self.applet

        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        cg = self.config()
        self.cfg['panelRatio'] = F(cg.readEntry('panelRatio', '0.0'))
        self.cfg['header'] = U(cg.readEntry('header', ''))
        self.cfg['headerfont'] = U(cg.readEntry('headerfont', ''))
        self.cfg['plotterheader'] = cg.readEntry('plotterheader', False).toBool()
        try:
            self.cfg['plotters'] = eval(U(cg.readEntry('plotters', '')))
            # Check for 0.1
            for plotter in self.cfg['plotters']:
                for graph in plotter['graphs']:
                    for i, source in enumerate(graph['cfg']):
                        if isinstance(graph['cfg'][i], tuple):
                            graph['cfg'][i] = {}
                            graph['cfg'][i]['dataengine'] = source[0]
                            graph['cfg'][i]['source'] = source[1]
                            graph['cfg'][i]['value'] = source[2]
                            graph['cfg'][i]['max'] = u'max'
                            graph['cfg'][i]['min'] = u'min'
                            graph['cfg'][i]['unit'] = u'units'
        except:
            self.cfg['plotters'] = {}

        self.smengine = self.applet.dataEngine('systemmonitor')
        self.allSystemmonitorSources = self.smengine.sources()
        self.activeSystemmonitorSources = self.parseSystemmonitorSources()
        self.createPlotters()
        self.connect(self.smengine, SIGNAL('sourceAdded(const QString&)'), self.sourceAdded)
        self.connect(self.smengine, SIGNAL('sourceRemoved(const QString&)'), self.sourceRemoved)
        if len(self.allSystemmonitorSources) == 0:
            self.sourceTimer = QTimer()
            self.sourceTimer.setSingleShot(True)
            self.connect(self.sourceTimer, SIGNAL('timeout()'), self.checkKeepAlive)
        else:
            self.sourceTimer = None

    def sourceAdded(self, name):
        self.allSystemmonitorSources.append(name)
        if name in self.activeSystemmonitorSources:
            self.connectSystemMonitorSource(name)
        if self.sourceTimer != None and not self.sourceTimer.isActive():
            self.sourceTimer.start(0)

    def connectSystemMonitorSource(self, name):
        if name in self.allSystemmonitorSources:
            # Hack for correctly update 'systemmonitor' dataengine
            self.halfSecondSource[U('systemmonitor:' + name)] = True
            self.smengine.connectSource(name, self, 500)
            self.checkKeepAlive()

    def sourceRemoved(self, name):
        self.allSystemmonitorSources.removeAll(name)
        self.checkKeepAlive()

    def checkKeepAlive(self):
        # Another hack to get sourceAdded signals when we have only one source
        # TODO Fix these in systemmonitor dataengine someday
        self.sourceTimer = None
        count = 0
        for source in self.activeSystemmonitorSources:
            if source in self.allSystemmonitorSources:
                count += 1
        if count == 0 and not self.keepAlive:
            #print 'connect network/interfaces/lo/receiver/data'
            self.keepAlive = True
            self.smengine.connectSource('network/interfaces/lo/receiver/data', self, 1000)
        elif count > 0 and self.keepAlive:
            #print 'disconnect'
            self.keepAlive = False
            self.smengine.disconnectSource('network/interfaces/lo/receiver/data', self)

    def parseSystemmonitorSources(self):
        result = []
        if self.cfg['plotters']:
            for plotter in self.cfg['plotters']:
                for graph in plotter['graphs']:
                    for cfg in graph['cfg']:
                        if cfg['dataengine'] == 'systemmonitor':
                            result.append(cfg['source'])
        return result

    def createPlotters(self):
        layout = self.applet.layout()
        if layout is None:
            layout = QGraphicsLinearLayout(Qt.Vertical, self.applet)
            layout.setContentsMargins(0, 0, 0, 0)
            layout.setSpacing(0)
        while layout.count() > 0:
            item = layout.itemAt(0)
            layout.removeAt(0)
            del item
        if len(self.cfg['plotters']) < 1:
            self.setConfigurationRequired(True, i18n('No plotters configured'))
            return
        self.setConfigurationRequired(False, '')

        if len(self.cfg['header']) > 0:
            h = Plasma.Frame(self.applet)
            h.setText(self.cfg['header'])
            if isKDEVersion(4,3,74):
                f = QFont()
                f.fromString(self.cfg['headerfont'])
                h.setFont(f)
            layout.addItem(h)
        self.plotters.clear()
        for plotter in self.cfg['plotters']:
            p = ComplexPlotterWidget(self.applet, plotter, self.cfg)
            for source in p.sources().values():
                self.plotters[source['source']] = p
                if source['dataengine'] == 'systemmonitor':
                    self.connectSystemMonitorSource(source['source'])
                else:
                    self.dataEngine(source['dataengine']).connectSource(\
                            source['source'], self, plotter['cfg']['interval'])
            layout.addItem(p)

    @pyqtSignature("dataUpdated(const QString &, const Plasma::DataEngine::Data &)")
    def dataUpdated(self, sourceName, data):
        name = U(sourceName)
        #print name
        if name in self.plotters:
            plotter = self.plotters[name]
            # Hack for correctly update 'systemmonitor' dataengine ---------------------
            source = plotter.sources()[name]
            key = source['dataengine'] + ':' + name
            if key in self.halfSecondSource and self.halfSecondSource[key] == True:
                self.halfSecondSource[key] = False
                #self.dataEngine(c['dataengine']).disconnectSource(c['source'], self)
                self.dataEngine(source['dataengine']).connectSource(source['source'], \
                                self, plotter.interval())
            # --------------------------------------------------------------------------
            plotter.dataUpdated(name, data)

    @pyqtSignature("configAccepted()")
    def configAccepted(self):
        cg = self.config()
        self.cfg = self.configPage.data()
        cg.writeEntry('plotters', repr(self.cfg['plotters']))
        cg.writeEntry('header', self.cfg['header'])
        cg.writeEntry('headerfont', self.cfg['headerfont'])
        cg.writeEntry('plotterheader', self.cfg['plotterheader'])
        cg.writeEntry('panelRatio', self.cfg['panelRatio'])
        self.activeSystemmonitorSources = self.parseSystemmonitorSources()
        self.createPlotters()
        self.constraintsEvent(Plasma.FormFactorConstraint)

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
            minSize = self.layout().minimumSize()
            # print minSize, self.size(), self.cfg['panelRatio']
            if self.formFactor() == Plasma.Horizontal and self.cfg['panelRatio'] > 0.0:
                self.setMinimumWidth(self.size().height() * self.cfg['panelRatio'])
                self.setMaximumWidth(self.size().height() * self.cfg['panelRatio'])
                self.setMinimumHeight(minSize.height())
                self.setMaximumHeight(QWIDGETSIZE_MAX)
            elif self.formFactor() == Plasma.Vertical and self.cfg['panelRatio'] > 0.0:
                self.setMinimumWidth(minSize.width())
                self.setMaximumWidth(QWIDGETSIZE_MAX)
                self.setMinimumHeight(self.size().width() * self.cfg['panelRatio'])
                self.setMaximumHeight(self.size().width() * self.cfg['panelRatio'])
            else:
                self.setMinimumHeight(minSize.height())
                self.setMaximumHeight(QWIDGETSIZE_MAX)
                self.setMinimumWidth(minSize.width())
                self.setMaximumWidth(QWIDGETSIZE_MAX)
            # print self.minimumSize(), self.maximumSize(), self.size()
        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))

def CreateApplet(parent):
    return ComplexPlotter(parent)

