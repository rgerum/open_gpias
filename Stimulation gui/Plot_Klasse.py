#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Created on Mon Dec  4 09:35:19 2017

@author: strebms
"""

from PyQt5.QtWidgets import QApplication, QWidget, QGridLayout
from PyQt5 import QtCore
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
import numpy as np
from scipy.signal import butter, lfilter

class plotWidget (QWidget):
    
    def __init__(self, data, number, parent = None):
        
        super().__init__(parent = parent)
        plt.close("all")
        self.idx = number
        self.title = "Plot" + str(number+1)
        
        self.threshold = 0.05

        #extracting x,y and z chanel from data array
        self.data_x = data[0,:]
        self.data_y = data[1,:]
        self.data_z = data[2,:]
        

        #extracting trigger, stimulus and noise burst from data array
        self.data_tr = data[3,:]
        self.data_stim = data[4,:]
        self.data_burst = data[5,:]
        
        #data for information about current measurement
        if data[6][1] == 1:
            self.noise = "band"
        elif data[6][1]== 2:
            self.noise = "broadband"
        elif data[6][1]== 3:
            self.noise = "notched"
        else:
            self.noise = "No"
            
        if data[6][2] == True:
            self.noiseGap = "Yes"
        else: self.noiseGap = "False"
        self.noiseFreqMin = str(data[6][3])
        self.noiseFreqMax = str(data[6][4])
        self.preStimAtten = str(data[6][5])
        self.preStimFreq = str(data[6][6])
        self.ISI = str(data[6][7])
        self.noiseTime = str(data[6][8])
        
        #Measurnment time
        self.t = np.linspace(0.0, 950.0, self.data_x.__len__()) 
                
        #variable for moevment control
        self.valid_trial = None
        
        #data, total acceleration, low pass filtered and calibrated
        self.data_filt = self.rms(self.data_x/0.9027, self.data_y, self.data_z/3.8773) 
        
        #size and position of plot window
        self.left = 50
        self.top = 40
        self.width = 1500
        self.height = 1100
        
        #initiation of canvas and toolbar
        self.figure = plt.figure(1)
        self.canvas = FigureCanvas(self.figure) 
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.canvas.toolbar.hide()
        
        self.grid = QGridLayout()
        self.setLayout(self.grid)
        
        self.grid.addWidget(self.canvas, 1,0,1,3)
        self.grid.addWidget(self.toolbar, 0,0,1,3)
        
        #size and position of subplots
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
        
        #check if animal has moved
        self.valid_trial = self.movement_check()
        
        #caption of plot window
        #if invalid trial:
        if not self.valid_trial:
            self.figure.suptitle("Trial invalid", fontsize=50, color='r')
        #if valid trial: information about current measurement
        else:
            self.figure.suptitle("noise: "+self.noise+"; noiseGap: "+self.noiseGap+"; noiseFreqMin: "+self.noiseFreqMin
                                +"Hz; noiseFreqMax: "+self.noiseFreqMax+"Hz; \n preStimAtten: "+ self.preStimAtten
                                +"dBspl; preStimFreq: "+self.preStimFreq+"Hz; ISI: "+self.ISI+"ms; noiseTime: " 
                                +self.noiseTime + "ms", fontsize=18)

        #plotting of noise burst, trigger and stimulus
        self.plot_tr_stim_burst (self.data_tr, self.data_stim, self.data_burst, self.t)
        #plotting of raw data: acceleration of X-, Y- and Z-Axis
        self.plot_raw(self.data_x, self.data_y, self.data_z,self.t)
        self.plot_total()
            
        #func
    def esc(self):
        self.toolbar.setParent(None)
        self.toolbar.deleteLater()
        self.toolbar = None
        self.canvas.setParent(None)
        self.canvas.deleteLater()
        self.canvas = None
        #self.grid.setParent(None)
        self.grid.deleteLater()
        #self.grid = None
        self.close()
        self = None
        
    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_T:
            if self.canvas.toolbar.isHidden():
                self.canvas.toolbar.show()
            else:
                self.canvas.toolbar.hide()
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()
            
        #plotting of trigger, stimulation and noise burst
    def plot_tr_stim_burst (self, data_tr, data_stim, data_burst, t):
        pp = self.figure.add_subplot(self.gs[0, 0])
        
        pp.plot(t, data_tr, color='y', label='Trigger')
        pp.plot(t, data_stim, color='g', label='prestimulus')
        pp.plot(t, data_burst, color='r', label='noise burst')
        pp.grid(True)
        pp.set_xlim((0,950))
        pp.set_ylim((-0.5,3.5))        
        pp.legend(loc='upper left',bbox_to_anchor=(0, 1),  shadow=True, ncol=2)
        
        #title of X-Axis
        pp.set_title ('Stimulus', fontsize = 15)
        
        #title of Y-Axis
        pp.set_xlabel('time relative to stimulation onset [ms]', fontsize = 14)
        pp.set_ylabel('Volt', fontsize = 14) 
        
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
        xd.set_xlim((0,950))
        
        yd.plot(t, data_y)
        yd.grid(True)
        yd.set_ylim((-0.5,0.5))
        yd.set_xlim((0,950))
        
        zd.plot(t, data_z)
        zd.grid(True)
        zd.set_ylim((-0.5,0.5))
        zd.set_xlim((0,950))
        
        #plotting of total acceleration (rms)
    def plot_total (self):
        ta = self.figure.add_subplot(self.gs[2,:])
        
        ta.plot(self.t, self.data_filt)
        ta.grid(True)
        #limitation of Y-Axis: 1 m/s^2
        ta.set_ylim(0, 1.0)
        
        #horizontal line for movement threshold
        ta.axhline(y=self.threshold, xmax=0.84210526315, xmin=0, color ='k', label = 'movement threshold')

        ta.set_xlabel ('time relative to stimulation onset [ms]', fontsize = 14)
        ta.set_ylabel ('response amplitude [$m/s^2$]', fontsize = 14)
        ta.set_title ('total acceleration', fontsize = 15)
        ta.set_xlim((0,950))
        
        #arrow ponting at the maximum
        self.annot_max(self.t[8000:], self.data_filt[8000:], ax=None)
        
        #vertical line for prestimulus and noise burst
        ta.axvline(x=700, color='g',label='prestimulus')
        ta.axvline(x=800, color = 'r',label='noise burst')
        ta.legend(loc='upper left',bbox_to_anchor=(0, 1),  shadow=True, ncol=2)
        
        #calculation of max acceleration
    def get_max (self):
        #calculation of maximum only if trial is valid
        if self.valid_trial:
            #searching for maximum after stimulus
            data = self.data_filt[800:]
            return max(data)
        else:
            return np.NaN
        
        #calculation of root mean square data and low pass filtering
    def rms (self, data_x, data_y, data_z):
        data = np.empty(shape=(data_x.__len__(),1))
        
        data_xf = self.butter_lowpass_filter(data_x)
        data_yf = self.butter_lowpass_filter(data_y)
        data_zf = self.butter_lowpass_filter(data_z)
        
        data = np.sqrt((data_xf/.300)**2 + (data_yf/.300)**2 + (data_zf/.300)**2)
        return data
        
        #check if animal has moved before noise burst
    def movement_check (self):
        #data until threshold
        val = self.data_filt[:8000]
        if max(val) > self.threshold:
           return False
        else:
           return True
        
         #arrow pointing to max
    def annot_max(self,x,y, ax=None):
        xmax = x[np.argmax(y)]
        ymax = y.max()
        #arrow after noise burst
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
        b,a = self.butter_lowpass(45, 6, 10000)
        y = lfilter(b, a, data)
        return y
###################################