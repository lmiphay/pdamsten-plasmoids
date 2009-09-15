#!/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright (c) 2009 Petri Damstén <damu@iki.fi>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU Library General Public License version 2 as
#    published by the Free Software Foundation
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

# pycurl supports easy file upload so using it
import pycurl
import ConfigParser, os, sys
from xml.dom import minidom
from datetime import datetime
from subprocess import *
import codecs

#---------------------------------------------------------------------------------------------------

if len(sys.argv) < 2:
    print 'publish.py plasmoidname'
    sys.exit(1)

plasmoid = sys.argv[1].strip('/ ')
if not os.path.exists(plasmoid):
    print 'Can\'t find plasmoid: ' + plasmoid
    sys.exit(1)

announce = '1'
if len(sys.argv) > 2:
    announce = sys.argv[2]

plasmoidid = ''
version = ''
comment = ''
name = ''
buf = ''
contentType = '77'  # Plasmoid Script
depend = '50'       # KDE 4.x
license = '1'       # GPL
gitCommitCmd = 'git commit -a'
config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/.kde-look.org/credentials'))
user = config.get('Credentials', 'user')
password = config.get('Credentials', 'password')
url = 'http://www.kde-look.org/'
defaultText = 'If you want to contact me by email, send patches or bug reports address can \n\
be found from the about dialog and plasmoid package.\n\
\n\
Source can also be found from the git repository:\n\
http://www.gitorious.org/pdamsten/plasmoids'

#---------------------------------------------------------------------------------------------------

def X(result):
    if not result:
        sys.exit(1)

def _(cmd):
    #print cmd
    process = Popen([cmd], shell = True, stdin = PIPE, stdout = PIPE, bufsize = 512 * 1024,
                    close_fds = True, stderr = STDOUT)
    process.wait()
    output = process.stdout.read().strip()
    #print output
    return (process.returncode, output)

def appendToFontOfFile(name, s):
    f = codecs.open(name, 'r+', 'utf-8')
    content = f.read()
    f.truncate(0)
    f.seek(0)
    content = s + content
    f.write(content)
    f.close()

def replaceInFile(name, old, new):
    f = codecs.open(name, 'r+', 'utf-8')
    content = f.read()
    f.truncate(0)
    f.seek(0)
    content = content.replace(old, new)
    f.write(content)
    f.close()

def inputWithDefault(prompt, default = None):
    if default:
        prompt = '%s [%s]: ' % (prompt, default)
    else:
        prompt += ': '
    result = raw_input(prompt)
    if not result and default:
        return default
    return result

def upload(cmd, params):
    def body(b):
        global buf
        buf += b

    global buf
    buf = ''
    c = pycurl.Curl()
    c.setopt(c.URL, url + cmd)
    c.setopt(c.HTTPPOST, params)
    #c.setopt(c.VERBOSE, 1)
    c.setopt(c.USERPWD, '%s:%s' % (user, password))
    c.setopt(pycurl.WRITEFUNCTION, body)
    c.perform()
    c.close()
    return checkResult(buf)

def checkResult(result):
    try:
        dom = minidom.parseString(result)
        sc = dom.getElementsByTagName('statuscode')[0].childNodes[0].nodeValue
        return (sc == '100')
    except:
        return False

def gitTag(s):
    print 'Tagging.'
    #return (_('git tag %s' % s)[0] == 0)
    return True

def gitCommit():
    print 'Committing changes.'
    while True:
        s = _('git status')[1]
        if s.find('working directory clean') == -1:
            #if _(gitCommitCmd)[0] != 0:
            #    return False
            return True # TODO debug
        else:
            return True

def makePackages():
    return (_('./make.sh')[0] == 0)

def updateVersion():
    print 'Updating version and changelog.'
    global plasmoidid
    global version
    global comment
    global name
    config = ConfigParser.RawConfigParser()
    config.read('./%s/metadata.desktop' % plasmoid)
    origVersion = config.get('Desktop Entry', 'X-KDE-PluginInfo-Version')
    plasmoidid = config.get('Desktop Entry', 'X-KDE-PluginInfo-Website')
    plasmoidid = plasmoidid[plasmoidid.find('=') + 1:]
    comment = config.get('Desktop Entry', 'Comment')
    name = config.get('Desktop Entry', 'Name')
    version = unicode(float(origVersion) + 0.1)
    version = inputWithDefault('New version', version)
    if (origVersion != version):
        # RawConfigParser messes file don't use that for writing
        replaceInFile('./%s/metadata.desktop' % plasmoid, \
                      'X-KDE-PluginInfo-Version=%s' % origVersion, \
                      'X-KDE-PluginInfo-Version=%s' % version)
        appendToFontOfFile('./%s/Changelog' % plasmoid, \
                '%s  Version %s\n  * \n\n' % (datetime.today().strftime('%Y-%d-%m'), version))
    editor = os.environ['EDITOR']
    os.system(editor + ' ./%s/Changelog' % plasmoid)
    return True

def uploadFile():
    print 'Uploading file: ./%s.plasmoid' % plasmoid
    if plasmoidid == '':
        return False
    params = [
        ('localfile', (pycurl.FORM_FILE, './%s.plasmoid' % plasmoid))
    ]
    return upload('v1/content/uploaddownload/%s' % plasmoidid, params)

def uploadInfo():
    print 'Updating info: %s' % plasmoidid
    if plasmoidid == '':
        return False
    params = [
        ('name', name),
        ('type', contentType),
        ('depend', depend),
        ('downloadtyp1', '0'), # uploaded file
        ('downloadname1', 'Plasmoid'),
        ('description', comment + '\n\n' + defaultText),
        ('licensetype', license),
        ('version', version),
        ('homepage', ''),
        ('changelog', open('./%s/Changelog' % plasmoid).read()),
        ('announceupdate', announce)
    ]
    return upload('v1/content/edit/%s' % plasmoidid, params)

#---------------------------------------------------------------------------------------------------

X(gitCommit())
X(updateVersion())
X(makePackages())
X(uploadInfo())
X(uploadFile())
X(gitCommit())
X(gitTag(name + ' ' + version))

