# -*- coding: utf-8 -*-
"""
/***************************************************************************
 IschiaSeismicScenario
                                 A QGIS plugin
 Create a seismic shaking scenario for Ischia Island
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-09-30
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Salvatore D'Amico - INGV-OE
        email                : salvatore.damico@ingv.it
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
import os.path
import math

from qgis.core import *
from qgis.gui import *  
from qgis.utils import iface

from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from qgis.PyQt.QtWidgets import *

from qgis import processing

# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .ischia_seismic_scenario_dialog3 import IschiaSeismicScenarioDialog
# Import the code for probabilit scenario
from .scenario import Scenario


class IschiaSeismicScenario:
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
            'IschiaSeismicScenario_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&Ischia Seismic Scenario')

        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

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
        return QCoreApplication.translate('IschiaSeismicScenario', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            # Adds plugin icon to Plugins toolbar
            self.iface.addToolBarIcon(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = os.path.join(self.plugin_dir, 'icon.png')
        self.add_action(
            icon_path,
            text=self.tr(u'Make the scenario'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr(u'&Ischia Seismic Scenario'),
                action)
            self.iface.removeToolBarIcon(action)


    def addEpicenterToMap(self, lat, lon, io):
        """ Add a point vector layer to the map for the epicenter. """
        
        # make a memory layer for the epicenter
        uri = "point?crs=epsg:4326"
        layerEpicenter = QgsVectorLayer(uri, "Epicenter", "memory")

        fields = QgsFields()
        fields.append(QgsField("Lat", QVariant.Double))
        fields.append(QgsField("Lon", QVariant.Double))
        fields.append(QgsField("I0", QVariant.Double))

        provider = layerEpicenter.dataProvider()
        provider.addAttributes(fields)
        layerEpicenter.updateFields() 
        
        feature = QgsFeature(fields)
        feature.setGeometry(QgsGeometry.fromWkt('Point ({0} {1})'.format(lon, lat)))
        feature.setAttribute('Lat', lat)
        feature.setAttribute('Lon', lon)
        feature.setAttribute('I0', io)
        provider.addFeatures([feature])
        
        return layerEpicenter
    
    
    def addGridToMap(self, lat, lon, width, height, spacing):
        """ Create a vector layer of squared polygon centered on epicenter. """
        
        # width, height and spacing are converted in meters
        width = width * 1000
        height = height * 1000
        spacing = spacing * 1000
        
        # get coordinate of epicenter in WGS84 / UTM zone 33N (epsg: 32633)
        transformer = QgsCoordinateTransform()
        transformer.setSourceCrs(QgsCoordinateReferenceSystem('epsg:4326'))
        transformer.setDestinationCrs(QgsCoordinateReferenceSystem('epsg:32633'))
        point = transformer.transform(lon, lat)
        
        # Define the limits of extension of the grid from width, height and spacing 
        x0 = point.x() - (width / 2)      
        x1 = point.x() + (width / 2)
        y0 = point.y() - (height / 2)
        y1 = point.y() + (height / 2)
        xd = spacing          
        yd = spacing
 
        fields = QgsFields()
        fields.append(QgsField("ID", QVariant.Int))
        fields.append(QgsField("Lat", QVariant.Double))
        fields.append(QgsField("Lon", QVariant.Double))
        fields.append(QgsField("Distance", QVariant.Double))
        fields.append(QgsField("I_ref", QVariant.Int))
        fields.append(QgsField("Prob01", QVariant.Double))
        fields.append(QgsField("Prob02", QVariant.Double))
        fields.append(QgsField("Prob03", QVariant.Double))
        fields.append(QgsField("Prob04", QVariant.Double))
        fields.append(QgsField("Prob05", QVariant.Double))
        fields.append(QgsField("Prob06", QVariant.Double))
        fields.append(QgsField("Prob07", QVariant.Double))
        fields.append(QgsField("Prob08", QVariant.Double))
        fields.append(QgsField("Prob09", QVariant.Double))
        fields.append(QgsField("Prob10", QVariant.Double))
        fields.append(QgsField("Prob11", QVariant.Double))
        fields.append(QgsField("Prob12", QVariant.Double))
       
        # Create a polygonal squared grid for the defined area
        gridresult = processing.run('qgis:creategrid', { 
            'CRS' : 'EPSG:32633', 
            'EXTENT' : '{0}, {1}, {2}, {3}'.format(x0, x1, y0, y1), 
            'OUTPUT' : 'memory:', 
            'TYPE' : 2, 
            'HOVERLAY' : 0, 
            'VOVERLAY' : 0, 
            'HSPACING' : xd, 
            'VSPACING' : yd 
        })['OUTPUT']
        
        # add fields to grid and remove fields added by the processing algorithm
        gridresult.dataProvider().deleteAttributes([0, 1, 2, 3, 4])
        gridresult.dataProvider().addAttributes(fields)
        gridresult.setName('Scenario')
        gridresult.updateFields()

        return gridresult


    def attenuazione_deterministica(self, Io, dist):
        """ Calculates the expected intensity at site Ix as fuzione of the
            attenuazion law. The relazione used is:
            DI = 4.003 * log10(dist) + 1.713
            Ix = Io - DI. """
        
        if dist > 0.4:
            # DI is calculated as function of distance
            DI = (4.003 * math.log10(dist) + 1.713)
            Ix = round(Io - DI)
        else:
            # DI is 0 because in near field there no attenuation
            Ix = math.floor(Io)
        
        return Ix



    def run(self):
        """Run method that performs all the real work"""

        plugin_dir = os.path.dirname(__file__)
        
        # basemap data
        municipalities_file = os.path.join(plugin_dir, 'geodata.gpkg') + '|layername=municipalities'
        municipalities_style = os.path.join(plugin_dir, 'styles', 'municipalities.qml')
        municipalities_name = 'Municipalities'
        localities_file = os.path.join(plugin_dir, 'geodata.gpkg') + '|layername=localities'
        localities_style = os.path.join(plugin_dir, 'styles', 'localities.qml')
        localities_name = 'Cities'

        # maskmap data
        maskmap_file = os.path.join(plugin_dir, 'geodata.gpkg') + '|layername=sea_mask'
        maskmap_style = os.path.join(plugin_dir, 'styles', 'sea_mask.qml')
        maskmap_name = 'Sea (mask)'
        
        # grid size
        center_lon = 13.90588
        center_lat = 40.72578
        width_km = 25
        height_km = 25
        spacing_km = 0.250

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        if self.first_start == True:
            self.first_start = False
            self.dlg = IschiaSeismicScenarioDialog()

        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            inputData = self.dlg.getData()
            lat = inputData['lat']
            lon = inputData['lon']
            io = inputData['io']
            probModel = inputData['probmodel']
            basemap = inputData['basemap']
            maskmap = inputData['maskmap']
            
            # create a group for the scenario
            if probModel:
                groupTitle = "Ischia Probabilistic scenario"
            else:
                groupTitle = "Ischia Deterministic scenario"
            grp = QgsProject.instance().layerTreeRoot().insertGroup(0, groupTitle)

            # make the epicenter layer
            layerEpicenter = self.addEpicenterToMap(lat, lon, io)
            QgsProject.instance().addMapLayer(layerEpicenter, False)
            grp.addLayer(layerEpicenter)
            styleFilename = os.path.join(self.plugin_dir, 'styles', 'epicenter.qml')
            layerEpicenter.loadNamedStyle(styleFilename)

            # make the grid
            layerGrid = self.addGridToMap(center_lat, center_lon, width_km, height_km, spacing_km)
            QgsProject.instance().addMapLayer(layerGrid, False)
            grp.addLayer(layerGrid)
            styleFilename = os.path.join(self.plugin_dir, 'styles', 'expected_intensity.qml')
            layerGrid.loadNamedStyle(styleFilename)

            # create the geometry for the epicenter
            # get coordinate of epicenter in WGS84 / UTM zone 33N (epsg: 32633)
            transformer = QgsCoordinateTransform()
            transformer.setSourceCrs(QgsCoordinateReferenceSystem('epsg:4326'))
            transformer.setDestinationCrs(QgsCoordinateReferenceSystem('epsg:32633'))
            point = transformer.transform(lon, lat)
            epicenter = QgsFeature()
            epicenter.setGeometry(QgsPoint(point))

            # Add a progress bar indicating the percentual of calculated nodes
            progress = QProgressBar()
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar = iface.messageBar().createMessage('Calculating scenario...')
            progressMessageBar.layout().addWidget(progress)
            iface.messageBar().pushWidget(progressMessageBar, Qgis.Info)

            features = layerGrid.getFeatures()
            count = (layerGrid.featureCount())
            progress.setMaximum(count)
            progress.setMinimum(1)
            for n, feature in enumerate(features):
                progress.setValue(n)

                # Calculate distance between each node (feature) and epicenter in km
                geomEpicenter = epicenter.geometry()
                geomFeature = feature.geometry().centroid()
                distKm = geomFeature.distance(geomEpicenter) / 1000
                
                # Calculate the expected intensity at site (feature)
                if probModel:
                    # probabilistic attenuation
                    prob = Scenario().prob(io, distKm)
                    Ix = Scenario().iMax(prob)
                    cp = Scenario().cumProb(prob)

                else:
                    # deterministic attenuation
                    Ix = self.attenuazione_deterministica(io, distKm)
                
                # Transform coordinate of the feature into WGS85
                transformer = QgsCoordinateTransform()
                transformer.setSourceCrs(QgsCoordinateReferenceSystem('epsg:32633'))
                transformer.setDestinationCrs(QgsCoordinateReferenceSystem('epsg:4326'))
                point = transformer.transform(geomFeature.asPoint())
                
                # Update fields of the feature
                dataprovider = layerGrid.dataProvider()
                attrs = {dataprovider.fieldNameIndex('ID'): n,
                         dataprovider.fieldNameIndex('Lat'): point.y(),
                         dataprovider.fieldNameIndex('Lon'): point.x(),
                         dataprovider.fieldNameIndex('I_ref'): Ix,
                         dataprovider.fieldNameIndex('Distance'): distKm,
                        }

                if probModel:
                    for n, pv in enumerate(cp):
                        attrs[dataprovider.fieldNameIndex('Prob{:02d}'.format(n+1))] = pv

                dataprovider.changeAttributeValues({feature.id(): attrs})
                
            # Destroy the message bar because the calculation is over
            iface.messageBar().clearWidgets()
            
            # add the maskmap
            if maskmap:
                vl = QgsVectorLayer(maskmap_file, maskmap_name, 'ogr')
                vl.loadNamedStyle(maskmap_style)
                ml = QgsProject.instance().addMapLayer(vl)
                vl.triggerRepaint()

            # Add the basemaps into a group
            if basemap:
                grp = QgsProject.instance().layerTreeRoot().insertGroup(0, 'Ischia Basemap')
                
                vl = QgsVectorLayer(municipalities_file, municipalities_name, 'ogr')
                vl.loadNamedStyle(municipalities_style)
                QgsProject.instance().addMapLayer(vl, False)
                grp.addLayer(vl)
                vl.triggerRepaint()
                
                vl = QgsVectorLayer(localities_file, localities_name, 'ogr')
                vl.loadNamedStyle(localities_style)
                QgsProject.instance().addMapLayer(vl, False)
                grp.addLayer(vl)
                vl.triggerRepaint()
           