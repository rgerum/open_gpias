Assembling the Setup
====================

Sensorplatform
--------------
irgendwas von Matze

Preperation
-----------

In order to make sure, there is no interruption while you assemble the hardware we advise you to make sure you do all preparations before you start to assemble:

- Obtain the needed hardware
- Install soundcard and NIDAQ-Card in the PC as described by their user manual
- After installing the soundcard put its settings on 4 input and 4 output channels
- Build the sensor platform
- Build at least one tube for the animals
- Solder the speaker cables to a bnc connectors (male)
- Think about where to place the hardware components and how to supply them with electricity

Hardware
--------

Place Hardware
~~~~~~~~~~~~~~

- Place the pc, monitor, mouse, keyboard and connect them
- Place the sensor platform in the soundproof chamber
- Place the speaker(s) in front of the sensor platform without them blocking each other and both being horizontally
  centered in front of the tube. Place the startle-stimulus-speaker close to the sensor platform, as it needs to produce
  a sound pressure level of 115 dB SPL which it will only manage if the distance is small. (max 5 cm???? 5 cm passt, oder?)
- Place the amplifiers at the desired places and connect them to electricity
- Place the powersupply for the sensor platform at the desired place and put it on 3V AC
 
Connect Hardware
~~~~~~~~~~~~~~~~

.. figure:: images/Hardware_Config.svg
    :alt: Hardware configuration
    :scale: 40%

The diagram shows how the different components are connected.

- NiDAQ-Card measures the data of the soundcard, therefore needs a BNC Tee connector on the plugs ai4 an ai5
- As we will connect the audiochannels using BNC-Cabels plug chinch-BNC(male) connectors into the channels 1,3,4 of the soundcard 
- Connect everything as stated by the following table

**SC**: soundcard
**SP**: sensor platform
**BB**: breakoutbox
**NI**: NiDAQ-Card
**AP**: amplifier pre-stimulus
**AS**: amplifier startle-stimulus

============== ========================= ==========
From           To                        Cable
-------------- ------------------------- ----------
NI             BB                        ??
SP-X           BB-ai0                    BNC
SP-Y           BB-ai1                    BNC
SP-Z           BB-ai2                    BNC
SC-1           BB-ai3                    BNC
SC-3           BB-ai4                    BNC
SC-4           BB-ai5                    BNC
BB-ai4         AP-in                     BNC
BB-ai5         AS-in                     BNC
AP-out         pre-stimulus speaker      BNC
AS-out         startle-stimulus speaker  BNC
powersupply    SP power in               ??
============== ========================= ==========
