#!/usr/bin/env python
# -*- coding: utf-8 -*-
# soundSignal.py

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

import os
import sys
import numpy as np
import scipy.signal
import math
import scipy
import sounddevice as sd
import datetime


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


class Signal:
    # maximum Sampling Rate
    SAMPLE_RATE = 96000
    # lautstärke des rauschens in dB
    # nur relevant, wenn noiseen == True
    # ist immer konstant bei 60 dB
    noiseSPL = 60

    # lautsärke des noiseburst
    burstSPL = 115

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

    h_inv_noiseburst = None
    h_inv_prestim = None

    def __init__(self, config):
        self.config = config

        # variable that holds the noiseburst freq
        self.noiseburstArray = []

        self.channels = [1, 3, 4]
        self.channel_latency = [0, 0, 14.8125, 14.8125]

        self.loadConfig()

    def loadConfig(self):
        """
        Load the config data.
        """
        self.channels = self.config.channels
        self.channel_latency = self.config.channel_latency

        if self.config.profile_loudspeaker_burst:
            with open(self.config.profile_loudspeaker_burst, "rb") as file:
                self.h_inv_noiseburst = np.load(file, allow_pickle=False, fix_imports=False)

        if self.config.profile_loudspeaker_noise:
            with open(self.config.profile_loudspeaker_noise, "rb") as file:
                self.h_inv_prestim = np.load(file, allow_pickle=False, fix_imports=False)

        self.SAMPLE_RATE = self.config.samplerate
        self.device = self.config.device

    def checkSettings(self):
        """
        Check if the soundcard supports the settings
        """
        print(self.config.device)
        print(max(self.config.channels))
        print(self.config.samplerate)

        try:
            #sd.check_output_settings(self.config.device, channels=max(self.config.channels), samplerate=self.config.samplerate)
            sd.play(np.zeros((10, max(self.config.channels))), device=self.config.device, samplerate=self.config.samplerate)
        except ValueError:
            i = -1
            for i in range(1000):
                i += 1
                if sd.query_devices(i)["name"] == self.config.device:
                    break
            try:
                sd.play(np.zeros((10, max(self.config.channels))), device=i,
                        samplerate=self.config.samplerate)
                #sd.check_output_settings(i, channels=max(self.config.channels),
                #                         samplerate=self.config.samplerate)
            except sd.PortAudioError as err:
                return False, str(err)
        except sd.PortAudioError as err:
            return False, str(err)
        return True, "Device %s ready to play %d channels at %d Hz" % (self.config.device, max(self.config.channels), self.config.samplerate)

    def pureTone(self, duration, frequency):
        """
        Generates a pure sine tone.

        Parameters
        ----------
        duration: number
            the duration of the tone in milliseconds.
        frequency : number
            the frequency of the tone in Hz.

        Returns
        -------
        tone : ndarray
            the resulting sine tone.
        """
        a = np.arange(self._getNumSamples(duration))
        a = np.sin(a * 2 * np.pi * frequency / self.SAMPLE_RATE)
        return self._smoothEdges(a, 10)

    def gaussianWhiteNoise(self, duration, smooth=0):
        """
        Generates period with gaussian white noise. The mean of the gauss is 0 and the standard deviation is 1.

        Parameters
        ----------
        duration: number
            the duration of the noise in milliseconds.

        Returns
        -------
        tone : ndarray
            the resulting noise signal.
        """
        mean = 0
        std = 1
        num_samples = self._getNumSamples(duration)
        random = np.random.RandomState()
        random.seed(1234)
        samples = random.normal(mean, std, size=num_samples)
        # 0.3% of the values are outside the 3 sigma range, but this should not cause problems.
        # it is not possible to norm by the maximum, as long samples would be too loud.
        samples /= 3 * std
        if smooth:
            return self._smoothEdges(samples, smooth)
        return samples

    def bandFilteredNoise(self, duration, cut_low, cut_high, smooth=20):
        """
        Generates period with gaussian white noise filtered by a bandpass.

        Parameters
        ----------
        duration: number
            the duration of the noise in milliseconds.
        cut_low: number
            the lower frequency of the bandpass in Hz.
        cut_high: number
            the upper frequency of the bandpass in Hz.

        Returns
        -------
        tone : ndarray
            the resulting noise signal.
        """
        b, a = self._butterBandpass(cut_low, cut_high)
        y = scipy.signal.lfilter(b, a, self.gaussianWhiteNoise(duration, smooth=0))
        if smooth:
            return self._smoothEdges(y, smooth)
        else:
            return y

    def notchFilteredNoise(self, duration, cut_low, cut_high, smooth=20):
        """
        Generates period with gaussian white noise filtered by a bandpass and a notch filter.

        Parameters
        ----------
        duration: number
            the duration of the noise in milliseconds.
        cut_low: number
            the lower frequency of the bandpass in Hz.
        cut_high: number
            the upper frequency of the bandpass in Hz.

        Returns
        -------
        tone : ndarray
            the resulting noise signal.
        """
        raw_noise = self.bandFilteredNoise(duration, 200, 20000, smooth=0)
        b, a = self._butterBandpass(cut_low, cut_high)
        band_noise = scipy.signal.lfilter(b, a, raw_noise)
        notch_noise = raw_noise - band_noise
        if smooth:
            return self._smoothEdges(notch_noise, smooth)
        else:
            return notch_noise

    def noiseBurst(self):
        """
        Generates a 20ms broadband noise burst 15ms rising edge 5ms

        Returns
        -------
        tone : ndarray
            the resulting noise signal.
        """
        if self.noiseburstArray == []:
            print("generate noiseburst array")
            x = self.gaussianWhiteNoise(self.timeNoiseBurst)
            x_adjusted = self._adjustFreqAndLevel(x, self.burstSPL, prestim_signal=False)
        return self._smoothEdges(x_adjusted, self.edgeTimeNoiseBurst)

    def silence(self, duration):
        """
        Generates a period of silence.
        
        Parameters
        ----------
        duration: number
            the duration of the silence in milliseconds.

        Returns
        -------
        tone : ndarray
            the resulting silence signal.
        """
        x = np.zeros(self._getNumSamples(duration))
        return x

    def _getNumSamples(self, duration):
        """
        Get the number of samples needed to play a tone for ms milliseconds.

        Parameters
        ----------
        duration: number
            the duration of the silence in milliseconds.

        Returns
        -------
        samples: number
            the number of samples that corresponds to the duration.
        """
        return int(duration * self.SAMPLE_RATE / 1000)

    def _sinSquareEdge(self, duration):
        """
        Returns an array with sin(x)^2 distributed values between 0 and 1
        the length is the number of samples that are needed for ms.

        Parameters
        ----------
        duration: number
            the duration of the edge in milliseconds.

        Returns
        -------
        tone : ndarray
            the smoothed edges.
        """
        samples = self._getNumSamples(duration)
        return np.sin(np.linspace(0, np.pi / 2, num=samples)) ** 2

    def _smoothEdges(self, signal, duration):
        """
        Apply a rising and a falling edge to the signal.

        Parameters
        ----------
        signal: ndarray
            the signal that should receive smooth edges.
        duration: number
            the duration of the rising and falling edge in milliseconds.

        Returns
        -------
        tone : ndarray
            the signal with smoothed edges.
        """
        # ensure that the time is smaller than half of the signal length
        duration = min((duration, len(signal) / self.SAMPLE_RATE * 1000 / 2))
        # create an array ones that has same length as the signal
        amplitude_factor = np.ones(len(signal))
        # add the rising edge
        rising_edge = self._sinSquareEdge(duration)
        amplitude_factor[:len(rising_edge)] = rising_edge
        # add the falling edge
        falling_edge = 1-self._sinSquareEdge(duration)
        amplitude_factor[-len(falling_edge):] = falling_edge
        # return the signal multiplied with the edges
        return signal*amplitude_factor

    def _checkBandpass(self, low, high, b, a):
        """
        This function checks if the bandpass does its work correctly.
        Usually everything works but if high or low get to near to the nyq Frequency some error may occur.

        Parameters
        ----------
        low: number
            the lower frequency of the filter.
        high: number
            the upper frequency of the filter.
        b:
            the b output of the scipy.signal.butter function
        a:
            the a output of the scipy.signal.butter function

        Returns
        -------
        valid: bool
            whether the filter worked properly or not.
        """
        w, h = scipy.signal.freqz(b, a, worN=self.SAMPLE_RATE)
        i = int(low * self.SAMPLE_RATE) + 1
        j = int(high * self.SAMPLE_RATE) - 1
        while i <= j:
            if abs(h[i]) > math.sqrt(2) or abs(h[i]) < math.sqrt(1 / 2):
                print("bandpass didn't work properly")
                return False
            i += 1
        return True

    def _butterBandpass(self, lowcut, highcut, order=2):
        """
        Returns numerator and denominator of butter band pass filter.

        Parameters
        ----------
        lowcut: number
            the lower frequency of the filter.
        highcut: number
            the upper frequency of the filter.
        order: number, optional
            the order of the filter.

        Returns
        -------
        valid: bool
            numerator and denominator of butter band pass filter.
        """
        nyq = 0.5 * self.SAMPLE_RATE
        low = lowcut / nyq
        high = highcut / nyq
        if low > 1 or high > 1 or low > high:
            raise ValueError("butter_bandpass got bad values")
        b, a = scipy.signal.butter(order, [low, high], btype='band')
        if self._checkBandpass(low, high, b, a):
            return b, a
        else:
            raise ValueError

    def _soundPressureLevel(self, signal, prestim_signal=True):
        """ retruns the actual Noise level signal will produce at the mouse
            prestim_signal defines if it is the prestim signal or the noiseburst
        """
        b, a = self._butterBandpass(350, 20000, order=4)
        filtered_signal = scipy.signal.lfilter(b, a, signal)
        if prestim_signal:  # TODO what are these values?
            v0 = self.config.speaker_amplification_factor[0]  # 0.000019
        else:
            v0 = self.config.speaker_amplification_factor[1]  # 0.001 / 3200
        squared = filtered_signal ** 2
        sum_squared = np.sum(squared)
        effective_value = (sum_squared / np.sum(filtered_signal != 0)) ** 0.5
        level = np.log10(effective_value / v0) * 20
        return level

    def _adjustFactorAttenuation(self, aimed_db, signal, prestim_signal=True):
        """ calculates an adjust factor which raises the noiselevel of signal to aimed_db """
        db_now = self._soundPressureLevel(signal, prestim_signal=prestim_signal)
        ret = 10 ** ((aimed_db - db_now) / 20)
        return ret

    def _flattenFrequencyResponse(self, signal, prestim_signal=True):
        """ flattens the frequency response with help of the equalizer calculated by nlms
            only returns the part of the convolution at which point the max of the h_inv enters/leaves signal
        """
        if prestim_signal:
            equalizer = self.h_inv_prestim
        else:
            equalizer = self.h_inv_noiseburst
        if equalizer is None:
            return signal
        adjusted_signal = np.convolve(signal, equalizer)
        idx_max = np.argmax(equalizer)
        output = adjusted_signal[idx_max:len(adjusted_signal) + 1 - len(equalizer) + idx_max]
        return output

    def _checkOutputSignal(self, signal):
        """ check whether only 0.4% of the signal are above 1
            this is supposed to prevent clipping
        """
        condition = signal > 1
        values_above_one = np.extract(condition, signal)
        if len(values_above_one) > 0.004 * len(signal):
            print("signal has too many values above 1!")
            raise ValueError(
                "The Signal that is supposed to be played has too many values above 1. this will corrupt the output!")

    def _adjustFreqAndLevel(self, signal, attenuation, prestim_signal=True):
        """ adjust signal to have a flat frequency response and the right sound pressure level when played on the speaker """
        adjust_factor = self._adjustFactorAttenuation(attenuation, signal, prestim_signal=prestim_signal)
        flattened = self._flattenFrequencyResponse(signal, prestim_signal=prestim_signal)
        output = flattened * adjust_factor
        self._checkOutputSignal(output)
        return output

    """ protocols """

    def _addChannelLatency(self, signal, latency, max_latency):
        """
        Shift a channel to neutralize the latency of the channel of the soundcard.

        Parameters
        ----------
        signal: ndarray
            the signals to shift.
        latency: number
            the latency in milliseconds.
        max_latency: number
            the maximum latency.

        Returns
        -------
        output: ndarray
            the joined channels.
        """
        return np.concatenate((self.silence(max_latency-latency), signal, self.silence(latency)))

    def _joinChannels(self, *signals):
        """
        Join the signals to the output with applying the latency shift of the channels.

        Parameters
        ----------
        signals: ndarray
            the signals to join.

        Returns
        -------
        output: ndarray
            the joined channels.
        """
        # check how much he channels are shifted
        max_latency = np.max(self.channel_latency)
        # check how many channel t up should have
        max_channels = np.max(self.channels)
        # iterate over the signals
        output = None
        for index in range(len(signals)):
            # get the channel
            channel = self.channels[index]-1
            # add the latency shift
            signal = self._addChannelLatency(signals[index], self.channel_latency[channel], max_latency)
            # initialize the output array if it is still None
            if output is None:
                output = np.zeros((len(signal), max_channels))
            # add the signal
            output[:, channel] = signal
        # return the joined output
        return output

    def getSignalFromProtocol(self, this_trial):
        # should never occur if the config array is loaded from a correctly generated config file
        # but is no big hold up
        if len(this_trial) != 8:
            raise RuntimeError("Config array is wrong, please generate a new one")
        noise = this_trial[noiseIDX]
        noiseGap = this_trial[noiseGapIDX]
        noiseFreqMin = this_trial[noiseFreqMinIDX]
        noiseFreqMax = this_trial[noiseFreqMaxIDX]
        preStimSPL = this_trial[preStimAttenIDX]
        preStimFreq = this_trial[preStimFreqIDX]
        ISI = this_trial[ISIIDX]
        noiseTime = this_trial[noiseTimeIDX]
        if noise:
            return self.gpiasGap(noiseFreqMin, noiseFreqMax, noiseTime, noise_type=noise, doGap=noiseGap)
        else:
            return self.asrPrepuls(preStimFreq, preStimSPL, ISI, prepulse=preStimSPL >= 0)

    def getProtocolDuration(self, protocol, idx):
        noisetimes = protocol[idx:, noiseTimeIDX]
        ISIs = protocol[idx:, ISIIDX]
        msleft = np.sum(ISIs) + np.sum(noisetimes) + 2000 * len(ISIs)
        return datetime.timedelta(seconds=msleft / 1000)


    def gpiasGap(self, noiseFreqMin, noiseFreqMax, noiseTime, noise_type=1, doGap=True):
        """
        Compose the output for the GPIAS protocol.

        Parameters
        ----------
        noiseFreqMin: number
            the minimum of the noise band.
        noiseFreqMax: number
            the maximum of the noise band.
        noiseTime: number
            the time from the beginning of the noise to the noise burst
        noise_type: int
            the type of the noise: 1 band noise, 2 broad band, 3 notch noise.
        doGap: bool
            whether to present a gap or not.

        Returns
        -------
        output: ndarray
            the joined channels.
        """

        def noise(duration):
            if noise_type == 1:  # band noise
                return self.bandFilteredNoise(duration, noiseFreqMin, noiseFreqMax)
            elif noise_type == 2:  # broadband
                return self.bandFilteredNoise(duration, 200, 20000)
            elif noise_type == 3:  # notch noise
                return self.notchFilteredNoise(duration, noiseFreqMin, noiseFreqMax)
            else:
                print("wrong noise type")
                return

        """ pre stimulus channel """

        if doGap:
            # times
            time_noise1 = noiseTime - self.timeToNoiseBurst
            time_gap = self.timeGap
            time_noise2 = self.timeToNoiseBurst - self.timeGap + self.timeNoiseBurst

            noise1 = self._adjustFreqAndLevel(noise(time_noise1), self.noiseSPL, prestim_signal=True)
            noise2 = self._adjustFreqAndLevel(noise(time_noise2), self.noiseSPL, prestim_signal=True)

            # join the signal: noise + silence + noise
            preStimArray = np.concatenate((noise1,
                                           self.silence(time_gap),
                                           noise2))

        else:
            # times
            time_noise = noiseTime + self.timeNoiseBurst

            # join the signal: noise
            preStimArray = noise(time_noise)

            # adjust the output
            preStimArray = self._adjustFreqAndLevel(preStimArray, self.noiseSPL, prestim_signal=True)

        """ startle pulse channel """
        time_noise = noiseTime
        time_burst = self.timeNoiseBurst

        # join the signal: silence + burst
        burstArray = np.concatenate((self.silence(time_noise),
                                     self.gaussianWhiteNoise(time_burst, smooth=self.edgeTimeNoiseBurst)))

        # adjust the output
        burstArray = self._adjustFreqAndLevel(burstArray, self.burstSPL, prestim_signal=False)

        """ trigger channel """
        triggerArray = np.concatenate((self.silence(time_noise),
                                      np.ones(self._getNumSamples(time_burst)) * 0.1))

        # join the channels and apply the channels' latencies
        matrixToPlay = self._joinChannels(triggerArray, preStimArray, burstArray)

        return matrixToPlay, noiseTime + self.timeNoiseBurst

    def asrPrepuls(self, preStimFreq, preStimLevel, ISI, prepulse=True):
        """
        Compose the output for the ASR protocol.

        Parameters
        ----------
        preStimFreq: number
            the frequency of the pre-stimulus.
        preStimLevel: number
            the sound pressure level of the pre-stimulus.
        ISI: number
            the time between this and the previous stimulus.
        prepulse: bool
            whether to present a pre-pulse or not.

        Returns
        -------
        output: ndarray
            the joined channels.
        """

        """ pre stimulus channel """
        if prepulse:
            # times
            time_silence1 = ISI - self.timeToNoiseBurst
            time_tone = self.timePreStim + 2 * self.edgeTimePreStim
            time_silence2 = self.timeToNoiseBurst - time_tone + self.timeNoiseBurst

            # join the signal: silence + tone + silence
            preStimArray = np.concatenate((self.silence(time_silence1),
                                           self.pureTone(time_tone, preStimFreq),
                                           self.silence(time_silence2)))

            # adjust the output
            preStimArray = self._adjustFreqAndLevel(preStimArray, preStimLevel, prestim_signal=True)

        else:
            # times
            time_total = ISI + self.timeNoiseBurst

            # join the signal: silence
            preStimArray = self.silence(time_total)


        """ startle pulse channel """
        time_silence = ISI
        time_burst = self.timeNoiseBurst

        # join the signal: silence + burst
        burstArray = np.concatenate((self.silence(time_silence),
                                     self.gaussianWhiteNoise(time_burst, smooth=self.edgeTimeNoiseBurst)))

        # adjust the output
        burstArray = self._adjustFreqAndLevel(burstArray, self.burstSPL, prestim_signal=False)

        """ trigger channel """
        triggerArray = np.concatenate((self.silence(time_silence),
                                      np.ones(self._getNumSamples(time_burst))*0.1))

        # join the channels and apply the channels' latencies
        matrixToPlay = self._joinChannels(triggerArray, preStimArray, burstArray)

        return matrixToPlay, ISI + self.timeNoiseBurst
