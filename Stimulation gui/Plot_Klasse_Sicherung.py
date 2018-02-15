#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Created on Mon Dec  4 09:35:19 2017

@author: strebms
"""

import sys
from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from scipy.signal import butter, lfilter

class plotWidget (QWidget):
    
    def __init__(self, data, number):
        
        self.idx = number
        
        self.title = "Plot" + str(number+1)
   
    
        #extracting x,y and z chanel from data array
        self.data_x = data[number,0,:]
        self.data_y = data[number,1,:]
        self.data_z = data[number, 2,:]
        

        #extracting trigger, stimulus and noise burst from data array
        self.data_tr = data[number,3,:]
        self.data_stim = data[number,4,:]
        self.data_burst = data[number,5,:]
        
        if data[number][6][1] == True:
            self.noise = "Yes"
        else:
            self.noise = "No"
            
        if data[number][6][2] == True:
            self.noiseGap = "Yes"
        else: self.noiseGap = "False"
        
        self.noiseFreqMin = str(data[number][6][3])
        self.noiseFreqMax = str(data[number][6][4])
        self.preStimAtten = str(data[number][6][5])
        self.preStimFreq = str(data[number][6][6])
        self.ISI = str(data[number][6][7])
        self.noiseTime = str(data[number][6][8])
        
        
        
        self.t = np.linspace(0.0, 1000.0, self.data_x.__len__())
        
        super().__init__()
        self.valid_trial = self.movement_check (self.rms(self.data_x, self.data_y, self.data_z))
        self.max = self.get_max()
    
        
        self.left = 100
        self.top = 30
        self.width = 1100
        self.height = 1100
        
        self.figure = plt.figure()
        self.canvas = FigureCanvas(self.figure)     
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.canvas.toolbar.hide()
        
        grid = QGridLayout()
        self.setLayout(grid)
        
        grid.addWidget(self.canvas, 1,0,1,3)
        grid.addWidget(self.toolbar, 0,0,1,3)
        
        self.figure.subplots_adjust(left=0.05)     
        self.figure.subplots_adjust(right=0.95)
        self.figure.subplots_adjust(bottom=0.1)
        self.figure.subplots_adjust(top=0.9)
        self.figure.subplots_adjust (hspace=0.3)
        
        self.gs = gridspec.GridSpec(3,2)

        self.initUI() 
        
    def initUI(self):
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.setWindowTitle(self.title)
        
    def plot(self):
        
        if not self.valid_trial:
            self.figure.suptitle("Trial invalid", fontsize=50, color='r')
        else:

            self.figure.suptitle("noise: "+self.noise+"; noiseGap: "+self.noiseGap+"; noiseFreqMin: "+self.noiseFreqMin
                                +"Hz; noiseFreqMax: "+self.noiseFreqMax+"Hz; \n preStimAtten: "+ self.preStimAtten
                                +"dBspl; preStimFreq: "+self.preStimFreq+"Hz; ISI: "+self.ISI+"ms; noiseTime: " 
                                +self.noiseTime + "ms", fontsize=18)
            #TODO Turner, etc.
            self.plot_tr_stim_burst (self.data_tr, self.data_stim, self.data_burst, self.t)
            self.plot_raw(self.data_x, self.data_y, self.data_z,self.t)
            self.plot_total(self.t, self.data_x, self.data_y, self.data_z)
            
    def esc(self):
        self.close()
        
    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_T:
            if self.canvas.toolbar.isHidden():
                self.canvas.toolbar.show()
            else:
                self.canvas.toolbar.hide()
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
            
        #plotting of trigger und stimulation burst
    def plot_tr_stim_burst (self, data_tr, data_stim, data_burst, t):
        pp = self.figure.add_subplot(self.gs[0, 0])
        
        pp.plot(t, data_tr, color='y', label='Trigger')
        pp.plot(t, data_stim, color='g', label='prestimulus')
        pp.plot(t, data_burst, color='r', label='noise burst')
        pp.grid(True)
        pp.set_ylim((-0.5,3.5))        
        pp.legend(loc='upper left',bbox_to_anchor=(0, 1),  shadow=True, ncol=2)
        
        pp.set_title ('Stimulus', fontsize = 15)
        
        pp.set_xlabel('time relative to stimulation onset [ms]', fontsize = 14)
        pp.set_ylabel('V', fontsize = 14) 
        
        #plotting of x, y and z signals
    def plot_raw (self, data_x, data_y, data_z,t):
        xd = self.figure.add_subplot(self.gs[0,1])  
        yd = self.figure.add_subplot(self.gs[1,0])
        zd = self.figure.add_subplot (self.gs[1,1])
                
        xd.set_xlabel('time relative to stimulation onset [ms]', fontsize = 14)
        yd.set_xlabel('time relative to stimulation onset [ms]', fontsize = 14)
        zd.set_xlabel('time relative to stimulation onset [ms]', fontsize = 14)
        
        xd.set_ylabel('response amplitude [V]', fontsize = 14)
        yd.set_ylabel('response amplitude [V]', fontsize = 14)
        zd.set_ylabel('response amplitude [V]', fontsize = 14)
        
        xd.set_title ('acceleration x-axis (raw)', fontsize = 15)
        yd.set_title ('acceleration y-axis (raw)', fontsize = 15)
        zd.set_title ('acceleration z-axis (raw)', fontsize = 15)
        
        xd.axvline(x=700, color='g', label='prestimulus')
        xd.axvline(x=800, color = 'r', label='noise burst')
        xd.legend(loc='upper left',bbox_to_anchor=(0, 1),  shadow=True, ncol=2)
        
        yd.axvline(x=700, color='g', label='prestimulus')
        yd.axvline(x=800, color = 'r',label='noise burst')
        yd.legend(loc='upper left',bbox_to_anchor=(0, 1),  shadow=True, ncol=2)
        
        zd.axvline(x=700, color='g',label='prestimulus')
        zd.axvline(x=800, color = 'r',label='noise burst')
        zd.legend(loc='upper left',bbox_to_anchor=(0, 1),  shadow=True, ncol=2)
        
        xd.plot(t, data_x)
        xd.grid(True)   
        xd.set_ylim((-0.5,0.5))
        
        yd.plot(t, data_y)
        yd.grid(True)
        yd.set_ylim((-0.5,0.5))
        
        zd.plot(t, data_z)
        zd.grid(True)
        zd.set_ylim((-0.5,0.5))
        
        #plotting of total acceleration (rms)
    def plot_total (self, t, data_x, data_y, data_z):
        ta = self.figure.add_subplot(self.gs[2,:])
        
        data = self.rms(data_x/0.9027, data_y, data_z/3.8773)
        
        "Kalibrierung"
        "x / 0.9027"
        "y als Referenz"
        "z / 3.8773"
            
        ta.plot(t, data)
        ta.grid(True)
        ta.set_ylim(0, 2.5)
        
        ta.set_xlabel ('time relative to stimulation onset [ms]', fontsize = 14)
        ta.set_ylabel ('response amplitude [m/s^2]', fontsize = 14)
        ta.set_title ('total acceleration', fontsize = 15)
        
        self.annot_max(t, data, ax=None)
        
        ta.axvline(x=700, color='g',label='prestimulus')
        ta.axvline(x=800, color = 'r',label='noise burst')
        ta.legend(loc='upper left',bbox_to_anchor=(0, 1),  shadow=True, ncol=2)
        
    #calculation of max acceleration
    #TODO eigene Methode geschrieben
    def get_max (self):
        if self.valid_trial == True:
            data = self.rms(self.data_x/0.9027, self.data_y, self.data_z/3.8773)
            return max(data)
        else:
            return np.NaN
        
    #calculation of root mean square data
    def rms (self, data_x, data_y, data_z):
        data = np.empty(shape=(data_x.__len__(),1))
        
        data_xf = self.butter_lowpass_filter(data_x)
        data_yf = self.butter_lowpass_filter(data_y)
        data_zf = self.butter_lowpass_filter(data_z)
        
        data = np.sqrt((data_xf/.300)**2 + (data_yf/.300)**2 + (data_zf/.300)**2)
        
        return data
    
    def movement_check (self, data):
        val = data[:800]
        #TODO: Achim nach richtigem Threshold fragen
        if max(val) > 0.4:
           return False
        else:
           return True
        
         #arrow pointing to max
    def annot_max(self,x,y, ax=None):
        xmax = x[np.argmax(y)]
        ymax = y.max()
        text="at t={:.3f}, max. acceleration={:.3f}".format(xmax, ymax)
        if not ax:
            ax=plt.gca()
            bbox_props = dict(boxstyle="square,pad=0.3", fc="w", ec="k", lw=0.72)
            arrowprops=dict(arrowstyle="->",connectionstyle="angle,angleA=0,angleB=60")
            kw = dict(xycoords='data',textcoords="axes fraction",
                      arrowprops=arrowprops, bbox=bbox_props, ha="right", va="top")
            ax.annotate(text, xy=(xmax, ymax), xytext=(0.94,0.96), **kw)
                
##########low pass filter##########
    def butter_lowpass(self, cutoff, oder, sf):
        N = oder
        Fc = cutoff
        nyq = sf/2
        b,a = butter(N, Fc/nyq, btype='low', analog=False)
        return b,a
    
    def butter_lowpass_filter(self, data):
        b,a = self.butter_lowpass(45, 3, 10000)
        y = lfilter(b, a, data)
        return y
###################################

def main():
    #file = open("C:\Messdaten ohne sinn\matze_hinrich_Pre__turner_2017-12-12_15-03_extracted_data.npy", "rb")
    #arr = np.load("E:\BA_Geordnet\Messarrays\Experimenter_Maus_Pre_or_Post__turner_2017-12-19_09-08_extracted_data.npy")     
    "Kalibration xy"
    #arr = np.load("E:\Kalibration\Kalibration\waagerecht.npy")

    "Kalibartion yz"
    arr = np.load("E:\Kalibration\Kalibration\yz.npy")
    
    app = QApplication(sys.argv)
    w = plotWidget(arr, 0)
    w.plot()
    w.show()
    sys.exit(app.exec_())
    
if __name__ == '__main__':
    main()