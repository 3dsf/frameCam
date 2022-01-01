#!/usr/bin/env python3

### List available camera outputs formats

import subprocess, json, sys

def listPixelFmtRefLines(cam):
  # ffmpeg output with v4l2 and ffmpeg pixel format mat names to be correlated 
  listCmd = ['ffplay', '-f', 
          'v4l2', '-list_formats', 'all',
          '-i', f'/dev/video{cam}', '-hide_banner']
  out = subprocess.Popen(listCmd,
             stdout=subprocess.PIPE,
             stderr=subprocess.STDOUT)
  stdout,stderr = out.communicate()
  return stdout.decode('UTF-8').splitlines()

def getCamFormats(cam):  #  ex 0
  listCmdFfmpegFormats = ['ffplay', '-f',
          'v4l2', '-list_formats', 'all',
          '-i', f'/dev/video{cam}', '-hide_banner']
  fOut = subprocess.Popen(listCmdFfmpegFormats,
             stdout=subprocess.PIPE,
             stderr=subprocess.STDOUT)
  fStdout,fStderr = fOut.communicate()
  pxFmtRef = fStdout.decode('UTF-8').splitlines()

  listCmd = ['v4l2-ctl', '-d', f'/dev/video{cam}', '--list-formats-ext']
  out = subprocess.Popen(listCmd,
             stdout=subprocess.PIPE,
             stderr=subprocess.STDOUT)
  stdout,stderr = out.communicate()
  
  linesOut = stdout.decode('UTF-8').splitlines()
 
  lastLine = linesOut[-1]

  dictFormats = dict()
  dictReso = dict()
  listFps = []
  ffmpegPxFmt = ''
  res = ''

  # Pixel Format --> Resolution --> FPS
  for line in linesOut:
    #Skip menu legend lines which are denoted by 4 tabs
    if line.startswith('\t['):   # [0] & Color Fmt 
      if listFps:
        dictFormats.update({ffmpegPxFmt: dictReso})
      v4l2PxFmt = line.split('(')[1].split(')')[0]
      for linePxFmt in pxFmtRef:
        if linePxFmt.find(v4l2PxFmt) != -1:
          ffmpegPxFmt = linePxFmt.split(':')[1].strip()
    elif line.startswith('\t\tS'):
      if res != '':  
        dictReso.update({res: listFps})
        listFps = []
      w, h = line.split()[2].split('x')
      res = f'{w}x{h}'
    elif line.startswith('\t\t\tI'):
      fps = line.split()[3].strip('(')
      listFps.append(fps)
    if line == lastLine:
      res = f'{w}x{h}'
      dictReso.update({res : listFps})
      dictFormats.update({ffmpegPxFmt: dictReso})

  return dictFormats

if __name__ == "__main__":
  cam = 0

  if len(sys.argv) > 1:
    cam = sys.argv[1]

  #pxFmtRef = listPixelFmtRefLines(cam)
  print(json.dumps(getCamFormats(cam), indent=2))

