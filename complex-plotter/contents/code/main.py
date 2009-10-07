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

    def init(self):
        # To find ui files from package dir
        UiHelper.applet = self.applet
        # This trickers source list fill so they are ready when needed (e.g. config)
        self.allSystemmonitorSources = self.applet.dataEngine('systemmonitor').sources()

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

        self.systemmonitorSources = self.systemmonitorSources()
        for source in self.systemmonitorSources:
            if source not in self.allSystemmonitorSources:
                self.connect(self.applet.dataEngine('systemmonitor'),
                                SIGNAL('sourceAdded(const QString&)'), self.sourceAdded)
                return
        self.createPlotters()

    def sourceAdded(self, name):
        print name
        self.allSystemmonitorSources.append(name)
        for source in self.systemmonitorSources:
            if source not in self.allSystemmonitorSources:
                return
        QTimer.singleShot(0, self.createPlotters)

    def systemmonitorSources(self):
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
                        # Hack for correctly update 'systemmonitor' dataengine
                        self.halfSecondSource[c['dataengine'] + c['source']] = True
                        self.dataEngine(c['dataengine']).connectSource(\
                                c['source'], self, 500)
                    else:
                        self.dataEngine(c['dataengine']).connectSource(\
                                c['source'], self, plotter['cfg']['interval'])
            self.plotterData[p]['current'] = list(self.plotterData[p]['initial'])
            p.setThinFrame(False)
            layout.addItem(p)

    @pyqtSignature("dataUpdated(const QString &, const Plasma::DataEngine::Data &)")
    def dataUpdated(self, sourceName, data):
        source = self.sources[U(sourceName)]
        cfg = source[2]
        #print self.sources, sourceName, data, cfg['value']
        valueName = QString(cfg['value'])
        if data.has_key(valueName):
            plotter = source[0]
            index = source[1]
            key = cfg['dataengine'] + cfg['source']
            if self.halfSecondSource[key]:
                # Hack for correctly update 'systemmonitor' dataengine
                self.halfSecondSource[key] = False
                #self.dataEngine(c['dataengine']).disconnectSource(c['source'], self)
                self.dataEngine(cfg['dataengine']).connectSource(cfg['source'], \
                                self, source[3])
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

