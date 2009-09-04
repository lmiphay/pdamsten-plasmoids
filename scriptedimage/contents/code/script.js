/*
 * Copyright (c) 2008-2009 Petri Damsten <damu@iki.fi>
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
var g_image = "";
var g_scaling = -1;
var g_interval = -1;
var g_intervalUnit = -1;
var g_img;
var g_src = "";

function init()
{
    //alert("init")
    g_img = new Image();
    g_img.onload = widhtHeightReady;

    constraintsEvent(FormFactorConstraint);
    configChanged();
}

function connectEngine()
{
    //alert("connectEngine")
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
        var engine = window.applet.dataEngine("executable");
        engine.connectSource(script, interval * 1000);
    } else  {
        var engine = window.applet.dataEngine("time");
        engine.connectSource("Local", interval * 1000);
    }
}

function constraintsEvent(constraints)
{
    //alert("constraintsEvent")
    if (constraints & FormFactorConstraint) {
        switch (window.applet.formFactor) {
            case Planar:
            case MediaCenter:
                window.applet.setAspectRatioMode(IgnoreAspectRatio);
                break;
            case Horizontal:
            case Vertical:
                window.applet.setAspectRatioMode(Square);
                break;
        }
    } else if (constraints & SizeConstraint) {
        updateImage();
    }
}

function dataUpdated(source, data)
{
    //alert("dataUpdated")
    if (g_useScript) {
        if (!data.contains("stdout")) {
            return;
        }
        isrc = data.value("stdout").split('\n')[0];
    } else {
        isrc = g_image;
    }
    if (g_src != isrc || isrc == '') {
        g_img.src = isrc;
    } else {
        g_img.src = isrc + '?' + new Date().getTime();
    }
    g_src = isrc;
}

function themeChanged()
{
    //alert("themeChanged")
    updateImage();
}

function widhtHeightReady()
{
    //alert("widhtHeightReady")
    updateImage();
}

function updateImage()
{
    //alert("updateImage")
    if (g_img.width == 0 || g_img.height == 0) {
        return;
    }
    var size = window.applet.size();
    var margins = window.applet.getContentsMargins();
    var w = size[size_width] - margins[margin_left] - margins[margin_right];
    var h = size[size_height] - margins[margin_top] - margins[margin_bottom];
    switch (g_scaling) {
        case 0: // No scaling
            document.getElementById('image').width = g_img.width;
            document.getElementById('image').height = g_img.height;
            break;
        case 1: // Scale content to applet
            document.getElementById('image').width = w;
            document.getElementById('image').height = h;
            break;
        case 2: // Scale content to applet, keep aspect ratio
            var sx = w / g_img.width;
            var sy = h / g_img.height;
            if (sx > sy) {
                document.getElementById('image').width = sy * g_img.width;
                document.getElementById('image').height = h;
            } else {
                document.getElementById('image').width = w;
                document.getElementById('image').height = sx * g_img.height;
            }
            break;
        case 3: // Scale applet to content
            document.getElementById('image').width = g_img.width;
            document.getElementById('image').height = g_img.height;
            w = g_img.width + margins[margin_left] + margins[margin_right];
            h = g_img.height + margins[margin_top] + margins[margin_bottom];
            window.applet.resize(w, h);
            break;
    }
    //alert(g_img.src)
    document.getElementById('image').src = g_img.src;
}

function configChanged()
{
    //alert("configChanged")
    var cfg = window.applet.config();
    g_useScript = cfg.readEntry("imageScriptRadio", false);
    g_script = cfg.readEntry("imageScript", "");
    g_image = cfg.readEntry("imageUrl", "");
    g_scaling = cfg.readEntry("scaling", 0);
    g_interval = cfg.readEntry("interval", 0);
    g_intervalUnit = cfg.readEntry("intervalUnit", 1);

    switch (g_scaling) {
        case 0: // No scaling
            window.applet.setScrollBarPolicy(Vertical, ScrollBarAsNeeded);
            window.applet.setScrollBarPolicy(Horizontal, ScrollBarAsNeeded);
            window.applet.setAspectRatioMode(IgnoreAspectRatio);
            break;
        case 1: // Scale content to applet
        case 2: // Scale content to applet, keep aspect ratio
            window.applet.setScrollBarPolicy(Vertical, ScrollBarAlwaysOff);
            window.applet.setScrollBarPolicy(Horizontal, ScrollBarAlwaysOff);
            window.applet.setAspectRatioMode(IgnoreAspectRatio);
            break;
        case 3: // Scale applet to content
            window.applet.setScrollBarPolicy(Vertical, ScrollBarAlwaysOff);
            window.applet.setScrollBarPolicy(Horizontal, ScrollBarAlwaysOff);
            window.applet.setAspectRatioMode(FixedSize);
            break;
    }
    if ((g_useScript && g_script == "") || (!g_useScript && g_image == "")) {
        window.applet.setConfigurationRequired(true);
    } else {
        window.applet.setConfigurationRequired(false);
        connectEngine();
    }
}
