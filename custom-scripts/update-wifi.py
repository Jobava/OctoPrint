#!/usr/bin/python

import requests
import sys
import os


# using a hardcoded API key for now
API_KEY = 'CFEE7B3229164DD59F27E9B9604A6B96'

r = requests.get("http://127.0.0.1/api/files?apikey={}".format(API_KEY))

if r.status_code != 200:
    print "Can't retrieve the file list from the SD card"
    sys.exit(1)

if not any(x['display']=='WIFI.gcode' and 
       x['refs']['download'] and 
       x['refs']['download'].endswith('/downloads/files/local/WIFI.gcode') for x in r.json()['files']
       ):
    print "API output is malformed"
    sys.exit(1)

r = requests.get("http://127.0.0.1/downloads/files/local/WIFI.gcode")
if r.status_code != 200:
    print "Can't retrieve the file with the WIFI coordinates"
    sys.exit(1)

wifi_lines = r.text.split("\n")

ssid = [line for line in wifi_lines if 'SSID' in line.upper()]
if not ssid:
    print "Can't retrieve the SSID from the wifi coords file"
    sys.exit(1)
ssid = ssid[0].split("SSID:")
if len(ssid) != 2:
    print "SSID line is malformed"
    sys.exit(1)
ssid = ssid[1].strip()

psk = [line for line in wifi_lines if 'PAROLA' in line.upper()]
if not psk:
    print "Can't retrieve the wifi password"
    sys.exit(1)
psk = psk[0].split("Parola:")
if len(psk) != 2:
    print "Wifi password line is malformed"
    sys.exit(1)
psk = psk[1].strip()

print "New SSID and password:\n{}\n{}".format(ssid, psk)

with open('/boot/octopi-wpa-supplicant.txt', 'r') as f:
    octopi_wpa_lines = f.readlines()
    section_begin = [i for i, line in enumerate(octopi_wpa_lines) if '## WPA/WPA2 secured' in line]
    if not section_begin:
        print "Expected to have a line containing '## WPA/WPA2 secured' in /boot/octopi-wpa-supplicant.txt"
        sys.exit(1)
    section_begin = section_begin[0]
    ssid_line = section_begin + 2
    if not 'ssid="' in octopi_wpa_lines[ssid_line]:
        print "Expected 'ssid=' to be 2 lines below the '## WPA/WPA2 secured' line in /boot/octopi-wpa-supplicant.txt"
        sys.exit(1)
    ssid = octopi_wpa_lines[ssid_line].split('=')
    if not len(ssid) == 2:
        print "The ssid= line (below '## WPA/WPA2 secured') is malformed, it doesn't have a value."
        sys.exit(1)
    ssid = ssid[1].strip()

    psk_line = section_begin + 3
    if not 'psk=' in octopi_wpa_lines[psk_line]:
        print "Expected 'psk=' to be 3 lines below the '## WPA/WPA2 secured' line in /boot/octopi-wpa-supplicant.txt"
        sys.exit(1)
    psk = octopi_wpa_lines[psk_line].split('=')
    if not len(psk) == 2:
        print "The psk= line (below '## WPA/WPA2 secured') is malformed, it doesn't have a value."
        sys.exit(1)
    psk = psk[1].strip()

os.system('/bin/mv /boot/octopi-wpa-supplicant.txt /boot/octopi-wpa-supplicant.txt.old')
with open('/boot/octopi-wpa-supplicant.txt', 'w') as f:
    octopi_wpa_lines[ssid_line] = ssid
    octopi_wpa_lines[psk_line] = psk
    f.write("\n".join(octopi_wpa_lines))
    print "File write successful!"

print "Now cleaning up, deleting http://127.0.0.1/api/files/local/WIFI.gcode"
d = requests.delete('http://127.0.0.1/api/files/local/WIFI.gcode', data={'X-Api-Key':API_KEY})
if not d.status_code == 204:
    print "Expected status code 204 after deleting the WIFI.gcode file"
    sys.exit(1)

print "ALL DONE"

# normal exit code
sys.exit(0)
