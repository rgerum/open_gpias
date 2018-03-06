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
