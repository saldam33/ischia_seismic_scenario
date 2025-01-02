#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  IschiaSeismicScenarioDialog3.py
#  
#  Copyright 2023 Salvatore D'Amico <salvatore.damico@ingv.it>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  

import os
from math import floor
from statistics import NormalDist

from qgis.PyQt import uic
from qgis.PyQt import QtWidgets

# This loads your .ui file so that PyQt can populate your plugin with the elements from Qt Designer
FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'ischia_seismic_scenario_dialog_base3.ui'))


class IschiaSeismicScenarioDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        """Constructor."""
        super(IschiaSeismicScenarioDialog, self).__init__(parent)
        # Set up the user interface from Designer through FORM_CLASS.
        # After self.setupUi() you can access any designer object by doing
        # self.<objectname>, and you can use autoconnect slots - see
        # http://qt-project.org/doc/qt-4.8/designer-using-a-ui-file.html
        # #widgets-and-dialogs-with-auto-connect
        self.setupUi(self)
        
        # connect signals to slots
        self.doubleSpinBoxMw.valueChanged.connect(self.doubleSpinBoxMw_valueChanged)
        self.comboBoxIo.currentIndexChanged.connect(self.comboBoxIo_indexChanged)
        self.radioButtonMag.toggled.connect(self.radioButtonMag_toggled)
        self.radioButtonInt.toggled.connect(self.radioButtonInt_toggled)
        
    
        
    def radioButtonMag_toggled(self, buttonstatus):
        """ Enable the use of moment magnitude to calculate the scenario. """
        self.doubleSpinBoxMw.setEnabled(buttonstatus)
        
        
        
    def radioButtonInt_toggled(self, buttonstatus):
        """ Enable the use of epicentral intensity to calculate the scenario. """ 
        self.comboBoxIo.setEnabled(buttonstatus)
        
        
        
    def comboBoxIo_indexChanged(self, index):
        """ Verify if the selected intensity is usable for probabilistic model. """
        
        indexI0 = (6, 7, 8, 9, 10, 11)
        # Magnitude from Selva et al. 2020
        mwMean =  (3.2, 3.6, 4.0, 4.4, 4.8, 5.2)
        mdMean =  (3.5, 3.9, 4.2, 4.5, 4.8, 5.1)
       
        if indexI0[index]  < 8:
            self.radioButtonProb.setEnabled(False)
            self.radioButtonDeter.setChecked(True)
        else:
            self.radioButtonProb.setEnabled(True)
        
        
        
    def doubleSpinBoxMw_valueChanged(self, mValue):
        """ Check if the magnitude value is usable for probabilistic model. """

        indexI0 = (6, 7, 8, 9, 10, 11)
        # Magnitude from Selva et al. 2020
        mwMean =  (3.2, 3.6, 4.0, 4.4, 4.8, 5.2)
        mdMean =  (3.5, 3.9, 4.2, 4.5, 4.8, 5.1)

        if mValue < 4.0:
            self.radioButtonProb.setEnabled(False)
            self.radioButtonDeter.setChecked(True)
        else:
            self.radioButtonProb.setEnabled(True)
            
    
    
    def getData(self):
        """ Returns input data of the dialog to user as a dictionary. """
        
        # ~ intensity = {'11': 11, '10-11': 10.5, '10': 10, '9-10': 9.5, 
                     # ~ '9': 9, '8-9': 8.5, '8': 8}
        
        try:
            lat = float(self.lineEditLat.text()) 
        except:
            lat = 0
            
        try:
            lon = float(self.lineEditLon.text())
        except:
            lon = 0
        
        if self.radioButtonInt.isChecked():
            i0 = float(self.comboBoxIo.currentText())
        else:
            n = self.comboBoxMtype.currentIndex()
            i0 = mag2int(self.doubleSpinBoxMw.value(), n)
        
        data = {'lat': lat,
                'lon': lon,
                'io':  i0,
                'probmodel': self.radioButtonProb.isChecked(),
                'basemap': self.checkBoxIschia.isChecked(),
                'maskmap': self.checkBoxSea.isChecked(),
            }
        
        return data



def mag2int(magnitude, mtype=0):
    """ Calculate le most probable Epicentral Intensity, given the magnitude. """

    # Initialize data from Selva et al. 2020
    epicInt = (  4,   5,   6,   7,   8,   9,  10,  11)
    mwMean =  (2.2, 2.7, 3.2, 3.6, 4.0, 4.4, 4.8, 5.2)
    mwStd =   (0.6, 0.6, 0.5, 0.5, 0.5, 0.5, 0.5, 0.8)
    mdMean =  (2.7, 3.1, 3.5, 3.9, 4.2, 4.5, 4.8, 5.1)
    mdStd =   (0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2, 0.2)
    
    # Initialize the array for the probability related to magnitude
    p = [0] * len(epicInt)

    if mtype == 1:
        mMean = mwMean
        mStd = mwStd
    else:
        mMean = mdMean
        mStd = mdStd

    # Calculate the probability for each epicInt
    for m, n in enumerate(epicInt):
        p[m] = NormalDist(mu=mMean[m], sigma=mStd[m]).pdf(magnitude)
        
    # Calculate the greater probability and related epicentral intensity
    maxP = max(p)
    intensity = epicInt[p.index(maxP)]

    return intensity



def main(args):
    app = QtWidgets.QApplication(sys.argv)
    # Create the dialog and keep reference
    dlg = IschiaSeismicScenarioDialog()
    exitCode = dlg.exec()
    
    if exitCode == 1:
        print(dlg.getData())

    return 0



if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
