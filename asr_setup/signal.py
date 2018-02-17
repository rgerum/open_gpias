# -*- coding: utf-8 -*-
"""
Created on Thu Oct 26 10:03:06 2017

@author: rahlfshh
"""

import os
import sys
import numpy as np
from scipy.signal import butter, lfilter
import math
import scipy

class Signal:
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

    def __init__(self):
        with open(os.path.join(os.path.dirname(__file__), "equalizer", "equalizer schreckstimulus.npy"), "rb") as file:
            self.h_inv_noiseburst = np.load(file, allow_pickle=False, fix_imports=False)

        with open(os.path.join(os.path.dirname(__file__), "equalizer", "equalizer praestimulus lautsprecher.npy"), "rb") as file:
            self.h_inv_prestim = np.load(file, allow_pickle=False, fix_imports=False)

        # variable that holds the noiseburst freq
        self.noiseburstArray = []

    def pureTone(self, freq, ms):
        """ generate a pure sine tone """
        a = np.arange(self.get_num_samples(ms))
        a = np.sin(a * 2 * np.pi * freq / self.SAMPLE_RATE)
        return a

    def gaussianWhiteNoise(self, ms):
        mean = 0
        std = 1
        num_samples = self.get_num_samples(ms)
        samples = np.random.normal(mean, std, size=num_samples)
        # 0.3% der werte liegen außerhalb der 3 sigma umgebung, das sollte kein all zu großes probem sein.
        # auf maxima zu normieren geht nicht, da ansonsten lange samples zu laut sind
        samples /= 3 * std
        return samples


    def checkBandpass(self, low, high, b, a):
        """ This function checks if the bandpass does its work correctly.
            Usually everything works but if high or low get to near to the nyq Frequency some error my occur
        """
        w, h = scipy.signal.freqz(b, a, worN=self.SAMPLE_RATE)
        i = int(low * self.SAMPLE_RATE) + 1
        j = int(high * self.SAMPLE_RATE) - 1
        while i <= j:
            if abs(h[i]) > math.sqrt(2) or abs(h[i]) < math.sqrt(1 / 2):
                print("bandpass didnt work propperly")
                return False
            i += 1
        return True

    def butter_bandpass(self, lowcut, highcut, order=2):
        """ returns numerator and denominator of butter band pass filter """
        nyq = 0.5 * self.SAMPLE_RATE
        low = lowcut / nyq
        high = highcut / nyq
        if low > 1 or high > 1 or low > high:
            raise ValueError("butter_bandpass got bad Values")
        b, a = butter(order, [low, high], btype='band')
        if self.checkBandpass(low, high, b, a):
            return b, a
        else:
            raise ValueError
        return b, a

    def band_filtered_gaussian_white_noise(self, cut_low, cut_high, ms):
        """ Returns a bandfiltered gausian distributed white noise """
        b, a = self.butter_bandpass(cut_low, cut_high)
        y = lfilter(b, a, self.gaussianWhiteNoise(ms))
        return y

    def notch_filtered_gaussian_white_noise(self, cut_low, cut_high, ms):
        raw_noise = self.band_filtered_gaussian_white_noise(200, 20000, ms)
        b, a = self.butter_bandpass(cut_low, cut_high)
        band_noise = lfilter(b, a, raw_noise)
        notch_noise = raw_noise - band_noise
        return notch_noise

    def noiseBurst(self):
        """ produce a 20ms Broad Band NoiseBurst 15ms rising edge 5ms """
        if self.noiseburstArray == []:
            print("generate noiseburst array")
            x = self.gaussianWhiteNoise(self.timeNoiseBurst)
            x_adjusted = self.adjust_freq_and_atten(x, self.noiseBurstAtten, prestim_signal=False)
            steigende = self.sinSquareRisingEdge(self.edgeTimeNoiseBurst)
            x_adjusted[0:len(steigende)] *= steigende
            noiseburstArray = x_adjusted
        return noiseburstArray

    def silence(self, ms):
        """ returns an array with zeros, this is silence """
        x = np.zeros(self.get_num_samples(ms))
        return x

    def get_num_samples(self, ms):
        """ returns the number of samples needed to play a tone for ms milliseconds """
        return int(ms * self.SAMPLE_RATE / 1000)

    def sinSquareRisingEdge(self, ms):
        """ returns an array with sin(x)^2 distributed Values inbetween 0 and 1
            the length is the number of samples that are needed for ms
        """
        samples = self.get_num_samples(ms)
        return np.sin(np.linspace(0, np.pi / 2, num=samples)) ** 2

    def sinSquareFallingEdge(self, ms):
        """ returns an array with sin(x)^2 distributed Values inbetween 1 and 0
            the length is the number of samples that are needed for ms
        """
        samples = self.get_num_samples(ms)
        return 1 - np.sin(np.linspace(0, np.pi / 2, num=samples)) ** 2

    def soundPressureLevel(self, signal, prestim_signal=True):
        """ retruns the actual Noise level signal will produce at the mouse
            prestim_signal defines if it is the prestim signal or the noiseburst
        """
        b, a = self.butter_bandpass(350, 20000, order=4)
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

    def adjust_factor_attenuation(self, aimed_db, signal, prestim_signal=True):
        """ calculates an adjust factor which raises the noiselevel of signal to aimed_db """
        db_now = self.soundPressureLevel(signal, prestim_signal=prestim_signal)
        ret = 10 ** ((aimed_db - db_now) / 20)
        return ret

    def flaten_the_frequency_response(self, signal, prestim_signal=True):
        """ flatens the frequency response with help of the equalizer calculated by nlms
            only returns the part of the convlution at which point the max of the h_inv enters/leaves signal
        """
        if prestim_signal:
            equalizer = self.h_inv_prestim
        else:
            equalizer = self.h_inv_noiseburst
        adjusted_signal = np.convolve(signal, equalizer)
        idx_max = np.argmax(equalizer)
        output = adjusted_signal[idx_max:len(adjusted_signal) + 1 - len(equalizer) + idx_max]
        return output

    def check_output_signal(self, signal):
        """ check whether only 0.4% of the signal are above 1
            this is supposed to prevent clipping
        """
        condition = signal > 1
        values_above_one = np.extract(condition, signal)
        if len(values_above_one) > 0.004 * len(signal):
            print("signal has too many values above 1!")
            raise ValueError(
                "The Signal that is supposed to be played has too many values above 1. this will corrupt the output!")

    def adjust_freq_and_atten(self, signal, attenuation, prestim_signal=True):
        """ adjust signal to have a flat frequency response and the right sound pressure level when played on the speaker """
        adjust_factor = self.adjust_factor_attenuation(attenuation, signal, prestim_signal=prestim_signal)
        flattened = self.flaten_the_frequency_response(signal, prestim_signal=prestim_signal)
        output = flattened * adjust_factor
        self.check_output_signal(output)
        return output

    """ protocols """

    # delay trigger because otherwise trigger is 14.8125 ms to early
    # 14.8125 is correct for sampling rates of 48000 and 96000 at the stxII
    def adjust_trigger_timing(self, preStimArray, burstArray, triggerArray, ms=14.8125):
        delayArray = self.silence(ms)
        triggerArray = np.concatenate((delayArray, triggerArray))
        burstArray = np.concatenate((burstArray, delayArray))
        preStimArray = np.concatenate((preStimArray, delayArray))
        return preStimArray, burstArray, triggerArray

    # plays a gpias Stimulation including a gap
    # noiseFreqMin => minimum of the noise band
    # noiseFreqMax => maximum of the noiseband
    # noiseTime    => time from beginning of noise to noiseburst
    def gpias_gap(self, noiseFreqMin, noiseFreqMax, noiseTime, noise_type=1, gap=True):
        if noise_type == 1:  # band noise
            preStimArray = self.band_filtered_gaussian_white_noise(noiseFreqMin, noiseFreqMax, noiseTime + self.timeNoiseBurst)
        elif noise_type == 2:  # broadband
            preStimArray = self.band_filtered_gaussian_white_noise(200, 20000, noiseTime + self.timeNoiseBurst)
        elif noise_type == 3:  # notch noise
            preStimArray = self.notch_filtered_gaussian_white_noise(noiseFreqMin, noiseFreqMax, noiseTime + self.timeNoiseBurst)
        else:
            print("wrong noise type")
            return
        preStimArray = self.adjust_freq_and_atten(preStimArray, self.noiseAtten, prestim_signal=True)
        if gap:
            falling_edge = self.sinSquareFallingEdge(self.edgeTimeNoiseGap)
            silent_time = self.silence(self.timeGap)
            rising_edge = self.sinSquareRisingEdge(self.edgeTimeNoiseGap)
            gap = np.concatenate((falling_edge, silent_time, rising_edge))
            ending = np.concatenate((gap, np.ones(self.get_num_samples(self.timeToNoiseBurst + self.timeNoiseBurst) - len(gap))))
            preStimArray[-len(ending):] *= ending
        burstArray = np.concatenate((self.silence(noiseTime), self.noiseBurst()))
        if gap:
            triggerArray = np.zeros(len(preStimArray))
            triggerArray[-len(self.noiseBurst()):] = np.ones(len(self.noiseBurst())) * 0.1
        else:
            triggerArray = np.zeros(len(burstArray))
            triggerArray[self.get_num_samples(noiseTime):] = np.ones(len(self.noiseBurst())) * 0.1

        # delay trigger because otherwise trigger is 14.8125 ms to early
        # 14.8125 is correct for samplingrates of 48000 and 96000 at the stxII
        preStimArray, burstArray, triggerArray = self.adjust_trigger_timing(preStimArray, burstArray, triggerArray,
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
        preStimArray = self.silence(ISI + self.timeNoiseBurst)
        if prepulse:
            prepuls = self.pureTone(preStimFreq, self.timePreStim + 2 * self.edgeTimePreStim)
            prepuls = self.adjust_freq_and_atten(prepuls, preStimAtten, prestim_signal=True)
            rising_edge = self.sinSquareRisingEdge(self.edgeTimePreStim)
            prepuls[:len(rising_edge)] *= rising_edge
            falling_edge = self.sinSquareFallingEdge(self.edgeTimePreStim)
            prepuls[-len(falling_edge):] *= falling_edge
            preStimArray[
            self.get_num_samples(ISI - self.timeToNoiseBurst):self.get_num_samples(ISI - self.timeToNoiseBurst) + len(prepuls)] = prepuls
        burstArray = np.concatenate((self.silence(ISI), self.noiseBurst()))
        triggerArray = np.zeros(len(burstArray))
        triggerArray[-len(self.noiseBurst()):] = np.ones(len(self.noiseBurst())) * 0.1
        # delay trigger because otherwise trigger is 14.8125 ms to early
        # 14.8125 is correct for samplingrates of 48000 and 96000 at the stxII
        preStimArray, burstArray, triggerArray = self.adjust_trigger_timing(preStimArray, burstArray, triggerArray,
                                                                            ms=14.8125)
        # zeroarray for silent channel
        zeroArray = np.zeros(len(preStimArray))
        # stack different channels
        matrixToPlay = np.dstack((triggerArray, zeroArray, preStimArray, burstArray))[0]

        return matrixToPlay, ISI + self.timeNoiseBurst
