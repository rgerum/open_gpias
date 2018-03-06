Calibration
===========

Frequency correction
--------------------
As this setup is no all in one setup it may differ from other setups and the transfer function will be different.
That's why you need to calculate a new equalizer for your setup.
There for you have two programs, "equalizer_prestimulus.py" and "equalizer_startlestimulus.py".

.. warning::
    Read this first before you use them! If you do not take care of these instructions, you may destroy your speaker!

The problem is that if you use a different speaker, amplifier, or soundcard the audiosignal may be too strong for your
speaker and destroys it. That's why we limited the maximum Value using the variable noisefactor_max and adjusted it to
 our setup. If you are not sure what Value to take, start with a very small one. Very small means a Value which is 1000
 or 10000 times smaller than the value you would expect. Than follow the instructions below and if the speakers aren't
 loud enough(<60dB) increase the Value for noisefactor_max by a factor of 10 and repeat until it works.

Preparation for frequency correction
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. As a lot of soundcards are not able to play 7.1 sound and record simultaneously we us audio outputs 1 and 2. But in
 the final setup the speakers are plugged into channels 3 and 4. That's why you need to take the bnc-cable of the
 prestimulus(channel3) and plug it into chanel 1. And take the bnc-cable of the startle stimulus(channel4) and plug it
 into channel 2.
2. Connect the microphone with the dB-measurement device
3. Connect the output of the dB-measurement device with the line-in of your soundcard
4. Turn on dB-Measurement device
5. Adjust the input and output gain so that you can measure 60 dB SPL
6. Place the microphone together with some rubber foam or fabric in the tube. The foam/fabric is supposed to "behave"
   like the animal and the microphone are the ears of the animal. So try to place them accordingly.
7. place the tube on the sensor platform
8. Turn on the amplifiers

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
- if error "didn't find an apropriate noisefactor, is the microphone plugged in, the dezibelmeter at the right attenuation and the amplifier turned on?" occurs:
    - did you do all of the questioned? 
    - if not do it and try again
    - if yes try again and see if you hear a sound and if your dB device shows something, if not increase the Variable noisefactor_max and try again
- if no error:
    - does the graph "residual error signal power (logarithmic)" look correct? if yes follow the steps below. If not try again after you checked if all the parameters are correct and everything is plugged in correct.
- copy "equalizer schreckstimulus.npy" into the folder "as_setup/Stimulation gui"

calibrate dB SPL
^^^^^^^^^^^^^^^^
das muss ich noch machen, weil ich da nen programm zu schreiben muss, damit das einfacher ist...

After calibration
^^^^^^^^^^^^^^^^^
- Plug audio cables back into their correct place
    - SC-1(Trigger) -> BB-ai3
    - SC-3(Prestim) -> BB-ai4 BNC
    - SC-4(Startle) -> BB-ai5 BNC
- Remove microphone and foam/fabric from tube
- Turn of dB-measurement device
- Unplug line-in from soundcard
