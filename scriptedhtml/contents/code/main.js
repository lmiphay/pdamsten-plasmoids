/*
 * Copyright (c) 2009 Petri Damsten <damu@iki.fi>
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

var g_useScript = false;
var g_script = "";
var g_html = "";
var g_interval = -1;
var g_intervalUnit = -1;
var g_web

plasmoid.init = function()
{
    //print("init")
    layout = new LinearLayout(plasmoid);
    g_web = new WebView();
    g_web.loadFinished.connect(plasmoid.loadFinished);
    layout.addItem(g_web);
    plasmoid.configChanged();
}

plasmoid.connectEngine = function()
{
    //print("connectEngine")
    plasmoid.busy = true;
    var script = g_script.replace("file://", "");
    var interval;

    switch (g_intervalUnit) {
        case 0:
            interval = g_interval;
            break;
        case 1:
            interval = g_interval * 60;
            break;
        case 2:
            interval = g_interval * 60 * 60;
            break;
    }

    if (g_useScript) {
        var engine = dataEngine("executable");
        engine.connectSource(script, this, interval * 1000);
    } else  {
        var engine = dataEngine("time");
        engine.connectSource("Local", this, interval * 1000);
    }
}

plasmoid.loadFinished = function(success)
{
    //print("loadFinished")
    plasmoid.busy = false;
}

plasmoid.formFactorChanged = function()
{
    //print("formFactorChanged")
    switch (plasmoid.formFactor) {
        case Planar:
        case MediaCenter:
            plasmoid.setAspectRatioMode(IgnoreAspectRatio);
            break;
        case Horizontal:
        case Vertical:
            plasmoid.setAspectRatioMode(Square);
            break;
    }
}

plasmoid.configChanged = function()
{
    //print('configChanged');
    g_useScript = plasmoid.readConfig("htmlScriptRadio");
    g_script = plasmoid.readConfig("htmlScript");
    g_html = plasmoid.readConfig("htmlUrl");
    g_interval = plasmoid.readConfig("interval");
    g_intervalUnit = plasmoid.readConfig("intervalUnit");

    if ((g_useScript && g_script == "") || (!g_useScript && g_html == "")) {
        plasmoid.setConfigurationRequired(true);
    } else {
        plasmoid.setConfigurationRequired(false);
        plasmoid.connectEngine();
    }
}

plasmoid.dataUpdated = function(source, data)
{
    //print('dataUpdate');
    if (g_useScript) {
        if (typeof(data["stdout"]) != "string") {
            return;
        }
        g_web.url = Url(data["stdout"].replace("\n", ""));
    } else {
        g_web.url = Url(g_html);
    }
}

plasmoid.init();