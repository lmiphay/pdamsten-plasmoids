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
    plasmoid.setAspectRatioMode(KeepAspectRatio);
    m_layout = new LinearLayout(plasmoid);
    m_layout.setContentsMargins(0, 0, 0, 0);
    m_layout.setItemSpacing(SPACING);
    plasmoid.configChanged();

    // TODO No way to set my own property? Using QPropertyAnimation as QVariantAnimation.
    m_anim = animation("Property");
    m_anim.targetObject = plasmoid;
    m_anim.valueChanged.connect(plasmoid.onValueChange);
    m_anim.startValue = 0;
    m_anim.endValue = 1;
    m_anim.duration = 500;
    m_anim.type = plasmoid.OutCirc;

    // TODO Applet cannot handle mouse presses? Make transparent widget for getting clicks.
    w = new IconWidget();
    m_layout.addItem(w);
    w.clicked.connect(plasmoid.onClick);
}

plasmoid.onValueChange = function(value)
{
    plasmoid.update();
    if (m_anim.currentValue == 1.0) {
        m_values = []
        for (i = 0; i < m_count; ++i) {
            m_values.push(Math.floor(Math.random() * 6) + 1);
        }
        m_anim.direction = 1;
        m_anim.start();
    }
}

plasmoid.onClick = function(button)
{
    print('onClick');
    m_anim.direction = 0;
    m_anim.start();
}

plasmoid.paintElement = function(painter, element, opacity)
{
    if (opacity > 0.0) {
        if (m_svg.hasElement(element)) {
            rect = plasmoid.rect();
            r = m_svg.elementRect(element);
            if (opacity != 1.0) {
                painter.opacity = opacity;
            }
            m_svg.paint(painter, r.x + rect.x, r.y + rect.y, element);
        }
    }
}

plasmoid.paintInterface = function(painter)
{
    // TODO Can't make custom widgets? Plasma::SvqWidget is too simple for this so paint it here.
    rect = plasmoid.rect();
    if (m_svg.size != rect.size) {
        m_svg.resize(rect.width, rect.height);
    }
    plasmoid.paintElement(painter, 'background', 1.0);
    plasmoid.paintElement(painter, 'value' + m_values[0], 1.0 - m_anim.currentValue);
    plasmoid.paintElement(painter, 'whirl', m_anim.currentValue);
}

plasmoid.configChanged = function()
{
    print('configChanged');
    m_count = plasmoid.readConfig("itemCount");
    //svg = plasmoid.readConfig("itemSvg");
    svg = "Vegas Plasma Dice";
    m_svg = new Svg(svg);

    // TODO vertical (panel)
    h = plasmoid.rect().height;
    // TODO Only way to get margins?
    plasmoid.resize(200, 200);
    hm = 200 - plasmoid.rect().width;
    vm = 200 - plasmoid.rect().height;
    // resize to item count
    plasmoid.resize(hm + m_count * h + (m_count - 1) * SPACING, h + vm);
    plasmoid.setMinimumSize(hm + m_count * MINSIZE + (m_count - 1) * SPACING, MINSIZE + vm);

    m_values = []
    for (i = 0; i < m_count; ++i) {
        m_values.push(1);
    }
}

plasmoid.init();
