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
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *
from PyKDE4.kio import *
from helpers import *

class PlotterDialog(KDialog, UiHelper):
    def __init__(self, parent):
        UiHelper.__init__(self, 'plotter.ui')
        KDialog.__init__(self, parent)

        self.setMainWidget(self.ui)
        self.connect(self.labelsCheck, SIGNAL('stateChanged(int)'), self.enableItems)
        self.connect(self.backgroundCombo, SIGNAL('currentIndexChanged(int)'), self.enableItems)
        self.connect(self.autorangeCheck, SIGNAL('stateChanged(int)'), self.enableItems)
        self.connect(self.vlinesCheck, SIGNAL('stateChanged(int)'), self.enableItems)
        self.connect(self.hlinesCheck, SIGNAL('stateChanged(int)'), self.enableItems)
        self.enableItems()

    def setData(self, data):
        interval = data['interval']
        a = [1000, 60, 60, 24]
        for i, m in enumerate(a):
            if interval % m != 0 or i == len(a) - 1 or interval == 0:
                self.intervalSpin.setValue(interval)
                self.intervalCombo.setCurrentIndex(i)
                break
            interval /= m
        self.unitEdit.setText(data['unit'])
        self.scaleEdit.setText(str(data['scale']))
        self.labelsCheck.setChecked(data['labels'])
        f = QFont()
        f.fromString(data['font'])
        self.labelFont.setFont(f)
        self.fontColorCombo.setColor(QColor(data['fontcolor']))
        self.topbarCheck.setChecked(data['topbar'])
        if len(data['bgcolor']) == 0 and len(data['bgsvg']) == 0:
            self.backgroundCombo.setCurrentIndex(0)
        elif len(data['bgcolor']) != 0:
            self.backgroundCombo.setCurrentIndex(1)
            self.bgColorCombo.setColor(QColor(data['bgcolor']))
        else:
            self.backgroundCombo.setCurrentIndex(2)
            self.bgSvgCombo.setText(data['bgsvg'])
        self.bgSvgCombo.comboBox().addItem(i18n('Default'))
        self.stackCheck.setChecked(data['stack'])
        self.autorangeCheck.setChecked(data['autorange'])
        self.maxEdit.setText(str(data['max']))
        self.minEdit.setText(str(data['min']))
        self.vlinesCheck.setChecked(data['vlines'])
        self.vcolorCombo.setColor(QColor(data['vcolor']))
        self.vdistanceSpin.setValue(data['vdistance'])
        self.vscrollCheck.setChecked(data['vscroll'])
        self.hpixelsSpin.setValue(data['hpixels'])
        self.hlinesCheck.setChecked(data['hlines'])
        self.hcolorCombo.setColor(QColor(data['hcolor']))
        self.hcountSpin.setValue(data['hcount'])
        self.enableItems()

    def data(self):
        data = {}
        a = [1, 1000, 60 * 1000, 60 * 60 * 1000, 24 * 60 * 60 * 1000]
        data['interval'] = self.intervalSpin.value() * a[self.intervalCombo.currentIndex()]
        data['unit'] = U(self.unitEdit)
        data['scale'] = float(self.scaleEdit.text())
        data['labels'] = self.labelsCheck.isChecked()
        data['font'] = U(self.labelFont.font())
        data['fontcolor'] = U(self.fontColorCombo.color())
        data['topbar'] = self.topbarCheck.isChecked()
        data['bgcolor'] = ''
        data['bgsvg'] = ''
        if self.backgroundCombo.currentIndex() == 1:
            data['bgcolor'] = U(self.bgColorCombo.color())
        elif self.backgroundCombo.currentIndex() == 1:
            data['bgsvg'] = U(self.bgSvgCombo.text())
        data['stack'] = self.stackCheck.isChecked()
        data['autorange'] = self.autorangeCheck.isChecked()
        data['max'] = float(self.maxEdit.text())
        data['min'] = float(self.minEdit.text())
        data['vlines'] = self.vlinesCheck.isChecked()
        data['vcolor'] = U(self.vcolorCombo.color())
        data['vdistance'] = self.vdistanceSpin.value()
        data['vscroll'] = self.vscrollCheck.isChecked()
        data['hpixels'] = self.hpixelsSpin.value()
        data['hlines'] = self.hlinesCheck.isChecked()
        data['hcolor'] = U(self.hcolorCombo.color())
        data['hcount'] = self.hcountSpin.value()
        return data

    def enableItems(self):
        self.labelFont.setEnabled(self.labelsCheck.isChecked())
        self.fontLabel.setEnabled(self.labelsCheck.isChecked())
        self.bgColorLabel.setVisible(self.backgroundCombo.currentIndex() == 1)
        self.bgColorCombo.setVisible(self.backgroundCombo.currentIndex() == 1)
        self.bgSvgLabel.setVisible(self.backgroundCombo.currentIndex() == 2)
        self.bgSvgCombo.setVisible(self.backgroundCombo.currentIndex() == 2)
        self.minLabel.setEnabled(not self.autorangeCheck.isChecked())
        self.minEdit.setEnabled(not self.autorangeCheck.isChecked())
        self.maxLabel.setEnabled(not self.autorangeCheck.isChecked())
        self.maxEdit.setEnabled(not self.autorangeCheck.isChecked())
        self.vcolorLabel.setEnabled(self.vlinesCheck.isChecked())
        self.vcolorCombo.setEnabled(self.vlinesCheck.isChecked())
        self.vdistanceLabel.setEnabled(self.vlinesCheck.isChecked())
        self.vdistanceSpin.setEnabled(self.vlinesCheck.isChecked())
        self.vscrollLabel.setEnabled(self.vlinesCheck.isChecked())
        self.vscrollCheck.setEnabled(self.vlinesCheck.isChecked())
        self.hcolorLabel.setEnabled(self.hlinesCheck.isChecked())
        self.hcolorCombo.setEnabled(self.hlinesCheck.isChecked())
        self.hcountLabel.setEnabled(self.hlinesCheck.isChecked())
        self.hcountSpin.setEnabled(self.hlinesCheck.isChecked())
