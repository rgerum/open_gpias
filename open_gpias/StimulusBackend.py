#!/usr/bin/env python
# -*- coding: utf-8 -*-
# StimulusBackend.py

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


def findPlateauRegion(data, thresh, min_width):
    high_indices = np.where(data > thresh)[0]
    count = 0
    start = None
    for v, index in zip(np.diff(high_indices), high_indices):
        if v != 1:
            count = 0
            start = None
        else:
            if start is None:
                start = index
            count += 1
            if count == min_width:
                return start


class Measurement(QtCore.QObject):
    trial_finished = QtCore.Signal('PyQt_PyObject', 'PyQt_PyObject', 'PyQt_PyObject')
    measurement_finished = QtCore.Signal('PyQt_PyObject', 'PyQt_PyObject')
    error = QtCore.Signal(str)

    stopped = QtCore.Signal()
    paused = QtCore.Signal()
    resumed = QtCore.Signal()

    data = None
    protocol = None

    pause = False
    stop = False

    def __init__(self, protocol, config, signal=None):
        QtCore.QObject.__init__(self)
        self.protocolWidget = protocol
        self.config = config

        if signal is not None:
            self.signal = signal
        else:
            self.signal = Signal(config)

    def run_thread(self):
        """  runs the thread to start the ASR-measurements """
        self.protocol = self.protocolWidget.protocol

        # extracted measured data of the form [trial number][channel][data]
        data_extracted = np.zeros((len(self.protocol), 7, int(0.95 * self.config.recordingrate) + 2))

        # notify main thread, that the measurement will be started
        self.trial_finished.emit(data_extracted, -1, self.protocol)

        # loop over all ASR measurements
        for idxStartle in range(len(self.protocol)):
            print("startle idx: " + str(idxStartle))

            # check if the main thread has scheduled the measurement to stop
            if self.check_stop():
                return

            # get the current trial
            this_trial = self.protocol[idxStartle]

            # play the trial
            stimulation_duration = self.play_stimulation(this_trial)

            # record the sound and acceleration
            data = self.perform_nidaq_recording(stimulation_duration).copy()

            # post-process the recorded data
            data_extracted, found_threshold = self.extract_data(data, data_extracted, idxStartle, this_trial)

            # notify the main thread that the trial is finished
            self.trial_finished.emit(data_extracted, idxStartle, self.protocol)

        print('measurement completed')
        # notify the main thread that the measurement is finished
        self.measurement_finished.emit(data_extracted, None)

    def check_stop(self):
        # handle pausing, stopping and resuming
        if self.pause:
            self.paused.emit()  # notify main thread

            while self.pause:
                if self.stop:
                    self.stop = False
                    self.stopped.emit()
                    return True
                time.sleep(0.1)
            self.resumed.emit()

        if self.stop:
            self.stopped.emit()
            return True

        return False

    def play(self, matrix_to_play):

        try:
            sd.play(matrix_to_play, samplerate=self.config.samplerate, device=self.config.device)
        except ValueError:
            i = -1
            for i in range(1000):
                i += 1
                if sd.query_devices(i)["name"] == self.config.device:
                    break
            try:
                sd.play(matrix_to_play, samplerate=self.config.samplerate, device=i)
            except sd.PortAudioError as err:
                self.error.emit(str(err))
        except sd.PortAudioError as err:
            self.error.emit(str(err))

    def play_stimulation(self, this_trial):
        """
        play Stimulation sound and trigger returns time the stimulation plays in ms
        careful this is the time the stimulation needs in ms, there is no buffer included
        the needed buffer may depend on the soundcard
        """
        matrix_to_play, duration = self.signal.getSignalFromProtocol(this_trial)
        self.play(matrix_to_play)
        # perform the measurement of the data
        # 1000 ms is the buffer that is needed usually because sd.play doesn't start the sound immediately
        # the buffer that is needed may depend on the soundcard you use
        return duration + 1000

    def checkNiDAQ(self):
        # check if a task can be created
        try:
            analog_input = daq.Task()
        except NameError:
            return False, "niDAQmx library not found!"

        # check if a channel can be set
        name = bytes(self.config.recording_device, 'utf-8') + b'/ai0:5'
        analog_input.CreateAIVoltageChan(name, b'', daq.DAQmx_Val_Cfg_Default,
                                         -10., 10., daq.DAQmx_Val_Volts, None)
        analog_input.CfgSampClkTiming(b'', self.config.recordingrate, daq.DAQmx_Val_Rising, daq.DAQmx_Val_FiniteSamps, 1000)
        # return the status
        return True, "niDAQmx device %s ready to record channels ai0-5 at %d Hz" % (self.config.recording_device, self.config.recordingrate)

    def perform_nidaq_recording(self, duration_ms):
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
        # channel ai3: trigger pulse
        # channel ai4: pre-stimulus
        # channel ai5: startle-stimulus

        name = bytes(self.config.recording_device, 'utf-8') + b'/ai0:5'
        analog_input.CreateAIVoltageChan(name, b'', daq.DAQmx_Val_Cfg_Default, -10., 10., daq.DAQmx_Val_Volts,
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

    def extract_data(self, data, data_extracted, idxStartle, this_trial):
        """
        update matrix which holds the extracted Data
        data is all data
        data_extracted is data of prior iterations and empty rows for coming iterations
        rate: sample rate of measurement
        """
        data = data.reshape(6, len(data)//6)
        thresh = 0.2  # threshold für Trigger

        # save which measurement was performed
        data_extracted[idxStartle][6][1:9] = this_trial

        # normalize the acceleration sensor results
        data[:3] /= np.array(self.config.acceleration_sensor_factors)[:, None]

        # find the first frame where the trigger is higher than the threshold
        # data[3] is the threshold channel
        try:
            i = findPlateauRegion(data[3], thresh, 10)
        except IndexError:
            self.error.emit("No trigger in measurement.")
            # no trigger pulse found
            return data_extracted, False

        # trigger pulse too early
        if i < 0.5 * self.config.recordingrate:
            self.error.emit("Trigger too early measurement.")
            raise RuntimeError("There was a trigger in the first 0.5 seconds of the data, this is not supposed to "
                               "happen! Check config array and trigger channel (ai03).")

        # eliminate offset by taking the mean of the data without stimuli
        # and subtract it from all the data before plotting
        offset = data[:3, int(i - 0.8 * self.config.recordingrate):i]
        offset_mean = np.mean(offset, axis=1)

        # extract all data 800ms prior to trigger
        data = data[:, int(i - 0.8 * self.config.recordingrate):int(i - 0.8 * self.config.recordingrate) + data_extracted.shape[2]]
        # subtract the xyz offset
        data[:3, :] -= offset_mean[:, None]
        # add the data to the extracted data array
        data_extracted[idxStartle, 0:6, :] = data

        return data_extracted, True
