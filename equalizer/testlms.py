# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 13:16:07 2017

@author: rahlfshh
translated to python from matlab version provided by the LMS FAU-Erlangen
"""
import numpy as np
import matplotlib.pyplot as plt
# Parameters
# general parameters
fs = 22000 # sampling rate in Hz
duration = 10 # signal duration in seconds

# LMS algorithm
mu = 0.1# stepsize for LMS algorithm
L = 1024# filter length for LMS algorithm in samples

# equalizing filter computation
L_eq = 1024
delta = 1e-2
nFFT = 10*L_eq# heuristical choice; must be >= than L_eq


## Artificial impulse response
# normally, this impulse response is not known and instead estimated, e.g.,
# via the (N)LMS algorithm (see below)
#h = double((1:L).'==20) + double((1:L).' > 20) .* exp(-((1:L).'-20)*0.01) .* randn(L,1);
h = np.linspace(1,0,num = L)
#h = fftfilt(ones(5,1)./5,h); % averaging with sliding windows acts as a lowpass filter (=> higher frequencies attenuated)

# Visualization of generated impulse response and magnitude frequency response
plt.figure(1)
plt.subplot(211)
plt.plot(h)
plt.xlabel('tap')
plt.ylabel('amplitude')
plt.title('time-domain impulse response')
print(" ")
plt.subplot(212)
plt.plot(10*np.log10(np.absolute(np.fft.fft(h))))
plt.xlabel('frequency bin index')
plt.ylabel('magnitude [dB]')
plt.title('magnitude response')
print(" ")
# Signals
x = np.random.randn(fs*duration)# playback signal, 10 seconds of white Gaussian noise
d = np.convolve(h,x) # recorded microphone signal; here computed by convolution of the playback signal x with the impulse response h (see above)

h_hat = np.zeros(len(h)) # estimate of the acoustic impulse response from above, used in LMS algorithm, initally all zero
e = np.zeros(len(x))# error signal of LMS algorithm, used to adapt filter weights and show convergence

# performance measures for LMS algorithm
e_sys = np.zeros(len(x))# system distance, i.e., "how well" the impulse response is identified


# LMS algorithm to identify impulse response
buffer_in = np.zeros(len(h_hat))
for kSample in range(len(x)):
    
    buffer_in = np.concatenate((x[kSample:kSample+1], buffer_in[:-1]))
    
    y = np.dot(buffer_in.transpose() , h_hat) # filter input with h_hat, 
    e[kSample] = d[kSample] - y # compute error signal by difference of estimated and true signal
    
    # (N)LMS filter update
    h_hat = h_hat + mu * ((buffer_in * e[kSample]) / (sum(np.absolute(buffer_in)**2)+np.finfo(float).eps))
    #was heißt da das eps??? 
    
    e_sys[kSample] = sum(np.absolute(h_hat - h)**2)
    
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
plt.figure(10)
plt.subplot(211)
plt.plot(10*np.log10(np.absolute(e)**2))
plt.title('residual error signal power (logarithmic)')
print(" ")
plt.subplot(212)
plt.plot(10*np.log10(e_sys/e_sys[1]))
plt.title('normalized system distance (logarithmic)')
print(" ")
# Determine equalization filter
H = np.fft.fft(h_hat, nFFT) # transform into frequency domain with additional zero-padding

# compute inverse transfer function: separate phase and magnitude to apply
# regularization only to magnitude
H_inv = (np.exp(-1j*np.angle(H)))/(np.absolute(H)+delta)

# transform back into time domain and enforce a real-valued impulse
# response (it might not be real-valued due to numerical inaccuracy)
h_inv_raw = np.real(np.fft.ifft(H_inv, nFFT))

# concatenate acausal part (appears at the very end of the raw inverse
# impulse response) and the causal part (appears at the beginning)
h_inv = np.concatenate((h_inv_raw[int(-L_eq/2):],h_inv_raw[:int(L_eq/2)]))
# apply time-domain window
h_inv = h_inv * np.hamming(L_eq)

## Equalization performance
h_eq = np.convolve(h_inv,h_hat)# equalized impulse response

import sounddevice as sd
sound = sd.rec(5*40000,samplerate = 40000,channels = 1)
sd.play(sound,40000)
import time 
time.sleep(6)
sound2 = np.convolve(np.convolve(sound.transpose()[0],h), h_inv)
sd.play(sound2,40000)

H1 = np.absolute(np.fft.fft(sound,nFFT))
for i in range(len(H1)):
    if np.absolute(H1[i])>0.1:
        pass
        #print(i)
H2 = np.absolute(np.fft.fft(sound2,nFFT))
for i in range(len(H2)):
    if np.absolute(H2[i])>500:
        	print(i)
# Visualization of equalized impulse response and magnitude frequency response
plt.figure(2)
plt.subplot(211)
plt.plot(h_eq)
plt.xlabel('tap')
plt.ylabel('amplitude')
plt.title('time-domain impulse response')
print(" ")
plt.subplot(212)
plt.plot(10*np.log10(np.absolute(np.fft.fft(h_eq))))
plt.xlabel('frequency bin index')
plt.ylabel('magnitude [dB]')
plt.title('magnitude response')
print(" ")
### Comparison of magnitude responses
#plt.figure(3)
#plt.plot(np.linspace(0,fs/2,L), 10*np.log10(np.absolute(np.fft.fft(h))),'k','DisplayName','Unequalized')
#plt.plot(np.linspace(0,fs/2,L+L_eq-1), 10*np.log10(np.absolute(np.fft.fft(h_eq))),'r','LineWidth',2,'DisplayName','Equalized')
#plt.xlabel('frequency [Hz]')
#plt.ylabel('magnitude [dB]')
