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
from PyKDE4.kdeui import *
from helpers import *

class AddDialog(KDialog, UiHelper):
    def __init__(self, parent, applet):
        UiHelper.__init__(self, 'add.ui')
        KDialog.__init__(self, parent)

        self.setMainWidget(self.ui)
        sensors = {}
        engine = applet.dataEngine('systemmonitor')
        for sensor in engine.sources():
            data = engine.query(sensor)
            item = QListWidgetItem()
            if QString(u'name') in data:
                item.setText(data[QString(u'name')].toString())
            else:
                item.setText(sensor)
            item.setData(Qt.UserRole, sensor)
            self.searchList.addItem(item)

        self.searchEdit.setListWidget(self.searchList)
        self.searchList.sortItems()
        QTimer.singleShot(0, self.searchEdit.setFocus)

    def selected(self):
        item = self.searchList.currentItem()
        if item is not None:
            d = item.data(Qt.UserRole)
            if d.typeName() == 'QString':
                data = {}
                data['name'] = unicode(item.text())
                data['dataengine'] = u'systemmonitor'
                data['source'] = unicode(item.data(Qt.UserRole).toString())
                data['value'] = u'value'
                data['min'] = u'min'
                data['max'] = u'max'
                data['unit'] = u'units'
                return data
            else:
                return eval(unicode(item.data(Qt.UserRole).toString()))
        return None

