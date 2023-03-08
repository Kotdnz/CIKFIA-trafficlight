#!/bin/sh

# In an empty SD-CARD
# under OS - mount card
# create empty fle "ssh"
#
# create
# wpa_supplicant.conf
#
#ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
#update_config=1
#country=US
#
#network={
#        scan_ssid=1
#        ssid="My-home-TP-LINK"
#        psk="kostya-secret"
#        key_mgmt=WPA-PSK
#}
#
# reboot
#
# change root pas
sudo passwd

# change pi pass
sudo passwd pi

# install the dependencies
sudo apt-get upgrade
sudo apt-get update
sudo apt-get install python-pip
pip install paho-mqtt
pip install RPi.GPIO
pip install flask
pip install simplejson


# get source code
# scp rev_01.3.zip pi@10.0.0.121:/home/pi
# unpak and check permissions
# depend of PCB version in file mySubscriber
# we need to check the versions 26-19 or 19-26
#

apt-get install mosquitto
/etc/init.d/mosquitto start

nano /etc/rc.local
# insert the following strings before the string
# exit 0
#
# /usr/bin/python /home/pi/web-server/webserver.py &
# /usr/bin/python /home/pi/mySubscriber.py &
#

# next section - configure raspberry as WiFi access point
# Install the access point and network management software
sudo apt-get install dnsmasq hostapd

sudo systemctl unmask hostapd
sudo systemctl enable hostapd

#Define the wireless interface IP configuration
sudo nano /etc/dhcpcd.conf

# add to the end
interface wlan0
    static ip_address=172.20.20.1/24
    nohook wpa_supplicant


# Configure the DHCP and DNS services for the wireless network
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.orig
sudo nano /etc/dnsmasq.conf
#
# Use the require wireless interface - usually wlan0
interface=wlan0     
dhcp-range=172.20.20.10,172.20.20.220,255.255.255.0,24h
domain=wlan

# Configure the access point software
sudo nano /etc/hostapd/hostapd.conf

country_code=UA
interface=wlan0
ssid=KartingSystemV1
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=6jBwdfHrMgNvxe32JaMB
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP

# run all
sudo systemctl reboot
