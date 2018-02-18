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
import matplotlib.pyplot as plt
from PyQt5 import QtCore

try:
    import PyDAQmx as daq
except NotImplementedError as err:
    print(err, file=sys.stderr)
import ctypes

from .signal import Signal


# Indices to access the config array
# Need To match indices of BackendPlaylist
noiseIDX = 0
noiseGapIDX = 1
noiseFreqMinIDX = 2
noiseFreqMaxIDX = 3
preStimAttenIDX = 4
preStimFreqIDX = 5
ISIIDX = 6
noiseTimeIDX = 7


class Measurement(QtCore.QObject):
    finished = QtCore.Signal('PyQt_PyObject', 'PyQt_PyObject')
    backup = QtCore.Signal('PyQt_PyObject', 'PyQt_PyObject')
    plot_data = QtCore.Signal('PyQt_PyObject', 'PyQt_PyObject')
    update_timer = QtCore.Signal('PyQt_PyObject', 'PyQt_PyObject')
    stopped = QtCore.Signal()
    paused = QtCore.Signal()
    resumed = QtCore.Signal()

    # TODO fs_measurement sollte auch globale variable sein
    def __init__(self, konfigList, fs_measurement):
        QtCore.QObject.__init__(self)
        self.konfigList = konfigList
        self.fs_measurement = fs_measurement
        self.pause = False  # pause measurement at start of iteration
        self.stop = False  # stop measurement at start of iteration
        self.thisplot = None  # TODO MS
        np.random.seed(1234)

        self.signal = Signal()
        # Stimulus immergleich

    # runs the thread to start the ASR-measurements
    def run_thread(self):
        # all data measures for this measurement, if you want to increase the
        # measurement sample rate you might consider changing this to only
        # containing the recent measurement. Be careful to change this in
        # the hole code!
        all_data = np.zeros((len(self.konfigList), 1 + int(6 * self.fs_measurement * 16.5)))

        # extracted measured Data of the form [index of konfigarray][channel][data]
        data_extracted = np.zeros((len(self.konfigList), 7, int(0.95 * self.fs_measurement) + 2))
        self.update_timer.emit(self.konfigList, 0)

        # loop over all ASR measurements
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

            # save a backup in case measurement stops or program crashes
            self.backup.emit(data_extracted, all_data)

            # plot the measured data
            self.plot_data.emit(data_extracted, idxStartle)

            self.update_timer.emit(self.konfigList, idxStartle)

            # if the stimulation crashes or the sound card isn't active there
            # will be no trigger. This is absolutely not supposed to happen
            if not foundThreshold:
                print("there was no trigger in measurement number " + str(idxStartle))
        print('measurement completed')
        # Inform main thread and send data
        self.finished.emit(data_extracted, all_data)

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
            matrixToPlay, result = self.signal.gpias_gap(noiseFreqMin, noiseFreqMax, noiseTime, noise_type=noise, gap=noiseGap)
        else:
            matrixToPlay, result = self.signal.asr_prepuls(preStimFreq, preStimAtten, ISI, prepulse=preStimAtten >= 0)
        self.play(matrixToPlay)
        return result

    # performs the measurement using a NI-DAQ card
    # it performs the measurement for duration_ms milliseconds
    def perform_measurement(self, duration_ms):
        rate = self.fs_measurement  # sampling rate of measurement
        num_data_points = int(duration_ms * rate / 1000)
        self.data = np.zeros((6 * num_data_points,), dtype=np.float64)
        # try to connect to NiDAQ Card. If not return dummy measurement
        try:
            analog_input = daq.Task()
        except NameError:
            time.sleep(duration_ms / 1000)
            return self.data

        read = daq.int32()

        # channel ai0: x-Data
        # channel ai1: y-Data
        # channel ai2: z-Data
        # channel ai3: Triggerpulse
        # channel ai4: Prestim
        # channel ai5: noiseburst

        analog_input.CreateAIVoltageChan(b'Dev2/ai0:5', b'', daq.DAQmx_Val_Cfg_Default, -10., 10., daq.DAQmx_Val_Volts,
                                         None)
        analog_input.CfgSampClkTiming(b'', rate, daq.DAQmx_Val_Rising, daq.DAQmx_Val_FiniteSamps, num_data_points)

        # DAQmx Start Code
        analog_input.StartTask()

        # DAQmx Read Code
        analog_input.ReadAnalogF64(num_data_points, duration_ms / 1000, daq.DAQmx_Val_GroupByChannel, self.data,
                                   6 * num_data_points, ctypes.byref(read), None)
        # DAQmx stop the task
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
