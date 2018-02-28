Ensambling the Setup
====================
Sensorplatform
--------------
irgendwas von Matze

Preperation
-----------

In order to make sure, there is no interuption while you ensamble the hardware we advise you to make sure you do all preperations befor you start to ensamble:

- Obtain the needed hardware
- Install soundcard and NIDAQ-Card in the PC as described by their user manual
- After installing the soundcard put its settings on 4 input and 4 output chanels
- Build the sensorplatform
- Build at least one tube for the animals
- Solder the speaker cabels to a bnc connectors(male)
- Think about where to place the hardware components and how to supply them with electricity

Hardware
--------

Place Hardware
^^^^^^^^^^^^^^

- Place the pc, monitor, mouse, keyboard and connect them
- Place the sensor platform in the soundproof chamber
- Place the speaker(s) infront of the sensorplatform without them blocking each other and both beeing horizontally centered infront of the tube. Place the startle-stimulus-speaker close to the sensor platform, as it needs to produce a sound pressure level of 115 dB SPL which it will only manage if the distance is small. (max 5 cm???? 5 cm passt, oder?)
- Place the amplifiers at the desired places and connect them to electricity
- Place the powersupply for the sensor platform at the desired place and put it on 3V AC
 
Connet Hardware
^^^^^^^^^^^^^^^
Generally you can rely on the diagramm [hier das diagramam mit der Hardware] but to make sure you connect everything correct follow these steps and make sure that you label all cabels:

- As the NIDAQ-Card will measure the Data of the soundcard there needs to be a BNC Tee connector on the plugs ai4 an ai5
- As we will connect the audiochannels using BNC-Cabels plug chinch-BNC(male) connectors into the channels 1,3,4 of the soundcard 
- Connect everything as stated by the following table

SC:Soundcard
SP:Sensorplatform
BB:Breakoutbox
NI:NIDAQ-Card
AP:Amplifier Prestimulus
AS:Amplifier Startle-Stimulus

===========  ==============  ========== 
From         To              Cabel
-----------  --------------  ----------
NI           BB              ??
SP-X         BB-ai0          BNC
SP-Y         BB-ai1          BNC
SP-Z         BB-ai2          BNC
SC-1         BB-ai3          BNC
SC-3         BB-ai4          BNC
SC-4         BB-ai5          BNC
BB-ai4       AP-in           BNC
BB-ai5       AS-in           BNC
AP-out       Prespeaker      BNC
AS-out       Startlespeaker  BNC
powersupply  SP power in     ??
===========  ==============  ==========

Software
--------
Install the software (da weiß ich nicht genau, was man schreibe sollte)

Freuency correction
-------------------
As this setup is no all in one setup it may differ from other setups and the transfer function will be different. Thats why you need to calculate a new equalizer for your setup.
There for you have two progamms, "equalizer_prestimulus.py" and "equalizer_startlestimulus.py". 

**Read this first befor you use them! If you do not take care of these instructions, you may destroy your speaker!**

The problem is that if you use a different speaker, amplifier, or soundcard the audiosignal may be too strong for your speaker and destroys it. That's why we limited the maximum Value using the variable noisefactor_max and adjusted it to our setup. If you are not sure what Value to take, start with a very small one. Very small means a Value which is 1000 or 10000 times smaller than the value you would expect. Than follow the instructions below and if the speakers aren't loud enough(<60dB) increase the Value for noisefactor_max by a factor of 10 and repeat untill it works.

Preperation for frequency correction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. As a lot of soundcards are not able to play 7.1 sound and record simulatiously we us audio outputs 1 and 2. But in the final setup the speakers are pluggd into chanels 3 and 4. Thats why you need to take the bnc-cabel of the prestimulus(channel3) and plug it into chanel 1. And take the bnc-cabel of the startl stimulus(channel4) and plug it into channel 2.
2. Connect the microphone with the dB-measurement device
3. Connect the output of the dB-measurement device with the line-in of your soundcard
4. Turn on dB-Measurement device
5. Adjust the input and output gain so that you can measure 60 dB SPL
6. Place the microphone together with some fome or fabric in the tube. The foam/fabric is supposed to "behave" like the animal and the microphone are the ears of the animal. So try to place them accordingly.
7. place the tube on the sensor platform
8. Turn on the amplifiers

Measure impulse response and calculate equalizer
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
- execute "equalizer_prestimulus.py"
- if error "didn't find an apropriate noisefactor, is the microfon plugged in, the dezibelmeter at the right attenuation and the amplifier turned on?" occurs:
    - did you do all of the questioned? 
    - if not do it and try again
    - if yes try again and see if you hear a sound and if your dB device shows something, if not increase the Variable noisefactor_max and try again
- if no error:
    - does the graph "residual error signal power (logarithmic)" look correct? if yes follow the steps below. If not try again after you cecked if all the parameters are correct and everything is plugged in correct.
- copy "equalizer praestimulus lautsprecher.npy" into the folder "as_setup/Stimulation gui"
- execute "equalizer_startlestimulus.py.py"
- if error "didn't find an apropriate noisefactor, is the microfon plugged in, the dezibelmeter at the right attenuation and the amplifier turned on?" occurs:
    - did you do all of the questioned? 
    - if not do it and try again
    - if yes try again and see if you hear a sound and if your dB device shows something, if not increase the Variable noisefactor_max and try again
- if no error:
    - does the graph "residual error signal power (logarithmic)" look correct? if yes follow the steps below. If not try again after you cecked if all the parameters are correct and everything is plugged in correct.
- copy "equalizer schreckstimulus.npy" into the folder "as_setup/Stimulation gui"

calibrate dB SPL
^^^^^^^^^^^^^^^^
das muss ich noch machen, weil ich da nen programm zu schreiben muss, damit das einfacher ist...

After calibration
^^^^^^^^^^^^^^^^^
- Plug audio cabels back into their correct place
    - SC-1(Trigger) -> BB-ai3
    - SC-3(Prestim) -> BB-ai4 BNC
    - SC-4(Startle) -> BB-ai5 BNC
- Remove microphone and foam/fabric from tube
- Turn of dB-measurement device
- Unplug line-in from soundcard
