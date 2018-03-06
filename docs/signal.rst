Protocols
=========

Protocols can be created or loaded in the protocols module.

Currently two types of protocols are implemented: hearing threshold measurements and GPIAS measurements.

All measurements are divided in multiple trials, all ending with a startle-stimulus. At the beginning of each measurement,
five trials without pre-stimulus are presented, to get the animal used to the startle-stimuli.

The trials in each protocol are randomized to prevent habituation effects of the animal.


Hearing threshold
-----------------

For hearing threshold measurements, each trial can have a pre-stimulus in the form of a short (40 ms) pure tone 100 ms
before the startle stimulus. For the protocol a frequency range (with octave, 1/2 octave or 1/4 octave steps), a sound
pressure level range and a repetition count can be specified.

GPIAS
-----

For GPIAS measurements, each trials has a white noise presented before the startle-stimulus. The noise can be interrupted
by a short (50 ms, flattened with 20 ms sin²-ramps) gap of silence. The noise can be broad band, a frequency band centered
around a middle frequency or a notch filtered noise. For each measurement different middle frequencies can be specified,
as well as the number of measurement repetitions.
