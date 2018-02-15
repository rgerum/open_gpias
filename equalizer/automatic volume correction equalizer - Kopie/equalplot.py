# -*- coding: utf-8 -*-
"""
Created on Sat Feb  3 21:58:12 2018

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



#file = open("h of system after equalization.npy", "rb")
h_hat = np.load("h of system after equalization.npy")
file.close()


fig2 = plt.figure(2) 
ax = fig2.add_subplot(211)
plt.plot(h_hat)
plt.xlabel('tap')
plt.ylabel('amplitude')
plt.title('time-domain impulse response')
simpleaxis(ax)


ax2 = fig2.add_subplot(212)
#TODO hier 10 oder 20*log(*2)???
ax2.plot(np.linspace(0,fs/4,num=int(len(h_hat)/4)), 10*np.log10(np.absolute(np.fft.fft(h_hat)[:int(len(h_hat)/4)])))
plt.xlabel('frequency [hz]')
plt.ylabel('magnitude [dB]')
plt.title('magnitude response')
simpleaxis(ax2)
print(" ")