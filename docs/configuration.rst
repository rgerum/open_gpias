Configuration
=============

As every setup differs slightly from the components and how the parts are installed, the measurement setup needs to be
configured in order to work properly. Open GPIAS therefore has a configuration module that allows to provide the needed
information.

Soundcard
---------

To create the acoustic stimuli, a soundcard is used. The right device has to be selected, as well as which channels
are connected to the loudspeakers.

- **sound device**: the device or driver that is used
- **channel trigger**: the soundcard's output channel that is used to play the trigger signal, that is send to the NiDAQ
  card, in order to synchronize the stimulus and the measured response. Default 1
- **channel pre-stimulus**: the soundcard's output channel that is connected to the NiDAQ card and the pre-stimulus
  loudspeaker. Default 3
- **channel startle-stimulus**: the soundcard's output channel that is connected to the NiDAQ card and the startle-stimulus
  loudspeaker. If only one loudspeaker is used, select the same channel as for the pre-stimulus. Default 4
- **sample rate**: the sampling rate for the sound playback. Default 96000
- **channel latency**: the delay for the playback for the different channels. Often soundcards delay the playback for
  some channels in order to generate surround sound, this offset can be corrected in our software. Example: 0, 0, 14.8125, 14.8125
  for the *Asus Xonar Essence STX II*.

Loudspeakers
------------

To get the desired playback of the acoustic stimuli, the loudspeakers have to be configured properly. The amplification
factor has to be given, as well as an equalizer profile to guarantee a flat frequency response function.

- **speaker amplification factor**: the value used to multiply internal values to generate the desired sound pressure level
  from the loudspeakers. This depends on the loudspeakers and the amplifiers. The first value is for the pre-stimulus
  loudspeaker, the second for the startle-stimulus loudspeaker. Example: 1.9e-05,3.125e-07
- **equalizer profile**: the recorded profile for the speaker. See calibration for details.

NiDAQ Card
----------

The data is recorded with a NiDAQ card. Currently we do not allow a different configuration of the channels, but the
device can have different names, depending on the installation.

- **recording device**: the name of the device, as seen e.g. in NiMAX. Typically, names start with "Dev" followed by a number. Example "Dev2".
- **recording rate**: the rate for the data recording in Hz. Default 10000

Acceleration Sensors
--------------------

The acceleration sensors measure the response of the animal in three spatial directions.

- **acceleration sensor factors**: three factors for the different acceleration sensors. Amplitudes will be divided by this
  factor to account for different sensitivities. Example: 0.9027,1.0,3.8773. See calibration for details.