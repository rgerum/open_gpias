Calibration
===========

Frequency correction
--------------------
The transfer function of a loudspeaker defines how the input frequencies are reproduced by the loudspeaker. As every
loudspeaker is different and details depend on the measurement setup, it has to be calibrated for the use of Open GPIAS.

We therefore provide a calibration routine.

.. warning::
    Read this first before you use them! If you do not take care of these instructions, you may destroy your speaker!

The problem is that if you use a different speaker, amplifier, or soundcard the audiosignal may be too strong for your
speaker and destroys it. That's why we limited the maximum Value using the variable noisefactor_max and adjusted it to
our setup. If you are not sure what value to take, start with a very small one. Very small means a Value which is 1000
or 10000 times smaller than the value you would expect. Than follow the instructions below and if the speakers aren't
loud enough(<60dB) increase the Value for noisefactor_max by a factor of 10 and repeat until it works.

Preparation for frequency correction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. as a lot of soundcards are not able to play 7.1 sound and record simultaneously we us audio outputs 1 and 2. But in
   the final setup the speakers are plugged into channels 3 and 4. That's why you need to take the bnc-cable of the
   prestimulus(channel3) and plug it into chanel 1. And take the bnc-cable of the startle stimulus(channel4) and plug it
   into channel 2.
2. connect the microphone with the dB-measurement device
3. connect the output of the dB-measurement device with the line-in of your soundcard
4. turn on dB-Measurement device
5. adjust the input and output gain so that you can measure 60 dB SPL
6. place the microphone together with some rubber foam or fabric in the tube. The foam/fabric is supposed to "behave"
   like the animal and the microphone are the ears of the animal. So try to place them accordingly.
7. place the tube on the sensor platform
8. turn on the amplifiers

Measure impulse response and calculate equalizer
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
- execute "equalizer_prestimulus.py"
- if error "didn't find an appropriate noise factor, is the microphone plugged in, the dezibelmeter at the right attenuation and the amplifier turned on?" occurs:

    - did you do all of the questioned? 
    - if not do it and try again
    - if yes try again and see if you hear a sound and if your dB device shows something, if not increase the Variable noisefactor_max and try again

- if no error:

    - does the graph "residual error signal power (logarithmic)" look correct? if yes follow the steps below. If not try again after you checked if all the parameters are correct and everything is plugged in correct.

- copy "equalizer praestimulus lautsprecher.npy" into the folder "as_setup/Stimulation gui"
- execute "equalizer_startlestimulus.py.py"
- if error "didn't find an appropriate noisefactor, is the microphone plugged in, the dezibelmeter at the right attenuation and the amplifier turned on?" occurs:

    - did you do all of the questioned? 
    - if not do it and try again
    - if yes try again and see if you hear a sound and if your dB device shows something, if not increase the Variable noisefactor_max and try again

- if no error:

    - does the graph "residual error signal power (logarithmic)" look correct? if yes follow the steps below. If not try again after you checked if all the parameters are correct and everything is plugged in correct.

- copy "equalizer schreckstimulus.npy" into the folder "as_setup/Stimulation gui"

calibrate dB SPL
----------------
An implementation to simplify this procedure will come in future releases.

calibrate acceleration sensors
------------------------------
Depending on the construction of the sensor platform, the measured acceleration in the different spacial directions can
be different. Therefore, these sensors have to be calibrated to return the same values when stimulated with the same force.

For this calibration, we use a vibrational motor that is put on the sensor platform. The sensor is placed once in every
spacial direction (x, y, and z) and the output of the sensor is recorded. The amplitudes of these measurements define
the calibration parameters; the factors that are used to normalize the output of the sensors.

After calibration
~~~~~~~~~~~~~~~~~
- Plug audio cables back into their correct place

    - SC-1(trigger) ⇒  BB-ai3
    - SC-3(pre-stimulus) ⇒ BB-ai4 BNC
    - SC-4(startle-stimulus) ⇒ BB-ai5 BNC

- Remove microphone and foam/fabric from tube
- Turn of dB-measurement device
- Unplug line-in from soundcard
