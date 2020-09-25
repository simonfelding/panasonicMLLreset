# panasonicMLLreset
Panasonic plasma TV MLL reset script for Raspberry Pi, instead of Arduino.

A bug in the old (2008-2011?) Panasonic plasma TVs cause them to get less black over time.
Tested on Raspberry Pi 4 only.

Requires i2c modules loaded with "modprobe i2c-bcm2835 i2c-dev"
Requires the user to be in the i2c group.
requires pip install smbus2

argument -s makes it run silent. Run without arguments first so you know if it works.

# For the 2009 Panasonic TV I have, you need this for the cable:
Connector: JST PHR-11
Crimps (PH 2.0mm): SPH-004T-P0.5S
Four jumper cables.

# be aware that the Raspberry Pi pinout is as follows.
Pana pin 3->gpio pin 6 (GND)
Pana pin 8->gpio pin 5 (SCL)
Pana pin 9->gpio pin 3 (SDA)
Pana pin 10->gpio pin 9 (GND)
