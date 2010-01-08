#!/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright (c) 2009 Petri Damstén <damu@iki.fi>
#    Copyright (c) 2007 Paolo Capriotti <p.capriotti@gmail.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details
#
#    You should have received a copy of the GNU Library General Public
#    License along with this program; if not, write to the
#    Free Software Foundation, Inc.,
#    51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
#

#    C++ to python conversion by Petri Damstén <damu@iki.fi>

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *


def qBound(minValue, value, maxValue):
    return max(min(value, maxValue), minValue)


class BackgroundDelegate(QAbstractItemDelegate):
    AuthorRole, ScreenshotRole, ResolutionRole, PathRole = range(Qt.UserRole, Qt.UserRole + 4)
    SCREENSHOT_SIZE = 60
    MARGIN = 5

    def __init__(self, ratio, parent):
        QAbstractItemDelegate.__init__(self, parent)
        self.ratio = ratio

    def paint(self, painter, option, index):
        v = index.model().data(index, Qt.DisplayRole)
        title = index.model().data(index, Qt.DisplayRole).toString()
        author = index.model().data(index, self.AuthorRole).toString()
        resolution = index.model().data(index, self.ResolutionRole).toString()
        pix = QPixmap(index.model().data(index, self.ScreenshotRole))

        # highlight selected item
        QApplication.style().drawControl(QStyle.CE_ItemViewItem, option, painter, None)

        # draw pixmap
        maxheight = self.SCREENSHOT_SIZE
        maxwidth = int(maxheight * self.ratio)

        if not pix.isNull():
            sz = pix.size()
            x = self.MARGIN + (maxwidth - pix.width()) / 2
            y = self.MARGIN + (maxheight - pix.height()) / 2
            imgRect = QRect(option.rect.topLeft(), pix.size()).translated(x, y)
            painter.drawPixmap(imgRect, pix)

        # draw text
        painter.save()
        font = painter.font()
        font.setWeight(QFont.Bold)
        painter.setFont(font)

        if option.state & QStyle.State_Selected:
            painter.setPen(QApplication.palette().brush(QPalette.HighlightedText).color())
        else:
            painter.setPen(QApplication.palette().brush(QPalette.Text).color())

        x = option.rect.left() + self.MARGIN * 2 + maxwidth

        textRect = QRect(x, option.rect.top() + self.MARGIN,
                         option.rect.width() - x - self.MARGIN, maxheight)
        text = QString(title)
        authorCaption = QString()

        if not author.isEmpty():
            authorCaption = i18nc('Caption to wallpaper preview, %1 author name',
                                  'by %1', author)
            text += '\n' + authorCaption

        boundingRect = painter.boundingRect(textRect, Qt.AlignVCenter | Qt.TextWordWrap, text)
        boundingRect = boundingRect.intersected(option.rect)
        painter.drawText(boundingRect, Qt.TextWordWrap, title)
        titleRect = painter.boundingRect(boundingRect, Qt.TextWordWrap, title)
        lastText = titleRect.bottomLeft()

        if not author.isEmpty():
            authorRect = QRect(lastText, textRect.size()).intersected(option.rect)

            if not authorRect.isEmpty():
                painter.setFont(KGlobalSettings.smallestReadableFont())
                painter.drawText(authorRect, Qt.TextWordWrap, authorCaption)
                lastText = painter.boundingRect(authorRect, Qt.TextWordWrap,
                                                authorCaption).bottomLeft()

        if not resolution.isEmpty():
            resolutionRect = QRect(lastText, textRect.size()).intersected(option.rect)
            if not resolutionRect.isEmpty():
                painter.setFont(KGlobalSettings.smallestReadableFont())
                painter.drawText(resolutionRect, Qt.TextWordWrap, resolution)

        painter.restore()

    def sizeHint(self, option, index):
        title = index.model().data(index, Qt.DisplayRole).toString()
        maxwidth = int(self.SCREENSHOT_SIZE * self.ratio)
        font = option.font

        font.setWeight(QFont.Bold)
        fm = QFontMetrics(font)
        # print QSize(maxwidth + qBound(100, fm.width(title), 500), \
        #       self.SCREENSHOT_SIZE + self.MARGIN * 2)
        return QSize(maxwidth + qBound(100, fm.width(title), 500),
                     self.SCREENSHOT_SIZE + self.MARGIN * 2)


