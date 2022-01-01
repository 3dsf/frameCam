#!/usr/bin/env python3

### Get /proc/bus/input/devices as dictionary (JSON) output
######  Makes dictionary with Physical Address as key

import subprocess, json

def getDeviceName(cam, key):
  listCmd = [ 'udevadm', 'info', '--query=property', f'--name=/dev/video{cam}' ]
  out = subprocess.Popen(listCmd,
             stdout=subprocess.PIPE,
             stderr=subprocess.STDOUT)
  stdout,stderr = out.communicate()
  lines = stdout.decode('UTF-8').splitlines()
  for line in lines:
    if key in line:
      keyValue = line.split('=')[1]
      break
  return keyValue

if __name__ == "__main__":
  cam = 0
  key = 'ID_MODEL='
  print(getDeviceName(cam,key))
