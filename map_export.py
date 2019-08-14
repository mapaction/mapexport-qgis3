# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MapExport
                             A QGIS plugin
 Export a selected print composer to pdf and jpg, create a metadata file and zip
                              -------------------
        begin                : 2017-09-01
        git sha              : $Format:%H$
        copyright            : (C) 2017 by MapAction
        email                : ascott@mapaction.org
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from __future__ import absolute_import
from builtins import str
from builtins import range
from builtins import object
import os.path
import sys
import errno
import tempfile
import datetime
import zipfile
import xml.etree.cElementTree as ET
from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication
from qgis.PyQt.QtWidgets import QAction
from qgis.PyQt.QtGui import QIcon
from . import resources
# from qgis.core import QgsMapLayerRegistry
from qgis.core import QgsProject
from qgis.core import QgsMapLayer
from qgis.core import *
# from PyQt4.QtCore import *
from qgis.utils import *
from qgis.gui import QgsMessageBar
import xml.etree.cElementTree as ET
import subprocess
import site
import csv
msgBar = iface.messageBar()


from qgis.PyQt.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QFileInfo, QDir, QUrl, QTimer, Qt, QObject 
from qgis.PyQt.QtWidgets import QAction, QListWidgetItem, QFileDialog, QDialogButtonBox, QMenu, QMessageBox, QApplication
from qgis.PyQt.QtGui import QIcon, QPainter, QCursor, QDesktopServices
from qgis.PyQt.QtPrintSupport import QPrinter

from qgis.core import *
from qgis.gui import QgsMessageBar

# Initialize Qt resources from file resources.py
from . import resources
# Import the code for the dialog
from .map_export_dialog import MapExportDialog


class MapExport(object):
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'MapExport_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dlg = MapExportDialog()
        
        self.arret = False

    # noinspection PyMethodMayBeStatic

    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('MapExport', message)

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        # Create action that will start plugin configuration
       
        self.action = QAction(QIcon(':/plugins/MapExport/icons/icon.png'),
                              self.tr(u'Export JPG and PDF and zip up'),
                              self.iface.mainWindow()
                              )
       
         # Connect the action to the run method
        self.action.triggered.connect(self.run)

        # Connect to the export button to do the real work
        self.dlg.exportButton.clicked.connect(self.saveFile)

          # Connect to the update button to update variable values
        self.dlg.updateVarVals.clicked.connect(self.updateVars)

          # Connect to the browser button to select export folder
        self.dlg.browser.clicked.connect(self.browseDir)

        # Connect some actions to manage dialog status while another project is opened
        self.iface.newProjectCreated.connect(self.dlg.close)
        self.iface.projectRead.connect(self.renameDialog)
   
        # Add toolbar button and menu item0
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu(u'&Map Export', self.action)
  
        # Hide the Cancel button at the opening
        self.dlg.btnCancel = self.dlg.buttonBox.button(QDialogButtonBox.Cancel)
        self.dlg.btnCancel.hide()
        self.dlg.btnClose = self.dlg.buttonBox.button(QDialogButtonBox.Close)


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""

        self.iface.removePluginMenu(u'&Map Export', self.action)
        # self.iface.removePluginMenu(u'&Map Export', self.helpAction)
        self.iface.removeToolBarIcon(self.action)

    def getNewCompo(self, w, cView):
        """Function that finds new composer to be added to the list."""

        nameCompo = cView.name()
        if not w.findItems(nameCompo, Qt.MatchExactly):
            item = QListWidgetItem()
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            item.setText(nameCompo)
            w.addItem(item)
            
    def getNewComp(self, w, cView):
        """Function that finds new composer to be added to the list."""

        nameCompo = cView.name()
        item = QString()
        item.setText(nameCompo)
        w.addItem(item)

    def populateComposerSelect(self, w):
        """Called to populate the composer list when opening a new dialog."""

        # Get  all the composers in a previously emptied list
        w.clear()
        # Populate the drop down of composers
        for cView in QgsProject.instance().layoutManager().printLayouts():
            composer_name = cView.name()
            self.dlg.composerSelect.addItem(composer_name)

    def populateMetadataItems(self, m, composer):
        """Called to populate the current value of metadata items when opening a dialogue
        Project first
        for metadata items
        if type = projects
            get current value using name warning in variable doesn't exist, prompt to create?
        else
            get current value if any using selected print composer and name
        """
        currProject = QgsProject.instance()
        for x in m:
            ma_variable = str(x[0])
            elem_name = str(x[1])
            elem_name = elem_name.strip()
            ma_level = str(x[2])
            ma_level = ma_level.strip()
            if (ma_level == 'project'):
                QgsMessageLog.logMessage('Warning: level ' + str(ma_level),  'MapExport')
                 # get current value for variable from project and populate field
                if ma_variable == 'ma_country':
                    # QgsMessageLog.logMessage('Warning: variable ' + str(QgsExpressionContextUtils.projectScope().variable(ma_variable)),  'MapExport')
                    self.dlg.maCountry.setText(str(QgsExpressionContextUtils.projectScope(currProject).variable('ma_variable')))
                elif ma_variable == 'ma_crs':
                    self.dlg.maCrs.setText(str(QgsExpressionContextUtils.projectScope(currProject).variable(ma_variable)))
                elif ma_variable == 'ma_glide_number':
                    self.dlg.maGlide.setText(str(QgsExpressionContextUtils.projectScope(currProject).variable(ma_variable)))
                elif ma_variable == 'ma_organisation':
                    self.dlg.maOrganisation.setText(str(QgsExpressionContextUtils.projectScope(currProject).variable(ma_variable)))
            elif (ma_level == 'composer'):
#                if ma_variable =='ma_language':
 #                   self.dlg.maLanguage.setText('french')
                for composer in QgsProject.instance().layoutManager().printLayouts():
                    if composer.name() == self.dlg.composerSelect.currentText():
                        if ma_variable == 'ma_map_number':
                            self.dlg.maMapNumber.setText(str(QgsExpressionContextUtils.layoutScope(composer).variable(ma_variable)))
                        elif ma_variable == 'ma_summary':
                            self.dlg.maSummary.setText(str(QgsExpressionContextUtils.layoutScope(composer).variable(ma_variable)))
                        elif ma_variable == 'ma_language':
                            self.dlg.maLanguage.setText(str(QgsExpressionContextUtils.layoutScope(composer).variable(ma_variable)))
                        elif ma_variable == 'ma_datasource':
                            self.dlg.maDatasource.setText(str(QgsExpressionContextUtils.layoutScope(composer).variable(ma_variable)))
                        elif ma_variable == 'ma_title':
                            self.dlg.maTitle.setText(str(QgsExpressionContextUtils.layoutScope(composer).variable(ma_variable)))
                       # elif ma_variable == 'ma_created':
                        #    self.dlg.maCreated.setDate(str(QgsExpressionContextUtils.compositionScope(composer.composition()).variable(ma_variable)))

            else:
                QgsMessageLog.logMessage('Warning: level ' + str(ma_level),  'MapExport')
                
        # output composer variables
        """
        To add:
        - themes
        
        for composer in self.iface.activeComposers():
            if composer.composerWindow().windowTitle() == self.dlg.composerSelect.currentText():
                date_now = datetime.date.today().strftime("%B %d, %Y")
                ET.SubElement(mapdata,'lastUpdated').text = date_now
                title = composer.composerWindow().windowTitle()
                ET.SubElement(mapdata,'jpgfilename').text = composer.composerWindow().windowTitle() + '.jpg'
                ET.SubElement(mapdata,'pdffilename').text = composer.composerWindow().windowTitle() + '.pdf'
                item = composer.composition().getComposerItemById('main')
                # main_map = [item for item in composer.composition().items() if item.type() == QgsComposerItem.ComposerMap]
                # Get the attr by name and call 
                QgsMessageLog.logMessage('Warning: map item ' + str(item),  'MapExport')
                QgsMessageLog.logMessage('Warning: map item type ' + str(item.type),  'MapExport')
                map_scale = getattr(item, 'scale')()
                
                ET.SubElement(mapdata,'scale').text = str(map_scale)
                map_extent = item.currentMapExtent()
                map_xmin = map_extent.xMinimum()
                map_xmax = map_extent.xMaximum()
                map_ymin = map_extent.yMinimum()
                map_ymin = map_extent.yMaximum()
                QgsMessageLog.logMessage('Scale 1 ' + str(map_xmin), 'MapExport')
                ET.SubElement(mapdata,'xmin').text = str(map_xmin)
                
                for x in metadata_list:
                    ma_variable = str(x[0])
                    elem_name = str(x[1])
                    elem_name = elem_name.strip()
                    ma_level = str(x[2])
                    ma_level = ma_level.strip()
                    if ma_level == 'composer':
                        elem_value = str(QgsExpressionContextUtils.compositionScope(composer.composition()).variable(ma_variable))
                        ET.SubElement(mapdata,elem_name).text = elem_value
                        if elem_value.strip():
                            QgsMessageLog.logMessage(ma_variable + ' exported as ' + elem_value, 'MapExport')
                        else:
                            msgBar.pushMessage('Warning: missing value for ' + ma_variable,  5)
                            QgsMessageLog.logMessage('Warning: missing value for ' + ma_variable, 'MapExport')
                tree = ET.ElementTree(settings)
                """

 
    def browseDir(self):
        """Open the browser so the user selects the output directory."""

        settings = QSettings()
        
        # Remember the last export location (may need changing)
        dir = settings.value('/UI/lastSaveAsImageDir')  
        folderDialog = QFileDialog.getExistingDirectory(
            None,
            '',
            dir,
            QFileDialog.ShowDirsOnly
            )

        if folderDialog == '':
            self.dlg.path.setText(self.dlg.path.text())
        else:
            self.dlg.path.setText(folderDialog)

    def checkFolder(self, outputDir):
        """Ensure export's folder exists and is writeable."""

        # It'd be better to find a way to check writeability in the first try...
        try:
            os.makedirs(outputDir)
            # settings.setValue('/UI/lastSaveAsImageDir', outputDir)
        except Exception as e:
            # if the folder already exists then let's check it's writeable
            if e.errno == errno.EEXIST:
                try:
                    testfile = tempfile.TemporaryFile(dir = outputDir)
                    testfile.close()
                except Exception as e:
                    if e.errno in (errno.EACCES, errno.EPERM):
                        QMessageBox.warning(None, self.tr(u'Unable to write in folder'),
                            self.tr(u"You don't have rights to write in this folder. "\
                            "Please select another one."),
                            QMessageBox.Ok, QMessageBox.Ok)
                    else:
                        raise
                    self.browseDir()
                else:
                    return True
            # if the folder doesn't exist and can't be created then choose another directory
            elif e.errno in (errno.EACCES, errno.EPERM):
                QMessageBox.warning(None, self.tr(u'Unable to use the directory'),
                    self.tr(u"You don't have rights to create or use such a folder. " \
                    "Please select another one."),
                    QMessageBox.Ok, QMessageBox.Ok)
                self.browseDir()
            # for anything else, let user know (mind if it's worth!?)
            else:
                QMessageBox.warning(None, self.tr(u'An error occurred : '),
                    u'{}'.format(e), QMessageBox.Ok, QMessageBox.Ok)
                self.browseDir()
        else: # if it is created with no exception
            return True

    def checkFilled(self, d):
        """Check if all the mandatory informations are filled."""

        missed = []
        for (x, y) in d:
            if not y: # if the second value is null, 0 or empty
                # outline the first item in red
                x.setStyleSheet('border-style: outset; border-width: 1px; border-color: red')
                # retrieve the missing value
                missed.append(y)
            else:
                x.setStyleSheet('border-color: palette()')
        # and if there are missing values, show error message and stop execution
        if missed:
            self.iface.messageBar().pushMessage('Map Export : ',
                self.tr(u'Please consider filling the mandatory field(s) outlined in red.'),
                level = QgsMessageBar.CRITICAL,
                duration = 5)
            return False
        # otherwise let's proceed the export
        else:
            return True

    def initGuiButtons(self):
        """Init the GUI to follow export processes."""

        self.dlg.exportButton.setEnabled(False)

        # Activate the Cancel button to stop export process, and hide the Close button
        self.dlg.buttonBox.rejected.disconnect(self.dlg.reject)
        self.dlg.btnClose.hide()
        self.dlg.btnCancel.show()
        self.dlg.buttonBox.rejected.connect(self.stopProcessing)

    def pageProcessed(self):
        """Increment the page progressbar."""

        self.dlg.pageBar.setValue(self.dlg.pageBar.value() + 1)

    def stopProcessing(self):
        """Help to stop the export processing."""

        self.arret = True

    def restoreGui(self):
        """Reset the GUI to its initial state."""

        QTimer.singleShot(1000, lambda: self.dlg.pageBar.setValue(0))
        QTimer.singleShot(1000, lambda: self.dlg.updateBar.setValue(0))
        self.dlg.printinglabel.setText('')
        
        # Reset standardbuttons and their functions and labels
        self.dlg.buttonBox.rejected.disconnect(self.stopProcessing)
        self.dlg.buttonBox.rejected.connect(self.dlg.reject)
        self.dlg.btnCancel.hide()
        self.dlg.btnClose.show()
        QApplication.restoreOverrideCursor()
        self.dlg.exportButton.setEnabled(True)

        self.arret = False

    def msgEmptyPattern(self):
        """Display a message to tell there's no pattern filename for atlas
        TODO: offer the ability to fill the pattern name.
        """
        self.iface.messageBar().pushMessage(
            self.tr(u'Empty filename pattern'),
                self.tr(u'The print composer "{}" has an empty filename '\
                    'pattern. {}_$feature is used as default.'
                    ).format(self.title, self.title),
            level = QgsMessageBar.WARNING
            )

    def updateVars(self):
        # Progress bar
        # check if all the mandatory infos are filled and if ok, export
        # if self.checkFilled(d) and self.checkFolder(folder):
        i = 0
        # Init progressbars
        self.initGuiButtons()
        QApplication.setOverrideCursor(Qt.BusyCursor)

        self.dlg.updateBar.setValue(0)
        self.dlg.updateBar.setMaximum(11)

        # self.dlg.composerSelect.currentIndex():
        title = self.dlg.composerSelect.currentText()
            
        self.dlg.printinglabel.setText(self.tr(u'Updating {}...').format(title))

        # process input events in order to allow canceling
        QCoreApplication.processEvents()
        #  self.exportCompo(cView, folder, title)
            

            
        # update variable values from form 
        # set variable from current form value
        # ma_country_val = self.dlg.maCountry.text()
        # update PROJECT variable from form
        QgsExpressionContextUtils.setProjectVariable('ma_country',self.dlg.maCountry.text())
        self.dlg.updateBar.setValue(self.dlg.updateBar.value() + 1)
        QgsExpressionContextUtils.setProjectVariable('ma_glide_number',self.dlg.maGlide.text())
        self.dlg.updateBar.setValue(self.dlg.updateBar.value() + 1)
        QgsExpressionContextUtils.setProjectVariable('ma_crs',self.dlg.maCrs.text())
        self.dlg.updateBar.setValue(self.dlg.updateBar.value() + 1)
        QgsExpressionContextUtils.setProjectVariable('ma_organisation',self.dlg.maOrganisation.text())
        self.dlg.updateBar.setValue(self.dlg.updateBar.value() + 1)
        QgsExpressionContextUtils.setProjectVariable('ma_country',self.dlg.maCountry.text())
        self.dlg.updateBar.setValue(self.dlg.updateBar.value() + 1)
        # Language
        QgsExpressionContextUtils.setProjectVariable('ma_language',self.dlg.maLanguage.text())
        self.dlg.updateBar.setValue(self.dlg.updateBar.value() + 1)
             

        for composer in self.iface.activeComposers():
            if composer.composerWindow().windowTitle() == self.dlg.composerSelect.currentText():
                QgsMessageLog.logMessage('Warning: value for ' + self.dlg.maSummary.toPlainText(), 'MapExport')
                # Map Number
                QgsExpressionContextUtils.setCompositionVariable(composer.composition(),'ma_map_number',self.dlg.maMapNumber.text())
                self.dlg.updateBar.setValue(self.dlg.updateBar.value() + 1)
                # Map Title
                QgsExpressionContextUtils.setCompositionVariable(composer.composition(),'ma_title',self.dlg.maTitle.text())
                self.dlg.updateBar.setValue(self.dlg.updateBar.value() + 1)
                # Date Created
                QgsExpressionContextUtils.setCompositionVariable(composer.composition(),'ma_created',self.dlg.maCreated.date())
                self.dlg.updateBar.setValue(self.dlg.updateBar.value() + 1)

             
                # Map Summary
                QgsExpressionContextUtils.setCompositionVariable(composer.composition(),'ma_summary',self.dlg.maSummary.toPlainText())
                self.dlg.updateBar.setValue(self.dlg.updateBar.value() + 1)
                # Data sources
                QgsExpressionContextUtils.setCompositionVariable(composer.composition(),'ma_datasource',self.dlg.maDatasource.toPlainText())
                self.dlg.updateBar.setValue(self.dlg.updateBar.value() + 1)
                
                

                # str(QgsExpressionContextUtils.compositionScope(composer.composition()).variable(ma_variable))
                # self.dlg.maMapNumber.text()
                # date_now = datetime.date.today().strftime("%B %d, %Y")
                # ET.SubElement(mapdata,'lastUpdated').text = date_now
        i = i + 1
        QApplication.restoreOverrideCursor()

        # show an ending message 
        # in case of abortion
        if self.arret:
            self.iface.messageBar().pushMessage(
                self.tr(u'Operation interrupted : '),
                self.tr(u'Maps on {} have been '\
                    'exported to "{}" before cancelling. '\
                    'Some files may be incomplete.'
                    ).format(i,folder),
                level = Qgis.Info, duration = 10
                )
        # or when export ended completely
        else:
            self.iface.messageBar().pushMessage(
                self.tr(u'Operation finished : '),
                self.tr(u'The maps have been '\
                    'exported to "{}".'
                    ).format(title),
                level = Qgis.Info, duration = 50
                )
                # keep in memory the output folder
            # Reset the GUI
            self.restoreGui()
            

        
    def saveFile(self):
        """Check if the conditions are filled to export file(s) and
        export the checked composers to the specified file format."""

        # Ensure list of print composers is up to date
        self.dlg.composerSelect.currentIndex()
        cView = QgsProject.instance().layoutManager().layoutByName(self.dlg.composerSelect.currentText())
     #   for composer in QgsProject.instance().layoutManager().printLayouts():
             
 #       cView = [composer.layoutByName(self.dlg.composerSelect.currentText()) for composer in QgsProject.instance().layoutManager().printLayouts() 
 #               if composer.name() == self.dlg.composerSelect.currentText()][0]
        # Update variable values
        # QgsExpressionContextUtils.setProjectVariable(ma_country,'hello world')
        
         # get the output directory
        folder = self.dlg.path.text()
        # Are there at least one composer checked,
        # an output folder indicated and an output file format chosen?
        d = {
            # the folder box and its text
            (self.dlg.path, folder),
            }

        # check if all the mandatory infos are filled and if ok, export
        if self.checkFilled(d) and self.checkFolder(folder):
            i = 0
            # Init progressbars
            self.initGuiButtons()
            QApplication.setOverrideCursor(Qt.BusyCursor)

            # for self.dlg.composerSelect.currentIndex():
            title = self.dlg.composerSelect.currentText()
            
            self.dlg.printinglabel.setText(
                self.tr(u'Exporting {}...').format(title)
                )

            # process input events in order to allow canceling
            QCoreApplication.processEvents()
            self.exportCompo(cView, folder, title)
            i = i + 1
            QApplication.restoreOverrideCursor()

            # show an ending message 
            # in case of abortion
            if self.arret:
                self.iface.messageBar().pushMessage(
                    self.tr(u'Operation interrupted : '),
                    self.tr(u'Maps on {} have been '\
                        'exported to "{}" before cancelling. '\
                        'Some files may be incomplete.'
                        ).format(i,folder),
                    level = Qgis.Info, duration = 10
                    )
            # or when export ended completely
            else:
                self.iface.messageBar().pushMessage(
                    self.tr(u'Operation finished : '),
                    self.tr(u'The maps have been '\
                        'exported to "{}".'
                        ).format(os.path.join(folder, title)),
                    level = Qgis.Info, duration = 50
                    )
                # keep in memory the output folder
            # Reset the GUI
            self.restoreGui()
            
    def exportCompo(self, cView, folder, title):
        """Function that sets how to export files."""
        currProject = QgsProject.instance()
        printer = QPrinter()
        painter = QPainter()
        exporter = QgsLayoutExporter(cView)
        #Let's use custom export properties if there are
        # exportSettings = self.overrideExportSetings(cView, extension)

        # Set page progressbar maximum value
        # possible for atlases once the rendering has begun
#        maxpages = cView.numPages()
#       self.dlg.pageBar.setValue(0)
#        self.dlg.pageBar.setMaximum(maxpages)
           # Do the export process
        if not os.path.exists(os.path.join(folder, title)):
            os.makedirs(os.path.join(folder, title))
        exporter.exportToPdf(os.path.join(folder, title, title + '.pdf'), QgsLayoutExporter.PdfExportSettings())
        exporter.exportToImage(os.path.join(folder, title, title + '.jpg'), QgsLayoutExporter.ImageExportSettings())
#        self.printToRaster(cView, os.path.join(folder, title), title, '.jpg')
        self.pageProcessed()
        
        """
        Do the metadata export
        """
        # read CSV file & load into list
        with open(os.path.join(self.plugin_dir,"input/metadata_items.csv"), 'r') as metadata_file:
            reader = csv.reader(metadata_file, delimiter=',')
            metadata_list = list(reader)
            # print(metadata_list)
        
        settings = ET.Element("mapdoc")
        mapdata = ET.SubElement(settings, "mapdata")
        # output QGIS variables
        ET.SubElement(mapdata,'operationID').text = 'product-type-testing'
        ET.SubElement(mapdata,'versionNumber').text = '1'
        ET.SubElement(mapdata,'status').text = 'new'
        
        map_extent = str(self.iface.mapCanvas().extent())
        xmin = str(self.iface.mapCanvas().extent().xMinimum())
        xmax = str(self.iface.mapCanvas().extent().xMaximum())
        ymin = str(self.iface.mapCanvas().extent().yMinimum())
        ymax = str(self.iface.mapCanvas().extent().yMaximum())
        ET.SubElement(mapdata,'xmin').text = xmin
        ET.SubElement(mapdata,'xmax').text = xmax
        ET.SubElement(mapdata,'ymin').text = ymin
        ET.SubElement(mapdata,'ymax').text = ymax
       
        # output project variables
        for x in metadata_list:
            ma_variable = str(x[0])
            elem_name = str(x[1])
            elem_name = elem_name.strip()
            ma_level = str(x[2])
            ma_level = ma_level.strip()
            if (ma_level == 'project'):
                elem_value = str(QgsExpressionContextUtils.projectScope(currProject).variable(ma_variable))
                ET.SubElement(mapdata,elem_name).text = elem_value
                if elem_value.strip():
                    QgsMessageLog.logMessage(ma_variable + ' exported as ' + elem_value, 'MapExport')
                else:
                    msgBar.pushMessage('Warning: missing value for ' + ma_variable,  5)
                    QgsMessageLog.logMessage('Warning: missing value for ' + ma_variable, 'MapExport')
        # output composer variables
        """
        To add:
        - themes
        """

        for composer in QgsProject.instance().layoutManager().printLayouts():
            if composer.name() == self.dlg.composerSelect.currentText():
                date_now = datetime.date.today().strftime("%B %d, %Y")
                ET.SubElement(mapdata,'lastUpdated').text = date_now
                title = composer.name()
                ET.SubElement(mapdata,'jpgfilename').text = composer.name() + '.jpg'
                ET.SubElement(mapdata,'pdffilename').text = composer.name() + '.pdf'
                item = composer.itemById('main')
                # main_map = [item for item in composer.composition().items() if item.type() == QgsComposerItem.ComposerMap]
                # Get the attr by name and call 
                QgsMessageLog.logMessage('Warning: map item ' + str(item),  'MapExport')
                QgsMessageLog.logMessage('Warning: map item type ' + str(item.type),  'MapExport')
                map_scale = getattr(item, 'scale')()
                
                ET.SubElement(mapdata,'scale').text = str(map_scale)
                map_extent = item.extent()
                map_xmin = map_extent.xMinimum()
                map_xmax = map_extent.xMaximum()
                map_ymin = map_extent.yMinimum()
                map_ymin = map_extent.yMaximum()
                QgsMessageLog.logMessage('Scale 1 ' + str(map_xmin), 'MapExport')
                ET.SubElement(mapdata,'xmin').text = str(map_xmin)
                
                for x in metadata_list:
                    ma_variable = str(x[0])
                    elem_name = str(x[1])
                    elem_name = elem_name.strip()
                    ma_level = str(x[2])
                    ma_level = ma_level.strip()
                    if ma_level == 'composer':
                        elem_value = str(QgsExpressionContextUtils.projectScope(currProject).variable(ma_variable))
                        ET.SubElement(mapdata,elem_name).text = elem_value
                        if elem_value.strip():
                            QgsMessageLog.logMessage(ma_variable + ' exported as ' + elem_value, 'MapExport')
                        else:
                            msgBar.pushMessage('Warning: missing value for ' + ma_variable,  5)
                            QgsMessageLog.logMessage('Warning: missing value for ' + ma_variable, 'MapExport')
                tree = ET.ElementTree(settings)
                tree.write(os.path.join(folder, title, title + '.xml'))
        
        
        # Set the location and the file name of the zip
        zippath = os.path.join(folder, title)
        zf = zipfile.ZipFile(os.path.abspath(folder) +  os.sep + title + ".zip", "w")
        for dirnames,folders,files in os.walk(os.path.join(folder, title)):
            #  for root, dirs, files in os.walk(folder):
            for file in files:
                zf.write(os.path.join(os.path.join(folder, title),file),file)
        zf.close()
 
    def composeritemattr(composername, mapname, attrname,feature):
        composers = iface.activeComposers()
        # Find the composer with the given name
        comp = [composer.composition() for composer in composers 
                if composer.composerWindow().windowTitle() == composername]
        # Find the item
        item = comp.getComposerItemById(mapname)
        # Get the attr by name and call 
        return getattr(item, attrname)()
         

    def printToRaster(self, cView, folder, name, ext):
        """Export to image raster."""

        for numpage in range(0, cView.numPages()):
            if self.arret:
                break
            # process input events
            QCoreApplication.processEvents()

            # managing multiple pages in the composition
            imgOut = cView.printPageAsRaster(numpage)
            if numpage == 0:
                imgOut.save(os.path.join(folder, name + ext))
            else:
                imgOut.save(os.path.join(folder, name + '_'+ str(numpage + 1) + ext))
            self.pageProcessed()

    def renameDialog(self):
        """Name the dialog with the project's title or filename."""
        
        prj = QgsProject.instance()
        if prj.title() != '':
            self.dlg.setWindowTitle(u'Map Export - {}'.format(prj.title()))
        else:
            self.dlg.setWindowTitle(u'Map Export - {}'.format(
                os.path.splitext(os.path.split(prj.fileName())[1])[0]))

    def run(self):
        """Run method that performs all the real work."""

        # when no composer is in the project, display a message about the lack of composers and exit
        if len(QgsProject.instance().layoutManager().printLayouts()) == 0:
            self.iface.messageBar().pushMessage(
                'Map Export : ',
                self.tr(u'There is currently no print composer in the project. '\
                'Please create at least one before running this plugin.'),
                level = Qgis.Info, duration = 5
                )
            self.dlg.close()
        else:
            self.renameDialog()
            # show the dialog and fill the widget the first time
            if not self.dlg.isVisible():
                self.populateComposerSelect(self.dlg.composerSelect)
                self.dlg.show()
                # Create a list from the metadata items CSV
                with open(os.path.join(self.plugin_dir,"input/metadata_items.csv"), 'r') as metadata_file:
                    reader = csv.reader(metadata_file, delimiter=',')
                    metadata_list = list(reader)
                    # Call the function to populate metadata items in dialogue with current values
                    self.populateMetadataItems(metadata_list,self.dlg.composerSelect)
            else:
                # if the dialog is already opened but not on top of other windows
                # Put it on the top of all other widgets,
                self.dlg.activateWindow()

