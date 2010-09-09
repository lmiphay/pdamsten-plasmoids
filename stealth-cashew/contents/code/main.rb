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

require 'plasma_applet'
require 'korundum4'

module StealthCashew

class Main < PlasmaScripting::Applet
    slots :setCashewOpacity

    def initialize(parent, args = nil)
        super
    end

    def init()
        cg = config()
        if cg.readEntry("firstTime", 1) == 1
            setGlobalShortcut(KDE::Shortcut.new('Ctrl+Alt+0'))
            cg.writeEntry("firstTime", 0)
            Qt::Timer.singleShot(0, @applet_script.applet, SLOT(:showConfigurationInterface))
        else
            setCashewOpacity()
        end
        setGeometry(0, 0, 1, 1)
        # Don't want toolbox on hover for this applet
        setAcceptHoverEvents(false)
        Qt::Object.connect(self, SIGNAL('activate()'),
                           @applet_script.applet, SLOT('showConfigurationInterface()'))
        Qt::Object.connect(containment().corona(),
                           SIGNAL('immutabilityChanged(Plasma::ImmutabilityType)'),
                           self, SLOT('setCashewOpacity()'))
    end

    def configChanged
        setCashewOpacity()
    end

    def constraintsEvent(constraints)
        if constraints.to_i & Plasma::FormFactorConstraint.to_i
            setBackgroundHints(NoBackground)
        elsif constraints.to_i & Plasma::ImmutableConstraint.to_i
            setCashewOpacity()
        end
    end

    def setCashewOpacity()
        cg = config()
        if immutability() == Plasma::Mutable
            opacity = cg.readEntry("unlockedOpacity", 100) / 100.0
        else
            opacity = cg.readEntry("lockedOpacity", 100) / 100.0
        end
        for containment in containment().corona().containments()
            cashew = false
            begin # KDE 4.5
                item = containment.toolBox
                if item
                    cashew = true
                end
            rescue
                for item in containment.childItems()
                    if item.zValue() == 10000000.0
                        if item.isWidget() == false # KDE 4.3
                            cashew = true
                            break
                        else # KDE 4.4
                            i = Qt::Internal.cast_object_to(item, Qt::GraphicsWidget)
                            # TODO Handle Plasma::DesktopToolBox & Plasma::PanelToolBox separately
                            if i.inherits("Plasma::InternalToolBox")
                                cashew = true
                                break
                            end
                        end
                    end
                end
            end
            if cashew
                item.setOpacity(opacity)
                item.setFlag(Qt::GraphicsItem::ItemDoesntPropagateOpacityToChildren, true)
            end
        end
    end
end

end