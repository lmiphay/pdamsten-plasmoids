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

from PyQt4.QtCore import Qt
from PyQt4.QtCore import SIGNAL
from PyQt4.QtCore import QRectF
from PyQt4.QtGui  import QPainter
from PyKDE4.plasma import Plasma
from fader import Fader
from image import ImagePainter
from button import ButtonHelper

class Slider(ButtonHelper, ImagePainter, Plasma.Slider):
    def __init__(self, parent = None):
        Plasma.Slider.__init__(self, parent)
        self.setOrientation(Qt.Horizontal)
        ImagePainter.__init__(self)
        ButtonHelper.__init__(self)
