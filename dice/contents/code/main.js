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

SPACING = 10;
MINSIZE = 20;

// TODO No way to read these from dir and put them to the config dialog?
SVGS = ["Vegas Plasma Dice", "Euro Coin", "Normal Dice", "Deck of Cards", "Pills"];

plasmoid.init = function()
{
    plasmoid.setAspectRatioMode(KeepAspectRatio);

    m_count = 0;
    m_maxValue = 0;
    m_id = 0;
    m_locked = [];
    m_values = [];
    m_avoidDuplicates = false;
    m_lockEnabled = false;
    m_svg = null;
    m_margins = [0, 0]

    m_lockedColor = new QColor(255, 255, 255);
    m_lockedColor.alpha = 128;

    m_layout = new LinearLayout(plasmoid);
    m_layout.setContentsMargins(0, 0, 0, 0);
    m_layout.spacing = 0;

    // TODO No way to add my own property? Using QPropertyAnimation as QVariantAnimation.
    m_anim = animation("Property");
    m_anim.targetObject = plasmoid;
    m_anim.valueChanged.connect(plasmoid.onValueChange);
    m_anim.startValue = 0;
    m_anim.endValue = 1;
    m_anim.duration = 500;
    m_anim.direction = AnimationForward;
    m_anim.easingCurve = new QEasingCurve(QEasingCurve.OutSine);

    m_timer = QTimer(plasmoid);
    m_timer.singleShot = true;
    m_timer.interval = 400;
    m_timer.timeout.connect(plasmoid.toggleLocked);

    plasmoid.configChanged();
}

plasmoid.onValueChange = function(value)
{
    if (m_anim.currentValue == 1.0) {
        for (i = 0; i < m_count; ++i) {
            if (!m_locked[i]) {
                v = (Math.ceil(Math.random() * m_maxValue));
                if (m_avoidDuplicates) {
                    for (j = v; j < v + m_maxValue; ++j) {
                        found = false;
                        for (k = 0; k < i; ++k) {
                            if (m_values[k] == v) {
                                found = true;
                                break;
                            }
                        }
                        if (!found) {
                            break;
                        }
                        v = (j % m_maxValue) + 1;
                    }
                }
                m_values[i] = v;
            }
        }
        m_anim.direction = AnimationBackward;
        m_anim.start();
    }
    if (m_anim.currentValue == 0.0) {
        for (i = 0; i < m_count; ++i) {
            m_locked[i] = false;
        }
    }
    plasmoid.update();
}

plasmoid.animate = function()
{
    m_anim.direction = AnimationForward;
    m_anim.start();
}

plasmoid.toggleLocked = function()
{
    m_locked[m_id] = !m_locked[m_id];
    plasmoid.update();
}

plasmoid.onClick = function(id)
{
    if (!m_lockEnabled) {
        plasmoid.animate();
    } else {
        // We get single click also when we double click
        m_id = id;
        m_timer.start();
    }
}

plasmoid.onDoubleClick = function()
{
    m_timer.stop();
    plasmoid.animate();
}

plasmoid.paintElementWithOpacity = function(painter, x, y, element, opacity)
{
    if (opacity > 0.0) {
        if (m_svg.hasElement(element)) {
            r = m_svg.elementRect(element);
            painter.opacity = opacity;
            m_svg.paint(painter, x + r.x, y + r.y, element);
        }
    }
}

plasmoid.paintElementFlipped = function(painter, x, y, element, flip)
{
    if (flip > 0.0) {
        if (m_svg.hasElement(element)) {
            r = m_svg.elementRect(element);
            painter.opacity = 1.0;
            if (flip == 1.0) {
                m_svg.paint(painter, x + r.x, y + r.y, element);
            } else {
                h = r.height * flip;
                m_svg.paint(painter, x + r.x, y + r.y + ((r.height - h) / 2.0),
                            r.width, h, element);
            }
        }
    }
}

plasmoid.paintInterface = function(painter)
{
    // TODO Can't make custom widgets? Plasma::SvqWidget is too simple for this so paint it here.
    if (plasmoid.formFactor == Vertical) {
        short = plasmoid.rect.width;
        long = plasmoid.rect.height;
    } else {
        short = plasmoid.rect.height;
        long = plasmoid.rect.width;
    }
    size = QSizeF(short, short);
    if (m_count > 1) {
        spacing = (long - (m_count * short)) / (m_count - 1);
    } else {
        spacing = 0;
    }
    if (m_svg.size != size) {
        m_svg.resize(short, short);
    }
    for (i = 0; i < m_count; ++i) {
        if (plasmoid.formFactor == Vertical) {
            x = plasmoid.rect.x;
            y = plasmoid.rect.y + (i * (short + spacing));
        } else {
            x = plasmoid.rect.x + (i * (short + spacing));
            y = plasmoid.rect.y;
        }
        if (m_locked[i]) {
            anim = 0.0;
        } else {
            anim = m_anim.currentValue;
        }
        if (m_svg.hasElement('whirl')) {
            // Fade animation
            plasmoid.paintElementWithOpacity(painter, x, y, 'background', 1.0);
            plasmoid.paintElementWithOpacity(painter, x, y, 'value' + m_values[i], 1.0 - anim);
            plasmoid.paintElementWithOpacity(painter, x, y, 'whirl', anim);
        } else {
            // Flip animation
            plasmoid.paintElementFlipped(painter, x, y, 'background', 1.0 - anim);
            plasmoid.paintElementFlipped(painter, x, y, 'value' + m_values[i], 1.0 - anim);
        }
        if (m_locked[i]) {
            if (m_anim.state == 2 && m_anim.direction == AnimationBackward) {
                painter.opacity = m_anim.currentValue;
            } else {
                painter.opacity = 1.0;
            }
            painter.fillRect(x, y, short, short, m_lockedColor);
        }
    }
}

plasmoid.checkSize = function()
{
    if (plasmoid.formFactor == Vertical) {
        short = plasmoid.rect.width;
    } else if (plasmoid.formFactor == Horizontal) {
        short = plasmoid.rect.height;
    }
    print(short);
    print(m_margins);
    if (plasmoid.formFactor == Vertical) {
        plasmoid.setMinimumSize(short, m_count * short + (m_count - 1) * SPACING);
    } else if (plasmoid.formFactor == Horizontal) {
        plasmoid.setMinimumSize(m_count * short + (m_count - 1) * SPACING, short);
    } else {
        plasmoid.setMinimumSize(m_margins[0] + m_count * MINSIZE + (m_count - 1) * SPACING,
                                m_margins[1] + MINSIZE);
        plasmoid.resize(m_margins[0] + m_count * short + (m_count - 1) * SPACING,
                        m_margins[1] + short);
    }
}

plasmoid.formFactorChanged = function()
{
    print("formFactorChanged: " + plasmoid.formFactor);
    plasmoid.checkSize();
}

plasmoid.sizeChanged = function()
{
    print("sizeChanged: " + plasmoid.rect.width + ", " + plasmoid.rect.height);
    plasmoid.checkSize();
}

plasmoid.configChanged = function()
{
    while (m_layout.count > 0) {
        m_layout.removeAt(0);
    }

    m_count = plasmoid.readConfig("itemCount");
    svg = plasmoid.readConfig("itemSvg");
    m_lockEnabled = (plasmoid.readConfig("mode") == 1);
    m_svg = new Svg(SVGS[svg]);
    m_svg.multipleImages = true;
    m_maxValue = m_svg.elementRect('values-hint').width;
    m_avoidDuplicates = m_svg.hasElement('avoid-same-values');

    if (plasmoid.formFactor == Vertical) {
        short = plasmoid.rect.width;
    } else {
        short = plasmoid.rect.height;
    }

    // TODO Only way to get margins?
    plasmoid.resize(200, 200);
    m_margins = [200 - plasmoid.rect.width, 200 - plasmoid.rect.height];

    plasmoid.checkSize();

    m_values = [];
    m_locked = [];
    for (i = 0; i < m_count; ++i) {
        m_values.push(1);
        m_locked.push(false);

        // TODO Applet cannot handle mouse presses? Make transparent widgets for getting clicks.
        w = new IconWidget();
        m_layout.addItem(w);
        // TODO plasmoid.sender does not seem to work?
        eval('f = function() { plasmoid.onClick(' + i + '); }');
        w.clicked.connect(f);
        w.doubleClicked.connect(plasmoid.onDoubleClick);
    }
    plasmoid.update();
}

plasmoid.init();
