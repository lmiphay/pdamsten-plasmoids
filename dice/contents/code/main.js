/*
 * Copyright (c) 2010 Petri Damsten <damu@iki.fi>
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License as
 * published by the Free Software Foundation; either version 2 of
 * the License, or (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

SPACING = 10
MINSIZE = 20

plasmoid.init = function()
{
    print("init")
    m_layout = 0
    plasmoid.setAspectRatioMode(KeepAspectRatio);
    m_layout = new LinearLayout(plasmoid);
    m_layout.setContentsMargins(0, 0, 0, 0);
    m_layout.setItemSpacing(SPACING);
    plasmoid.configChanged();

    // TODO No way to set my own property? Using QPropertyAnimation as QVariantAnimation.
    m_anim = animation("Property");
    print(m_anim);
    m_anim.targetObject = plasmoid;
    m_anim.valueChanged.connect(plasmoid.onValueChange);
    m_anim.startValue = 0;
    m_anim.endValue = 1;
    m_anim.duration = 1000;

    // TODO Applet cannot handle mouse presses? Make transparent widget for getting clicks.
    w = new IconWidget();
    m_layout.addItem(w);
    w.clicked.connect(plasmoid.onClick);

    m_anim.start();
}

plasmoid.onValueChange = function(value)
{
    print('onValueChange');
    print(m_anim.currentValue);
}

plasmoid.onClick = function(button)
{
    print('onClick');
}

plasmoid.paintInterface = function(painter)
{
    print ('paintInterface');
    // TODO Can't make custom widgets? Plasma::SvqWidget is too simple for this so paint it here.
    rect = plasmoid.rect();
    m_svg.resize(rect.width, rect.height);
    m_svg.paint(painter, rect.x, rect.y);
}

plasmoid.configChanged = function()
{
    print('configChanged');
    while (m_layout.count > 0) {
        m_layout.removeAt(0);
    }
    count = plasmoid.readConfig("itemCount");
    //m_svg = plasmoid.readConfig("itemSvg");
    svg = "Vegas Plasma Dice";

    // TODO vertical (panel)
    h = plasmoid.rect().height;
    // TODO Only way to get margins?
    plasmoid.resize(200, 200);
    hm = 200 - plasmoid.rect().width;
    vm = 200 - plasmoid.rect().height;
    // resize to item count
    plasmoid.resize(hm + count * h + (count - 1) * SPACING, h + vm);
    plasmoid.setMinimumSize(hm + count * MINSIZE + (count - 1) * SPACING, MINSIZE + vm);

    m_svg = new Svg(svg);
}

plasmoid.init();
