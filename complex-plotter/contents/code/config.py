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
from add import AddDialog
from plotter import PlotterDialog
from helpers import *

DEFAULTCFG = {
    'interval': 60000,
    'unit': '',
    'scale': 1,
    'labels': True,
    'font': 'Sans,8,-1,5,50,0,0,0,0,0',
    'fontcolor': '#000000',
    'topbar': False,
    'bgcolor': '',
    'bgsvg': U(i18n('Default')),
    'stack': True,
    'autorange': True,
    'max': 100,
    'min': 0,
    'vlines': False,
    'vcolor': '#000000',
    'vdistance': 50,
    'vscroll': False,
    'hpixels': 1,
    'hlines': True,
    'hcolor': '#000000',
    'hcount': 5,
    'valueplace': 0,
    'valueformat': '{value0:1.1f} {unit0}',
    'valuefont': 'Sans,8,-1,5,50,0,0,0,0,0'
}

class ComplexDelegate(QStyledItemDelegate):
    def __init__(self, parent):
        QStyledItemDelegate.__init__(self, parent)

    def paint(self, painter, option, index):
        QStyledItemDelegate.paint(self, painter, option, index)
        if index.column() == 1 and self.isGraph(index):
            color = U(index.data())
            if len(color) > 0:
                rc = option.rect
                rc.adjust(2, 5, -2, -5)
                painter.fillRect(rc, QColor(color))

    def isGraph(self, index):
        return index.parent().isValid()

    def createEditor(self, parent, option, index):
        if index.column() == 1:
            if self.isGraph(index):
                return KColorCombo(parent)
            else:
                return None
        else:
            return QStyledItemDelegate.createEditor(self, parent, option, index)

    def setEditorData(self, editor, index):
        if index.column() == 1 and self.isGraph(index):
            editor.setColor(QColor(U(index.data())))
        else:
            return QStyledItemDelegate.setEditorData(self, editor, index)

    def setModelData(self, editor, model, index):
        if index.column() == 1 and self.isGraph(index):
            model.setData(index, editor.color().name())
        else:
            return QStyledItemDelegate.setModelData(self, editor, model, index)

    def sizeHint(self, option, index):
        hint = QStyledItemDelegate.sizeHint(self, option, index)
        hint.setHeight(max(hint.height(), 25)) # Get this from somewhere...
        return hint

class ConfigPage(QWidget, UiHelper):
    def __init__(self, parent, applet):
        QWidget.__init__(self, parent)
        UiHelper.__init__(self, 'config.ui', self)

        self.applet = applet
        self.plottersTreeView.setItemDelegate(ComplexDelegate(self))
        self.model = QStandardItemModel(self)
        self.model.setHeaderData(0, Qt.Horizontal, i18n("Name"))
        self.plottersTreeView.setModel(self.model)
        self.model.setHorizontalHeaderLabels([i18n('Name'), i18n('Color')])
        self.plottersTreeView.header().setStretchLastSection(False)
        self.plottersTreeView.header().resizeSection(1, 125)
        self.plottersTreeView.header().setResizeMode(0, QHeaderView.Stretch)
        self.plottersTreeView.header().setResizeMode(1, QHeaderView.Fixed)

        self.connect(self.addGraphButton, SIGNAL('clicked()'), self.addGraphButtonClicked)
        self.connect(self.addPlotterButton, SIGNAL('clicked()'), self.addPlotterButtonClicked)
        self.connect(self.removeButton, SIGNAL('clicked()'), self.removeButtonClicked)
        self.connect(self.upButton, SIGNAL('clicked()'), self.upButtonClicked)
        self.connect(self.downButton, SIGNAL('clicked()'), self.downButtonClicked)
        self.connect(self.configureAllPlottersButton, SIGNAL('clicked()'),
                     self.configureAllPlottersButtonClicked)
        self.connect(self.configurePlotterButton, SIGNAL('clicked()'),
                     self.configurePlotterButtonClicked)
        self.connect(self.plottersTreeView.selectionModel(),
                     SIGNAL('selectionChanged(const QItemSelection&, const QItemSelection&)'),
                     self.enableItems)
        self.enableItems()

    def setData(self, data):
        self.headerEdit.setText(data['header'])
        self.headerCheck.setChecked(data['plotterheader'])
        self.panelRatioSpinBox.setValue(data['panelRatio'])
        f = QFont()
        f.fromString(data['headerfont'])
        self.headerFont.setFont(f)
        for plotter in data['plotters']:
            c = DEFAULTCFG.copy()
            c.update(plotter['cfg'])
            p = self.addPlotter(plotter['name'], c)
            for graph in plotter['graphs']:
                self.addGraph(graph['name'], graph['color'], graph['cfg'], p)

    def data(self):
        data = {}
        data['header'] = U(self.headerEdit)
        data['headerfont'] = U(self.headerFont.font())
        data['plotterheader'] = self.headerCheck.isChecked()
        data['panelRatio'] = self.panelRatioSpinBox.value()
        data['plotters'] = []
        for i in range(self.model.rowCount()):
            p = self.model.item(i)
            plotter = {}
            plotter['name'] = U(p)
            plotter['cfg'] = eval(U(p.data()))
            plotter['graphs'] = []
            for j in range(p.rowCount()):
                graph = {}
                g = p.child(j)
                graph['name'] = U(g)
                graph['cfg'] = eval(U(g.data()))
                graph['color'] = U(p.child(j, 1))
                plotter['graphs'].append(graph)
            data['plotters'].append(plotter)
        return data

    def enableItems(self):
        self.headerFont.setVisible(isKDEVersion(4,3,74))
        self.headerFontLabel.setVisible(isKDEVersion(4,3,74))
        index = self.plottersTreeView.selectionModel().currentIndex()
        item = self.model.itemFromIndex(index)
        if item is None:
            rows = 0
        elif item.parent() is None:
            rows = self.model.rowCount()
        else:
            rows = item.parent().rowCount()

        self.removeButton.setEnabled(index.isValid())
        self.upButton.setEnabled(index.row() > 0)
        self.downButton.setEnabled(index.isValid() and index.row() < rows - 1)
        self.configureAllPlottersButton.setEnabled(self.model.rowCount() > 0)
        self.configurePlotterButton.setEnabled(not item is None and item.parent() is None)

    def addGraphButtonClicked(self):
        dlg = AddDialog(self, self.applet)
        if dlg.exec_() == QDialog.Accepted:
            s = dlg.selected()
            if s is not None:
                self.addGraph(s['name'], '#000000', [s])

    def addPlotterButtonClicked(self):
        self.addPlotter()

    def removeButtonClicked(self):
        index = self.plottersTreeView.selectionModel().currentIndex()
        if self.model.removeRow(index.row(), index.parent()):
            self.enableItems()

    def configureAllPlottersButtonClicked(self):
        dlg = PlotterDialog(self)
        data = eval(U(self.model.item(0).data()))
        data['graphCount'] = 0
        for i in range(self.model.rowCount()):
            if self.model.item(i).rowCount() > data['graphCount']:
                data['graphCount'] = self.model.item(i).rowCount()
        dlg.setData(data)
        if dlg.exec_() == QDialog.Accepted:
            for i in range(self.model.rowCount()):
                self.model.item(i).setData(repr(dlg.data()))

    def configurePlotterButtonClicked(self):
        index = self.plottersTreeView.selectionModel().currentIndex()
        item = self.model.itemFromIndex(index)
        dlg = PlotterDialog(self)
        data = eval(U(item.data()))
        data['graphCount'] = item.rowCount()
        dlg.setData(data)
        if dlg.exec_() == QDialog.Accepted:
            item.setData(repr(dlg.data()))

    def upButtonClicked(self):
        self.move(-1)

    def downButtonClicked(self):
        self.move(1)

    def move(self, direction):
        index = self.plottersTreeView.selectionModel().currentIndex()
        item = self.model.itemFromIndex(index)
        if item.parent() is None:
            items = self.model.takeRow(index.row())
            self.model.insertRow(index.row() + direction, items)
        else:
            parent = item.parent()
            items = parent.takeRow(index.row())
            parent.insertRow(index.row() + dir, items)
        self.selectAndScroll(items[0])

    def selectAndScroll(self, item):
        self.plottersTreeView.expandAll()
        self.plottersTreeView.selectionModel().setCurrentIndex(item.index(),
                QItemSelectionModel.ClearAndSelect)
        self.plottersTreeView.scrollTo(item.index())
        self.enableItems()

    def addPlotter(self, name = i18n('Plotter'), cfg = DEFAULTCFG):
        item = QStandardItem(name)
        font = QFont(item.data(Qt.FontRole))
        font.setBold(True)
        item.setData(font, Qt.FontRole)
        item.setData(repr(cfg))
        self.model.appendRow([item])
        self.selectAndScroll(item)
        return item

    def addGraph(self, name, color, cfg, parent = None):
        if parent is None:
            if self.model.rowCount() == 0:
                self.addPlotter()
            index = self.plottersTreeView.selectionModel().currentIndex()
            if not index.isValid():
                parent = self.model.item(0)
            else:
                parent = self.model.itemFromIndex(index)
            if parent.parent() != None:
                parent = parent.parent()
        item = QStandardItem(name)
        item.setData(repr(cfg))
        parent.appendRow([item, QStandardItem(color)])
        self.selectAndScroll(item)
