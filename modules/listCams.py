#!/usr/bin/env python3

### 
######  

import subprocess, json
from multiprocessing.dummy import Pool as ThreadPool

listCams = []

def getCams(cam):
  global listCams 
  out = subprocess.Popen(['v4l2-ctl', '--device', f'/dev/video{cam}', '--get-input'],
             stdout=subprocess.PIPE,
             stderr=subprocess.STDOUT)
  stdout,stderr = out.communicate()

  linesOut = stdout.decode('UTF-8').split()[3]

  if linesOut == '0':
    listCams.append(cam)

  return listCams

def main():
  pool = ThreadPool(16)  
  pool.map(getCams, range(0,49)) # Increase upper range to check more cams
  pool.close()
  pool.join()
  return sorted(listCams)

if __name__ == "__main__":
  print(main())
