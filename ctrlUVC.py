#!/usr/bin/env python3

### Controls UVC setting using   v4l2-ctl

import os, sys, subprocess, json
import cv2
import numpy as np
from functools import partial

def getCamSettings(camDevice):
  out = subprocess.Popen(['v4l2-ctl', '-d', camDevice, '--list-ctrls-menu'],
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
  camSettings.update({'deviceAddress': camDevice})

  print(json.dumps(camSettings, indent=2))

  return camSettings

def updateUVCsetting(setting, step, deviceAddress  , value):
                  # ('gamma', 1   , /dev/video0, 30   )
  #v4l2-ctl -d /dev/video0 --set-ctrl=brightness=50
  value = int(int(step) * round(value/int(step)))
  out = subprocess.Popen(['v4l2-ctl', '-d', deviceAddress, 
      f'--set-ctrl={setting}={value}'], 
      stdout=subprocess.PIPE,
      stderr=subprocess.STDOUT)
  stdout,stderr = out.communicate()
  test = "pass" if stdout.decode('UTF-8') == '' else "fail"
  print(f'setting requested -- {setting} -->  {value}    test: {test}')
  if test == 'fail': 
    print(f'\n--- {setting} is likely locked, check if set to Auto on another slider')
    print(f'--- v4l2-ctl error message :\n{stdout.decode("UTF-8")}')


def defaultSettings(camSettings,window):
  for x in camSettings['settings']:
    cv2.setTrackbarPos(x, window, int(camSettings['settings'][x]['default']))

def nothingOf(value):
  z = 1

def actionCommander(pressedKey):
  breakBool = False
  # Quit
  if pressedKey == ord('q'):
    breakBool = True
  elif cv2.getWindowProperty(winControls,cv2.WND_PROP_VISIBLE) < 1:
    breakBool = True
  if showViewer:
    if cv2.getWindowProperty(winImage,cv2.WND_PROP_VISIBLE) < 1:
      breakBool = True
  # set default settings
  if pressedKey == ord('d'):
    print('--- default setting applied ---')
    defaultSettings(camSettings,winControls)
  return breakBool

# Create window and add sliders poputlated from camSettings
def createSettingsControlWindow(camSettings,window):
  lineImage = 255 * np.ones((1,600,3), np.uint8)
  cv2.imshow(window, lineImage)
  if os.path.isfile(".ctrlUVC.session"):
    f = open(".ctrlUVC.session", "r")
    y, x = f.read().split()
    f.close
    cv2.moveWindow(window, int(x), int(y))
  for x in camSettings['settings']:
    if camSettings['settings'][x]['type'] == 'bool':
      cv2.createTrackbar(x, window,
              int(camSettings['settings'][x]['value']),  # current cam value
              int(1),                        # max =  1 for bool
              partial(updateUVCsetting,      # new value is passed implicitly
              x,                             # setting name
              1,
              camSettings['deviceAddress'])) # value step  = 1 for bool
      cv2.setTrackbarMin(x, window,          # 
              int(0)                     )   # min =  0 for bool
    else:
      cv2.createTrackbar(x, window, 
              int(camSettings['settings'][x]['value']),  # current cam value
              int(camSettings['settings'][x]['max']),    # max value
              partial(updateUVCsetting,      # new value is passed implicitly 
              x,                             # setting name
              camSettings['settings'][x]['step'],        # value step
              camSettings['deviceAddress'])) # url address
      cv2.setTrackbarMin(x, window, 
              int(camSettings['settings'][x]['min']) )  # min value
      if 'legend' in camSettings['settings'][x]:
        text = f'{" " * 30} (for above) --  {camSettings["settings"][x]["legend"]}'
        text = text + (90-len(text)) * " "
        cv2.createTrackbar(text,window,
              1,                            # step
              1,                            #  max --> 
              nothingOf)                    # callable function - does nothing
        cv2.setTrackbarMin(text,window,
              1)                            # min -- if min=max : slider locks

#######
#######

if __name__ == "__main__":
  # Cam can be passed as command line argument
  cam = '/dev/video0'
  showViewer = True
  if len(sys.argv) > 1:
    cam = sys.argv[1]
    if len(sys.argv) > 2 and int(sys.argv[2]) == 0:
      showViewer = False

  camSettings = getCamSettings(cam)  # ex  cam = /dev/video0               
  
  winControls = 'camera controls  ---  press \'d\' to set camera defaults' 
  createSettingsControlWindow(camSettings, winControls)

  if showViewer:
    winImage = 'viewer for camera controls'
    cap = cv2.VideoCapture(cam)
    ret, frame = cap.read()
    cv2.imshow(winImage, frame)
  
    # Main program loop 
    while(cap.isOpened()):
      ret, frame = cap.read()
      if ret == True:
        cv2.imshow(winImage,frame)
      # Key / window closing bindings 
      ## If returns True, it will break loop
      if actionCommander(cv2.waitKey(1) & 0xFF):
        break

    w,h,ww,hh = cv2.getWindowImageRect(winControls)  # w
    print(h,'--',w)    # height , width
    f = open(".ctrlUVC.session", "w")
    f.write(f'{h} {w}')
    f.close()

    cap.release()
    cv2.destroyAllWindows()
  else:
    while True:
      if actionCommander(cv2.waitKey(1) & 0xFF):
        break
    w,h,ww,hh = cv2.getWindowImageRect(winControls)  # w
    print(h,'--',w)    # height , width
    f = open(".ctrlUVC.session", "w")
    f.write(f'{h} {w}')
    f.close()
    cv2.destroyAllWindows()
