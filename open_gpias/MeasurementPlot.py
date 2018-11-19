#!/usr/bin/env python
# -*- coding: utf-8 -*-
# MeasurementPlot.py

# Copyright (c) 2018, Richard Gerum, Achim Schilling, Hinrich Rahlfs, Matthias Streb
#
# This file is part of ASR-Setup.
#
# ASR-Setup is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ASR-Setup is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ASR-Setup. If not, see <http://www.gnu.org/licenses/>

from qtpy import QtCore, QtGui, QtWidgets
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from scipy.signal import butter, lfilter
import pandas as pd


class plotWidget(QtWidgets.QWidget):
    data = None

    def __init__(self, parent=None, config=None):
        super().__init__(parent=parent)
        self.layout = QtWidgets.QHBoxLayout()
        self.setLayout(self.layout)
        self.config = config

        # initiation of canvas and toolbar
        self.figure = plt.figure("measurement")
        self.canvas = FigureCanvas(self.figure)
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.canvas.toolbar.hide()

        self.ax1 = self.figure.add_subplot(3, 1, 1)
        self.ax2 = self.figure.add_subplot(3, 1, 2)
        self.ax3 = self.figure.add_subplot(3, 1, 3)

        self.layout.addWidget(self.canvas)
        self.layout.addWidget(self.toolbar)

        self.plot_tr_stim_burst()
        self.plot_raw()
        self.plot_total()

        self.figure.tight_layout(rect=[0, 0, 0.8, 1])

    def setData(self, data, number):
        self.idx = number
        self.title = "Plot" + str(number + 1)

        # create a pandas dataframe from the recorded data
        self.data = pd.DataFrame(data.T, columns=["x", "y", "z", "trigger", "stimulus", "burst", "protocol"])

        # data for information about current measurement
        if data[6][1] == 1:
            self.noise = "band"
        elif data[6][1] == 2:
            self.noise = "broadband"
        elif data[6][1] == 3:
            self.noise = "notched"
        else:
            self.noise = "No"

        if data[6][2] is True:
            self.noiseGap = "Yes"
        else:
            self.noiseGap = "False"
        self.noiseFreqMin = str(data[6][3])
        self.noiseFreqMax = str(data[6][4])
        self.preStimAtten = str(data[6][5])
        self.preStimFreq = str(data[6][6])
        self.ISI = str(data[6][7])
        self.noiseTime = str(data[6][8])

        # Measurement time
        self.t = np.linspace(0.0, 950.0, self.data["x"].__len__())

        # variable for movement control
        self.valid_trial = None

        # data, total acceleration, low pass filtered and calibrated
        self.data_filt = self.rms(self.data["x"], self.data["y"], self.data["z"])

        self.plot_tr_stim_burst()
        self.plot_raw()
        self.plot_total()

        self.canvas.draw()

    def plot(self):
        # check if animal has moved
        self.valid_trial = self.movementCheck()

        # caption of plot window
        # if invalid trial:
        if not self.valid_trial:
            self.figure.suptitle("Trial invalid", fontsize=50, color='r')
        # if valid trial: information about current measurement
        else:
            self.figure.suptitle(
                "noise: " + self.noise + "; noiseGap: " + self.noiseGap + "; noiseFreqMin: " + self.noiseFreqMin
                + "Hz; noiseFreqMax: " + self.noiseFreqMax + "Hz; \n preStimAtten: " + self.preStimAtten
                + "dBspl; preStimFreq: " + self.preStimFreq + "Hz; ISI: " + self.ISI + "ms; noiseTime: "
                + self.noiseTime + "ms", fontsize=18)

        # plotting of noise burst, trigger and stimulus
        self.plot_tr_stim_burst(self.data_tr, self.data_stim, self.data_burst, self.t)
        # plotting of raw data: acceleration of X-, Y- and Z-Axis
        self.plot_raw(self.data_x, self.data_y, self.data_z, self.t)
        self.plot_total()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_T:
            if self.canvas.toolbar.isHidden():
                self.canvas.toolbar.show()
            else:
                self.canvas.toolbar.hide()
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()

    def plot_tr_stim_burst(self):
        """
        Plotting of trigger, stimulation and noise burst.
        """
        ax = self.ax1
        ax.cla()

        if self.data is not None:
            ax.plot(self.t, self.data["trigger"], color='y', label='Trigger')
            ax.plot(self.t, self.data["stimulus"], color='g', label='prestimulus')
            ax.plot(self.t, self.data["burst"], color='r', label='noise burst')

        ax.grid(True)
        ax.set_xlim((0, 950))
        ax.set_ylim((-3.5, 3.5))
        ax.legend(loc='upper left', bbox_to_anchor=(1., 1), shadow=True, ncol=1)

        # title of X-Axis
        #ax.set_title('Stimulus')

        # title of Y-Axis
        #ax.set_xlabel('time relative to stimulation onset [ms]')
        ax.set_ylabel('Volt')

    def plot_raw(self):
        """ plotting of x, y and z signals """
        ax = self.ax2
        ax.cla()

        #ax.set_xlabel('time relative to stimulation onset [ms]')

        ax.set_ylabel('response\namplitude [V]')

        #ax.set_title('acceleration x-axis (raw)')

        ax.axvline(x=700, color='g', label='prestimulus')
        ax.axvline(x=800, color='r', label='noise burst')
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1), shadow=True, ncol=1)

        if self.data is not None:
            ax.plot(self.t, self.data["x"])
            ax.plot(self.t, self.data["y"])
            ax.plot(self.t, self.data["z"])
        ax.grid(True)
        ax.set_ylim((-0.5, 0.5))
        ax.set_xlim((0, 950))

    def plot_total(self):
        """
        Plotting of total acceleration (rms).
        """
        ax = self.ax3
        ax.cla()

        if self.data is not None:
            ax.plot(self.t, self.data_filt)

            # horizontal line for movement threshold
            ax.axhline(y=self.config.acceleration_threshold, xmax=0.84210526315, xmin=0, color='k', label='movement threshold')

            # arrow pointing at the maximum
            self.annot_max(self.t[8000:], self.data_filt[8000:], ax=None)

        ax.grid(True)
        # limitation of Y-Axis: 1 m/s^2
        ax.set_ylim(0, 1.0)
        ax.set_xlabel('time relative to stimulation onset [ms]')
        ax.set_ylabel('response\namplitude [m/s²]')
        #ax.set_title('total acceleration')
        ax.set_xlim((0, 950))

        # vertical line for prestimulus and noise burst
        ax.axvline(x=700, color='g', label='prestimulus')
        ax.axvline(x=800, color='r', label='noise burst')
        ax.legend(loc='upper left', bbox_to_anchor=(1, 1), shadow=True, ncol=1)

    def get_max(self):
        """
        Calculation of max acceleration
        """
        # calculation of maximum only if trial is valid
        if self.valid_trial:
            # searching for maximum after stimulus
            data = self.data_filt[800:]
            return max(data)
        else:
            return np.NaN

    def rms(self, data_x, data_y, data_z):
        """ calculation of root mean square data and low pass filtering """
        data = np.empty(shape=(data_x.__len__(), 1))

        data_xf = self.butter_lowpass_filter(data_x)
        data_yf = self.butter_lowpass_filter(data_y)
        data_zf = self.butter_lowpass_filter(data_z)

        data = np.sqrt((data_xf / .300) ** 2 + (data_yf / .300) ** 2 + (data_zf / .300) ** 2)
        return data

    def movementCheck(self):
        """ check if animal has moved before noise burst """
        # data until threshold
        val = self.data_filt[:8000]
        if max(val) > self.config.acceleration_threshold:
            return False
        else:
            return True

    def annot_max(self, x, y, ax=None):
        """
        Add an arrow pointing to max.
        """
        xmax = x[np.argmax(y)]
        ymax = y.max()
        # arrow after noise burst
        text = "at t={:.3f}, max. acceleration={:.3f}".format(xmax, ymax)
        if not ax:
            ax = plt.gca()
            bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
            arrowprops = dict(arrowstyle="->", connectionstyle="angle,angleA=0,angleB=60")
            kw = dict(xycoords='data', textcoords="axes fraction",
                      arrowprops=arrowprops, bbox=bbox_props, ha="right", va="top")
            ax.annotate(text, xy=(xmax, ymax), xytext=(0.94, 0.96), **kw)

    ##########low pass filter##########
    def butter_lowpass(self, cutoff, oder, sf):
        N = oder
        Fc = cutoff
        nyq = sf / 2
        b, a = butter(N, Fc / nyq, btype='low', analog=False)
        return b, a

    def butter_lowpass_filter(self, data):
        b, a = self.butter_lowpass(45, 6, 10000)
        y = lfilter(b, a, data)
        return y
    ###################################
