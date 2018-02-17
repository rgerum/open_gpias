# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 10:03:06 2017

@author: rahlfshh
"""

import os
import sys
import sounddevice as sd
import numpy as np
import time
from scipy.signal import butter, lfilter
import math
import scipy
from PyQt5 import QtCore

try:
    import PyDAQmx as daq
except NotImplementedError as err:
    print(err, file=sys.stderr)
import ctypes

import matplotlib.pyplot as plt

##############unveränderliche Größen##############
# maximum Sampling Rate
SAMPLE_RATE = 96000
# lautstärke des rauschens in dB
# nur relevant, wenn noiseen == True
# ist immer konstant bei 60 dB
noiseAtten = 60

# lautsärke des noiseburst
noiseBurstAtten = 115

# Zeitraum über den prestim, noiseBurst und noiseGap eintreten in ms
edgeTimePreStim = 10
edgeTimeNoiseGap = 20
edgeTimeNoiseBurst = 5

# Zeit, die der Prestimulus auf voller lautstärke ist
timePreStim = 10

# Zeit, die die Rauschlücke in vollkommener Stille dauert
# nur relevant, wenn NoiseGap ==True und Noise== True
timeGap = 10

# Zeit, die der Prestimulus oder die NoiseGap vor dem NoiseBurst kommen in ms
# nur relevant, wenn noise oder PreStim == True
timeToNoiseBurst = 100

# Zeit, die der NoiseBurst dauert in ms
timeNoiseBurst = 20

if 1:
    file = open(os.path.join(os.path.dirname(__file__), "equalizer", "equalizer schreckstimulus.npy"), "rb")
    global h_inv_noiseburst
    h_inv_noiseburst = np.load(file, allow_pickle=False, fix_imports=False)
    file.close()
    file = open(os.path.join(os.path.dirname(__file__), "equalizer", "equalizer praestimulus lautsprecher.npy"), "rb")
    global h_inv_prestim
    h_inv_prestim = np.load(file, allow_pickle=False, fix_imports=False)
    file.close()

# variable that holds the noiseburst freq
noiseburstArray = []


def pureTone(freq, ms):
    a = np.arange(get_num_samples(ms))
    a = np.sin(a * 2 * np.pi * freq / SAMPLE_RATE)
    return (a)


def gaussianWhiteNoise(ms):
    mean = 0
    std = 1
    num_samples = get_num_samples(ms)
    samples = np.random.normal(mean, std, size=num_samples)
    # 0.3% der werte liegen außerhalb der 3 sigma umgebung, das sollte kein all zu großes probem sein.
    # auf maxima zu normieren geht nicht, da ansonsten lange samples zu laut sind
    samples /= 3 * std
    return samples


# This function checks if the bandpass does its work correctly.
# Usualy everythink works
# but if high or low get to near to the nyq Frequency some eroor my occure
def checkBandpass(low, high, b, a):
    w, h = scipy.signal.freqz(b, a, worN=SAMPLE_RATE)
    i = int(low * SAMPLE_RATE) + 1
    j = int(high * SAMPLE_RATE) - 1
    while i <= j:
        if (abs(h[i]) > math.sqrt(2) or abs(h[i]) < math.sqrt(1 / 2)):
            print("bandpass didnt work propperly")
            return False
        i += 1
    return True


# returns numerator and denominator of butter band pass filter
def butter_bandpass(lowcut, highcut, order=2):
    nyq = 0.5 * SAMPLE_RATE
    low = lowcut / nyq
    high = highcut / nyq
    if low > 1 or high > 1 or low > high:
        raise ValueError("butter_bandpass got bad Values")
    b, a = butter(order, [low, high], btype='band')
    if checkBandpass(low, high, b, a):
        return b, a
    else:
        raise ValueError
    return b, a


# Returns a bandfiltered gausian distributed white noise
def band_filtered_gaussian_white_noise(cut_low, cut_high, ms):
    b, a = butter_bandpass(cut_low, cut_high)
    y = lfilter(b, a, gaussianWhiteNoise(ms))
    return y


def notch_filtered_gaussian_white_noise(cut_low, cut_high, ms):
    raw_noise = band_filtered_gaussian_white_noise(200, 20000, ms)
    b, a = butter_bandpass(cut_low, cut_high)
    band_noise = lfilter(b, a, raw_noise)
    notch_noise = raw_noise - band_noise
    return notch_noise


# produce a 20ms Broad Band NoiseBurst 15ms rising edge 5ms
def noiseBurst():
    global noiseburstArray
    if (noiseburstArray == []):
        print("generate noiseburst array")
        x = gaussianWhiteNoise(timeNoiseBurst)
        x_adjusted = adjust_freq_and_atten(x, noiseBurstAtten, prestim_signal=False)
        steigende = sinSquareRisingEdge(edgeTimeNoiseBurst)
        x_adjusted[0:len(steigende)] *= steigende
        noiseburstArray = x_adjusted
    return noiseburstArray


# returns an array with zeros, this is silence
def silence(ms):
    x = np.zeros(get_num_samples(ms))
    return x


# returns the number of samples needed to play a tone for ms milliseconds
def get_num_samples(ms):
    return int(ms * SAMPLE_RATE / 1000)


# returns an array with sin(x)^2 distributed Values inbetween 0 and 1
# the length is the number of samples that are needed for ms
def sinSquareRisingEdge(ms):
    samples = get_num_samples(ms)
    return np.sin(np.linspace(0, np.pi / 2, num=samples)) ** 2


# returns an array with sin(x)^2 distributed Values inbetween 1 and 0
# the length is the number of samples that are needed for ms
def sinSquareFallingEdge(ms):
    samples = get_num_samples(ms)
    return 1 - np.sin(np.linspace(0, np.pi / 2, num=samples)) ** 2


# retruns the actual Noise level signal will produce at the mouse
# prestim_signal defines if it is the prestim signal or the noiseburst
def soundPressureLevel(signal, prestim_signal=True):
    b, a = butter_bandpass(350, 20000, order=4)
    filtered_signal = lfilter(b, a, signal)
    if prestim_signal:
        v0 = 0.000019
    else:
        v0 = 0.001 / 3200
    squared = filtered_signal ** 2
    sumsquared = np.sum(squared)
    effektivwert = (sumsquared / len(filtered_signal)) ** (1 / 2)
    pegel = np.log10(effektivwert / v0) * 20
    return pegel


# calculates an adjust factor which raises the noiselevel of signal
# to aimed_db
def adjust_factor_attenuation(aimed_db, signal, prestim_signal=True):
    db_now = soundPressureLevel(signal, prestim_signal=prestim_signal)
    ret = 10 ** ((aimed_db - db_now) / 20)
    return ret


# flatens the frequency response with help of the equalizer calculated by nlms
# only returns the part of the convlution at which point the max of the h_inv enters/leaves signal
def flaten_the_frequency_response(signal, prestim_signal=True):
    if prestim_signal:
        global h_inv_prestim
        equalizer = h_inv_prestim
    else:
        global h_inv_noiseburst
        equalizer = h_inv_noiseburst
    adjusted_signal = np.convolve(signal, equalizer)
    idx_max = np.argmax(equalizer)
    output = adjusted_signal[idx_max:len(adjusted_signal) + 1 - len(equalizer) + idx_max]
    return output


# check wether only 0.4% of the signal are above 1
# this is supposed to prevent clipping
def check_output_signal(signal):
    condition = signal > 1
    values_above_one = np.extract(condition, signal)
    if len(values_above_one) > 0.004 * len(signal):
        print("signal has too many values above 1!")
        raise ValueError(
            "The Signal that is supposed to be played has too many values above 1. this will corrupt the output!")


# adjust signal to have a flat frequency response and the right sound pressure level when played on the speaker
def adjust_freq_and_atten(signal, attenuation, prestim_signal=True):
    adjust_factor = adjust_factor_attenuation(attenuation, signal, prestim_signal=prestim_signal)
    flattened = flaten_the_frequency_response(signal, prestim_signal=prestim_signal)
    output = flattened * adjust_factor
    check_output_signal(output)
    return output


# Indices to acces the konfig array
# Need To match indices of BackendPlaylist
noiseIDX = 0
noiseGapIDX = 1
noiseFreqMinIDX = 2
noiseFreqMaxIDX = 3
preStimAttenIDX = 4
preStimFreqIDX = 5
ISIIDX = 6
noiseTimeIDX = 7


#########This code is adapted from BERA-Messung.py by abrsetup
class Measurement(QtCore.QObject):
    finished = QtCore.pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')
    backup = QtCore.pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')
    plot_data = QtCore.pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')
    update_timer = QtCore.pyqtSignal('PyQt_PyObject', 'PyQt_PyObject')
    stopped = QtCore.pyqtSignal()
    paused = QtCore.pyqtSignal()
    resumed = QtCore.pyqtSignal()

    # TODO fs_measurement sollte auch globale variable sein
    def __init__(self, konfigList, fs_measurement):
        QtCore.QObject.__init__(self)
        self.konfigList = konfigList
        self.fs_measurement = fs_measurement
        self.pause = False  # pause measurement at start of iteration
        self.stop = False  # stop measurement at start of iteration
        self.thisplot = None  # TODO MS
        np.random.seed(1234)
        # Stimulus immergleich

    # runs the thread to start the ASR-measurements
    def run_thread(self):
        # all data measures for this measurement, if you want to increase the
        # measurement sample rate you might consider changing this to only
        # containing the recent measurement. Be carefull to change this in
        # the hole code!
        all_data = np.zeros((len(self.konfigList), 1 + int(6 * self.fs_measurement * 16.5)))

        # extracted measured Data of the form [index of konfigarray][channel][data]
        data_extracted = np.zeros((len(self.konfigList), 7, int(0.95 * self.fs_measurement) + 2))
        self.update_timer.emit(self.konfigList, 0)

        # loo over al ASR measurements
        for idxStartle in range(len(self.konfigList)):
            print("startleidx: " + str(idxStartle))
            # handle pausing,stopping and resuming
            if self.pause:
                self.paused.emit()  # notify main thread

                while self.pause:
                    if self.stop:
                        self.stop = False
                        self.stopped.emit()
                        return
                    time.sleep(0.1)
                self.resumed.emit()

            if self.stop:
                self.stopped.emit()
                return

            thisKonfig = self.konfigList[idxStartle]
            stimulation_duration = self.play_stimulation(thisKonfig) + 1000

            # perform the measurement of the Data
            # 1000 ms is the buffer that is needed usually because sd.play doesn't start the sound immediately
            # the buffer that is needed may depend on the soundcard you use
            data = self.perform_measurement(stimulation_duration + 1000)
            all_data[idxStartle][0] = len(data)
            all_data[idxStartle][1:len(data) + 1] = data
            data_extracted, foundThreshold = self.extract_data(data, data_extracted, self.fs_measurement, idxStartle)
            # save which measurement was performed
            data_extracted[idxStartle][6][1:9] = thisKonfig

            # save a backup in case measurement stops or programm crashes
            self.backup.emit(data_extracted, all_data)

            # plot the measured Data
            self.plot_data.emit(data_extracted, idxStartle)

            self.update_timer.emit(self.konfigList, idxStartle)

            # if the stimulation crashes or the sound card isn't active there
            # will be no trigger. This is absolutely not supposed to happen
            if not foundThreshold:
                print("there was no trigger in measurement number " + str(idxStartle))
        print('measurement completed')
        # Inform main thread and send data
        self.finished.emit(data_extracted, all_data)

    # delay trigger because otherwise trigger is 14.8125 ms to early
    # 14.8125 is correct for samplingrates of 48000 and 96000 at the stxII
    def adjust_trigger_timing(self, preStimArray, burstArray, triggerArray, ms=14.8125):
        delayArray = np.zeros(int(SAMPLE_RATE * ms / 1000))
        triggerArray = np.concatenate((delayArray, triggerArray))
        burstArray = np.concatenate((burstArray, delayArray))
        preStimArray = np.concatenate((preStimArray, delayArray))
        return (preStimArray, burstArray, triggerArray)

    # plays a gpias Stimulation including a gap
    # noiseFreqMin => minimum of the noise band
    # noiseFreqMax => maximum of the noiseband
    # noiseTime    => time from beginning of noise to noiseburst
    def play_gpias_gap(self, noiseFreqMin, noiseFreqMax, noiseTime, noise_type=1):
        if noise_type == 1:  # band noise
            preStimArray = band_filtered_gaussian_white_noise(noiseFreqMin, noiseFreqMax, noiseTime + timeNoiseBurst)
        elif noise_type == 2:  # broadband
            preStimArray = band_filtered_gaussian_white_noise(200, 20000, noiseTime + timeNoiseBurst)
        elif noise_type == 3:  # notch noise
            preStimArray = notch_filtered_gaussian_white_noise(noiseFreqMin, noiseFreqMax, noiseTime + timeNoiseBurst)
        else:
            print("wrong noise type")
            return
        preStimArray = adjust_freq_and_atten(preStimArray, noiseAtten, prestim_signal=True)
        falling_edge = sinSquareFallingEdge(edgeTimeNoiseGap)
        silent_time = silence(timeGap)
        rising_edge = sinSquareRisingEdge(edgeTimeNoiseGap)
        gap = np.concatenate((falling_edge, silent_time, rising_edge))
        ending = np.concatenate((gap, np.ones(get_num_samples(timeToNoiseBurst + timeNoiseBurst) - len(gap))))
        preStimArray[-len(ending):] *= ending
        burstArray = np.concatenate((silence(noiseTime), noiseBurst()))
        triggerArray = np.zeros(len(preStimArray))
        print(get_num_samples(timeNoiseBurst) == len(noiseBurst()))
        triggerArray[-len(noiseBurst()):] = np.ones(len(noiseBurst())) * 0.1
        # delay trigger because otherwise trigger is 14.8125 ms to early
        # 14.8125 is correct for samplingrates of 48000 and 96000 at the stxII
        preStimArray, burstArray, triggerArray = self.adjust_trigger_timing(preStimArray, burstArray, triggerArray,
                                                                            ms=14.8125)
        plt.plot(triggerArray)
        # zeroarray for silent channel
        zeroArray = np.zeros(len(preStimArray))
        # stack different channels
        matrixToPlay = np.dstack((triggerArray, zeroArray, preStimArray, burstArray))[0]
        self.play(matrixToPlay)

        return noiseTime + timeNoiseBurst

    # plays a gpias Stimulation without a gap
    # noiseFreqMin => minimum of the noise band
    # noiseFreqMax => maximum of the noiseband
    # noiseTime    => time from beginning of noise to noiseburst
    def play_gpias_no_gap(self, noiseFreqMin, noiseFreqMax, noiseTime, noise_type=1):
        if noise_type == 1:
            preStimArray = band_filtered_gaussian_white_noise(noiseFreqMin, noiseFreqMax, noiseTime + timeNoiseBurst)
        elif noise_type == 2:
            preStimArray = band_filtered_gaussian_white_noise(200, 20000, noiseTime + timeNoiseBurst)
        elif noise_type == 3:
            preStimArray = notch_filtered_gaussian_white_noise(noiseFreqMin, noiseFreqMax, noiseTime + timeNoiseBurst)
        else:
            print("wrong noise type")
            return
        preStimArray = adjust_freq_and_atten(preStimArray, noiseAtten, prestim_signal=True)
        burstArray = np.concatenate((silence(noiseTime), noiseBurst()))
        triggerArray = np.zeros(len(burstArray))
        triggerArray[get_num_samples(noiseTime):] = np.ones(len(noiseBurst())) * 0.1

        # delay trigger because otherwise trigger is 14.8125 ms to early
        # 14.8125 is correct for samplingrates of 48000 and 96000 at the stxII
        preStimArray, burstArray, triggerArray = self.adjust_trigger_timing(preStimArray, burstArray, triggerArray,
                                                                            ms=14.8125)
        # zeroarray for silent channel
        zeroArray = np.zeros(len(preStimArray))
        # stack different channels
        matrixToPlay = np.dstack((triggerArray, zeroArray, preStimArray, burstArray))[0]
        # matrixToPlay=np.dstack((preStimArray,burstArray))[0]
        self.play(matrixToPlay)
        return noiseTime + timeNoiseBurst

    # plays a asr-stimulation including a prepuls as prestimulus
    # preStimFreq => frequency of the prestimulus
    # preStimAtten=> attenuation of the prestimulus, this is how loud the 
    #                prepuls is supposed to be in dB SPL
    # ISI         => Time between this and the prior stimulus
    def play_asr_prepuls(self, preStimFreq, preStimAtten, ISI):
        preStimArray = silence(ISI + timeNoiseBurst)
        prepuls = pureTone(preStimFreq, timePreStim + 2 * edgeTimePreStim)
        prepuls = adjust_freq_and_atten(prepuls, preStimAtten, prestim_signal=True)
        rising_edge = sinSquareRisingEdge(edgeTimePreStim)
        prepuls[:len(rising_edge)] *= rising_edge
        falling_edge = sinSquareFallingEdge(edgeTimePreStim)
        prepuls[-len(falling_edge):] *= falling_edge
        preStimArray[
        get_num_samples(ISI - timeToNoiseBurst):get_num_samples(ISI - timeToNoiseBurst) + len(prepuls)] = prepuls
        burstArray = np.concatenate((silence(ISI), noiseBurst()))
        triggerArray = np.zeros(len(burstArray))
        triggerArray[-len(noiseBurst()):] = np.ones(len(noiseBurst())) * 0.1
        # delay trigger because otherwise trigger is 14.8125 ms to early
        # 14.8125 is correct for samplingrates of 48000 and 96000 at the stxII
        preStimArray, burstArray, triggerArray = self.adjust_trigger_timing(preStimArray, burstArray, triggerArray,
                                                                            ms=14.8125)
        # zeroarray for silent channel
        zeroArray = np.zeros(len(preStimArray))
        # stack different channels
        matrixToPlay = np.dstack((triggerArray, zeroArray, preStimArray, burstArray))[0]
        self.play(matrixToPlay)
        return ISI + timeNoiseBurst

    # plays a asr-stimulation without the prepuls
    # ISI         => Time between this and the prior stimulus
    def play_asr_no_prepuls(self, ISI):
        preStimArray = silence(ISI + timeNoiseBurst)
        burstArray = np.concatenate((silence(ISI), noiseBurst()))
        triggerArray = np.zeros(len(burstArray))
        triggerArray[-len(noiseBurst()):] = np.ones(len(noiseBurst())) * 0.1
        # delay trigger because otherwise trigger is 14.8125 ms to early
        # 14.8125 is correct for samplingrates of 48000 and 96000 at the stxII
        preStimArray, burstArray, triggerArray = self.adjust_trigger_timing(preStimArray, burstArray, triggerArray,
                                                                            ms=14.8125)
        # zeroarray for silent channel
        zeroArray = np.zeros(len(preStimArray))
        # stack different channels
        matrixToPlay = np.dstack((triggerArray, zeroArray, preStimArray, burstArray))[0]

        self.play(matrixToPlay)
        return ISI + timeNoiseBurst

    def play(self, matrixToPlay):
        sd.play(matrixToPlay)#, samplerate=SAMPLE_RATE, device='Speakers (ASUS Essence STX II Audio)')

    # play Stimulation sound and trigger returns time the stimulation plays in ms
    # carefull this is the time the stimulation needs in ms, there is no buffer included
    # the needed buffer may depend on the soundcard
    def play_stimulation(self, thisKonfig):
        print(thisKonfig)
        # should never occure if the konfig array is loaded from a correctly generated konfig file
        # but is no big hold up
        if len(thisKonfig) != 8:
            raise RuntimeError("Konfig array is wrong, please generate a new one")
        noise = thisKonfig[noiseIDX]
        noiseGap = thisKonfig[noiseGapIDX]
        noiseFreqMin = thisKonfig[noiseFreqMinIDX]
        noiseFreqMax = thisKonfig[noiseFreqMaxIDX]
        preStimAtten = thisKonfig[preStimAttenIDX]
        preStimFreq = thisKonfig[preStimFreqIDX]
        ISI = thisKonfig[ISIIDX]
        noiseTime = thisKonfig[noiseTimeIDX]
        if noise:
            if noiseGap:
                return self.play_gpias_gap(noiseFreqMin, noiseFreqMax, noiseTime, noise_type=noise)
            else:
                return self.play_gpias_no_gap(noiseFreqMin, noiseFreqMax, noiseTime, noise_type=noise)
        else:
            if preStimAtten >= 0:
                return self.play_asr_prepuls(preStimFreq, preStimAtten, ISI)
            else:
                return self.play_asr_no_prepuls(ISI)

    # performs the measurement using a NI-DAQ card
    # it performs the measurement for durarion_ms milöliseconds
    def perform_measurement(self, duration_ms):
        rate = self.fs_measurement  # samplingrate of measurement
        num_data_points = int(duration_ms * rate / 1000)
        self.data = np.zeros((6 * num_data_points,), dtype=np.float64)
        # try to connect to NiDAQ Card. If not return dummy measurement
        try:
            analog_input = daq.Task()
        except NameError:
            time.sleep(duration_ms / 1000)
            return self.data

        read = daq.int32()

        ###channel ai0: x-Data
        ###channel ai1: y-Data
        ###channel ai2: z-Data
        ###channel ai3: Triggerpulse
        ###channel ai4: Prestim
        ###channel ai5: noiseburst

        analog_input.CreateAIVoltageChan(b'Dev2/ai0:5', b'', daq.DAQmx_Val_Cfg_Default, -10., 10., daq.DAQmx_Val_Volts,
                                         None)
        analog_input.CfgSampClkTiming(b'', rate, daq.DAQmx_Val_Rising, daq.DAQmx_Val_FiniteSamps, num_data_points)
        #
        #        # DAQmx Start Code
        analog_input.StartTask()
        #
        #        # DAQmx Read Code
        analog_input.ReadAnalogF64(num_data_points, duration_ms / 1000, daq.DAQmx_Val_GroupByChannel, self.data,
                                   6 * num_data_points, ctypes.byref(read), None)
        #
        analog_input.StopTask()
        return self.data

    # update matrix which holds the extracted Data
    # data is all data
    # data_extracted is data of prior iterations and empty rows for comming iteratons
    # rate: samplerate of measurement
    def extract_data(self, data, data_extracted, rate, idxStartle):
        thresh = 0.2  # threshold für Trigger
        data_x = np.zeros(int(len(data) / 6))  # x-channel of sensor
        data_y = np.zeros(int(len(data) / 6))  # y-channel of sensor
        data_z = np.zeros(int(len(data) / 6))  # z-channel of sensor
        data_trigger = np.zeros(int(len(data) / 6))  # trigger-channel of audio cardr
        data_prestim_audio = np.zeros(int(len(data) / 6))  # prestim-channel of audio card
        data_burst_audio = np.zeros(int(len(data) / 6))  # noise burst-channel of audio card
        data_x[:] = data[0:int(len(data) / 6)]
        data_y[:] = data[int(len(data) / 6):int(len(data) / 3)]
        data_z[:] = data[int(len(data) / 3):int(len(data) / 2)]
        data_trigger[:] = data[int(len(data) / 2):int(2 * len(data) / 3)]
        data_prestim_audio[:] = data[int(2 * len(data) / 3):int(5 * len(data) / 6)]
        data_burst_audio[:] = data[int(5 * len(data) / 6):]

        i = 0
        for trigger in data_trigger:
            # print(trigger)
            if trigger > thresh:  # here is the trigger and the sound begins
                if i < 0.5 * rate:
                    raise RuntimeError(
                        "There was a trigger in the first 0.5 seconds of the data, this is not supposed to happen! check konfig array and trigger channel(ai03)")

                # eliminate offset by taking the mean of the data without stimuli
                # and substract it from all the data before plotting
                offset_x = data_x[int(i - 0.8 * rate):i]
                offset_y = data_y[int(i - 0.8 * rate):i]
                offset_z = data_z[int(i - 0.8 * rate):i]

                offset_x_mean = np.mean(offset_x, axis=0)
                offset_y_mean = np.mean(offset_y, axis=0)
                offset_z_mean = np.mean(offset_z, axis=0)

                # extract all data 800ms trior to trigger
                data_extracted[idxStartle][0] = data_x[int(i - 0.8 * rate):int(i - 0.8 * rate) + len(
                    data_extracted[idxStartle][0])] - offset_x_mean
                data_extracted[idxStartle][1] = data_y[int(i - 0.8 * rate):int(i - 0.8 * rate) + len(
                    data_extracted[idxStartle][1])] - offset_y_mean
                data_extracted[idxStartle][2] = data_z[int(i - 0.8 * rate):int(i - 0.8 * rate) + len(
                    data_extracted[idxStartle][2])] - offset_z_mean

                data_extracted[idxStartle][3] = data_trigger[int(i - 0.8 * rate):int(i - 0.8 * rate) + len(
                    data_extracted[idxStartle][3])]
                data_extracted[idxStartle][4] = data_prestim_audio[int(i - 0.8 * rate):int(i - 0.8 * rate) + len(
                    data_extracted[idxStartle][4])]
                data_extracted[idxStartle][5] = data_burst_audio[int(i - 0.8 * rate):int(i - 0.8 * rate) + len(
                    data_extracted[idxStartle][5])]

                return data_extracted, True
            i += 1
        return data_extracted, False
##    
# meiner = Measurement([],10000)
# meiner.play_asr_no_prepuls(10000)
# meiner.play_asr_prepuls(3000,60,10000)
# meiner.play_gpias_gap(2000,4000,10000)
# meiner.play_gpias_no_gap(2000,4000,10000)
# eine_var = sinSquareRisingEdge(20)
