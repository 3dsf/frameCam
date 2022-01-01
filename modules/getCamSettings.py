#!/usr/bin/env python3

### Get UVC settings from camera
######  Makes dictionary cam # as key

import sys, subprocess, json

def getCamSettings(cam):
  out = subprocess.Popen(['v4l2-ctl', '-d', f'/dev/video{cam}', '--list-ctrls-menu'],
             stdout=subprocess.PIPE,
             stderr=subprocess.STDOUT)
  stdout,stderr = out.communicate()
  
  linesOut = stdout.decode('UTF-8').splitlines()

  camSettings = dict()
  b = dict()

  nLines = len(linesOut)
  for i in range(0, nLines):
    #Skip menu legend lines which are denoted by 4 tabs
    if linesOut[i].startswith('\t\t\t\t'):
      continue
    
    a = dict()
    setting = linesOut[i].split(':',1)[0].split()   
            # ['brightness', '0x00980900', '(int)']
    param = linesOut[i].split(':',1)[1].split()     
    # ['min=-64', 'max=64', 'step=1', 'default=0', 'value=0']
    # Put paramaters into a dictionary
    for j in range(0, len(param)):
      a.update({param[j].split('=',1)[0]: param[j].split('=',1)[1]})
    # Add bitName and setting type to params dictionary 
    a.update({'bitName': setting[1]})
    a.update({'type': setting[2].strip("()")})
    # Create a legend for menu entries and add to dictionary with other params
    if a['type'] == 'menu':
      h = 0
      legend = ''
      while h >= 0:
        h += 1
        ih = i + h
        if linesOut[ih].startswith('\t\t\t\t') and (ih) <= nLines:
          legend = legend + linesOut[i+h].strip() + "   "
        else:
          h = -1
      a.update({'legend': legend})    # additional data on settings
      a.update({'step': 1})           # adding to work with updateUVCsetting()
    # Use setting name as key and dictionary of params as value
    b.update({setting[0]: a})
  camSettings.update({'settings': b})
  #camSettings.update({'deviceAddress': cam})

  return camSettings

if __name__ == "__main__":
  cam = 0

  if len(sys.argv) > 1:
    cam = sys.argv[1]

  print(json.dumps(getCamSettings(cam),indent=2))
