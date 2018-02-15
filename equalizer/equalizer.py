# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 13:16:07 2017

@author: rahlfshh
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
plt.rc("figure.subplot",bottom=0.15)     
plt.rc("figure.subplot",top=0.95)


def simpleaxis(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()

# Parameters
# general parameters
#TODO das könnte man auch mit 96000 machen, aber das dauert sehr lange, brauchen wir das?
fs = 96000 # sampling rate in Hz
duration = 5 # signal duration in seconds

# LMS algorithm
mu = 0.04# stepsize for LMS algorithm
L = 2048# filter length for LMS algorithm in samples

# equalizing filter computation
L_eq = 2048
delta = 1e-2
nFFT = 10*L_eq# heuristical choice; must be >= than L_eq


## Artificial impulse response
# normally, this impulse response is not known and instead estimated, e.g.,
# via the (N)LMS algorithm (see below)
#h = double((1:L).'==20) + double((1:L).' > 20) .* exp(-((1:L).'-20)*0.01) .* randn(L,1);
#h = np.linspace(1,0,num = L)
#h = fftfilt(ones(5,1)./5,h); % averaging with sliding windows acts as a lowpass filter (=> higher frequencies attenuated)

# Signals
x = np.random.randn(fs*duration)/500#*np.hamming(fs*duration) # playback signal, duration seconds of white Gaussian noise
print(max(x))
#d = np.convolve(x,h)
#trigger = np.ones(fs*duration)
#silence = np.zeros(int(fs*0.5))
#trigger = np.concatenate((silence,trigger))
#zeroArray = np.zeros(fs*duration + int(0.5*fs))
#matrixToPlay=np.dstack((np.concatenate((silence,x))/3,np.concatenate((silence,x))/3,trigger,trigger,trigger,trigger,trigger,trigger))[0]
d = sd.playrec(x, samplerate = fs, channels = 1,device = [1,7])
time.sleep(duration+3)
print(max(d))
#sd.play(d, samplerate = fs,device = [1,7])
#time.sleep(duration+3)
#sd.play(d,samplerate = fs)
#time.sleep(duration+2)
d = d.transpose()[0]
for i,item in enumerate(d):
    if item > 0.03:
        print(i)
        d = d[i-60:]
        break
#d , ok= perform_measurement(duration+3,fs,duration)
#sd.play(d, samplerate = fs, device = 'Speakers (ASUS Essence STX II Audio)')#recorded Signal
print(max(d))
#d= np.convolve(d,h)
#d = np.concatenate((np.zeros(512), d))
#

#sd.play(d,samplerate = 96000, device = 7)


h_hat = np.zeros(L) # estimate of the acoustic impulse response from above, used in LMS algorithm, initally all zero
e = np.zeros(len(x))# error signal of LMS algorithm, used to adapt filter weights and show convergence

# performance measures for LMS algorithm
e_sys = np.zeros(len(x))# system distance, i.e., "how well" the impulse response is identified


# LMS algorithm to identify impulse response
buffer_in = np.zeros(len(h_hat))
for kSample in range(len(d)):
    
    buffer_in = np.concatenate((x[kSample:kSample+1], buffer_in[:-1]))
    
    y = np.dot(buffer_in.transpose() , h_hat) # filter input with h_hat, 
    e[kSample] = d[kSample] - y # compute error signal by difference of estimated and true signal
    
    # (N)LMS filter update
    h_hat = h_hat + mu * ((buffer_in * e[kSample]) / (sum(np.absolute(buffer_in)**2)+np.finfo(float).eps))
    #was heißt da das eps??? 
    
    #e_sys[kSample] = sum(np.absolute(h_hat - h)**2)
    
#    if mod(kSample,1000) == 0 && 0
#        figure(10);
#        subplot(211);
#        plot(10*log10(abs(e).^2));
#        title('residual error signal power (logarithmic)');
#        
#        subplot(212);
#        plot(10*log10(e_sys./e_sys(1)));
#        title('normalized system distance (logarithmic)');
#        
#        pause(0.05);
#    end


# Performance measures for identification
fig10 = plt.figure(10)
ax = fig10.add_subplot(211)
ax.plot(10*np.log10(np.absolute(e)**2))
plt.title('residual error signal power (logarithmic)')
simpleaxis(ax)
#plt.subplot(212)
#plt.plot(10*np.log10(e_sys/e_sys[1]))
#plt.title('normalized system distance (logarithmic)')
#print(" ")
# Determine equalization filter
H = np.fft.fft(h_hat, nFFT) # transform into frequency domain with additional zero-padding

# compute inverse transfer function: separate phase and magnitude to apply
# regularization only to magnitude
H_inv = (np.exp(-1j*np.angle(H)))/(np.absolute(H)+delta)
#entfernen der hohen frequenzen weil das mikro da nicht mehr passt
#trotzdem Messung mit hoher sample rate, weil weit weg von nyq-freq
H_inv[int(len(H_inv)/4):int(len(H_inv)*3/4)] = np.ones(int(len(H_inv)*3/4)-int(len(H_inv)/4))


h_inv_raw = np.fft.ifft(H_inv, nFFT)
# transform back into time domain and enforce a real-valued impulse
# response (it might not be real-valued due to numerical inaccuracy)
h_inv_raw_real = np.real(h_inv_raw)

# concatenate acausal part (appears at the very end of the raw inverse
# impulse response) and the causal part (appears at the beginning)
#h_inv = np.concatenate((h_inv_raw_real[:int(L_eq/2)],h_inv_raw_real[int(-L_eq/2):]))
h_inv = np.concatenate((h_inv_raw_real[int(-L_eq/2):],h_inv_raw_real[:int(L_eq/2)]))

# apply time-domain window
h_inv = h_inv * np.hamming(L_eq)

## Equalization performance
h_eq = np.convolve(h_inv,h_hat)# equalized impulse response

fig1 = plt.figure(1)
ax = fig1.add_subplot(111)
ax.plot(h_eq)
plt.xlabel('tap')
plt.ylabel('amplitude')
plt.title('equalized impulse response')
print(" ")
simpleaxis(ax)





# Visualization of equalized impulse response and magnitude frequency response
fig2 = plt.figure(2)
ax = fig2.add_subplot(211)
plt.plot(h_hat)
plt.xlabel('tap')
plt.ylabel('amplitude')
plt.title('time-domain impulse response')
simpleaxis(ax)

ax2 = fig2.add_subplot(212)
#TODO hier 10 oder 20*log(*2)???
ax2.plot(np.linspace(0,fs/2,num=int(len(h_hat)/2)), 10*np.log10(np.absolute(np.fft.fft(h_hat)[:int(len(h_hat)/2)])))
plt.xlabel('frequency [hz]')
plt.ylabel('magnitude [dB]')
plt.title('magnitude response')
simpleaxis(ax2)
print(" ")
### Comparison of magnitude responses
#plt.figure(3)
#plt.plot(np.linspace(0,fs/2,L), 10*np.log10(np.absolute(np.fft.fft(h))),'k','DisplayName','Unequalized')
#plt.plot(np.linspace(0,fs/2,L+L_eq-1), 10*np.log10(np.absolute(np.fft.fft(h_eq))),'r','LineWidth',2,'DisplayName','Equalized')
#plt.xlabel('frequency [Hz]')
#plt.ylabel('magnitude [dB]')
#plt.figure(3)
#plt.subplot(211)
#plt.plot(h_inv)
#plt.xlabel('tap')
#plt.ylabel('amplitude')
#plt.title('inverse time-domain impulse response')
#print(" ")

file = open("equalizer praestimulus lautsprecher.npy", "wb")
np.save(file,h_inv,allow_pickle = False,fix_imports = False)
file.close()
