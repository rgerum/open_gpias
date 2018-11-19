#!/usr/bin/env python
# -*- coding: utf-8 -*-
# equalizer.py

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

import numpy as np
import matplotlib.pyplot as plt
import sounddevice as sd
import time
import os


def recordTransferFunction(output, pre):
    np.random.seed(1337)

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
    if pre:
        noisefactor_max = 0.01
    else:
        noisefactor_max = 0.003

    noisefactor = (noisefactor_min + noisefactor_max) / 2

    max_rec = 0

    adjust_x = np.random.randn(fs * adjust_duration)

    # find the right adjustment factor
    while max_rec < 0.2 or max_rec > 0.25:
        if pre:
            to_play = np.dstack((adjust_x, np.zeros(len(adjust_x))))[0]
        else:  # startle
            to_play = np.dstack((np.zeros(len(adjust_x)), adjust_x))[0]
        # play the signal
        d_adjust = sd.playrec(to_play * noisefactor, samplerate=fs, channels=1, device=[1, 7])
        # wait for the recording to finish
        time.sleep(adjust_duration + 2)

        # get the maximum
        max_rec = max(d_adjust)
        print("max_rec" + str(max_rec))
        print("noisefactor" + str(noisefactor))

        # if the amplitude is too small, increase it
        if max_rec < 0.2:
            noisefactor_min = noisefactor
            noisefactor = (noisefactor + noisefactor_max) / 2
            if abs(noisefactor - noisefactor_max) < 0.0001:
                raise RuntimeError("didn't find an appropriate noise factor, is the microphone plugged in, the dezibelmeter "
                                   "at the right attenuation and the amplifier turned on?")
        # if the amplitude is too big, decrease it
        elif max_rec > 0.25:
            noisefactor_max = noisefactor
            noisefactor = (noisefactor + noisefactor_min) / 2
            if abs(noisefactor - noisefactor_min) < 0.0001:
                raise RuntimeError(
                    "didn't find an appropriate noise factor, is the microphone plugged in, the dezibelmeter "
                    "at the right attenuation and the amplifier turned on?")
        # we found the right factor
        else:
            print("found an appropriate noise factor")
            break

    # Signals
    x = np.random.randn(fs * duration) * noisefactor  # *np.hamming(fs*duration) # playback signal, duration seconds of white Gaussian noise

    # compose the channels
    if pre:
        to_play = np.dstack((x, np.zeros(len(x))))[0]
    else:  # startle
        to_play = np.dstack((np.zeros(len(x)), x))[0]

    # play the sound and record
    d = sd.playrec(to_play, samplerate=fs, channels=1, device=[1, 7])
    # wait for the recording to finish
    time.sleep(duration + 2)

    # print the maximum of the signal
    print(max(d))

    # find the index where the signal starts
    for i, item in enumerate(d):
        if item > 0.03:
            print(i)
            # remove the beginning of the signal that was under the threshold
            d = d[max(i - 80, 0):]
            break
    print(max(d))

    h_hat = np.zeros(L)  # estimate of the acoustic impulse response from above, used in LMS algorithm, initally all zero
    e = np.zeros(len(x))  # error signal of LMS algorithm, used to adapt filter weights and show convergence

    # LMS algorithm to identify impulse response
    buffer_in = np.zeros(len(h_hat))
    for kSample in range(len(d) - 2 * L):
        # add the new value from left to the buffer. This means the buffer grows from left to right
        buffer_in = np.concatenate((x[kSample:kSample + 1], buffer_in[:-1]))

        y = np.dot(buffer_in.transpose(), h_hat)  # filter input with h_hat,
        e[kSample] = d[kSample] - y  # compute error signal by difference of estimated and true signal

        # (N)LMS filter update
        h_hat = h_hat + mu * ((buffer_in * e[kSample]) / (sum(np.absolute(buffer_in) ** 2) + np.finfo(float).eps))

    # store the residual error
    with open(os.path.join(output, "residual_error.npy"), "wb") as file:
        np.save(file, e, allow_pickle=False, fix_imports=False)

    # Determine equalization filter
    H = np.fft.fft(h_hat, nFFT)  # transform into frequency domain with additional zero-padding

    # compute inverse transfer function: separate phase and magnitude to apply
    # regularization only to magnitude
    H_inv = (np.exp(-1j * np.angle(H))) / (np.absolute(H) + delta)
    # remove the high frequencies because they are outside the range of the microphone
    # nevertheless, we record with a high sample rate to be far away from the Nyquist frequency
    mean_12_bis_20_kHz = np.mean(H_inv[int(len(H_inv) / 8):int(len(H_inv) * (20000 / fs))])
    H_inv[int(len(H_inv) * (20000 / fs)):int(len(H_inv) * ((fs - 20000) / fs))] = np.ones(
        int(len(H_inv) * ((fs - 20000) / fs)) - int(len(H_inv) * (20000 / fs))) * mean_12_bis_20_kHz

    if not pre:
        mean_2_bis_4_kHz = np.mean(H_inv[int(len(H_inv) * (2000 / fs)):int(len(H_inv) * (4000 / fs))])
        H_inv[int(len(H_inv) * (0 / fs)):int(len(H_inv) * (2000 / fs))] = np.ones(
            int(len(H_inv) * ((2000) / fs)) - int(len(H_inv) * (0 / fs))) * mean_2_bis_4_kHz

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

    with open(os.path.join(output, "h_of_system.npy"), "wb") as file:
        np.save(file, h_hat, allow_pickle=False, fix_imports=False)

    with open(os.path.join(output, "equalizer.npy"), "wb") as file:
        np.save(file, h_inv, allow_pickle=False, fix_imports=False)


def plotResults(h_inv, h_hat, e, fs):
    # Performance measures for identification
    fig10 = plt.figure(10)
    ax = fig10.add_subplot(211)
    ax.plot(10 * np.log10(np.absolute(e) ** 2))
    plt.title('residual error signal power (logarithmic)')

    # Equalization performance
    h_eq = np.convolve(h_inv, h_hat)  # equalized impulse response

    fig1 = plt.figure(1)
    ax = fig1.add_subplot(111)
    ax.plot(h_eq)
    plt.xlabel('tap')
    plt.ylabel('amplitude')
    plt.title('equalized impulse response')
    print(" ")

    # Visualization of equalized impulse response and magnitude frequency response
    fig2 = plt.figure(2, figsize=(8, 8))
    ax = fig2.add_subplot(211)
    plt.plot(h_hat)
    plt.xlabel('tap')
    plt.ylabel('amplitude')
    plt.title('time-domain impulse response')

    ax2 = fig2.add_subplot(212)

    ax2.plot(np.linspace(0, fs / 4, num=int(len(h_hat) / 4)),
             10 * np.log10(np.absolute(np.fft.fft(h_hat)[:int(len(h_hat) / 4)])))
    plt.xlabel('frequency [hz]')
    plt.ylabel('magnitude [dB]')
    plt.title('magnitude response')
    print(" ")
