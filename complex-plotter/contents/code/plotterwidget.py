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
from PyKDE4.plasma import Plasma
from config import DEFAULTCFG
from helpers import *
from string import Formatter

class ComplexPlotterWidget(QGraphicsWidget):
    def __init__(self, parent, cfg, header):
        QGraphicsWidget.__init__(self, parent)
        self.name = cfg['name']
        self.header = header
        self.cfg =  DEFAULTCFG.copy()
        self.cfg.update(cfg['cfg'])
        self.graphs = cfg['graphs']
        self.setLayout(QGraphicsLinearLayout(Qt.Vertical))
        self.setContentsMargins(0, 0, 0, 0)
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.formatter = Formatter()

        f = QFont()
        if self.header:
            header = Plasma.Frame(self)
            header.setText(plotter['name'])
            if isKDEVersion(4,3,74):
                f.fromString(self.cfg['headerfont'])
                header.setFont(f)
            layout().addItem(header)

        self.plotter = Plasma.SignalPlotter(self)
        self.plotter.setTitle(self.name)
        self.plotter.setUnit(self.cfg['unit'])
        self.plotter.setShowLabels(self.cfg['labels'])
        f.fromString(self.cfg['font'])
        self.plotter.setFont(f)
        self.plotter.setFontColor(QColor(self.cfg['fontcolor']))
        self.plotter.setShowTopBar(self.cfg['topbar'])
        if len(self.cfg['bgcolor']) > 0:
            self.plotter.setSvgBackground('')
            self.plotter.setBackgroundColor(QColor(self.cfg['bgcolor']))
        elif len(self.cfg['bgsvg']) > 0:
            self.plotter.setSvgBackground(self.cfg['bgsvg'])
        else:
            color = QColor()
            color.setAlpha(0)
            self.plotter.setBackgroundColor(color)
            self.plotter.setSvgBackground('')
        self.plotter.setStackPlots(self.cfg['stack'])
        self.plotter.setVerticalRange(self.cfg['min'], self.cfg['max'])
        self.plotter.setUseAutoRange(self.cfg['autorange'])
        self.plotter.setShowVerticalLines(self.cfg['vlines'])
        self.plotter.setVerticalLinesColor(QColor(self.cfg['vcolor']))
        self.plotter.setVerticalLinesDistance(self.cfg['vdistance'])
        self.plotter.setVerticalLinesScroll(self.cfg['vscroll'])
        self.plotter.setHorizontalScale(self.cfg['hpixels'])
        self.plotter.setShowHorizontalLines(self.cfg['hlines'])
        self.plotter.setHorizontalLinesColor(QColor(self.cfg['hcolor']))
        self.plotter.setHorizontalLinesCount(self.cfg['hcount'])
        self.plotter.scale(self.cfg['scale'])

        self.valueLabel = None
        if self.cfg['valueplace'] != 0 and isKDEVersion(4,3,74):
            row = int((self.cfg['valueplace'] - 1) / 3)
            col = (self.cfg['valueplace'] - 1) % 3
            self.valueLabel = Plasma.Frame(self.plotter)
            f.fromString(self.cfg['valuefont'])
            self.valueLabel.setFont(f)
            self.valueLabel.setZValue(10)
            hl = QGraphicsLinearLayout(Qt.Horizontal)
            if col > 0:
                hl.addStretch()
            hl.addItem(self.valueLabel)
            if col < 2:
                hl.addStretch()
            vl = QGraphicsLinearLayout(Qt.Vertical)
            if row > 0:
                vl.addStretch()
            vl.addItem(hl)
            if row < 2:
                vl.addStretch()
            self.plotter.setLayout(vl)

        self.initial = [0] * len(self.graphs)
        self.values = [0.0] * len(self.graphs)
        self.allUpdated = [0] * len(self.graphs)
        self.source2GraphIndex = {}
        self.sourceData = {}
        self.valueArgs = {}
        for i, graph in enumerate(self.graphs):
            self.plotter.addPlot(QColor(graph['color']))
            for source in graph['cfg']:
                self.source2GraphIndex[source['source']] = i
                self.sourceData[source['source']] = source
            self.initial[i] = len(graph['cfg'])
        self.current = list(self.initial)
        self.plotter.setThinFrame(False)
        self.layout().addItem(self.plotter)

    def interval(self):
        return self.cfg['interval']

    def sources(self):
        return self.sourceData

    def dataUpdated(self, name, data):
        #print name
        graphIndex = self.source2GraphIndex[name]
        source = self.sourceData[name]
        valueName = QString(source['value'])
        if valueName in data:
            # net has sometimes negative values
            if source['source'].startswith('network'):
                self.values[graphIndex] += max(0.0, F(data[valueName]))
            else:
                self.values[graphIndex] += F(data[valueName])
            self.current[graphIndex] -= 1
            if self.valueLabel:
                self.valueArgs['value%d' % graphIndex] = F(data[valueName])
                self.valueArgs['max%d' % graphIndex] = F(data[QString(source['max'])])
                self.valueArgs['min%d' % graphIndex] = F(data[QString(source['min'])])
                self.valueArgs['unit%d' % graphIndex] = U(data[QString(source['unit'])])
                self.valueArgs['name%d' % graphIndex] = source['name']
            if self.current == self.allUpdated:
                self.plotter.addSample(self.values)
                if self.valueLabel:
                    try:
                        self.valueLabel.setText(self.cfg['valueformat'].format(**self.valueArgs))
                    except:
                        pass
                self.current = list(self.initial)
                self.values = [0.0] * len(self.initial)
