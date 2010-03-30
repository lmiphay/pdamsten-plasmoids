#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#    Copyright (c) 2009 Petri Damstén <damu@iki.fi>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU Library General Public License as
#    published by the Free Software Foundation; either version 2, or
#    (at your option) any later version.
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
from urlparse import urlparse
import codecs

#---------------------------------------------------------------------------------------------------

if len(sys.argv) < 2:
    print 'publish.py plasmoidname'
    sys.exit(1)

plasmoid = sys.argv[1].strip('/ ')
if not os.path.exists(plasmoid):
    print 'Can\'t find plasmoid: ' + plasmoid
    sys.exit(1)

onlyText = False
if len(sys.argv) > 2:
    onlyText = (sys.argv[2] == '0')

plasmoidData = {
    'id': '',
    'name': '',
    'description': '',
    'origVersion': '',
    'version': '',
    'contact': '',
    'depends': '',
    'vcs': '',
    'wiki': '',
    'installing': ''
}

buf = ''

PlasmoidScript = '77'
KDE4x          = '50'
GPL            = '1'
UploadedFile   = '0'
Wiki           = '70'
Other          = '500'

gitCommitCmd = './git-commit-gui.py "%s"'
config = ConfigParser.ConfigParser()
config.read(os.path.expanduser('~/.kde-look.org/credentials'))
user = config.get('Credentials', 'user')
password = config.get('Credentials', 'password')
url = 'http://api.opendesktop.org/'
defaultText = 'Please send longer messages like patches, ' + \
'bug reports with outputs, etc. to my email.'

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
    if process.returncode != 0:
        print output
    return (process.returncode, output)

def appendToFrontOfFile(name, s):
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
        #print result
        dom = minidom.parseString(result)
        sc = dom.getElementsByTagName('statuscode')[0].childNodes[0].nodeValue
        return (sc == '100')
    except:
        return False

def tag(s):
    s = s.replace(' ', '-')
    s = s.lower()
    return s

def gitLog(s):
    s = tag(s)
    a = _('git log "%s.." "%s"' % (s, plasmoid))
    if a[0] != 0:
        return ''
    result = []
    for line in a[1].split('\n'):
        line = line.strip()
        if len(line) == 0:
            continue
        if 'commit ' in line or 'Author:' in line or 'Date:' in line:
            continue
        result.append('  * ' + line)
    return '\n'.join(result)

def gitTag(s):
    s = tag(s)
    print 'Tagging %s.' % s
    return (_('git tag "%s"' % s)[0] == 0)

def gitCommit(msg = ''):
    print 'Committing changes.'
    if _(gitCommitCmd % msg)[0] != 0:
        return False
    return True

def makePackage():
    return (_('cd %s && zip -9 -v -o -r ../%s.plasmoid * -x \*~ && cd ..' % \
           (plasmoid, plasmoid))[0] == 0)

def readEntry(config, group, entry, default = ''):
    try:
        return config.get(group, entry)
    except:
        return default

def readInfo():
    global plasmoidData

    print 'Reading info for ' + plasmoid + '.'
    config = ConfigParser.RawConfigParser()
    config.read('./%s/metadata.desktop' % plasmoid)
    plasmoidid = readEntry(config, 'Desktop Entry', 'X-KDE-PluginInfo-Website')
    plasmoidData['id'] = plasmoidid[plasmoidid.find('=') + 1:]
    plasmoidData['name'] = readEntry(config, 'Desktop Entry', 'Name')
    plasmoidData['description'] = readEntry(config, 'Desktop Entry', \
                                            'X-PublishInfo-LongDescription')
    if plasmoidData['description'] == '':
        plasmoidData['description'] = readEntry(config, 'Desktop Entry', 'Comment')
    plasmoidData['origVersion'] = readEntry(config, 'Desktop Entry', 'X-KDE-PluginInfo-Version')
    plasmoidData['version'] = plasmoidData['origVersion']
    plasmoidData['depends'] = readEntry(config, 'Desktop Entry', 'X-PublishInfo-Depends')
    plasmoidData['contact'] = readEntry(config, 'Desktop Entry', 'X-PublishInfo-Contact')
    plasmoidData['vcs'] = readEntry(config, 'Desktop Entry', 'X-PublishInfo-VCS')
    plasmoidData['wiki'] = readEntry(config, 'Desktop Entry', 'X-PublishInfo-Wiki')
    plasmoidData['installing'] = readEntry(config, 'Desktop Entry', 'X-PublishInfo-Installing')
    return True

def newVersion(version):
    v = version.split('.')
    return '%d.%d' % (int(v[0]), int(v[1]) + 1)

def updateVersion():
    global plasmoidData
    global plasmoid

    print 'Updating version and changelog.'
    plasmoidData['version'] = newVersion(plasmoidData['origVersion'])
    plasmoidData['version'] = inputWithDefault('New version', plasmoidData['version'])
    if (plasmoidData['origVersion'] != plasmoidData['version']):
        # RawConfigParser messes file don't use that for writing
        replaceInFile('./%s/metadata.desktop' % plasmoid, \
                      'X-KDE-PluginInfo-Version=%s' % plasmoidData['origVersion'], \
                      'X-KDE-PluginInfo-Version=%s' % plasmoidData['version'])
        log = gitLog(plasmoidData['name'] + ' ' + plasmoidData['origVersion'])
        appendToFrontOfFile('./%s/Changelog' % plasmoid, \
                '%s  Version %s\n%s\n\n' % \
                (datetime.today().strftime('%Y-%m-%d'), plasmoidData['version'], log))
    editor = os.environ['EDITOR']
    os.system(editor + ' ./%s/Changelog' % plasmoid)
    return True

def uploadFile():
    print 'Uploading file: ./%s.plasmoid' % plasmoid
    if plasmoidData['id'] == '':
        return False
    params = [
        ('localfile', (pycurl.FORM_FILE, '%s.plasmoid' % plasmoid))
    ]
    return upload('v1/content/uploaddownload/%s' % plasmoidData['id'], params)

def link(name, link):
    if name == '@domain':
        name = urlparse(link).netloc.split('.')[-2]
    #return '[url=%s]%s[/url]' % (link, name)
    # Does not support url=
    return '[url]%s[/url]' % (link)

def uploadInfo():
    print 'Updating info: %s' % plasmoidData['id']
    if plasmoidData['id'] == '':
        return False
    description = plasmoidData['description'] + '\n\n' + defaultText+ '\n'
    if plasmoidData['depends'] != '':
        description += '\n' + 'Plasmoid depends on: ' + plasmoidData['depends']
    if plasmoidData['contact'] != '':
        description += '\n' + 'Contact: ' + link('email', plasmoidData['contact'])
    if plasmoidData['vcs'] != '':
        description += '\n' + 'Browse Source: ' + link('@domain', plasmoidData['vcs'])
    if plasmoidData['installing'] != '':
        description += '\n' + 'Installing: ' + link('Howto', plasmoidData['installing'])
    if onlyText:
        announce = '0'
    else:
        announce = '1'
    params = [
        ('name', plasmoidData['name']),
        ('type', PlasmoidScript),
        ('depend', plasmoidData['depends']),
        ('downloadtyp1', UploadedFile),
        ('downloadname1', 'Plasmoid'),
        ('description', description),
        ('licensetype', GPL),
        ('version', plasmoidData['version']),
        ('changelog', open('./%s/Changelog' % plasmoid).read()),
        ('announceupdate', announce)
    ]
    if plasmoidData['wiki'] != '':
        params['homepage'] = plasmoidData['wiki']
        params['homepagetype'] = Wiki

    #print params
    return upload('v1/content/edit/%s' % plasmoidData['id'], params)

#---------------------------------------------------------------------------------------------------

if not onlyText:
    X(gitCommit())
X(readInfo())
if not onlyText:
    X(updateVersion())
    X(makePackage())

if inputWithDefault('Continue with upload?', 'yes') == 'yes':
    X(uploadInfo())
    if not onlyText:
        X(uploadFile())
        X(gitCommit('Update version and changelog'))
        if plasmoidData['origVersion'] != plasmoidData['version']:
            X(gitTag(plasmoidData['name'] + ' ' + plasmoidData['version']))
