"""
Copyright (c) 2018, 2020, 2021 Kevin Zheng

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *
import sys

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import (
    FigureCanvas, NavigationToolbar2QT as NavigationToolbar)
import skrf as rf

import math
import csv
import datetime

from s2p_view.about import Ui_About
from s2p_view.layout import Ui_MainWindow

paths = []         # list of s2p file paths
networks = []      # list of currently open rf.Network
network_dims = []  # max dimension of currently open networks
labels = []

class AboutDialog(QDialog, Ui_About):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.fig = Figure()
        self.setupUi(self)
        self.about = AboutDialog()

        self.actionAbout.triggered.connect(lambda: self.about.show())
        self.action_Open.triggered.connect(self.openDialog)
        self.actionReload.triggered.connect(reload)
        self.actionSave_Plot.triggered.connect(self.savePlot)
        self.actionClose_All.triggered.connect(closeAll)
        self.enableSmith(self.comboDisplay.currentText())
        self.comboDisplay.currentTextChanged.connect(self.enableSmith)
        self.plotButton.pressed.connect(self.plot)
        self.addToolBar(NavigationToolbar(self.canvas, self))

    def openDialog(self):
        paths, _ = QFileDialog.getOpenFileNames(self,
                filter="S-Parameter Files (*.s?p)")
        if len(paths) > 0:
            try:
                existing_open = len(networks)
                openMany(paths)
                refreshNets(autoCheck=(existing_open == 0))
            except FileNotFoundError as e:
                QMessageBox.critical(self, "Open Data Error", str(e))

    def savePlot(self):
        path, _ = QFileDialog.getSaveFileName(self, filter="Plot Outputs (*.eps *.pdf *.pgf *.png *.ps *.raw *.rgba *.svg *.svgz)")
        if len(path) > 0:
            try:
                self.fig.savefig(path)
            except Exception as e:
                QMessageBox.critical(self, "Save Plot Error", str(e))

    def checkDimEnable(self, autoCheck):
        """
        Enable/disable port plot checkboxes based on maximum currently-loaded
        dimension.
        """
        dim = max(network_dims + [0])  # handle empty network_dims
        def checkEnable(checkbox, ndims):
            if ndims <= dim:
                checkbox.setEnabled(True)
                if autoCheck:
                    checkbox.setChecked(True)
            else:
                checkbox.setEnabled(False)
                if autoCheck:
                    checkbox.setChecked(False)
        checkEnable(self.checkS11, 1)
        checkEnable(self.checkS21, 2)
        checkEnable(self.checkS12, 2)
        checkEnable(self.checkS22, 2)

    def plot(self):
        self.statusbar.showMessage("Plotting...", 100)
        app.processEvents()
        self.fig.clear()
        self.ax = self.fig.subplots()
        s = self.comboDisplay.currentText()
        legend = self.checkLegend.isChecked()
        

        for data, dim, label in zip(networks, network_dims, labels):
            data.frequency.unit = self.comboUnit.currentText().lower()
            
            r = self.lineRange.text()
            
            
            if len(r) > 0:
                try:
                    data = data[r]
                except (ValueError, KeyError):
                    self.statusbar.showMessage("Invalid range!", 3000)
                    return

            def plotIfChecked(c, m, n):
                if c.isChecked() and m < dim and n < dim:
                    path = ""
                    plot_fn = None
                    args_dict = { 'm': m,
                                  'n': n,
                                  'ax': self.ax,
                                  'show_legend': legend if label != "NONE"  else False }
                    if label != None:
                        args_dict['label'] = label                   

                    if s == 'Magnitude':
                        plot_fn = lambda x, m, n: x.plot_s_db(**args_dict)
                    elif s == 'Magnitude (Lin)':
                        plot_fn = lambda x, m, n: x.plot_s_mag(**args_dict)
                    elif s == 'Phase':
                        plot_fn = lambda x, m, n: x.plot_s_deg(**args_dict)
                    elif s == 'Smith':
                        args_dict['draw_labels'] = self.checkLabels.isChecked()
                        args_dict['draw_vswr'] = self.checkVSWR.isChecked()
                        plot_fn = lambda x, m, n: x.plot_s_smith(**args_dict)
                    elif s == 'Z Mag':
                        plot_fn = lambda x, m, n: x.plot_z_mag(**args_dict)
                    elif s == 'Z Real':
                        plot_fn = lambda x, m, n: x.plot_z_re(**args_dict)
                    elif s == 'Z Imag':
                        plot_fn = lambda x, m, n: x.plot_z_im(**args_dict)
                    elif s == 'Y Real':
                        plot_fn = lambda x, m, n: x.plot_y_re(**args_dict)
                    elif s == 'Y Imag':
                        plot_fn = lambda x, m, n: x.plot_y_im(**args_dict)

                    plot_fn(data, m, n)

            plotIfChecked(self.checkS11, 0, 0)
            plotIfChecked(self.checkS21, 1, 0)
            plotIfChecked(self.checkS12, 0, 1)
            plotIfChecked(self.checkS22, 1, 1)

        self.ax.grid('on')
        self.fig.tight_layout()

        self.canvas.draw()
        self.canvas.flush_events()

    def enableSmith(self, t):
        self.comboUnit.setEnabled(t != 'Smith')
        self.smithBox.setEnabled(t == 'Smith')

def openS2P(path):
    net = rf.Network(path)
    label = None
    with open(path) as f:
        for l in f.readlines():
            if len(l) > 0 and l[0] == '!':
                parts = l.strip().split(maxsplit=1)
                if parts[0] == '!Label' and len(parts) > 1:
                    label = parts[1]
    dim = net.s.shape[1]
    paths.append(path)
    networks.append(net)
    network_dims.append(dim)
    labels.append(label)

    mean = averageS21(path)
    try:
        writeToFile(mean, path)
    except:
        textpath = path + 'error.txt'
        try:
            with open(textpath, 'a') as txtFile:
                txtFile.writelines("Cannot open .csv file. try closing it.")
        except:
            pass
        
def writeToFile(mean, path):
    sep = '.'
    filepath = path.rpartition(sep)[0] + '.csv' 

    dateTime = datetime.datetime.now()
    headerDate = dateTime.strftime("%x")
    headerTime = dateTime.strftime("%X")
    hasHeader = False

    try:
        with open(filepath, 'rb') as csvFile:
            hasHeader = csv.Sniffer().has_header('Date')
    except:
        hasHeader = False

    with open(filepath, 'a') as csvFile:
        csvFile.seek(0)
        if hasHeader:
            writeToFile = csv.writer(csvFile)
            writeToFile.writerow([headerDate, headerTime, mean])
        else:
            writeToFile = csv.writer(csvFile)
            writeToFile.writerow(["Date", "Time", "Mean S21 Attenuation [dB]"])
            writeToFile.writerow([headerDate, headerTime, mean])

def averageS21(path):
    totalMagnitude = 0.0
    # To get mag, we need the sqrroot of real squared plus imaginary squared
    with open(path) as file:
        # Get number of avg points
        Lines = len(file.readlines()) - 1
        print(Lines)
        # Set file ref back to TOF (top of file)
        file.seek(1)
        for line in file:
            # Our watch character
            space = ' '
            # Obtain S21 real
            x = line.split(space,4)[3]
            # Obtain S21 imag
            y = line.split(space,5)[4]
            # Ignore top of file (header)... Can also file.seek(1)
            if x != 'RI' and y != 'R':
                magnitude = math.sqrt(math.pow(float(x), 2) + math.pow(float(y), 2))
                totalMagnitude = totalMagnitude + magnitude
    # Convert to dB from linear, and return
    return 20*math.log10(totalMagnitude/Lines)



def refreshNets(autoCheck):
    mainwin.checkDimEnable(autoCheck)
    mainwin.plot()

def openMany(paths):
    for path in paths:
        openS2P(path)

def reload(self):
    global paths, networks, network_dims, labels
    old_paths = paths
    paths = []
    networks = []
    network_dims = []
    labels = []
    openMany(old_paths)
    refreshNets(autoCheck=False)

def closeAll(self):
    global paths, networks, network_dims, labels
    paths = []
    networks = []
    network_dims = []
    labels = []
    refreshNets(autoCheck=True)

def main():
    global mainwin
    global app
    app = QApplication([])
    mainwin = MainWindow()
    mainwin.show()
    try:
        openMany(sys.argv[1:])
        refreshNets(autoCheck=True)
    except FileNotFoundError as e:
        print("Could not open files:", str(e), file=sys.stderr)
        quit()
    app.exec_()
