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
from config import DEFAULTCFG
from helpers import *

class ComplexPlotter(Applet):
    def __init__(self, parent, args = None):
        Applet.__init__(self, parent)
        self.cfg = {}
        self.sources = {}
        self.plotterData = {}
        self.halfSecondSource = {}
        self.keepAlive = False

    def init(self):
        # To find ui files from package dir
        UiHelper.applet = self.applet

        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        cg = self.config()
        self.cfg['header'] = U(cg.readEntry('header', ''))
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
        self.sources.clear()
        self.plotterData.clear()
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
            layout.addItem(h)
        for plotter in self.cfg['plotters']:
            if self.cfg['plotterheader']:
                h = Plasma.Frame(self.applet)
                h.setText(plotter['name'])
                layout.addItem(h)
            c = DEFAULTCFG.copy()
            c.update(plotter['cfg'])
            p = Plasma.SignalPlotter(self.applet)

            p.setTitle(plotter['name'])
            p.setUnit(c['unit'])
            p.setShowLabels(c['labels'])
            f = QFont()
            f.fromString(c['font'])
            p.setFont(f)
            p.setFontColor(QColor(c['fontcolor']))
            p.setShowTopBar(c['topbar'])
            if len(c['bgcolor']) != 0:
                p.setBackgroundColor(QColor(c['bgcolor']))
            elif QFile.exists(c['bgsvg']):
                p.setSvgBackground(c['bgsvg'])
            else:
                p.setSvgBackground('widgets/plot-background')
            p.setStackPlots(c['stack'])
            p.setVerticalRange(c['min'], c['max'])
            p.setUseAutoRange(c['autorange'])
            p.setShowVerticalLines(c['vlines'])
            p.setVerticalLinesColor(QColor(c['vcolor']))
            p.setVerticalLinesDistance(c['vdistance'])
            p.setVerticalLinesScroll(c['vscroll'])
            p.setHorizontalScale(c['hpixels'])
            p.setShowHorizontalLines(c['hlines'])
            p.setHorizontalLinesColor(QColor(c['hcolor']))
            p.setHorizontalLinesCount(c['hcount'])

            self.plotterData[p] = {}
            self.plotterData[p]['initial'] = [0] * len(plotter['graphs'])
            self.plotterData[p]['values'] = [0.0] * len(plotter['graphs'])
            self.plotterData[p]['current'] = [0] * len(plotter['graphs'])
            for i, graph in enumerate(plotter['graphs']):
                p.addPlot(QColor(graph['color']))
                for c in graph['cfg']:
                    self.sources[c['source']] = (p, i, c, plotter['cfg']['interval'])
                    self.plotterData[p]['initial'][i] += 1
                    self.plotterData[p]['current'][i] += 1
                    if c['dataengine'] == 'systemmonitor':
                        self.connectSystemMonitorSource(c['source'])
                    else:
                        self.dataEngine(c['dataengine']).connectSource(\
                                c['source'], self, plotter['cfg']['interval'])
            self.plotterData[p]['current'] = list(self.plotterData[p]['initial'])
            p.setThinFrame(False)
            layout.addItem(p)

    @pyqtSignature("dataUpdated(const QString &, const Plasma::DataEngine::Data &)")
    def dataUpdated(self, sourceName, data):
        name = U(sourceName)
        #print name
        if name in self.sources:
            source = self.sources[name]
            cfg = source[2]
            #print self.sources, sourceName, data, cfg['value']
            valueName = QString(cfg['value'])
            if valueName in data:
                plotter = source[0]
                index = source[1]
                # Hack for correctly update 'systemmonitor' dataengine ---------------------
                key = cfg['dataengine'] + ':' + cfg['source']
                if key in self.halfSecondSource and self.halfSecondSource[key] == True:
                    self.halfSecondSource[key] = False
                    #self.dataEngine(c['dataengine']).disconnectSource(c['source'], self)
                    self.dataEngine(cfg['dataengine']).connectSource(cfg['source'], \
                                    self, source[3])
                # --------------------------------------------------------------------------
                self.plotterData[plotter]['values'][index] += F(data[valueName])
                self.plotterData[plotter]['current'][index] -= 1
                if self.plotterData[plotter]['current'] == \
                        [0] * len(self.plotterData[plotter]['initial']):
                    plotter.addSample(self.plotterData[plotter]['values'])
                    self.plotterData[plotter]['current'] = \
                            list(self.plotterData[plotter]['initial'])
                    self.plotterData[plotter]['values'] = \
                            [0.0] * len(self.plotterData[plotter]['initial'])

    @pyqtSignature("configAccepted()")
    def configAccepted(self):
        cg = self.config()
        self.cfg = self.dlg.data()
        cg.writeEntry('plotters', repr(self.cfg['plotters']))
        cg.writeEntry('header', self.cfg['header'])
        cg.writeEntry('plotterheader', self.cfg['plotterheader'])
        self.activeSystemmonitorSources = self.parseSystemmonitorSources()
        self.createPlotters()

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
    return ComplexPlotter(parent)

