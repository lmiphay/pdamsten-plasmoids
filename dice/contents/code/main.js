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

g_layout = 0

plasmoid.init = function()
{
    print("init")
    plasmoid.setAspectRatioMode(KeepAspectRatio);
    g_layout = new LinearLayout(plasmoid);
    g_layout.setContentsMargins(0, 0, 0, 0);
    g_layout.setItemSpacing(SPACING);
    plasmoid.configChanged();
}

plasmoid.configChanged = function()
{
    print('configChanged');
    while (g_layout.count > 0) {
        g_layout.removeAt(0);
    }
    count = plasmoid.readConfig("itemCount");
    //g_svg = plasmoid.readConfig("itemSvg");
    svg = "Vegas Plasma Dice";

    // TODO vertical (panel)
    h = plasmoid.rect().height;
    // Get margins
    plasmoid.resize(200, 200);
    hm = 200 - plasmoid.rect().width;
    vm = 200 - plasmoid.rect().height;
    // resize to item count
    plasmoid.resize(hm + count * h + (count - 1) * SPACING, h + vm);
    plasmoid.setMinimumSize(hm + count * MINSIZE + (count - 1) * SPACING, MINSIZE + vm);

    svg = new Svg(svg);
    for (i = 0; i < count; ++i) {
        item = new SvgWidget(plasmoid);
        item.svg = svg;
        print (item.svg);
        //print (item.svg.imagePath);
        //print (item.svg.elementId);
        g_layout.addItem(item);
    }
}

plasmoid.init();