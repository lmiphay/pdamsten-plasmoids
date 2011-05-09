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
 * along with this program.  If not, see <http:www.gnu.org/licenses/>.
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
    //print("connectEngine. Unit: " + g_intervalUnit)
    plasmoid.busy = true;
    var interval;

    //print(typeof(g_intervalUnit));
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
        //print('Using executable dataengine: ' + interval * 1000);
        var engine = dataEngine("executable");
        engine.connectSource(g_script, this, interval * 1000);
    } else  {
        //print('Using time dataengine: '  + interval * 1000);
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
    g_useScript = (plasmoid.readConfig("htmlScriptRadio", false) == true);
    g_script = plasmoid.readConfig("htmlScript").path;
    g_html = plasmoid.readConfig("htmlUrl").toString;
    g_interval = parseInt(plasmoid.readConfig("interval", 1));
    g_intervalUnit = parseInt(plasmoid.readConfig("intervalUnit", 1));
    //print('Using script: ' + g_useScript)

    if ((g_useScript && g_script == "") || (!g_useScript && g_html == "")) {
        plasmoid.setConfigurationRequired(true);
    } else {
        plasmoid.setConfigurationRequired(false);
        plasmoid.connectEngine();
    }
}

plasmoid.dataUpdated = function(source, data)
{
    //print('dataUpdate. Using script: ' + g_useScript);
    if (g_useScript) {
        //print(typeof(data["stdout"]));
        if (typeof(data["stdout"]) != "string") {
            return;
        }
        a = data["stdout"].split("\n", 3);
        if (a.length < 3) {
          /* If we have only one line (and possibly empty line after that) consider it url */
          if (a.length < 2 || a[1] == "") { 
            g_web.url = Url(data["stdout"].replace("\n", ""));
            //print('Using stdout as url: ' + g_web.url);
            return;
          }
        }
        /* Otherwise it is html */
        //print('Using stdout as html.');
        g_web.html = data["stdout"];
    } else {
        //print('Setting URL: ' + g_html)
        g_web.url = Url(g_html);
    }
}

plasmoid.init();