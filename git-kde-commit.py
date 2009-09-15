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

import sys, time, os
from subprocess import *
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyKDE4.kdecore import *
from PyKDE4.kdeui import *
from PyKDE4.kparts import *


class Git():
    def __init__(self):
        self.branch = ''
        self.toCommit = []
        self.toAdd = []
        self.behind = 0
        self.updateStatus()

    def run(self, cmd):
        #print cmd
        process = Popen([cmd], shell = True, stdin = PIPE, stdout = PIPE, bufsize = 512 * 1024,
                        close_fds = True, stderr = STDOUT)
        while process.poll() == None:
            time.sleep(0.05)
            QApplication.processEvents()
        output = process.stdout.read().strip()
        #print output
        return (process.returncode, output)

    def diff(self, name):
        if os.path.exists(name):
            return self.run('git diff %s' % name)[1]
        return ''

    def add(self, name):
        return (self.run('git add %s' % name)[0] == 0)

    def commit(self, names, msg):
        names = ['"' + unicode(name) + '"' for name in names]
        return (self.run('git commit %s -m "%s"' % \
                (' '.join(names), msg.replace('"', '\\"')))[0] == 0)

    def updateStatus(self):
        s = self.run('git status')[1]
        add = False
        for line in s.split('\n'):
            if line.startswith('# On b'):
                self.branch = line[12:]
            elif line.startswith('# Untr'):
                add = True
            elif line.startswith('# Your'):
                self.behind = int(re.findall('(\d+)', line)[0])
            elif line[:2] == '#\t':
                s = line[2:].strip()
                if len(s) > 0:
                    if add:
                        self.toAdd.append(('add & commit', s, s))
                    else:
                        i = s.find(':')
                        name = s[i + 1:].strip()
                        a = name.split(' -> ')
                        if len(a) > 1:
                            a.pop(0)
                        self.toCommit.append((s[:i].strip(), name, a[0]))

class GitCommit(QWidget):
    def __init__(self, parent):
        QWidget.__init__(self, parent)
        self.temp = KTemporaryFile()
        self.temp.setSuffix('.diff')
        self.setupUi()
        self.git = Git()
        self.addFileItems(self.git.toCommit)
        self.addFileItems(self.git.toAdd, True)
        if self.filesList.topLevelItemCount() > 0:
            self.filesList.topLevelItem(0).setSelected(True)
            self.changeDiff(self.filesList.topLevelItem(0), None)
            self.selectAll()
            QTimer.singleShot(0, self.messageEdit.setFocus)
        else:
            self.commitButton.setEnabled(False)
            QTimer.singleShot(0, self.cancelButton.setFocus)

    def addFileItems(self, items, add = False):
        for i in items:
            item = QTreeWidgetItem([i[0], i[1]], int(add))
            item.setData(0, Qt.UserRole, i[2])
            self.filesList.addTopLevelItem(item)

    def setupUi(self):
        self.verticalLayout_3 = QVBoxLayout(self)
        self.verticalLayout_3.setObjectName("verticalLayout_3")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName("horizontalLayout_3")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.filesLabel = QLabel(self)
        self.filesLabel.setObjectName("filesLabel")
        self.verticalLayout.addWidget(self.filesLabel)
        self.filesList = QTreeWidget(self)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.filesList.sizePolicy().hasHeightForWidth())
        self.filesList.setSizePolicy(sizePolicy)
        self.filesList.setObjectName("filesList")
        self.filesList.setHeaderLabels([i18n('File'), i18n('Action')])
        self.filesList.header().resizeSection(0, 150)
        self.filesList.setMinimumSize(400, 0)
        self.verticalLayout.addWidget(self.filesList)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.selectAllButton = KPushButton(self)
        self.selectAllButton.setObjectName("selectAllButton")
        self.horizontalLayout.addWidget(self.selectAllButton)
        self.selectNoneButton = KPushButton(self)
        self.selectNoneButton.setObjectName("selectNoneButton")
        self.horizontalLayout.addWidget(self.selectNoneButton)
        self.verticalLayout.addLayout(self.horizontalLayout)
        self.messageLabel = QLabel(self)
        self.messageLabel.setObjectName("messageLabel")
        self.verticalLayout.addWidget(self.messageLabel)
        self.messageEdit = KTextEdit(self)
        sizePolicy = QSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.messageEdit.sizePolicy().hasHeightForWidth())
        self.messageEdit.setSizePolicy(sizePolicy)
        self.messageEdit.setObjectName("messageEdit")
        self.verticalLayout.addWidget(self.messageEdit)
        self.horizontalLayout_3.addLayout(self.verticalLayout)
        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName("verticalLayout_2")
        self.diffLabel = QLabel(self)
        self.diffLabel.setObjectName("diffLabel")
        self.verticalLayout_2.addWidget(self.diffLabel)
        self.part = KLibLoader.self().factory("katepart").create(self, "KatePart")
        self.part.setReadWrite(False)
        self.diffEdit = self.part.widget()
        self.diffEdit.setFocusPolicy(Qt.NoFocus)
        self.diffEdit.setObjectName("diffEdit")
        self.diffEdit.setSizePolicy(QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding))
        self.verticalLayout_2.addWidget(self.diffEdit)
        self.horizontalLayout_3.addLayout(self.verticalLayout_2)
        self.verticalLayout_3.addLayout(self.horizontalLayout_3)
        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        spacerItem = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)
        self.horizontalLayout_2.addItem(spacerItem)
        self.commitButton = KPushButton(self)
        self.commitButton.setAutoDefault(False)
        self.commitButton.setDefault(True)
        self.commitButton.setObjectName("commitButton")
        self.horizontalLayout_2.addWidget(self.commitButton)
        self.cancelButton = KPushButton(self)
        self.cancelButton.setObjectName("cancelButton")
        self.horizontalLayout_2.addWidget(self.cancelButton)
        self.verticalLayout_3.addLayout(self.horizontalLayout_2)
        self.filesLabel.setBuddy(self.filesList)
        self.messageLabel.setBuddy(self.messageEdit)
        self.diffLabel.setBuddy(self.diffEdit)

        self.setTabOrder(self.filesList, self.selectAllButton)
        self.setTabOrder(self.selectAllButton, self.selectNoneButton)
        self.setTabOrder(self.selectNoneButton, self.messageEdit)
        self.setTabOrder(self.messageEdit, self.diffEdit)
        self.setTabOrder(self.diffEdit, self.commitButton)
        self.setTabOrder(self.commitButton, self.cancelButton)

        self.filesLabel.setText(i18n("Files:"))
        self.selectAllButton.setText(i18n("Select All"))
        self.selectNoneButton.setText(i18n("Select None"))
        self.messageLabel.setText(i18n("Message:"))
        self.diffLabel.setText(i18n("Diff:"))
        self.commitButton.setText(i18n("Commit"))
        self.cancelButton.setText(i18n("Cancel"))

        self.connect(self.cancelButton, SIGNAL('clicked()'), self.parent().close)
        self.connect(self.selectAllButton, SIGNAL('clicked()'), self.selectAll)
        self.connect(self.selectNoneButton, SIGNAL('clicked()'), self.selectNone)
        self.connect(self.commitButton, SIGNAL('clicked()'), self.commit)
        self.connect(self.filesList,
                     SIGNAL('currentItemChanged(QTreeWidgetItem*, QTreeWidgetItem*)'),
                     self.changeDiff)

    def changeDiff(self, current, previous):
        if current:
            name = current.data(0, Qt.UserRole).toString()
            if current.type():
                self.part.openUrl(KUrl.fromPath(name))
            else:
                s = self.git.diff(name)
                if self.temp.open():
                    open(self.temp.fileName(), 'w').write(s)
                    self.part.openUrl(KUrl.fromPath(self.temp.fileName()))

    def selectAll(self):
        for i in range(self.filesList.topLevelItemCount()):
            self.filesList.topLevelItem(i).setFlags(
                    Qt.ItemIsUserCheckable | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
            self.filesList.topLevelItem(i).setCheckState(0, Qt.Checked)

    def selectNone(self):
        for i in range(self.filesList.topLevelItemCount()):
            self.filesList.topLevelItem(i).setCheckState(0, Qt.Unchecked)

    def commit(self):
        if self.messageEdit.toPlainText().isEmpty():
            self.messageEdit.setFocus()
            return
        a = []
        for i in range(self.filesList.topLevelItemCount()):
            item = self.filesList.topLevelItem(i)
            if item.checkState(0) == Qt.Checked:
                if item.type():
                    if not self.git.add(item.data(0, Qt.UserRole).toString()):
                        sys.exit(1)
                a.append(item.data(0, Qt.UserRole).toString())
        if len(a) > 0:
            if not self.git.commit(a, self.messageEdit.toPlainText()):
                sys.exit(1)
        self.parent().close()

class MainWindow(KMainWindow):
    def __init__(self):
        KMainWindow.__init__(self)
        self.resize(900, 700)
        self.setCentralWidget(GitCommit(self))


aboutData = KAboutData(
        'git-kde-commit',
        '',
        ki18n('git-kde-commit'),
        '0.1',
        ki18n('Gui for git commit & add'),
        KAboutData.License_GPL,
        ki18n('(c) Petri Damstén'),
        ki18n('none'),
        '',
        'damu@iki.fi'
)
KCmdLineArgs.init(sys.argv, aboutData)
app = KApplication()
mainWindow = MainWindow()
mainWindow.show()
app.connect(app, SIGNAL('lastWindowClosed()'), app.quit)
app.exec_()
