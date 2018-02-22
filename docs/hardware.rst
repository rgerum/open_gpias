Hardware
========

The acoustic startle response setup can only record data, if the required hardware is available.

Soundcard
---------

The soundcard should have at least **two** output channels. If two different loudspeakers for pre-stimulus and  startle-stimulus
should be used, the soundcard needs at least **three** channels:

- trigger channel
- pre stimulus
- startle stimulus

In our setup we use a *Asus Xonar Essence STX II* 7.1 soundcard (SNR: 124 dB, channels: 8, sampling rate: <192 kHz ).


NiDAQ-Card
----------
PCIe-6320 connected to a Breakoutbox BNC-2110

Loudspeaker
-----------
Pre-Stimulus Loudspeaker: Two-way loudspeaker Canton Plus XS.2
Sartle-Stimulus Loudspeaker: Neo-25s (Sinuslive)

Amplifier
---------
Broadband low noise Amplifier
-Amp74, Thomas Wulf, Frankfurt
-Amp75, Thomas Wulf, Frankfurt

Sensor System (for ASR Amplitude)
---------------------------------

.. figure:: images/Sensors.png
:alt: ConfigFile scope
:scale: 40%

Scope of ConfigFiles