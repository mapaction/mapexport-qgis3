# -*- coding: utf-8 -*-
"""
/***************************************************************************
 MapExportDialog
                                 A QGIS plugin
 Exports PDF, JPG and metadata XML
                             -------------------
        begin                : 2017-08-27
        git sha              : $Format:%H$
        copyright            : (C) 2017 by MapAction
        email                : info@mapaction.org
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
 Derived from the MapsPrinter plugin, with thanks to 
 Harrissou Sant-anna (Conseil d'Architecture, 
 d'Urbanisme et de l'Environnement du Maine-et-Loire)
"""

import os

from qgis.PyQt import QtWidgets, uic

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'map_export_dialog_base.ui'))


class MapExportDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(MapExportDialog, self).__init__(parent)
        # Set up the user interface from Designer.
        # After setupUI you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)