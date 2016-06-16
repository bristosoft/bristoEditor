#!/usr/bin/env python
# Copyright (c) 2007-8 Qtrac Ltd. All rights reserved.
# This program or module is free software: you can redistribute it and/or
# modify it under the terms of the GNU General Public License as published
# by the Free Software Foundation, either version 2 of the License, or
# version 3 of the License, or (at your option) any later version. It is
# provided for educational purposes and is distributed in the hope that
# it will be useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See
# the GNU General Public License for more details.
#
#
# June 12, 2016    Need to fix Window Menu methods at end 

import os
import platform
import sys
from PyQt4.QtCore import *
from PyQt4.QtGui import *
import textedit
import qrc_resources


__version__ = "1.0.0"


class MainWindow(QMainWindow):

    def __init__(self, parent=None):
        super(MainWindow, self).__init__(parent)
        
        # Attributes
        self._tabbed = False

        # Set up initial Multiple Document Interface
        self.mdi = QWorkspace()
        self.setCentralWidget(self.mdi)
        
        # Setup actions 
        # File Actions
        fileNewAction = self.createAction("&New", self.fileNew,
                QKeySequence.New, "filenew", "Create a text file")
        fileOpenAction = self.createAction("&Open...", self.fileOpen,
                QKeySequence.Open, "fileopen",
                "Open an existing text file")
        fileSaveAction = self.createAction("&Save", self.fileSave,
                QKeySequence.Save, "filesave", "Save the text")
        fileSaveAsAction = self.createAction("Save &As...",
                self.fileSaveAs, icon="filesaveas",
                tip="Save the text using a new filename")
        fileSaveAllAction = self.createAction("Save A&ll",
                self.fileSaveAll, "filesave",
                tip="Save all the files")
        fileQuitAction = self.createAction("&Quit", self.close,
                "Ctrl+Q", "filequit", "Close the application")
                
        # edit actions
        editCopyAction = self.createAction("&Copy", self.editCopy,
                QKeySequence.Copy, "editcopy",
                "Copy text to the clipboard")
        editCutAction = self.createAction("Cu&t", self.editCut,
                QKeySequence.Cut, "editcut",
                "Cut text to the clipboard")
        editPasteAction = self.createAction("&Paste", self.editPaste,
                QKeySequence.Paste, "editpaste",
                "Paste in the clipboard's text")
        
        # Mode Actions
        windowModeAction = self.createAction("&Windows",  self.windowMode,
                 "Alt+W","","Window Mode")
        tabbedModeAction = self.createAction("&Tabs",  self.tabbedMode,
                 "Alt+T", "","Tabbed Mode")
                
        # Window Actions
        self.windowNextAction = self.createAction("&Next",
                self.mdi.activateNextWindow, QKeySequence.NextChild)
        self.windowPrevAction = self.createAction("&Previous",
                    self.mdi.activatePreviousWindow,
                    QKeySequence.PreviousChild)
        self.windowCascadeAction = self.createAction("Casca&de",
                    self.mdi.cascade)
        self.windowTileAction = self.createAction("&Tile",
                    self.mdi.tile)
        self.windowRestoreAction = self.createAction("&Restore All",
                    self.windowRestoreAll)
        self.windowMinimizeAction = self.createAction("&Iconize All",
                self.windowMinimizeAll)
        self.windowArrangeIconsAction = self.createAction(
                    "&Arrange Icons", self.mdi.arrangeIcons)
        self.windowCloseAction = self.createAction("&Close",
                    self.mdi.closeActiveWindow, QKeySequence.Close)
        
        # About Actions
        abouteditor = self.createAction("About &Editor v. 0.1",  self.aboutEditor)
        aboutqt = self.createAction("About Qt",  self.aboutAboutQt)
                    
        # Setup Menus
        fileMenu = self.menuBar().addMenu("&File")
        self.addActions(fileMenu, (fileNewAction, fileOpenAction,
                fileSaveAction, fileSaveAsAction, fileSaveAllAction,
                None, fileQuitAction))
        editMenu = self.menuBar().addMenu("&Edit")
        self.addActions(editMenu, (editCopyAction, editCutAction,
                                   editPasteAction))
        modeMenu = self.menuBar().addMenu("&Mode")
        self.addActions(modeMenu, (windowModeAction,  tabbedModeAction))
                                   
        # Window Menu
        self.windowMenu = self.menuBar().addMenu("&Window")
        self.connect(self.windowMenu, SIGNAL("aboutToShow()"),
                        self.updateWindowMenu)
        
        # About Menu
        self.aboutMenu = self.menuBar().addMenu("&About")
        self.addActions(self.aboutMenu, (aboutqt,  abouteditor)) 
                        
        # Update the window menu
        self.updateWindowMenu()
        
        # Toolbars
        fileToolbar = self.addToolBar("File")
        fileToolbar.setObjectName("FileToolbar")
        self.addActions(fileToolbar, (fileNewAction, fileOpenAction,
                                          fileSaveAction))
        editToolbar = self.addToolBar("Edit")
        editToolbar.setObjectName("EditToolbar")
        self.addActions(editToolbar, (editCopyAction, editCutAction,
                                          editPasteAction))
                
      
        # Settings and Application State
        settings = QSettings()
        size = settings.value("MainWindow/Size",
                              QVariant(QSize(600, 500))).toSize()
        self.resize(size)
        position = settings.value("MainWindow/Position",
                                  QVariant(QPoint(0, 0))).toPoint()
        self.move(position)
        self.restoreState(
                settings.value("MainWindow/State").toByteArray())

        status = self.statusBar()
        status.setSizeGripEnabled(False)
        status.showMessage("Ready", 5000)
        

        # Using Q singleshot timer(millisec) instead of python time.sleep(sec)
        QTimer.singleShot(0, self.loadFiles)
        
        # Set MainWindow Title
        self.setWindowTitle("Text Editor")
        
    def runMode(self):
        # Set MDI or TABS in Central Widget
        if not self._tabbed:
            self.mdi = QWorkspace()
            self.setCentralWidget(self.mdi)
        else:
            self.tabWidget = QTabWidget()
            self.setCentralWidget(self.tabWidget)
            
        # Set up next and previous tab shortcuts if tabs selected        
        if self._tabbed:
            QShortcut(QKeySequence.PreviousChild, self, self.prevTab)
            QShortcut(QKeySequence.NextChild, self, self.nextTab)

        # Set up signal mapper if MDI selected
        if not self._tabbed:
            self.windowMapper = QSignalMapper(self)
            self.connect(self.windowMapper, SIGNAL("mapped(QWidget*)"),
                         self.mdi, SLOT("setActiveWindow(QWidget*)"))


    def createAction(self, text, slot=None, shortcut=None, icon=None,
                     tip=None, checkable=False, signal="triggered()"):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(":/%s.png" % icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            self.connect(action, SIGNAL(signal), slot)
        if checkable:
            action.setCheckable(True)
        return action


    def addActions(self, target, actions):
        for action in actions:
            if action is None:
                target.addSeparator()
            else:
                target.addAction(action)


    def closeEvent(self, event):
        failures = []
        if not self._tabbed:
            for textEdit in self.mdi.windowList():
                if textEdit.isModified():
                    try:
                        textEdit.save()
                    except IOError, e:
                        failures.append(str(e))
        else:
            for i in range(self.tabWidget.count()):
                textEdit = self.tabWidget.widget(i)
                if textEdit.isModified():
                    try:
                        textEdit.save()
                    except IOError, e:
                        failures.append(str(e))
        if failures and \
           QMessageBox.warning(self, "Text Editor -- Save Error",
                    "Failed to save%s\nQuit anyway?" % \
                    "\n\t".join(failures),
                    QMessageBox.Yes|QMessageBox.No) == QMessageBox.No:
            event.ignore()
            return
        settings = QSettings()
        settings.setValue("MainWindow/Size", QVariant(self.size()))
        settings.setValue("MainWindow/Position",
                QVariant(self.pos()))
        settings.setValue("MainWindow/State",
                QVariant(self.saveState()))
        files = QStringList()
        if not self._tabbed:
            for textEdit in self.mdi.windowList():
                if not textEdit.filename.startsWith("Unnamed"):
                    files.append(textEdit.filename)
        else:
            for i in range(self.tabWidget.count()):
                textEdit = self.tabWidget.widget(i)
                if not textEdit.filename.startsWith("Unnamed"):
                    files.append(textEdit.filename)
        settings.setValue("CurrentFiles", QVariant(files))
        if self._tabbed:
            while self.tabWidget.count():
                textEdit = self.tabWidget.widget(0)
                textEdit.close()
                self.tabWidget.removeTab(0)
        if not self._tabbed:
            self.mdi.closeAllWindows()
    
    
    def prevTab(self):
        last = self.tabWidget.count()
        current = self.tabWidget.currentIndex()
        if last:
            last -= 1
            current = last if current == 0 else current - 1
            self.tabWidget.setCurrentIndex(current)


    def nextTab(self):
        last = self.tabWidget.count()
        current = self.tabWidget.currentIndex()
        if last:
            last -= 1
            current = 0 if current == last else current + 1
            self.tabWidget.setCurrentIndex(current)



    def loadFiles(self):
        if not self._tabbed:
            if len(sys.argv) > 1:
                for filename in sys.argv[1:31]: # Load at most 30 files
                    filename = QString(filename)
                    if QFileInfo(filename).isFile():
                        self.loadFile(filename)
                        QApplication.processEvents()
        else:
        
            if len(sys.argv) > 1:
                count = 0
                for filename in sys.argv[1:]:
                    filename = QString(filename)
                    if QFileInfo(filename).isFile():
                        self.loadFile(filename)
                        QApplication.processEvents()
                        count += 1
                        if count >= 10: # Load at most 10 files
                            break
            else:
                settings = QSettings()
                files = settings.value("CurrentFiles").toStringList()
                for filename in files:
                    filename = QString(filename)
                    if QFile.exists(filename):
                        self.loadFile(filename)
                        QApplication.processEvents()


    def fileNew(self):
        textEdit = textedit.TextEdit()
        if not self._tabbed:
            self.mdi.addWindow(textEdit)
            textEdit.show()
        else:
            self.tabWidget.addTab(textEdit, textEdit.windowTitle())
            self.tabWidget.setCurrentWidget(textEdit)


    def fileOpen(self):
        filename = QFileDialog.getOpenFileName(self,
                            "Text Editor -- Open File")
        if not self._tabbed:                    
            if not filename.isEmpty():
                for textEdit in self.mdi.windowList():
                    if textEdit.filename == filename:
                        self.mdi.setActiveWindow(textEdit)
                        break
                else:
                    self.loadFile(filename)
        else:        
            if not filename.isEmpty():
                for i in range(self.tabWidget.count()):
                    textEdit = self.tabWidget.widget(i)
                    if textEdit.filename == filename:
                        self.tabWidget.setCurrentWidget(textEdit)
                        break
                else:
                    self.loadFile(filename)

    def loadFile(self, filename):
        textEdit = textedit.TextEdit(filename)
        try:
            textEdit.load()
        except (IOError, OSError), e:
            QMessageBox.warning(self, "Text Editor -- Load Error",
                    "Failed to load %s: %s" % (filename, e))
            textEdit.close()
            del textEdit
        else:
            if not self._tabbed:
                self.mdi.addWindow(textEdit)
                textEdit.show()
            else:
                self.tabWidget.addTab(textEdit, textEdit.windowTitle())
                self.tabWidget.setCurrentWidget(textEdit)


    def fileSave(self):
        if not self._tabbed:
            textEdit = self.mdi.activeWindow()
        else:
            textEdit = self.tabWidget.currentWidget()
            if textEdit is None or not isinstance(textEdit, QTextEdit):
                return
            try:
                textEdit.save()
                if self._tabbed:
                    if (self.tabWidget.tabText(
                        self.tabWidget.currentIndex()).startsWith("Unnamed-")):
                        self.tabWidget.setTabText(self.tabWidget.currentIndex(),
                            QFileInfo(textEdit.filename).fileName())
            except (IOError, OSError), e:
                QMessageBox.warning(self, "Editor -- Save Error",
                        "Failed to save %s: %s" % (textEdit.filename, e))


    def fileSaveAs(self):
        if not self._tabbed:
            textEdit = self.mdi.activeWindow()
        else:
            textEdit = self.tabWidget.currentWidget()
        if textEdit is None or not isinstance(textEdit, QTextEdit):
            return
        filename = QFileDialog.getSaveFileName(self,
                        "Editor -- Save File As",
                        textEdit.filename, "Text files (*.txt *.*)")
        if not filename.isEmpty():
            textEdit.filename = filename
            if self._tabbed:
                self.tabWidget.setTabText(self.tabWidget.currentIndex(),
                                          QFileInfo(filename).fileName())
            self.fileSave()


    def fileSaveAll(self):
        errors = []
        if not self._tabbed:
            for textEdit in self.mdi.windowList():
                if textEdit.isModified():
                    try:
                        textEdit.save()
                    except (IOError, OSError), e:
                        errors.append("%s: %s" % (textEdit.filename, e))
        else:
            for i in range(self.tabWidget.count()):
                textEdit = self.tabWidget.widget(i)
                if textEdit.isModified():
                    try:
                        textEdit.save()
                    except (IOError, OSError), e:
                        errors.append("%s: %s" % (textEdit.filename, e))
        if errors:
            QMessageBox.warning(self, "Editor -- "
                    "Save All Error",
                    "Failed to save\n%s" % "\n".join(errors))

    def fileCloseTab(self):
        textEdit = self.tabWidget.currentWidget()
        if textEdit is None or not isinstance(textEdit, QTextEdit):
            return
        textEdit.close()
        
    def editCopy(self):
        if not self._tabbed:
            textEdit = self.mdi.activeWindow()
        else:
            textEdit = self.tabWidget.currentWidget()
        if textEdit is None or not isinstance(textEdit, QTextEdit):
            return
        cursor = textEdit.textCursor()
        text = cursor.selectedText()
        if not text.isEmpty():
            clipboard = QApplication.clipboard()
            clipboard.setText(text)


    def editCut(self):
        if not self._tabbed:
            textEdit = self.mdi.activeWindow()
        else:
            textEdit = self.tabWidget.currentWidget()
        if textEdit is None or not isinstance(textEdit, QTextEdit):
            return
        cursor = textEdit.textCursor()
        text = cursor.selectedText()
        if not text.isEmpty():
            cursor.removeSelectedText()
            clipboard = QApplication.clipboard()
            clipboard.setText(text)


    def editPaste(self):
        if not self._tabbed:
            textEdit = self.mdi.activeWindow()
        else:
            textEdit = self.tabWidget.currentWidget()
        if textEdit is None or not isinstance(textEdit, QTextEdit):
            return
        clipboard = QApplication.clipboard()
        textEdit.insertPlainText(clipboard.text())


    def windowRestoreAll(self):
        for textEdit in self.mdi.windowList():
            textEdit.showNormal()


    def windowMinimizeAll(self):
        for textEdit in self.mdi.windowList():
            textEdit.showMinimized()

    def windowMode(self):
        if not self._tabbed:
            return
        else:
            self.fileSaveAll()                # Save all files
            self.tabWidget.destroy()          # Destroy our tab widget
            self._tabbed = False              # Set tabbed to false
            self.runMode()                    # Run the Mode method
            self.windowMenu.setEnabled(True)  # Enable Window Menu for windowMode

    def tabbedMode(self):
        if self._tabbed:
            return
        else:
            self.fileSaveAll()                # Save all files
            self.mdi.destroy()                # Destroy window workspace
            self.windowMenu.setEnabled(False) # Disable window Menu for tabbed mode
            self._tabbed = True               # Set tabbed to true
            self.runMode()                    # Run the Mode method

    def updateWindowMenu(self):
        self.windowMenu.clear()
        self.addActions(self.windowMenu, (self.windowNextAction,
                self.windowPrevAction, self.windowCascadeAction,
                self.windowTileAction, self.windowRestoreAction,
                self.windowMinimizeAction,
                self.windowArrangeIconsAction, None,
                self.windowCloseAction))
        textEdits = self.mdi.windowList()
        if not textEdits:
            return
        self.windowMenu.addSeparator()
        i = 1
        menu = self.windowMenu
        for textEdit in textEdits:
            title = textEdit.windowTitle()
            if i == 10:
                self.windowMenu.addSeparator()
                menu = menu.addMenu("&More")
            accel = ""
            if i < 10:
                accel = "&%d " % i
            elif i < 36:
                accel = "&%c " % chr(i + ord("@") - 9)
            action = menu.addAction("%s%s" % (accel, title))
            self.connect(action, SIGNAL("triggered()"),
                         self.windowMapper, SLOT("map()"))
            self.windowMapper.setMapping(action, textEdit)
            i += 1
    
    def aboutEditor(self):
        QMessageBox.about(self, "About Editor v. 0.1",
        """<b>About Editor v. 0.1</b> v %s
        <p>Copyright &copy; 2016 bristoSOFT 
        All rights reserved.
        <p>This editor is a multiinterface text editor.
        <p>Python %s - Qt %s - PyQt %s on %s""" % (
        __version__, platform.python_version(),
        QT_VERSION_STR, PYQT_VERSION_STR, platform.system()))

    def aboutAboutQt(self):
        msg = QMessageBox()
        msg.aboutQt(self, "About Qt")


if __name__ == '__main__':
    
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(":/icon.png"))
    app.setOrganizationName("Qtrac Ltd.")
    app.setOrganizationDomain("qtrac.eu")
    app.setApplicationName("Text Editor")
    form = MainWindow()
    form.show()
    app.exec_()
