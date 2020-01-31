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

In our setup, we use a *Asus Xonar Essence STX II* 7.1 soundcard (SNR: 124 dB, channels: 8, sampling rate: <192 kHz ).


Amplifier
---------
Broadband low noise amplifier

- Amp74, Thomas Wulf, Frankfurt
- Amp75, Thomas Wulf, Frankfurt

Loudspeaker
-----------
The setup can either be realized with one loudspeaker or two loudspeakers. Separating the pre-stimulus from the
startle-stimulus loudspeaker has the advantage, that the speaker for the pre-stimulus is not damaged by the repeated
application of loud startle-pulses.

The pre-stimulus speaker should be able to reproduce the signal faithfully, while the startle-stimulus speaker only needs
to be able to present a loud burst.

In our setup, we use:

- Two-way loudspeaker Canton Plus XS.2 for the pre-stimulus
- Neo-25s (Sinuslive) for the startle-stimulus


NiDAQ-Card
----------
The data acquisition card needs at least six channels and a recording rate of 10 kHz.

In our setup, we use a PCIe-6320 data acquisition card connected to a Breakoutbox BNC-2110.

Sensor platform
---------------

.. figure:: images/Sensors_Scheme.svg
    :alt: Scheme of the sensor platform

The sensor platform has to hold the animal at a fixed distance to the speakers. In addition, the animal has to be flexibly
mounted to allow for measurable vibrations when the animal twitches in response to a startle stimulus.

In our setup, we use a platform consisting of two plates. The upper plate has a mount for the animal restrainer and is
mounted on the lower plate by four springs and two rubber foam blocks for damping. Underneath the upper plate, an acceleration
sensor (ADXL 335 on a GY 61 board) is attached. The lower plate is screwed to the vibration isolated table.

We provide the technical drawings and CAD files for the sensor platform:

- `Complete_Sensory_Platform.pdf <https://github.com/rgerum/open_gpias_hardware/raw/master/SensorsystemCadDrawing/Complete_Sensory_Platform.pdf>`_
- `cadfiles.zip <https://github.com/rgerum/open_gpias_hardware/archive/master.zip>`_

Animal restrainer
-----------------
The animal restrainer has to hold the animal during the measurement. The restrainer should be designed, so that the animal
is not able to turn around, and that the restrainer does not cause acoustic distortions.

In our setup, we use an animal restrainer made out of an acrylic tube (length x inner diameter, small: 102mm x 27mm (for mouse, cap:
`cap_small.stl <https://github.com/rgerum/open_gpias_hardware/blob/master/caps/3D-printer/cap_small.stl>`_),
middle: 137mm x 37mm (small gerbil, cap:
`cap_normal.stl <https://github.com/rgerum/open_gpias_hardware/blob/master/caps/3D-printer/cap_normal.stl>`_),
big: 137mm x 42mm (big gerbil, cap:
`cap_big.stl <https://github.com/rgerum/open_gpias_hardware/blob/master/caps/3D-printer/cap_big.stl>`_)
covered with a wire mesh at the front end and a plastic cap (custom 3D print) at the rear end.

List of all components
----------------------

============================ ================================ ============ =================================================================================
Component                    Model                            Cost         Link
============================ ================================ ============ =================================================================================
Anechoic chamber
Vibration isolated table
PC
Soundcard                    Asus Xonar Essence STX II        310.00 €     https://www.amazon.com/Xonar-Essence-STX-II-7-1/dp/B00JF6RO7C
Amplifier (pre-stimulus)     Amp 74, Thomas Wulf, Frankfurt
Amplifier (startle-stimulus) Amp 75, Thomas Wulf, Frankfurt
Pre-stimulus speaker         Canton Plus XS.2                  71,00 €     https://www.elektrowelt24.eu/shop/product_info.php?refID=20123&products_id=486
Startle-stimulus speaker     Neo-25s, Sinuslive                44,00 €     https://www.amazon.de/Sinuslive-13496-Neo-25S-Hocht%C3%B6ner-Black/dp/B003A67KTK
Data acquisition card        PCIe-6320, National Instruments  625.00 €     http://www.ni.com/de-de/shop/select/multifunction-io-device
Breakout box                 BNC-2110, National Instruments   445.00 €     http://sine.ni.com/nips/cds/view/p/lang/de/nid/1865
Sensor platform              Own construction
Acceleration sensor          ADXL 335 on a GY 61 board          4.20 €     http://www.robotpark.com/GY-61-DXL335-3-Axis-Accelerometer-Module
Animal restrainer            Acrylic tube
                             3D printed cab
Wire Mesh                    Driller 16910; 1.4 x 1.4 mm        4.71 €     https://www.draht-driller.de/fliegengewebe-alu-zuschnitt
Springs                      Febrotec 1.4310 d=0.50 
                             Da=11.50 
                             L0=22.40 c=0.075							 
Cables
============================ ================================ ============ =================================================================================



