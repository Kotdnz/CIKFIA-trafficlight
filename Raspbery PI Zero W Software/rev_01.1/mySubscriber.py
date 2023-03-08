#!/usr/bin/python
# Thsi script started from /etc/rc.local by next command
# (sleep 10;/home/pi/mySubscriber.py)&
# Author kot.dnz@gmail.com
# 01-Sep-2018
# revision 1.1

# chamge the secuance
# add the count and cycle

import paho.mqtt.client as mqtt
import simplejson as json #import json
import RPi.GPIO as GPIO
import time
from threading import Timer
import syslog

broker_address = "localhost"
user = "point"
password = "mqtt"

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

startProc = False
hobbyProc = False
yellowProc = False

# declaring the pins
pins = {
   0: {"state" : GPIO.LOW, "pin": 26 },
   1: {"state" : GPIO.LOW, "pin": 19 },
   2: {"state" : GPIO.LOW, "pin": 6 },
   3: {"state" : GPIO.LOW, "pin": 5 },
   4: {"state" : GPIO.LOW, "pin": 22 },
   5: {"state" : GPIO.LOW, "pin": 27 },
   6: {"state" : GPIO.LOW, "pin": 17 },
   7: {"state" : GPIO.LOW, "pin":  4 }
   }

#declaring the bits mapping
lights = {
	"RED" :   0b10011110,
	"RED1":   0b10010000,
	"RED2":   0b10011000,
	"RED3":   0b10011100,
	"RED4":   0b10011110,
	"GREEN":  0b01011110,
	"GREEN3": 0b01011100,
	"GREEN2": 0b01011000,
	"GREEN1": 0b01010000,
	"YELLOW": 0b00000001,
	"LAST":   0b10100000,
	"PIT":    0b01100000,
	"LASTPIT": 0b00100000,
	"OFF":    0b11000000
        }

# declaring the procedures
# difference between CIK-FIA kind of procedure and hobby - where we will finish on sequence.
# At the [3] item or at the end [9].

# process sequence - what we show and after how many second
ProcArray = {
	0: {"cmd": "RED1", 	"delay":  1.0, "count": 1},
	1: {"cmd": "RED2", 	"delay":  1.0, "count": 1 },
	2: {"cmd": "RED3", 	"delay":  1.0, "count": 1 },
	3: {"cmd": "RED4", 	"delay":  1.0, "count": 1 },
	4: {"cmd": "GREEN", 	"delay":  135.0, "count": 1 },
	5: {"cmd": "GREEN3", 	"delay":  135.0, "count": 1 },
	6: {"cmd": "GREEN2", 	"delay":  135.0, "count": 1 },
	7: {"cmd": "GREEN1", 	"delay":  135.0, "count": 1 },
	8: {"cmd": "YELLOW", 	"delay":  0.30, "count": 200 },
	9: {"cmd": "RED4", 	"delay":  0.60, "count": 100 },
	10: {"cmd": "RED4",     "delay":  1.0, "count": 1 }
	}

# Set each pin as an output and make it low:
for pin in pins:
   GPIO.setup(pins[pin]['pin'], GPIO.OUT)
   GPIO.output(pins[pin]['pin'], pins[pin]['state'])

# check the diodes - running light
for pin in pins:
        GPIO.output(26, GPIO.HIGH)
        GPIO.output(19, GPIO.LOW)
        GPIO.output(pins[pin]['pin'], GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(pins[pin]['pin'], GPIO.LOW)
for pin in pins:
        GPIO.output(26, GPIO.LOW)
        GPIO.output(19, GPIO.HIGH)
        GPIO.output(pins[pin]['pin'], GPIO.HIGH)
        time.sleep(0.1)
        GPIO.output(pins[pin]['pin'], GPIO.LOW)
GPIO.output(19, GPIO.LOW)

# display function
def disp(cmd):
        iterator = 7
        global pins, lights
        matrix = lights[cmd]
        for pin in pins:
		# Uploading pin map into the matrix
		# n-th bit is set (1)
		if (matrix & (1<<iterator)):
			GPIO.output(pins[pin]['pin'], GPIO.HIGH)
		else:
			GPIO.output(pins[pin]['pin'], GPIO.LOW)
		iterator = iterator - 1

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	if rc == 0:
            syslog.syslog("Connected.")
            client.subscribe("cloud/#")
	else:
            syslog.syslog("Connection failed")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
     parsed_json = {}
     try:
        parsed_json = json.loads(str(msg.payload))
        global lights, startProc, hobbyProc, yellowProc
        for cmd in parsed_json:
          if cmd in lights:
                if parsed_json[cmd] == "ON":
		  	# on any new command finish all procedures
		  	startProc = False
			hobbyProc = False
			yellowProc = False
			procCount = 0
			# check if this one of our procedure
                        if cmd == "RED1":
				# start procedure - CIK-FIA race rules (1sec), no autostart
                                startProc = True
				rS = Timer(0, runProc)
				rS.start()
				return
                        if cmd == 'GREEN1':
				# hobby procedure = complete start procedure (1sec) + autostart +
				# roll back through green (2min) + Last lap + Pit
				hobbyProc = True
				rH = Timer(0, runProc)
				rH.start()
				return
			if cmd == "YELLOW":
				yellowProc = True
				rY = Timer(0, yellow)
				rY.start()
				return
			# if enyone of the our procedures - execute the particular cm
                        disp(cmd)
     except:
	syslog.syslog('bad json: %s', parsed_json)

# Yellow blinking procedure
def yellow():
		global yellowProc
		while yellowProc == True:
			disp('YELLOW')
			time.sleep(0.5)
			disp('OFF')
			time.sleep(0.5)

# Start or Hobby prcedure
def runProc():
		global hobbyProc
		global startProc
		global ProcArray
		if hobbyProc == True:
			iRange = 9
		elif startProc:
			iRange = 3
		else:
			return
		for act in ProcArray:
		   toggle = 1
		   for count in range(ProcArray[act]['count']):
			if toggle == 1:
			  disp(ProcArray[act]['cmd'])
			  toggle = 0
			else:
			  if ProcArray[act]['cmd'] == "YELLOW":
				disp("LASTPIT")
			  else:
				disp("OFF")
			  toggle = 1
			time.sleep(ProcArray[act]['delay'])

		   if act >= iRange:
			break
		   if hobbyProc == False and startProc == False:
			break

# MQTT related configurations and functions
client = mqtt.Client("piClient")
client.username_pw_set(user, password=password)
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_address, 1883, 60)

client.loop_forever()
