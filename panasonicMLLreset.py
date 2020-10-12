#!/usr/bin/env python3

# Panasonic Plasma TV MLL reset script for Raspberry Pi, instead of Arduino.
# A bug in the old Panasonic plasma TVs cause them to get less black over time.
# Tested on Raspberry Pi 4 only, but should work on all newer models.

# Requires i2c modules loaded with "modprobe i2c-bcm2835 i2c-dev"
# Requires the user to be in the i2c group.
# requires pip install smbus2

# argument -t enables transistor switch.
# argument -c uses CEC to reboot tv?
# argument -s makes it run silent. Run without arguments first so you know if it works.
# a number as argument skips i2c detection and uses the number as device address.

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

from smbus2 import SMBus, i2c
from time import sleep
from datetime import datetime
from syslog import syslog

# the offsets for the data we want, according to the guide at http://panasonic.mironto.sk.
# range syntax: range(start, stop, step). Stop not included.
# ... AS OPPOSED TO THE ARDUINO SCRIPT!
read_range=range(0,10) # why do we even need this extended range?
write_range=range(1,7)

# i2c = SMBus(1)  # Create a new I2C bus. disabled because I use with statements instead.
dev_addr = 9999 # harmless for now, in case i make an accident testing this.

def cec_reset():
	import cec
	cec.init()
	with cec.Device(cec.CECDEVICE_TV) as tv:
		tv.power_off()
		print("waiting for tv to power off.", end='', flush=True)
		while tv.is_on() == True:
			sleep(0.2)
			print(".", end='', flush=True)
		print("waiting for tv to power on.", end='', flush=True)
		tv.power_on()
		while tv.is_on() == False:
			sleep(0.2)
			print(".", end='', flush=True)
		print("\n")

def transistor_ctrl(state):
	import RPi.GPIO as gpio
	gpio_pin = 17 # note: board pin 11 is BCM GPIO 17
	if "-s" not in sys.argv[1:]: # for debugging
		print(f"gpio mode is {gpio.getmode()}")
	if gpio.getmode() != gpio.BCM: # this relies on BCM mode because I assume that's necessary when working with SMBus too.
		raise IOError("gpio BCM mode not set. exiting")
	else:
		if state = 1:
			gpio.setup(gpio_pin, gpio.OUT)
			gpio.output(gpio_pin, 1) # set gpio_pin to HIGH, enabling the switch.
			global gpio_pin_state
			gpio_pin_state = 1
			sleep(1)
		if state = "cleanup":
			gpio.cleanup()


def find_tv():
	found = []
	global dev_addr

	for arg in sys.argv[1:]: # if there is a number in arguments, it's the dev_addr
		try:
			dev_addr = int(sys.argv[arg])
		except:
			pass

	if dev_addr != 9999:
		break
	else:
			## Scan valid I2C 7-bit address range, avoiding invalid addresses:
	        ## (0-2=Different bus formats, 120-127=Reserved/10bit addresses)
	        ## NOTE: If the SDA line is being held LOW, it will appear that
	        ## devices are present at all slave addresses.
		with SMBus(1) as i2c:
			for addr in range(3, 120):
		        try:
		            ## Taken from i2cdetect.c - Do not perform write operations on
		            ## addresses that might contain EEPROMs to avoid corruption.

					if addr in range(0x30, 0x38) or addr in range(0x50, 0x60):
		                # Do a 1-byte read to see if a device exists at address.
		                	i2c.read_byte(dev_addr, addr)
		        except (IOError) as e:
		            # No ACK. Address is vacant.
		            pass
		        else:
		            print(f"Transaction was ACK'd. Found a device at: {addr}")
		            found.append(addr)

		if len(found) > 1:
			syslog("multiple devices found. write the address as an argument to the script.")
			if "-s" not in sys.argv[1:]:
				print(f"Devices found at: {found}")
				dev_addr = int(input("Enter device address (remember prefix 0x if input is hexadecimal): \n"))

		elif len(found == 1):
			dev_addr = found[0])
			print(f"dev address is {dev_addr}")
		else:
			if "-s" not in sys.argv[1:]:
				print("No device found")
			else:
				syslog("!!!! No i2c device found when scanning. No writing was attempted.")

def read_data(range):
	data = ""
	with SMBus(1) as i2c:
		for addr in range:
			data = data + str(i2c.read_byte(dev_addr, addr))
	return(data)

def write_zero():
	status = 0
	data = read_data(read_range)

	with SMBus(1) as i2c:
		try:
			for addr in write_range:
				try:
					i2c.write_byte(dev_addr, addr, 0)
					if "-s" not in sys.argv[1:]:
						status = status + 100/len(write_range)
						print(f"{status} done writing zeroes to pana tv.", end='\r')
				except:
					print(f'\n !!!! failed writing as pos: {addr}')
					print('trying again.')
					try:
						i2c.write_byte(dev_addr, addr, 0)
					except:
						raise IOError(f"failed writing zero again at pos: {addr} :(")

		except:
			with open('panasonic_error.log', 'a') as f:
				f.write(f"{datetime.now()}: Error writing to Panasonic TV at {dev_addr}. Following is the backup of the whole range of data (not just the date part): {data} \n")
			if "-s" in sys.argv[1:]:
				syslog(f"!!!! Write failed badly. Saved the whole read range of data (not just the date) as {os.getcwd()}/panasonic_error.log")
				raise IOError
			else:
				raise IOError(f"Failed badly. Saved the whole read range of data (not just the date) as {os.getcwd()}/panasonic_error.log")

		finally:
			print('\n .. done!')

def main():
	syslog('Attempting Panasonic MLL reset')
	if "-t" in sys.argv[1:]:
		transistor_ctl(1)
	if "-c" in sys.argv[1:]:
		cec_reset()

	find_tv()
	try:
		if "-s" in sys.argv[1:]: # short version of the script.
			write_zero()
			if read_data(write_range) == "0"*len(write_range): # if the range is all zeroes
				syslog("Successful Panasonic MLL reset.")
			else:
				syslog("!!!! Failed attempted Panasonic MLL reset")
				raise IOError
		else: # interactive version for testing
			print("Panasonic MLL reset script. This zeroes out the EEPROM timer as described on http://panasonic.mironto.sk")
			print("Reading EEPROM data:")
			data_read = read_data(read_range)
			print(data_read)
			print(f"The length of this range is: {len(data_read)}")
			if input("Does the data read look like numbers? Type yes to continue and write zeroes over the MLL timer only: \n").lower().strip() in ["yes", "y"]:
				write_zero()
				if read_data(write_range) == "0"*len(write_range)):
					print(f"It worked! Here's the whole thing: {read_data(read_range)}")
				else:
					print(f"!!!! Something is wrong. This should have a lot of zeroes: {read_data(read_range)}")
			else:
				print("yes was not typed, terminating.")

	finally:
		if "-t" in sys.argv[1:] and gpio_pin_state==1:
			transistor_ctl("cleanup")

if __name__ == "__main__":
	main()
