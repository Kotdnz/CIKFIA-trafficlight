#!/usr/bin/python
# Thsi script started from /etc/rc.local by next command
# (sleep 10;/home/pi/mySubscriber.py)&
# Author kot.dnz@gmail.com
# 19-Sep-2018
# revision 1.3
# Whats new in 1.2
# 1. Complete refactored the Threading (two new classes)
# 2. Added 10 & 15 minutes sessions
#    in the array I add the variable
#    if -1 delay value from global variable
# 3. Unbreakable Yellow via perpetual timer
#    Released by non stop timer
# 4. refacturing to be python3 ready - to relase into new order, not now
#

import paho.mqtt.client as mqtt
import paho.mqtt.publish as publish
import simplejson as json #import json
import RPi.GPIO as GPIO
import time
from InfiniteTimer import InfiniteTimer
import threading
import syslog

broker_address = "localhost"
#broker_address = "10.0.0.237"
# auth for subscriber
user = "point"
password = "mqtt"

#structure for publish
auth = {
        'username':"point",
        'password':"mqtt"
}

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)

# declaring the pins
pins = {
   0: {"state" : GPIO.LOW, "pin": 19 },
   1: {"state" : GPIO.LOW, "pin": 26 },
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
	"YELOFF": 0b11000000,
	"LAST":   0b10100000,
	"PIT":    0b01100000,
	"LASTPIT": 0b00100000,
	"OFF":    0b11000000
        }

# declaring the procedures
# difference between CIK-FIA kind of procedure and hobby - where we will finish on sequence.
# At the [3] item or at the end [9].
# the vaue 10 mean - we don't turn off the light and left the red4
cik = 3
hobby = 9

ShortMinDur = 135
LongMinDur  = 210

startProc = False
raceDuration = ShortMinDur
iRange = hobby

# we will store all last command to show except YELLOW
lastCmd = "OFF"

# process sequence - what we show and after how many second
ProcArray = {
	0: {"cmd": "RED1", 	"delay":  1.0, "count": 1},
	1: {"cmd": "RED2", 	"delay":  1.0, "count": 1 },
	2: {"cmd": "RED3", 	"delay":  1.0, "count": 1 },
	3: {"cmd": "RED4", 	"delay":  1.0, "count": 1 },
	4: {"cmd": "GREEN", 	"delay":  -1, "count": 1 },
	5: {"cmd": "GREEN3", 	"delay":  -1, "count": 1 },
	6: {"cmd": "GREEN2", 	"delay":  -1, "count": 1 },
	7: {"cmd": "GREEN1", 	"delay":  -1, "count": 1 },
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
        time.sleep(0.05)
        global lastCmd
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
        #store last cmd except YELLOW & YELOFF
        if cmd != "YELLOW" and cmd != "YELOFF" :
          lastCmd  = cmd

        # here we send the cmd to the secondary devices
        publish.single("second",
                payload=cmd,
                hostname=broker_address,
                client_id="MainServer",
                auth=auth)

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
	if rc == 0:
            syslog.syslog("Connected.")
            client.subscribe("cloud")
	else:
            syslog.syslog("Connection failed")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
     parsed_json = {}
     try :
        parsed_json = json.loads(str(msg.payload))
        global lights, startProc, rY, rH, iRange, raceDuration
        for cmd in parsed_json:
          if cmd in lights:
             if parsed_json[cmd] == "ON":
               # check if this one of our procedure
               if cmd == "RED1" :
                # start procedure - CIK-FIA race rules (1sec), no autostart
                raceDuration = 0
                iRange = cik
                startProc = True
                return
               if cmd == 'GREEN1':
                # hobby procedure = complete start procedure (1sec) + autostart +
                # roll back through green (2min) + Last lap + Pit
                # 10 minutes
                raceDuration = ShortMinDur
                iRange = hobby
                startProc = True
                return
               if cmd == 'GREEN2':
                # hobby procedure = complete start procedure (1sec) + autostart +
                # roll back through green (2min) + Last lap + Pit
                # 15 minutes
                raceDuration = LongMinDur
                iRange = hobby
                startProc = True
                return
               if cmd == "YELLOW":
                rY.start()
                return
               if cmd == "YELOFF":
                rY.cancel()
                disp( lastCmd )
                return
               startProc = False
               rY.cancel()
               disp( lastCmd )
               # if enyone of the our procedures - execute the particular cmd
               disp(cmd)
     except:
       print("bad json: %s", parsed_json)

yToggle = False
# Yellow blinking procedure
def myYellow():
	global yToggle
	if yToggle == True :
		disp('YELLOW')
		yToggle = False
	else :
		disp( lastCmd )
		yToggle = True


class procThread (threading.Thread):
   def __init__(self):
      threading.Thread.__init__(self)
      self.thread = None
      self._should_continue = False

   def run(self):
      if not self._should_continue :
        self._should_continue = True
        mainProc()

   def cancel(self):
        if self.thread is not None:
            self._should_continue = False
            self.thread.cancel()

# main Procedure
def mainProc():
  global startProc, iRange, raceDuration, ProcArray
  while True :
    if startProc == True :
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
             if ProcArray[act]['delay'] >= 0 :
                mySleep = ProcArray[act]['delay']
             else:
                mySleep = raceDuration
             count = 0
             while startProc == True and count <= mySleep:
                count = count + 0.1
                time.sleep(0.1)
                if not startProc:
                 break
             if act >= iRange:
                 startProc = False
                 break
           if not startProc:
             startProc = False
             break
      startProc = False
      time.sleep(0.1)

# MQTT related configurations and functions
client = mqtt.Client("piClient")
client.username_pw_set(user, password=password)
client.on_connect = on_connect
client.on_message = on_message

client.connect(broker_address, 1883, 60)

#define main proc thread
rH =  procThread()
rH.start()

# run the yellow threads
rY = InfiniteTimer(0.5, myYellow)

# loop to wait for mqtt
client.loop_forever()

