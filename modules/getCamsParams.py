#!/usr/bin/env python3

### Get /proc/bus/input/devices as dictionary (JSON) output
# -- linux

import json

#  --- requires linux ---
import listCams, getDeviceName, getCamSettings, getCamFormats
#      list    , string       , dict          , dict
#      v4l2-ctl, udevadm      , v4l2-ctl      , v4l2-ctl ffmpeg
#                                               ffmpeg call is slow, thus why multiprocessing

dictCamNames = dict()

def buildDict(cam):
  global dictCamNames 
  dictStuff = dict()
  dictStuff.update({ 'name' : f'{cam} -- {getDeviceName.getDeviceName(cam,"ID_MODEL=")}' })
  dictStuff.update(getCamSettings.getCamSettings(cam)) # comes wrapped in settings
  dictStuff.update({ 'formats' : getCamFormats.getCamFormats(cam) })
  dictCamNames.update({ int(cam) : dictStuff })

def main_threaded():
  from multiprocessing.dummy import Pool as ThreadPool
  pool = ThreadPool(17)  
  pool.map(buildDict, listCams.main())
  pool.close()
  pool.join()
  return dict(sorted(dictCamNames.items()))

def main_multi():
  from multiprocessing import Pool
  pool = Pool()
  pool.map(buildDict, listCams.main())
  pool.close()
  pool.join()
  return dict(sorted(dictCamNames.items()))

def main_unthreaded():
  for i in listCams.main():
    buildDict(i)
  return dictCamNames

def main():
  result = main_threaded()
  return result

if __name__ == "__main__":
  print(json.dumps(main_threaded(),indent=2))
  print(list(dictCamNames[6]['formats'].keys())[0])
  print(int(float(dictCamNames[6]['formats']['yuyv422']['424x240'][-1])))
