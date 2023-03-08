#!/usr/bin/python
import os
from flask import Flask, render_template, request
import paho.mqtt.publish as publish
import simplejson as json

app = Flask(__name__)
broker_address = "localhost"
auth = {
        'username':"point",
        'password':"mqtt"
}

lights = {"RED":"OFF","YELLOW":"OFF","GREEN":"OFF","RED1":"OFF","GREEN1":"OFF","OFF":"ON","PIT":"OFF","LAST":"OFF"}

#switch off all
def allOFF():
        global lights
	lights['RED'] = "OFF"
	lights['YELLOW'] = "OFF"
        lights['GREEN'] = "OFF"
	lights['RED1'] = "OFF"
	lights['GREEN1'] = "OFF"
	lights['PIT'] = "OFF"
	lights['LAST'] = "OFF"
	lights['OFF'] = "OFF"

@app.route("/")
def main():
   piTemp = getCPUtemperature()
   templateData = {
      'lights' : lights,
      'piTemp' : piTemp
   }
   return render_template('main.html', **templateData)

# The function below is executed when someone requests a URL with the pin number and action in it:
@app.route("/lights/<changeColor>/<action>")
def action(changeColor, action):
 try:
   global lights
   if changeColor in lights:
        # Get the device name for the pin being changed:
        colorName = lights[changeColor]
        if changeColor != "YELLOW":
			allOFF()
        # If the action part of the URL is "on," execute the code indented below:
        if action == "on":
            lights[changeColor] = "ON"
        if action == "off":
			if changeColor == 'RED1' :
				lights['GREEN'] = "ON"
			else :
				lights['OFF'] = "ON"

        publish.single("cloud",
                payload=json.dumps(lights),
                hostname=broker_address,
                client_id="WebServer",
                auth=auth)

 except:
   print('bad request')

 piTemp = getCPUtemperature()
 CPU_usage = getCPUuse()

 # RAM information
 # Output is in kb, here I convert it in Mb for readability
 RAM_stats = getRAMinfo()
 #RAM_total = round(int(RAM_stats[0]) / 1024,1)
 #RAM_used = round(int(RAM_stats[1]) / 1024,1)
 #RAM_free = round(int(RAM_stats[2]) / 1024,1)

 # Disk information
 DISK_stats = getDiskSpace()
 #DISK_total = DISK_stats[0]
 #DISK_free = DISK_stats[1]
 #DISK_perc = DISK_stats[3]

 templateData = {
      'lights' : lights,
      'piTemp' : piTemp,
      'cpu'    : CPU_usage,
      'disk'   : DISK_stats,
      'ram'    : RAM_stats
 }

 return render_template('main.html', **templateData)

# Return CPU temperature as a character string
def getCPUtemperature():
    res = os.popen('vcgencmd measure_temp').readline()
    return(res.replace("temp=","").replace("'C\n",""))

# Return RAM information (unit=kb) in a list
# Index 0: total RAM
# Index 1: used RAM
# Index 2: free RAM
def getRAMinfo():
    p = os.popen('free -h')
    i = 0
    while 1:
        i = i + 1
        line = p.readline()
        if i==2:
            return(line.split()[1:4])

def getCPUuse():
    return(str(os.popen("top -n1 | awk '/Cpu\(s\):/ {print $2}'").readline().strip(\
)))

# Return information about disk space as a list (unit included)
# Index 0: total disk space
# Index 1: used disk space
# Index 2: remaining disk space
# Index 3: percentage of disk used
def getDiskSpace():
    p = os.popen("df -h /")
    i = 0
    while 1:
        i = i +1
        line = p.readline()
        if i==2:
            return(line.split()[1:5])

if __name__ == "__main__":
   app.run(host='0.0.0.0', port=80, debug=True, threaded=True)
