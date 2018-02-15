# -*- coding: utf-8 -*-
"""
Created on Tue Jan 30 21:10:23 2018

@author: Hinrich Rahlfs
"""
import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
import time

plt.rc("font", size=20)
plt.rc("xtick", labelsize=20)
plt.rc("ytick", labelsize=20)
plt.rc("legend", fontsize=14)
plt.rc("lines", linewidth=3)
plt.rc("axes", linewidth=2)
plt.rc("axes", axisbelow=True)
plt.rc("ytick.major", pad=4)
plt.rc("xtick.major", pad=4)
plt.rc("legend", frameon=False)
#rc("lines", markeredgewidth=0.1)
plt.rc("lines", markersize=10)
#rc('text', usetex=True)

plt.rc("figure.subplot",left=0.15)  
plt.rc("figure.subplot",right=0.95)    
plt.rc("figure.subplot",bottom=0.05)     
plt.rc("figure.subplot",top=0.95)


def simpleaxis(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()
    
    
file = open("equalizer praestimulus lautsprecher.npy", "rb")
h_inv = np.load(file,allow_pickle = False,fix_imports = False)
file.close()

plt.plot(h_inv)
