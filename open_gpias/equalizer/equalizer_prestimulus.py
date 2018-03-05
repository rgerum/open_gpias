# -*- coding: utf-8 -*-
"""
Created on Mon Nov 27 13:16:07 2017

@author: rahlfshh
"""
import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
import time

np.random.seed(1337)

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
# rc("lines", markeredgewidth=0.1)
plt.rc("lines", markersize=10)
# rc('text', usetex=True)

plt.rc("figure.subplot", left=0.15)
plt.rc("figure.subplot", right=0.95)
plt.rc("figure.subplot", bottom=0.05)
plt.rc("figure.subplot", top=0.95)


def simpleaxis(ax):
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.get_xaxis().tick_bottom()
    ax.get_yaxis().tick_left()


fs = 96000  # sampling rate in Hz
duration = 2  # signal duration in seconds
adjust_duration = 1  # signal duration for adjustment

# LMS algorithm
mu = 0.2  # step size for LMS algorithm
L = 4096  # filter length for LMS algorithm in samples

# equalizing filter computation
L_eq = 4096
delta = 0.001
nFFT = 10 * L_eq  # heuristic choice; must be >= than L_eq

# start noise factor will, be increased appropriately
noisefactor_min = 0.00
# maximum noisefactor. Be careful, if the amplifier is to strong this needs to be lowered as your speeker might be destroyed otherwise
noisefactor_max = 0.01

noisefactor = (noisefactor_min + noisefactor_max) / 2

max_rec = 0

adjust_x = np.random.randn(fs * adjust_duration)

# find the right adjustment factor
while max_rec < 0.2 or max_rec > 0.25:
    to_play = np.dstack((adjust_x, np.zeros(len(adjust_x))))[0]
    d_adjust = sd.playrec(to_play * noisefactor, samplerate=fs, channels=1, device=[1, 7])
    time.sleep(adjust_duration + 2)
    ################d_adjust = np.convolve(h,adjust_x)*noisefactor
    ################d_adjust += np.random.randn(len(d_adjust))*0.01

    max_rec = max(d_adjust)
    print("max_rec" + str(max_rec))
    print("noisefactor" + str(noisefactor))

    if max_rec < 0.2:
        noisefactor_min = noisefactor
        noisefactor = (noisefactor + noisefactor_max) / 2
        if abs(noisefactor - noisefactor_max) < 0.0001:
            raise RuntimeError(
                "didn't find an apropriate noisefactor, is the microfon plugged in, the dezibelmeter at the right attenuation and the amplifier turned on?")
    elif max_rec > 0.25:
        noisefactor_max = noisefactor
        noisefactor = (noisefactor + noisefactor_min) / 2
        if abs(noisefactor - noisefactor_min) < 0.0001:
            raise RuntimeError(
                "didn't find an apropriate noisefactor, is the microfon plugged in, the dezibelmeter at the right attenuation and the amplifier turned on?")
    else:
        print("found an apropriate noisefactor")
        break

# Signals
x = np.random.randn(
    fs * duration) * noisefactor  # *np.hamming(fs*duration) # playback signal, duration seconds of white Gaussian noise

to_play = np.dstack((x, np.zeros(len(x))))[0]

d = sd.playrec(to_play, samplerate=fs, channels=1, device=[1, 7])
time.sleep(duration + 2)

print(max(d))

for i, item in enumerate(d):
    if item > 0.03:
        print(i)
        d = d[i - 80:]
        break
print(max(d))

h_hat = np.zeros(L)  # estimate of the acoustic impulse response from above, used in LMS algorithm, initially all zero
e = np.zeros(len(x))  # error signal of LMS algorithm, used to adapt filter weights and show convergence

# performance measures for LMS algorithm
e_sys = np.zeros(len(x))  # system distance, i.e., "how well" the impulse response is identified

# LMS algorithm to identify impulse response
buffer_in = np.zeros(len(h_hat))
for kSample in range(len(d) - 2 * L):
    buffer_in = np.concatenate((x[kSample:kSample + 1], buffer_in[:-1]))
    # print(len(buffer_in))
    # print(len(h_hat))
    y = np.dot(buffer_in.transpose(), h_hat)  # filter input with h_hat,
    e[kSample] = d[kSample] - y  # compute error signal by difference of estimated and true signal

    # (N)LMS filter update
    h_hat = h_hat + mu * ((buffer_in * e[kSample]) / (sum(np.absolute(buffer_in) ** 2) + np.finfo(float).eps))

# Performance measures for identification
fig10 = plt.figure(10)
ax = fig10.add_subplot(211)
ax.plot(10 * np.log10(np.absolute(e) ** 2))
plt.title('residual error signal power (logarithmic)')
simpleaxis(ax)
file = open("residual error1.npy", "wb")
np.save(file, e, allow_pickle=False, fix_imports=False)
file.close()

# Determine equalization filter
H = np.fft.fft(h_hat, nFFT)  # transform into frequency domain with additional zero-padding

# compute inverse transfer function: separate phase and magnitude to apply
# regularization only to magnitude
H_inv = (np.exp(-1j * np.angle(H))) / (np.absolute(H) + delta)
# entfernen der hohen frequenzen weil das mikro da nicht mehr passt
# trotzdem Messung mit hoher sample rate, weil weit weg von nyq-freq
mean_12_bis_20_kHz = np.mean(H_inv[int(len(H_inv) / 8):int(len(H_inv) * (20000 / 96000))])
H_inv[int(len(H_inv) * (20000 / fs)):int(len(H_inv) * ((fs - 20000) / fs))] = np.ones(
    int(len(H_inv) * ((fs - 20000) / fs)) - int(len(H_inv) * (20000 / fs))) * mean_12_bis_20_kHz

h_inv_raw = np.fft.ifft(H_inv, nFFT)
# transform back into time domain and enforce a real-valued impulse
# response (it might not be real-valued due to numerical inaccuracy)
h_inv_raw_real = np.real(h_inv_raw)

# concatenate acausal part (appears at the very end of the raw inverse
# impulse response) and the causal part (appears at the beginning)
# h_inv = np.concatenate((h_inv_raw_real[:int(L_eq/2)],h_inv_raw_real[int(-L_eq/2):]))
h_inv = np.concatenate((h_inv_raw_real[int(-L_eq / 2):], h_inv_raw_real[:int(L_eq / 2)]))

# apply time-domain window
h_inv = h_inv * np.hamming(L_eq)

## Equalization performance
h_eq = np.convolve(h_inv, h_hat)  # equalized impulse response

fig1 = plt.figure(1)
ax = fig1.add_subplot(111)
ax.plot(h_eq)
plt.xlabel('tap')
plt.ylabel('amplitude')
plt.title('equalized impulse response')
print(" ")
simpleaxis(ax)

# Visualization of equalized impulse response and magnitude frequency response
fig2 = plt.figure(2, figsize=(8, 8))
ax = fig2.add_subplot(211)
plt.plot(h_hat)
plt.xlabel('tap')
plt.ylabel('amplitude')
plt.title('time-domain impulse response')
simpleaxis(ax)

ax2 = fig2.add_subplot(212)

ax2.plot(np.linspace(0, fs / 4, num=int(len(h_hat) / 4)),
         10 * np.log10(np.absolute(np.fft.fft(h_hat)[:int(len(h_hat) / 4)])))
plt.xlabel('frequency [hz]')
plt.ylabel('magnitude [dB]')
plt.title('magnitude response')
simpleaxis(ax2)
print(" ")

file = open("h of system1.npy", "wb")
np.save(file, h_hat, allow_pickle=False, fix_imports=False)
file.close()

file = open("equalizer praestimulus lautsprecher.npy", "wb")
np.save(file, h_inv, allow_pickle=False, fix_imports=False)
file.close()
