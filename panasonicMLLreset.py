#!/usr/bin/env python3

# Panasonic Plasma TV MLL reset script for Raspberry Pi, instead of Arduino.
# A bug in the old Panasonic plasma TVs cause them to get less black over time.
# Tested on Raspberry Pi 4 only, but should work on all newer models.

# Requires i2c modules loaded with "modprobe i2c-bcm2835 i2c-dev"
# Requires the user to be in the i2c group.
# requires pip install smbus2

# argument -t enables transistor switch.
# argument -c uses CEC to reboot tv
# argument -s makes it run without asking.
# a number in arguments is taken as i2c address, 0x50 is assumed as default.

# For the 2009 Panasonic TV I have, you need this for the cable:
# Connector: JST PHR-11
# Crimps (PH 2.0mm): SPH-004T-P0.5S
# Four jumper cables.

# be aware that the Raspberry Pi pinout is as follows.
# Pana 3->gpio pin 6 (GND)
# Pana 8->gpio pin 5 (SCL)
# Pana 9->gpio pin 3 (SDA)
# Pana 10->gpio pin 9 (GND)

# transistor switch can be connected at at gpio pin 11.

from smbus2 import SMBus
from time import sleep
import RPi.GPIO as rgpio
import sys

# the offsets for the data we want, according to the guide at http://panasonic.mironto.sk.
# range syntax: range(start, stop, step). Stop not included.
# ... AS OPPOSED TO THE ARDUINO SCRIPT!
read_range=range(0,15) # why do we even need this extended range?
write_range=range(1,7)

dev_addr = 0x50 # harmless for now, in case i make an accident testing this.
bus = SMBus(1)

def transistor_init(state):
	rgpio.setmode(rgpio.BCM)
	ctrl_pin = 11
	gpio.setup(ctrl_pin, rgpio.OUT)
	if state == 1:
		gpio.output(ctrl_pin, 1) # set ctrl_pin to HIGH, enabling the switch.
		sleep(0.01)
	if state == 0:
		gpio.cleanup() # finish
def eeprom_set_addr(addr):
	bus.write_byte_data(dev_addr, addr//256, addr%256)

def eeprom_read_byte(addr):
	eeprom_set_addr(addr)
	return bus.read_byte(dev_addr)

def eeprom_write_byte(addr, byte) :
    data = [addr%256,byte]

    try:
        bus.write_i2c_block_data(dev_addr, addr//256, data)
    finally:
        sleep(0.1)

def cec_reset():
	import cec
	cec.init()
	tv = cec.Device(cec.CECDEVICE_TV)
	tv.standby()
	print("waiting for tv to power off.", end='', flush=True)
	while tv.is_on() == True:
		sleep(0.5)
		print(".", end='', flush=True)
	print("\n \n waiting for tv to power on.", end='', flush=True)
	tv.power_on()
	while tv.is_on() == False:
		sleep(0.5)
		print(".", end='', flush=True)
	print("\n")

def get_addr():
	global dev_addr
	for arg in sys.argv: # get dev_addr or assume default)
		try:
			if "x" in arg:
				dev_addr = int(arg.split("x")[1], 16) # argument is in hex.
			else:
				dev_addr = int(arg, 10) # argument is in decimal.
		except:
			pass
	print(f"TV i2c address is: {dev_addr:#0x}")

def main():
	get_addr()
	print("write range is:")
	read_bytes = []
	try:
		for addr in write_range:
			read_bytes.append(eeprom_read_byte(addr))
	except:
		raise IOError(f"Device not readable at {dev_addr:#0x}")
	print(read_bytes)
	if "-s" not in sys.argv[1:]:
		if input("Start writing zeroes to eeprom?: ") != "y":
			return

	print("writing zeroes")
	status=0
	for addr in write_range:
		eeprom_write_byte(addr, 0x00)
		status = status + 100/len(write_range)
		print(f"{status}% done writing zeroes to tv.", end='\r', flush=True)
	print("\n \n")

	print("read range is:")
	read_bytes = []
	for addr in read_range:
		read_bytes.append(eeprom_read_byte(addr))
	print(read_bytes)

if __name__ == "__main__":
	if "-t" in sys.argv[1:]:
		transistor_init(1)
	if "-c" in sys.argv[1:]:
		cec_reset()
	main()
	if "-t" in sys.argv[1:]:
		transistor_init(0)
	if "-c" in sys.argv[1:]:
		cec_reset()
