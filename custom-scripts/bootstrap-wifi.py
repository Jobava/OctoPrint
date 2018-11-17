#!/usr/bin/python

# Move this to /usr/bin/bootstrap-wifi.txt

import sys
import os
from os import listdir
from os.path import isfile, join
from datetime import datetime


# WIFI_PASSWORD_FOLDER = "."
# WIFI_FILE = "octopi-wpa-supplicant.txt"
# BACKUP_DIR = "backup"

WIFI_PASSWORD_FOLDER = "/media/usbstick"
WIFI_FILE = "/boot/octopi-wpa-supplicant.txt"
BACKUP_DIR = "/boot/backup"


print "Looking for WIFI.txt in {}".format(WIFI_PASSWORD_FOLDER)
all_files = [f for f in listdir(WIFI_PASSWORD_FOLDER) if isfile(join(WIFI_PASSWORD_FOLDER, f))]
wifi_txt = [f for f in all_files if 'wifi.txt' in f.lower()]
if not wifi_txt:
    print "WIFI.txt not found!"
    sys.exit(1)
wifi_txt = wifi_txt[0]

print "{} found".format(wifi_txt)
wifi_txt_lines = []
with open(WIFI_PASSWORD_FOLDER + '/' + wifi_txt, "r") as f:
    wifi_txt = f.read()
    wifi_txt_lines = wifi_txt.split("\r\n")
if not wifi_txt_lines:
    print "WIFI.txt found but can't be read or is empty."
    sys.exit(1)
if len(wifi_txt_lines) < 2:
    print "WIFI.txt needs at least 2 lines, one for SSID and another for the password"
    sys.exit(1)

new_ssid = wifi_txt_lines[0]
if ':' in new_ssid:
    new_ssid = new_ssid.split(':')[1].strip()
new_psk = wifi_txt_lines[1]
if ':' in new_psk:
    new_psk = new_psk.split(':')[1].strip()

# We now have the new SSID and new password
# time to check that they are different from the existing settings by parsing the
# WIFI_FILE (e.g. octopi-wpa-supplicant.txt)

with open(WIFI_FILE, 'r') as f:
    octopi_wpa_lines = [line for line in f]

    section_begin = [i for i, line in enumerate(octopi_wpa_lines) if '## WPA/WPA2 secured' in line]
    if not section_begin:
        print "Expected to have a line containing '## WPA/WPA2 secured' in {}".format(WIFI_FILE)
        sys.exit(1)
    section_begin = section_begin[0]

    ssid_line = section_begin + 2
    if not 'ssid="' in octopi_wpa_lines[ssid_line]:
        print "Expected 'ssid=' to be 2 lines below the '## WPA/WPA2 secured' line in {}".format(WIFI_FILE)
        sys.exit(1)
    ssid = octopi_wpa_lines[ssid_line].split('=')
    if not len(ssid) == 2:
        print "The ssid= line (below '## WPA/WPA2 secured') is malformed, it doesn't have a value."
        sys.exit(1)
    # ghetto way to strip leading and trailing quote marks: "SSID" -> SSID
    ssid = ssid[1].strip()[1:-1]

    psk_line = section_begin + 3
    if not 'psk=' in octopi_wpa_lines[psk_line] and not "key_mgmt=NONE" in octopi_wpa_lines[psk_line]:
        print "Expected 'psk=' or 'key_mgmt=NONE' to be 3 lines below the '## WPA/WPA2 secured' line in {}".format(WIFI_FILE)
        sys.exit(1)
    if 'key_mgmt=NONE' in octopi_wpa_lines[psk_line]:
        psk = ''
    else:
        psk = octopi_wpa_lines[psk_line].split('=')
        if not len(psk) == 2:
            print "The psk= line (below '## WPA/WPA2 secured') is malformed, it doesn't have a value."
            sys.exit(1)
        # ghetto way to strip leading and trailing quote marks: "PSK" -> PSK
        psk = psk[1].strip()[1:-1]

if ssid == new_ssid and psk == new_psk:
    print "No change in SSID or PSK"
    print "SSID remains '{}' and PSK remains '{}'".format(ssid, psk)
    sys.exit(1)
else:
    print "Old SSID: '{}', old password: '{}'".format(ssid, psk)
    if not new_psk:
        print "New SSID: {}, no password set".format(new_ssid)
    else:
        print "New SSID: {}, new password: {}".format(new_ssid, new_psk)

# SSID and password have changed, we need to overwrite the existing settings

# save the old WIFI_FILE (e.g. octopi-wpa-supplicant.txt)
save_filename = "{}_{}".format(WIFI_FILE,datetime.today().strftime('%Y-%m-%d_%H_%M_%S'))
backup_dir = BACKUP_DIR
if not os.path.exists(backup_dir):
    os.makedirs(backup_dir)

print "Saving existing {} in {}/{}".format(WIFI_FILE, BACKUP_DIR,save_filename)
os.system('/bin/mv {} {}/{}'.format(WIFI_FILE, BACKUP_DIR, save_filename))
with open(WIFI_FILE, 'w') as f:
    octopi_wpa_lines[ssid_line] = '  ssid="{}"\n'.format(new_ssid)
    if not new_psk:
        octopi_wpa_lines[psk_line] = "  key_mgmt=NONE\n"
    else:
        octopi_wpa_lines[psk_line] = '  psk="{}"\n'.format(new_psk)
    f.write("".join(octopi_wpa_lines))
    print "File write successful!"

print "ALL DONE"

# normal exit code
sys.exit(0)
