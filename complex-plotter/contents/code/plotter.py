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

        self.graphCount = 0
        self.setMainWidget(self.ui)
        self.connect(self.labelsCheck, SIGNAL('stateChanged(int)'), self.enableItems)
        self.connect(self.backgroundCombo, SIGNAL('currentIndexChanged(int)'), self.enableItems)
        self.connect(self.autorangeCheck, SIGNAL('stateChanged(int)'), self.enableItems)
        self.connect(self.vlinesCheck, SIGNAL('stateChanged(int)'), self.enableItems)
        self.connect(self.hlinesCheck, SIGNAL('stateChanged(int)'), self.enableItems)
        self.connect(self.valuePlacementCombo, SIGNAL('currentIndexChanged(int)'), self.enableItems)
        self.connect(self.valueFormatEdit, SIGNAL('textChanged(const QString&)'), self.setExample)
        self.connect(self.valueLabelFont, SIGNAL('fontSelected(const QFont&)'), self.setExample)
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
        self.maxEdit.setText(U(data['max']))
        self.minEdit.setText(U(data['min']))
        self.vlinesCheck.setChecked(data['vlines'])
        self.vcolorCombo.setColor(QColor(data['vcolor']))
        self.vdistanceSpin.setValue(data['vdistance'])
        self.vscrollCheck.setChecked(data['vscroll'])
        self.hpixelsSpin.setValue(data['hpixels'])
        self.hlinesCheck.setChecked(data['hlines'])
        self.hcolorCombo.setColor(QColor(data['hcolor']))
        self.hcountSpin.setValue(data['hcount'])
        self.valuePlacementCombo.setCurrentIndex(data['valueplace'])
        self.valueFormatEdit.setText(data['valueformat'])
        f = QFont()
        f.fromString(data['valuefont'])
        self.valueLabelFont.setFont(f)
        self.graphCount = data['graphCount']
        self.enableItems()
        self.setExample()

    def data(self):
        data = {}
        a = [1, 1000, 60 * 1000, 60 * 60 * 1000, 24 * 60 * 60 * 1000]
        data['interval'] = self.intervalSpin.value() * a[self.intervalCombo.currentIndex()]
        data['unit'] = U(self.unitEdit)
        data['scale'] = F(self.scaleEdit)
        data['labels'] = self.labelsCheck.isChecked()
        data['font'] = U(self.labelFont.font())
        data['fontcolor'] = U(self.fontColorCombo)
        data['topbar'] = self.topbarCheck.isChecked()
        data['bgcolor'] = u''
        data['bgsvg'] = u''
        if self.backgroundCombo.currentIndex() == 1:
            data['bgcolor'] = U(self.bgColorCombo)
        elif self.backgroundCombo.currentIndex() == 1:
            data['bgsvg'] = U(self.bgSvgCombo)
        data['stack'] = self.stackCheck.isChecked()
        data['autorange'] = self.autorangeCheck.isChecked()
        data['max'] = F(self.maxEdit)
        data['min'] = F(self.minEdit)
        data['vlines'] = self.vlinesCheck.isChecked()
        data['vcolor'] = U(self.vcolorCombo)
        data['vdistance'] = self.vdistanceSpin.value()
        data['vscroll'] = self.vscrollCheck.isChecked()
        data['hpixels'] = self.hpixelsSpin.value()
        data['hlines'] = self.hlinesCheck.isChecked()
        data['hcolor'] = U(self.hcolorCombo)
        data['hcount'] = self.hcountSpin.value()
        data['valueplace'] = self.valuePlacementCombo.currentIndex()
        data['valueformat'] = U(self.valueFormatEdit)
        data['valuefont'] = U(self.valueLabelFont.font())
        return data

    def enableItems(self):
        ver = isKDEVersion(4,3,74)
        self.valueLabel.setVisible(ver)
        self.valuePlacementCombo.setVisible(ver)
        self.valueFormatLabel.setVisible(ver)
        self.valueFormatEdit.setVisible(ver)
        self.exampleTitleLabel.setVisible(ver)
        self.valueExampleLabel.setVisible(ver)
        self.valueFontLabel.setVisible(ver)
        self.valueLabelFont.setVisible(ver)
        enabled = (self.valuePlacementCombo.currentIndex() != 0)
        self.valueFormatLabel.setEnabled(enabled)
        self.valueFormatEdit.setEnabled(enabled)
        self.exampleTitleLabel.setEnabled(enabled)
        self.valueExampleLabel.setEnabled(enabled)
        self.valueFontLabel.setEnabled(enabled)
        self.valueLabelFont.setEnabled(enabled)
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

    def setExample(self):
        self.valueExampleLabel.setFont(self.valueLabelFont.font())
        s = U(self.valueFormatEdit.text())
        valueArgs = {}
        for i in range(self.graphCount):
            valueArgs['value%d' % i] = 31.2345
            valueArgs['max%d' % i] = 100.0
            valueArgs['min%d' % i] = 0.0
            valueArgs['unit%d' % i] = u'°C'
            valueArgs['name%d' % i] = u'CPU Temp'
        try:
            self.exampleTitleLabel.setText(i18n('e.g.: '))
            s = s.format(**valueArgs)
        except:
            self.exampleTitleLabel.setText(i18n('error: '))
            (exception_type, value, exception_traceback) = sys.exc_info()
            s = U(value)
        self.valueExampleLabel.setText(s)
