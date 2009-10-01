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

import os, sys
from PyQt4.QtCore import *
from PyQt4.QtGui  import *
from PyKDE4.plasma import Plasma
from PyKDE4.plasmascript import Applet
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *
from image import Image
from button import Button
from slider import Slider
from layout import Layout
from label import Label
from frame import Frame
from fader import Fader
from helpers import *

def loadPlugin(name):
    plugin = name + 'Plugin'
    filename = unicode(KStandardDirs.locate('data', 'plasma_applet_now-rocking/' + plugin + '.py'))
    if filename != '':
        directory = os.path.dirname(filename)
        if directory not in sys.path:
            sys.path.append(directory)
        try:
            temp = __import__(plugin, globals(), locals(), [name])
            return temp.__dict__[name]
        except:
            return lambda *args: None


class Rocking(Applet):
    Stopped, Playing, Paused, NA = range(4)
    ButtonWidth = 24

    def __init__(self, parent, args = None):
        Applet.__init__(self, parent)
        self.coverPlugin = loadPlugin('cover')
        self.coverCache = {}
        self.connected = False
        self.allCaps = False
        self.player = u''
        self.artist = u''
        self.album = u''
        self.title = u''
        self.volume = 1000
        self.position = 0
        self.length = 0
        self.state = Rocking.NA
        self.controller = None
        self.artistWidget = None
        self.titleWidget = None
        self.volumeWidget = None
        self.positionWidget = None
        self.bar = None
        self.logo = None
        self.cover = None
        self.actions = []

    def __del__(self):
        # Getting crash without this...
        self.disconnect(Plasma.Theme.defaultTheme(), SIGNAL('themeChanged()'), self.themeChanged)

    def init(self):
        self.connect(self, SIGNAL('activate()'), self.playClicked)
        self.connect(Plasma.Theme.defaultTheme(), SIGNAL('themeChanged()'), self.themeChanged)

        self.engine = self.dataEngine('nowplaying')
        self.connect(self.engine, SIGNAL('sourceAdded(QString)'), self.playerAdded)
        self.connect(self.engine, SIGNAL('sourceRemoved(QString)'), self.playerRemoved)

        self.layout = QGraphicsLinearLayout(Qt.Vertical, self.applet)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(2)
        self.cover = Image(self.applet)
        self.cover.setZValue(-10)
        self.cover.setFadeChildren(False)
        self.connect(self.cover, SIGNAL('clicked()'), self.playClicked)
        self.layout.addItem(self.cover)

        self.coverLayout = Layout(self.cover)
        self.readConfig()

        self.connectToEngine()

        action = QAction(KIcon('transform-scale'), i18n('Make cover &square'), self)
        self.connect(action, SIGNAL('triggered(bool)'), self.makeSquare)
        self.actions.append(action)

        self.createButtonBar()

    def themeChanged(self):
        if self.artistWidget != None:
            self.artistWidget.setColor(Plasma.Theme.defaultTheme().color(Plasma.Theme.TextColor))
        if self.titleWidget != None:
            self.titleWidget.setColor(Plasma.Theme.defaultTheme().color(Plasma.Theme.TextColor))

    def makeSquare(self):
        w = self.cover.size().width() - self.cover.size().height()
        self.applet.resize(self.applet.size().width() - w, self.applet.size().height())

    def deleteArtistAndTitle(self):
        self.layout.removeItem(self.artistWidget)
        self.layout.removeItem(self.titleWidget)
        del self.artistWidget
        del self.titleWidget
        self.artistWidget = None
        self.titleWidget = None

    def createArtistAndTitle(self):
        if self.artistWidget == None:
            self.artistWidget = Label(self.applet)
            self.layout.addItem(self.artistWidget)

            self.titleWidget = Label(self.applet)
            self.layout.addItem(self.titleWidget)

            self.readConfig()

    def formatArtistAndTitle(self, s):
        if self.allCaps:
            return s.upper()
        return s

    def readConfig(self):
        cg = self.config()
        if self.artistWidget != None:
            f = QFont()
            self.allCaps = (cg.readEntry('allCaps') == QString('true'))

            f.fromString(cg.readEntry('artistFont'))
            self.artistWidget.setText(self.formatArtistAndTitle(self.artist))
            self.artistWidget.setFont(f)

            f.fromString(cg.readEntry('titleFont'))
            self.titleWidget.setText(self.formatArtistAndTitle(self.title))
            self.titleWidget.setFont(f)

        if cg.readEntry('keepRatio') != QString('false'):
            self.cover.setAspectRatioMode(Qt.KeepAspectRatio)
        else:
            self.cover.setAspectRatioMode(Qt.IgnoreAspectRatio)

        prev = self.logo
        self.logo = U(cg.readEntry('logo'))
        if self.logo == '':
            self.logo = U(self.applet.package().filePath('images', 'now-rocking.svgz'))
        else:
            self.logo = self.logo.replace('file://', '')
        if prev == '' or self.cover.image() == prev:
            self.cover.setImage(self.logo)

        self.layout.invalidate()

    def createButtonBar(self):
        # Button bar
        self.bar = Frame(self.cover)
        self.bar.setSvg(U(self.applet.package().filePath('images', 'frame.svgz')))

        (left, top, right, bottom) = self.bar.getContentsMargins()
        self.coverLayout.addItem(self.bar, \
                [(0, 1), (0, 1), (1, -1), (0, Rocking.ButtonWidth + top + bottom)])
        layout = Layout(self.bar)

        buttonsSvg = U(self.applet.package().filePath('images', 'buttons.svgz'))
        slidersSvg = U(self.applet.package().filePath('images', 'sliders.svgz'))

        self.prev = Button(self.bar)
        self.prev.hide()
        self.prev.setPrefix('prev')
        self.prev.setImage(buttonsSvg)
        self.connect(self.prev, SIGNAL('clicked()'), self.prevClicked)
        layout.addItem(self.prev, [(0, 0), (0, 0), (0, Rocking.ButtonWidth), (1, 0)])

        w = QGraphicsWidget(self.bar)
        sub = QGraphicsLinearLayout(Qt.Vertical, w)
        sub.setContentsMargins(0, 0, 0, 0)
        sub.setSpacing(0)
        sub.addStretch()
        sub2 = QGraphicsLinearLayout(Qt.Horizontal, sub)
        sub2.setContentsMargins(0, 0, 0, 0)

        self.current = Label(w)
        self.current.hide()
        self.current.setContentsMargins(5, 0, 0, 0)
        self.current.setTight(True)
        self.current.setFadeEnabled(False)
        self.current.setText('%d:%02d' % (self.position / 60, self.position % 60))
        f = self.current.font()
        f.setPointSize(8)
        self.current.setFont(f)
        self.current.setColor(QColor('#c0c0c0')) # TODO no hard coded colors
        self.current.setAlign(Qt.AlignLeft)
        sub2.addItem(self.current)
        sub2.addStretch()

        self.total = Label(w)
        self.total.hide()
        self.total.setContentsMargins(0, 0, 5, 0)
        self.total.setTight(True)
        self.total.setText('%d:%02d' % (self.length / 60, self.length % 60))
        f = self.total.font()
        f.setPointSize(8)
        self.total.setFont(f)
        self.total.setColor(QColor('#c0c0c0')) # TODO no hard coded colors
        self.total.setAlign(Qt.AlignRight)
        sub2.addItem(self.total)
        sub.addItem(sub2)

        self.positionWidget = Slider(w)
        self.positionWidget.hide()
        self.positionWidget.setRange(0, 100)
        self.positionWidget.setValue(50)
        self.positionWidget.setPrefix('position')
        self.positionWidget.setImage(slidersSvg)
        self.positionWidget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        self.positionWidget.setValue(self.position)
        self.positionWidget.setMaximum(self.length)
        self.connect(self.positionWidget, SIGNAL('sliderMoved(int)'), self.positionChanged)
        sub.addItem(self.positionWidget)
        sub.addStretch()
        layout.addItem(w, \
                [(0, Rocking.ButtonWidth + 1), (0, 0), (1, -5 * Rocking.ButtonWidth), (1, 0)])

        self.next = Button(self.bar)
        self.next.hide()
        self.connect(self.next, SIGNAL('clicked()'), self.nextClicked)
        self.next.setPrefix('next')
        self.next.setImage(buttonsSvg)
        layout.addItem(self.next, \
                [(1, -5 * Rocking.ButtonWidth + 1), (0, 0), (1, -4 * Rocking.ButtonWidth), (1, 0)])

        self.play = Button(self.bar)
        self.play.hide()
        self.connect(self.play, SIGNAL('clicked()'), self.playClicked)
        self.play.setPrefix('play')
        self.play.setImage(buttonsSvg)
        layout.addItem(self.play, \
                [(1, -4 * Rocking.ButtonWidth + 1), (0, 0), (1, -3 * Rocking.ButtonWidth), (1, 0)])

        self.stop = Button(self.bar)
        self.stop.hide()
        self.connect(self.stop, SIGNAL('clicked()'), self.stopClicked)
        self.stop.setPrefix('stop')
        self.stop.setImage(buttonsSvg)
        layout.addItem(self.stop, \
                [(1, -3 * Rocking.ButtonWidth + 1), (0, 0), (1, -2 * Rocking.ButtonWidth), (1, 0)])

        self.volumeWidget = Slider(self.bar)
        self.volumeWidget.hide()
        self.volumeWidget.setRange(0, 1000)
        self.volumeWidget.setValue(self.volume)
        self.volumeWidget.setPrefix('volume')
        self.volumeWidget.setImage(slidersSvg)
        self.connect(self.volumeWidget, SIGNAL('sliderMoved(int)'), self.volumeChanged)
        layout.addItem(self.volumeWidget, \
                [(1, -2 * Rocking.ButtonWidth + 1), (0, 0), (1, 0), (1, 0)])

        self.associateWidgets()
        self.barLayout = layout
        self.bar.hide()

    def associateWidgets(self):
        if self.controller != None and self.bar != None:
            self.controller.associateWidget(self.positionWidget, 'seek');
            self.controller.associateWidget(self.volumeWidget, 'volume');
            self.controller.associateWidget(self.prev, 'previous');
            self.controller.associateWidget(self.next, 'next');
            self.controller.associateWidget(self.stop, 'stop');
            self.checkPlayPause()

    def connectToEngine(self):
        self.connected = False
        self.engine.disconnectSource(self.player, self)
        if not self.engine.sources().contains(self.player) and self.engine.sources().count() > 0:
            self.player = QString(self.engine.sources().first())
        if self.engine.sources().contains(self.player):
            self.engine.connectSource(self.player, self, 500)
            try:
                self.controller = self.engine.serviceForSource(self.player)
            except:
                self.controller = None
                return
            self.associateWidgets()
            self.connected = True
        else:
            self.controller = None
            self.dataUpdated('', {})

    def playerAdded(self, player):
        if self.engine.sources().count() == 1:
            self.connectToEngine()

    def playerRemoved(self, player):
        if player == self.player:
            self.connectToEngine()

    def playClicked(self):
        if self.controller == None:
            return
        # VLC needs pause even if paused. play stops current track.
        if self.state == Rocking.Playing or self.player == 'org.mpris.vlc':
            self.controller.startOperationCall(self.controller.operationDescription('pause'))
        else:
            self.controller.startOperationCall(self.controller.operationDescription('play'))

    def stopClicked(self):
        if self.controller == None:
            return
        self.controller.startOperationCall(self.controller.operationDescription('stop'))

    def prevClicked(self):
        if self.controller == None:
            return
        self.controller.startOperationCall(self.controller.operationDescription('previous'))

    def nextClicked(self):
        if self.controller == None:
            return
        self.controller.startOperationCall(self.controller.operationDescription('next'))

    def positionChanged(self, value):
        if self.controller == None:
            return
        operation = self.controller.operationDescription('seek')
        operation.writeEntry('seconds', QVariant(value));
        self.controller.startOperationCall(operation);

    def volumeChanged(self, value):
        if self.controller == None:
            return
        operation = self.controller.operationDescription('volume')
        operation.writeEntry('level', QVariant(F(value) / 1000.0));
        self.controller.startOperationCall(operation);

    def constraintsEvent(self, constraints):
        #print ('main.py constraintsEvent')
        if constraints & Plasma.FormFactorConstraint:
            if self.formFactor() in [Plasma.Horizontal, Plasma.Vertical]:
                self.setAspectRatioMode(Plasma.Square)
                self.deleteArtistAndTitle()
            else:
                self.setAspectRatioMode(Plasma.IgnoreAspectRatio)
                self.createArtistAndTitle()

    def checkPlayPause(self):
        if self.controller == None or self.bar == None:
            return
        if self.state == Rocking.Playing:
            self.controller.associateWidget(self.play, 'pause');
            self.play.setPrefix('pause')
        else:
            self.controller.associateWidget(self.play, 'play');
            self.play.setPrefix('play')

    @pyqtSignature('dataUpdated(const QString&, const Plasma::DataEngine::Data&)')
    def dataUpdated(self, sourceName, data):
        #print data
        changed = False
        state = Rocking.Stopped
        if QString('State') in data:
            if U(data[QString('State')]) == u'playing':
                state = Rocking.Playing
            elif U(data[QString('State')]) == u'paused':
                state = Rocking.Paused
        if self.state != state:
            self.state = state
            self.checkPlayPause()
            changed = True

        if QString('Artist') in data:
            artist = U(data[QString('Artist')])
        elif self.player != '':
            artist = U(self.player)
            artist = artist[artist.rfind('.') + 1:].title()
        else:
            artist = U(i18n('No Player'))
        if artist != self.artist:
            self.artist = artist
            if self.artistWidget != None:
                self.artistWidget.setText(self.formatArtistAndTitle(self.artist))
            changed = True

        if QString('Title') in data:
            title = U(data[QString('Title')])
            if self.state == Rocking.Paused:
                title += U(i18n(' (paused)'))
            if self.state == Rocking.Stopped:
                title += U(i18n(' (stopped)'))
        else:
            if self.state == Rocking.Stopped:
                title = U(i18n('Stopped'))
            else:
                title = U(i18n('N/A'))
        if title != self.title:
            self.title = title
            if self.titleWidget != None:
                self.titleWidget.setText(self.formatArtistAndTitle(self.title))
            changed = True

        if QString('Album') in data:
            album = U(data[QString('Album')])
        else:
            album = ''
        if self.album != album:
            self.album = album
            changed = True

        if QString('Artwork') in data:
            if changed:
                self.cover.setImage(QPixmap(data[QString('Artwork')]))
        else:
            img = None
            if album != '':
                key = artist + '|' + album
                if key in self.coverCache:
                    img = self.coverCache[key]
                else:
                    img = self.coverPlugin(artist, album)
                    self.coverCache[key] = img
            if not img:
                img = self.logo

            if self.cover.image() != img:
                self.cover.setImage(img)

        if changed:
            self.artwork = self.cover.pixmap()
            self.artwork = self.artwork.scaled(QSize(50, 50), Qt.IgnoreAspectRatio, \
                                               Qt.SmoothTransformation)
            if self.formFactor() in [Plasma.Horizontal, Plasma.Vertical]:
                toolTip = Plasma.ToolTipContent(self.artist, self.title, self.artwork)
                Plasma.ToolTipManager.self().setContent(self.applet, toolTip)

        if QString('Volume') in data:
            v = I(F(data[QString('Volume')]) * 1000.0)
            if v != self.volume:
                self.volume = v
                if self.volumeWidget != None:
                    self.volumeWidget.setValue(v)

        if QString('Position') in data:
            v = I(data[QString('Position')])
            if v != self.position:
                self.position = v
                if self.positionWidget != None:
                    self.positionWidget.setValue(v)
                    self.current.setText('%d:%02d' % (v / 60, v % 60))

        if QString('Length') in data:
            v = I(data[QString('Length')])
            if v != self.length:
                self.length = v
                if self.positionWidget != None:
                    self.positionWidget.setMaximum(v)
                    self.total.setText('%d:%02d' % (v / 60, v % 60))

    def configChanged(self):
        self.readConfig()

    def contextualActions(self):
        if not self.formFactor() in [Plasma.Horizontal, Plasma.Vertical]:
            return self.actions
        else:
            return []

    def hoverEnterEvent(self, event):
        if self.connected and self.cover.size().width() > Rocking.ButtonWidth * 9:
            # TODO why buttons are half height without invalidate?
            self.barLayout.invalidate()
            self.bar.fadeIn(Fader.Medium)
        try:
            self.applet.hoverEnterEvent(event)
        except:
            pass

    def hoverLeaveEvent(self, event):
        if self.bar.isVisible():
            self.bar.fadeOut(Fader.Medium)
        try:
            self.applet.hoverLeaveEvent(event)
        except:
            pass

def CreateApplet(parent):
    return Rocking(parent)

