# -*- coding: utf-8 -*-
#
#   Copyright (C) 2009 Marco Martin <notmart@gmail.com>
#   Copyright (C) 2009 Petri Damstén <damu@iki.fi>
#
#   This program is free software you can redistribute it and/or modify
#   it under the terms of the GNU Library General Public License as
#   published by the Free Software Foundation either version 2, or
#   (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details
#
#   You should have received a copy of the GNU Library General Public
#   License along with this program if not, write to the
#   Free Software Foundation, Inc.,
#   51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

class Resizer():
    def __init__(self):
        self.actions = []
        self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
        toggleFixed = QAction(i18n('Set Flexible Size'), self)
        toggleFixed.setCheckable(True)
        self.actions.append(toggleFixed)
        self.addAction('toggle fixed', toggleFixed)
        self.connect(toggleFixed, SIGNAL('toggled(bool)'), self.toggleFixed)
        self.setCacheMode(DeviceCoordinateCache)

    def contextualActions():
        return self.actions

    def toggleFixed(flexible):
        self.fixedSize = not flexible
        if not self.fixedSize:
            self.setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
            self.setMinimumSize(0, 0)
        elif self.formFactor() == Plasma.Horizontal:
            self.setMaximumWidth(self.size().width())
            self.setMinimumWidth(self.size().width())
        elif self.formFactor() == Plasma.Vertical:
            self.setMaximumHeight(self.size().height())
            self.setMinimumHeight(self.size().height())

    def init(self):
        print '*******************'
        if self.containment():
            self.connect(self.containment(), SIGNAL('toolBoxVisibilityChanged(bool)'),
                         self.updateConfigurationMode)

        self.fixedSize = self.config().readEntry('FixedSize', False)
        fixedAction = self.action('toggle fixed')
        if fixedAction:
            fixedAction.setChecked(not self.fixedSize)

    def constraintsEvent(constraints):
        if constraints & Plasma.FormFactorConstraint:
            if formFactor() == Plasma.Horizontal:
                self.setMinimumWidth(self.minimumHeight())
                self.setMaximumWidth(self.maximumHeight())
                self.setMaximumHeight(QWIDGETSIZE_MAX)
                self.setMinimumHeight(0)
            elif formFactor() == Plasma.Vertical:
                self.setMinimumHeight(self.minimumWidth())
                self.setMaximumHeight(self.maximumWidth())
                self.setMaximumWidth(QWIDGETSIZE_MAX)
                self.setMinimumWidth(0)

        if constraints & Plasma.StartupCompletedConstraint:
            if not self.fixedSize:
                self.setMaximumSize(QWIDGETSIZE_MAX, QWIDGETSIZE_MAX)
                self.setMinimumSize(0, 0)
            elif self.formFactor() == Plasma.Horizontal:
                self.setMaximumWidth(self.size().width())
                self.setMinimumWidth(self.size().width())
            elif self.formFactor() == Plasma.Vertical:
                self.setMaximumHeight(self.size().height())
                self.setMinimumHeight(self.size().height())

        if constraints & Plasma.SizeConstraint:
            self.fixedSize = ((self.formFactor() == Plasma.Horizontal and \
                               self.maximumWidth() == self.minimumWidth()) or \
                              (self.formFactor() == Plasma.Vertical and \
                               self.maximumHeight() == self.minimumHeight()))
            self.config().writeEntry('FixedSize', self.fixedSize)

            fixedAction = action('toggle fixed')
            if fixedAction:
                fixedAction.setChecked(not self.fixedSize)

        self.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))


    def paintInterface(painter, option, contentsRect):
        if not  self.configurationMode:
            return

        painter.setRenderHint(QPainter.Antialiasing)
        p = Plasma.PaintUtils.roundedRectangle(contentsRect.adjusted(1, 1, -2, -2), 4)
        c = Plasma.Theme.defaultTheme().color(Plasma.Theme.TextColor)
        c.setAlphaF(0.3)

        painter.fillPath(p, c)

        painter.setRenderHint(QPainter.Antialiasing)
        c = Plasma.Theme.defaultTheme().color(Plasma.Theme.TextColor)
        c.setAlphaF(0.7)

        margin = 8

        path = QPainterPath()
        if formFactor() == Plasma.Horizontal:
            path = Plasma.PaintUtils.roundedRectangle(contentsRect.adjusted(1, 1, \
                    -contentsRect.width() + margin - 1, -2), 4)
            painter.fillPath(path, c)
            path = Plasma.PaintUtils.roundedRectangle(contentsRect.adjusted(contentsRect.width() - \
                    margin, 1, -2, -2), 4)
        elif formFactor() == Plasma.Vertical:
            path = Plasma.PaintUtils.roundedRectangle(contentsRect.adjusted(1, 1, -2, \
                    -contentsRect.height() + margin - 1), 4)
            painter.fillPath(path, c)
            path = Plasma.PaintUtils.roundedRectangle(contentsRect.adjusted(1, \
                    contentsRect.height()-margin, -2, -2), 4)
        painter.fillPath(path, c)

    def updateConfigurationMode(config):
        if config != self.configurationMode:
            self.configurationMode = config
            update()
