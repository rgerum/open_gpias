# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 10:03:06 2017

@author: rahlfshh
"""

import sys
import sounddevice as sd
import numpy as np
import time
from qtpy import QtCore

try:
    import PyDAQmx as daq
except NotImplementedError as err:
    print(err, file=sys.stderr)
import ctypes

from .soundSignal import Signal


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

    data = None
    protocol = None

    pause = False
    stop = False

    def __init__(self, protocol, config):
        QtCore.QObject.__init__(self)
        self.protocolWidget = protocol
        self.config = config

        self.signal = Signal(config)

    def run_thread(self):
        """  runs the thread to start the ASR-measurements """
        self.protocol = self.protocolWidget.protocol

        # all data measures for this measurement, if you want to increase the
        # measurement sample rate you might consider changing this to only
        # containing the recent measurement. Be careful to change this in
        # the hole code!
        all_data = np.zeros((len(self.protocol), 1 + int(6 * self.config.recordingrate * 16.5)))

        # extracted measured Data of the form [index of konfigarray][channel][data]
        data_extracted = np.zeros((len(self.protocol), 7, int(0.95 * self.config.recordingrate) + 2))
        self.update_timer.emit(self.protocol, 0)

        # loop over all ASR measurements
        for idxStartle in range(len(self.protocol)):
            print("startleidx: " + str(idxStartle))
            # handle pausing, stopping and resuming
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

            thisKonfig = self.protocol[idxStartle]
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

            self.update_timer.emit(self.protocol, idxStartle)

            # if the stimulation crashes or the sound card isn't active there
            # will be no trigger. This is absolutely not supposed to happen
            if not foundThreshold:
                print("there was no trigger in measurement number " + str(idxStartle))
        print('measurement completed')
        # Inform main thread and send data
        self.finished.emit(data_extracted, all_data)

    def play(self, matrixToPlay):
        sd.play(matrixToPlay)#, samplerate=SAMPLE_RATE, device='Speakers (ASUS Essence STX II Audio)')

    def play_stimulation(self, thisKonfig):
        """
        play Stimulation sound and trigger returns time the stimulation plays in ms
        careful this is the time the stimulation needs in ms, there is no buffer included
        the needed buffer may depend on the soundcard
        """
        print(thisKonfig)
        # should never occur if the konfig array is loaded from a correctly generated konfig file
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
            matrixToPlay, result = self.signal.gpiasGap(noiseFreqMin, noiseFreqMax, noiseTime, noise_type=noise, doGap=noiseGap)
        else:
            matrixToPlay, result = self.signal.asrPrepuls(preStimFreq, preStimAtten, ISI, prepulse=preStimAtten >= 0)
        self.play(matrixToPlay)
        return result

    def checkNiDAQ(self):
        try:
            analog_input = daq.Task()
        except NameError:
            return False, "niDAQmx library not found!"

        analog_input.CreateAIVoltageChan(self.config.recording_device + b'/ai0:5', b'', daq.DAQmx_Val_Cfg_Default,
                                         -10., 10., daq.DAQmx_Val_Volts, None)
        analog_input.CfgSampClkTiming(b'', self.config.recordingrate, daq.DAQmx_Val_Rising, daq.DAQmx_Val_FiniteSamps, 1000)
        return True, "niDAQmx device %s ready to record channels ai0-5 at %d Hz" % (self.config.recording_device, self.config.recordingrate)

    def perform_measurement(self, duration_ms):
        """
        performs the measurement using a NI-DAQ card
        it performs the measurement for duration_ms milliseconds
        """
        rate = self.config.recordingrate  # sampling rate of measurement
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

        analog_input.CreateAIVoltageChan(self.config.recording_device+b'/ai0:5', b'', daq.DAQmx_Val_Cfg_Default, -10., 10., daq.DAQmx_Val_Volts,
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

    def extract_data(self, data, data_extracted, idxStartle):
        """
        update matrix which holds the extracted Data
        data is all data
        data_extracted is data of prior iterations and empty rows for coming iterations
        rate: sample rate of measurement
        """
        data = data.reshape(6, len(data)//6)
        thresh = 0.2  # threshold für Trigger

        # find the first frame where the trigger is higher than the threshold
        # data[3] is the threshold channel
        try:
            i = np.where(data[3] > thresh)[0][0]
        except IndexError:
            # no trigger pulse found
            return data_extracted, False

        # trigger pulse too early
        if i < 0.5 * self.config.recordingrate:
            raise RuntimeError("There was a trigger in the first 0.5 seconds of the data, this is not supposed to happen! check konfig array and trigger channel(ai03)")

        # eliminate offset by taking the mean of the data without stimuli
        # and subtract it from all the data before plotting
        offset = data[:3, int(i - 0.8 * self.config.recordingrate):i]
        offset_mean = np.mean(offset, axis=0)

        # extract all data 800ms prior to trigger
        data = data[int(i - 0.8 * self.config.recordingrate):int(i - 0.8 * self.config.recordingrate) + data_extracted.shape[2]]
        # subtract the xyz offset
        data[:3, :] -= offset_mean
        # add the data to the extracted data array
        data_extracted[idxStartle, 0:6, :] = data

        return data_extracted, True
