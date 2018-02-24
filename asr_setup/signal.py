# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 10:03:06 2017

@author: rahlfshh
"""

import os
import sys
import numpy as np
import scipy.signal
import math
import scipy

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

    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), "equalizer", "equalizer schreckstimulus.npy"), "rb") as file:
            self.h_inv_noiseburst = np.load(file, allow_pickle=False, fix_imports=False)

        with open(os.path.join(os.path.dirname(__file__), "equalizer", "equalizer praestimulus lautsprecher.npy"), "rb") as file:
            self.h_inv_prestim = np.load(file, allow_pickle=False, fix_imports=False)

        # variable that holds the noiseburst freq
        self.noiseburstArray = []

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
        a = np.arange(self._get_num_samples(duration))
        a = np.sin(a * 2 * np.pi * frequency / self.SAMPLE_RATE)
        return self._smoothEdges(a, 10)

    def gaussianWhiteNoise(self, duration):
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
        num_samples = self._get_num_samples(duration)
        samples = np.random.normal(mean, std, size=num_samples)
        # 0.3% of the values are outside the 3 sigma range, but this should not cause problems.
        # it is not possible to norm by the maximum, as long samples would be too loud.
        samples /= 3 * std
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
        b, a = self._butter_bandpass(cut_low, cut_high)
        y = scipy.signal.lfilter(b, a, self.gaussianWhiteNoise(duration))
        if smooth:
            return self._smoothEdges(y, 20)
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
        b, a = self._butter_bandpass(cut_low, cut_high)
        band_noise = scipy.signal.lfilter(b, a, raw_noise)
        notch_noise = raw_noise - band_noise
        if smooth:
            return self._smoothEdges(notch_noise, 20)
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
            x_adjusted = self._adjust_freq_and_atten(x, self.burstSPL, prestim_signal=False)
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
        x = np.zeros(self._get_num_samples(duration))
        return x

    def _get_num_samples(self, duration):
        """ returns the number of samples needed to play a tone for ms milliseconds """
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
        samples = self._get_num_samples(duration)
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

    def _butter_bandpass(self, lowcut, highcut, order=2):
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
        b, a = self._butter_bandpass(350, 20000, order=4)
        filtered_signal = scipy.signal.lfilter(b, a, signal)
        if prestim_signal:  # TODO what are these values?
            v0 = 0.000019
        else:
            v0 = 0.001 / 3200
        squared = filtered_signal ** 2
        sumsquared = np.sum(squared)
        effektivwert = (sumsquared / len(filtered_signal)) ** (1 / 2)
        pegel = np.log10(effektivwert / v0) * 20
        return pegel

    def _adjust_factor_attenuation(self, aimed_db, signal, prestim_signal=True):
        """ calculates an adjust factor which raises the noiselevel of signal to aimed_db """
        db_now = self._soundPressureLevel(signal, prestim_signal=prestim_signal)
        ret = 10 ** ((aimed_db - db_now) / 20)
        return ret

    def _flatten_the_frequency_response(self, signal, prestim_signal=True):
        """ flattens the frequency response with help of the equalizer calculated by nlms
            only returns the part of the convolution at which point the max of the h_inv enters/leaves signal
        """
        if prestim_signal:
            equalizer = self.h_inv_prestim
        else:
            equalizer = self.h_inv_noiseburst
        adjusted_signal = np.convolve(signal, equalizer)
        idx_max = np.argmax(equalizer)
        output = adjusted_signal[idx_max:len(adjusted_signal) + 1 - len(equalizer) + idx_max]
        return output

    def _check_output_signal(self, signal):
        """ check whether only 0.4% of the signal are above 1
            this is supposed to prevent clipping
        """
        condition = signal > 1
        values_above_one = np.extract(condition, signal)
        if len(values_above_one) > 0.004 * len(signal):
            print("signal has too many values above 1!")
            raise ValueError(
                "The Signal that is supposed to be played has too many values above 1. this will corrupt the output!")

    def _adjust_freq_and_atten(self, signal, attenuation, prestim_signal=True):
        """ adjust signal to have a flat frequency response and the right sound pressure level when played on the speaker """
        adjust_factor = self._adjust_factor_attenuation(attenuation, signal, prestim_signal=prestim_signal)
        flattened = self._flatten_the_frequency_response(signal, prestim_signal=prestim_signal)
        output = flattened * adjust_factor
        self._check_output_signal(output)
        return output

    """ protocols """

    # delay trigger because otherwise trigger is 14.8125 ms to early
    # 14.8125 is correct for sampling rates of 48000 and 96000 at the stxII
    def _adjust_trigger_timing(self, preStimArray, burstArray, triggerArray, ms=14.8125):
        delayArray = self.silence(ms)
        triggerArray = np.concatenate((delayArray, triggerArray))
        burstArray = np.concatenate((burstArray, delayArray))
        preStimArray = np.concatenate((preStimArray, delayArray))
        return preStimArray, burstArray, triggerArray

    # plays a gpias Stimulation including a gap
    # noiseFreqMin => minimum of the noise band
    # noiseFreqMax => maximum of the noiseband
    # noiseTime    => time from beginning of noise to noiseburst
    def gpias_gap(self, noiseFreqMin, noiseFreqMax, noiseTime, noise_type=1, doGap=True):
        if noise_type == 1:  # band noise
            preStimArray = self.bandFilteredNoise(noiseTime + self.timeNoiseBurst, noiseFreqMin, noiseFreqMax)
        elif noise_type == 2:  # broadband
            preStimArray = self.bandFilteredNoise(noiseTime + self.timeNoiseBurst, 200, 20000)
        elif noise_type == 3:  # notch noise
            preStimArray = self.notchFilteredNoise(noiseTime + self.timeNoiseBurst, noiseFreqMin, noiseFreqMax)
        else:
            print("wrong noise type")
            return
        preStimArray = self._adjust_freq_and_atten(preStimArray, self.noiseSPL, prestim_signal=True)
        if doGap:
            falling_edge = self._sinSquareFallingEdge(self.edgeTimeNoiseGap)
            silent_time = self.silence(self.timeGap)
            rising_edge = self._sinSquareRisingEdge(self.edgeTimeNoiseGap)
            gap = np.concatenate((falling_edge, silent_time, rising_edge))
            ending = np.concatenate((gap, np.ones(self._get_num_samples(self.timeToNoiseBurst + self.timeNoiseBurst) - len(gap))))
            preStimArray[-len(ending):] *= ending
        burstArray = np.concatenate((self.silence(noiseTime), self.noiseBurst()))
        if doGap:
            triggerArray = np.zeros(len(preStimArray))
            triggerArray[-len(self.noiseBurst()):] = np.ones(len(self.noiseBurst())) * 0.1
        else:
            triggerArray = np.zeros(len(burstArray))
            triggerArray[self._get_num_samples(noiseTime):] = np.ones(len(self.noiseBurst())) * 0.1

        # delay trigger because otherwise trigger is 14.8125 ms to early
        # 14.8125 is correct for samplingrates of 48000 and 96000 at the stxII
        preStimArray, burstArray, triggerArray = self._adjust_trigger_timing(preStimArray, burstArray, triggerArray,
                                                                            ms=14.8125)
        # zeroarray for silent channel
        zeroArray = np.zeros(len(preStimArray))
        # stack different channels
        matrixToPlay = np.dstack((triggerArray, zeroArray, preStimArray, burstArray))[0]

        return matrixToPlay, noiseTime + self.timeNoiseBurst

    # plays a asr-stimulation including a prepuls as prestimulus
    # preStimFreq => frequency of the prestimulus
    # preStimAtten=> attenuation of the prestimulus, this is how loud the
    #                prepuls is supposed to be in dB SPL
    # ISI         => Time between this and the prior stimulus
    def asr_prepuls(self, preStimFreq, preStimAtten, ISI, prepulse=True):
        # silence
        # ISI - timeToNoiseBurst
        # rising_falling(pureTone(preStimFreq, self.timePreStim + 2 * self.edgeTimePreStim))
        # time: self.timePreStim + 2 * self.edgeTimePreStim
        # silence
        # ISI + timeNoiseBurst - (ISI - timeToNoiseBurst - prepuls)
        # timeNoiseBUrst + timeToNoiseBurst + self.timePreStim + 2 * self.edgeTimePreStim

        preStimArray = self.silence(ISI + self.timeNoiseBurst)
        if prepulse:
            prepuls = self.pureTone(self.timePreStim + 2 * self.edgeTimePreStim, preStimFreq)
            prepuls = self._adjust_freq_and_atten(prepuls, preStimAtten, prestim_signal=True)
            rising_edge = self._sinSquareRisingEdge(self.edgeTimePreStim)
            prepuls[:len(rising_edge)] *= rising_edge
            falling_edge = self._sinSquareFallingEdge(self.edgeTimePreStim)
            prepuls[-len(falling_edge):] *= falling_edge
            preStimArray[
            self._get_num_samples(ISI - self.timeToNoiseBurst):self._get_num_samples(ISI - self.timeToNoiseBurst) + len(prepuls)] = prepuls
        burstArray = np.concatenate((self.silence(ISI), self.noiseBurst()))
        triggerArray = np.zeros(len(burstArray))
        triggerArray[-len(self.noiseBurst()):] = np.ones(len(self.noiseBurst())) * 0.1
        # delay trigger because otherwise trigger is 14.8125 ms to early
        # 14.8125 is correct for samplingrates of 48000 and 96000 at the stxII
        preStimArray, burstArray, triggerArray = self._adjust_trigger_timing(preStimArray, burstArray, triggerArray,
                                                                            ms=14.8125)
        # zeroarray for silent channel
        zeroArray = np.zeros(len(preStimArray))
        # stack different channels
        matrixToPlay = np.dstack((triggerArray, zeroArray, preStimArray, burstArray))[0]

        return matrixToPlay, ISI + self.timeNoiseBurst
