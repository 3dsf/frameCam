#! /usr/bin/python3 

import gi
gi.require_version('Gtk', '3.0')

import threading, time, ffmpeg, subprocess, cv2, json
import numpy as np

from gi.repository import GLib, Gtk, GObject, GdkPixbuf, Gdk
from threading import Thread, Lock
from time import sleep, perf_counter

import sys, os, ast

from collections import deque

# add 'modules' folder to path
moduleDir = os.path.join(os.path.dirname(os.path.realpath(__file__)),'modules')
sys.path.insert(1, moduleDir)


import getCamsParams, vidTools

#debug stuff
a = 0
b = 0
c = 0
d = 0
def de():
  print('\n\t', 'ddCamNum', '\t', 'ddCamFmt', '\t', 'ddCamRes', '\t', 'ddCamFPS')
  print('\t', ddCamVal, '\t\t', ddFmtVal, '\t', ddResVal, '\t', ddFPSval)


import cfl
#Returns dictionary of function name[3:] which cuts the first 3 chars for the key
# and the function is the value.   ex {none : wb_none()}
wb_dict, of_dict = cfl.curateFunctionLists(moduleDir)
#wb_dict['none']()


camParams = getCamsParams.main()
#print(json.dumps(camParams, indent=2))

# Conver numpy to pixbuf format
def np2pixbuf(frame: np.array):
  #z = z.astype('uint8')
  h, w, c = frame.shape
  assert c == 3 or c == 4
  if hasattr(GdkPixbuf.Pixbuf,'new_from_bytes'):
    sFrame = GLib.Bytes.new(frame.tobytes())
    return GdkPixbuf.Pixbuf.new_from_bytes(sFrame, GdkPixbuf.Colorspace.RGB, c==4, 8, w, h, w*c)
  ''' from http://ostack.cn/?qa=1125282/  user: 深蓝 
  '''
  return GdkPixbuf.Pixbuf.new_from_data(frame.tobytes(),  GdkPixbuf.Colorspace.RGB, c==4, 8, w, h, w*c, None, None)

def vid2np(in_filename):
  x = str(meta['width']) + 'x' + str(meta['height'])
  y = ddFPSval
  z = ddFmtVal
  args = (
      ffmpeg
      .input(in_filename,
          s=x,
          framerate=y,
          pixel_format=z) 
      .output('pipe:', format='rawvideo', pix_fmt='bgr24')  # bgr24 for opencv
      .global_args("-hide_banner")
      .compile()
  )
  return subprocess.Popen(args, stdout=subprocess.PIPE, stdin=subprocess.PIPE)

def readFrameAsNp(stream, height, width):
  # Note: RGB24 == 3 bytes per pixel.
  h,w = int(height), int(width)
  frameSize = h * w * 3
  in_bytes = stream.stdout.read(frameSize)
  if len(in_bytes) == 0:
    frame = None
  else:
    if len(in_bytes) == frameSize:
      frame = (
        np
        .frombuffer(in_bytes, np.uint8)
        .reshape([h, w, 3])
      )
    else:
      frame = None
  return frame

#like defining but for subprocess

ffmpegDecode = subprocess.Popen(['echo'] )

ddWBtext = 'none'

meta = {}
meta.update({'width' : 8})
meta.update({'height' : 8})
meta.update({'fps' : 8})

meLock = False

ddCamVal = 0
ddFmtVal = list(camParams[ddCamVal]['formats'].keys())[0]
print(ddFmtVal)
ddResVal = list(camParams[ddCamVal]['formats'][ddFmtVal].keys())[0]
print(ddResVal)
meta['width'], meta['height'] = ddResVal.split('x')
print(meta['width'], meta['height'])
ddFPSval = camParams[ddCamVal]['formats'][ddFmtVal][ddResVal][0]
print(ddFPSval)
meta['fps'] = int(float(ddFPSval))

def cap(cam:int):
  global ffmpegDecode, meta, viewerOn, grabberOn
  print('\n\t\t\tCapture: ', cam, meta['width'], meta['height'], meta['fps'],'\n')
  de()
  viewerOn = False
  grabberOn = False
  time.sleep(.2)
  inputVid = f'/dev/video{cam}'
  #meta = vidTools.getMetaVideo(inputVid)
  ffmpegDecode.communicate(b'q')
  ffmpegDecode.wait
  ffmpegDecode = vid2np(inputVid)
  grabberOn = True
  viewerOn = True

  vMain.resize(1,1)
  

# GTK handlers called by ingrained glade
class Handlers:
  def showCamOptions(self, widget):
    print('\n\nha -- cam options\n')
    print(self, '---', widget,'\n')
  def windowXd(self, widget, data=None):
    global ffmpegDecode
    grabberOn = False
    viewerOn = False
    time.sleep(.1)
    ffmpegDecode.communicate(b'q')
    print('\n\nwindow X\'d\n\n')
    Gtk.main_quit()

combo = {}

class WindowMain:
  def __init__(self):
    global pie, vMain
    pie = self
    self.builder = Gtk.Builder()
    gladeFile = os.path.join(os.path.dirname(os.path.realpath(__file__)),'fc.gtk')
    self.builder.add_from_file(gladeFile)
    vMain = self.builder.get_object('vMain')
    self.vPort = self.builder.get_object('vPort')
    self.vGrid = self.builder.get_object('vGrid')
    self.viewer = self.builder.get_object('viewer')
    self.builder.connect_signals(Handlers())
    
    self.IWB()
    self.DDBuildCam()  #This will cascade other DDBuild functions
    de()
    combo['cam'].set_active(0)



  # Setup for combo boxes
  def comboSetup(self, codeRef, keyList, returnKey, func, gladeObjectID):
    global combo
    if codeRef in combo.keys():
      combo[codeRef].disconnect_by_func(eval(func))
      combo.pop(codeRef)
    combo.update({codeRef : pie.builder.get_object(gladeObjectID)})
    combo[codeRef].set_entry_text_column(0)
    eval(f'combo[codeRef].connect("changed", {func})')
    combo[codeRef].remove_all()
    print(f'combo setup for {codeRef} : ')
    for key in keyList:
      x = eval(returnKey)
      print(x, returnKey)
      combo[codeRef].append_text(x)
  
  # White Balance Select dropdown INIT
  def IWB(self):
    self.comboSetup('WB', list(wb_dict.keys()), 'key', 'pie.ddWB', 'comboWB')
    combo['WB'].set_active(0)

  # Camera Select dropdown INIT
  def DDBuildCam(self):
    self.comboSetup('cam', list(camParams.keys()), 
            "camParams[key]['name']", 'pie.ddCam', 'gCam')
    combo['cam'].set_active(0)

  # Camera Format dropdown INIT
  def DDBuildFmt(self):
    global ddFmtVal
    ddFmtVal = list(camParams[ddCamVal]['formats'].keys())[0]
    self.comboSetup('fmt', list(camParams[ddCamVal]['formats'].keys()), 
            "key", 'pie.ddFmt', 'gPixelFormat')
    combo['fmt'].set_active(0)

  # Camera Resolution dropdown INIT
  def DDBuildRes(self):
    global ddResVal
    ddResVal = list(camParams[ddCamVal]['formats'][ddFmtVal].keys())[0]
    print('\t\t expecting first value of new Res -->',ddResVal)
    self.comboSetup('res', list(camParams[ddCamVal]['formats'][ddFmtVal].keys()),
            "key", 'pie.ddRes', 'gRes')
    combo['res'].set_active(0)

  #Camera FPS dropdown INIT
  def DDBuildFPS(self):
    global ddFPSVal
    ddFPSVal = list(camParams[ddCamVal]['formats'][ddFmtVal][ddResVal])[0]
    self.comboSetup('FPS', list(camParams[ddCamVal]['formats'][ddFmtVal][ddResVal]),
            "key", 'pie.ddFPS', 'gFPS')
    combo['FPS'].set_active(0)

  ### GTK dropdown functions   #TODO1
  def ddWB(self,xxx):
    global ddWBtext, combo
    text = combo['WB'].get_active_text()
    if text is not None:
      ddWBtext = text
      print("\n\t\tWhite Balance = %s" % text)
    else:
      print() 
  
  def ddCam(self, xxx):
    global ddCamVal, combo, a
    a = a+1
    text = combo['cam'].get_active_text()
    print('\nexpecting selected camera---->', text)
    if text is not None:
      if ddCamVal != int(text.split()[0]):
        ddCamVal = int(text.split()[0])
        print("\n\t\tCamera Requested = %s" % text)
      self.DDBuildFmt()

  def ddFmt(self, xxx):
    global ddFmtVal, combo, b
    text = combo['fmt'].get_active_text()
    de()
    if text is not None:
      b = b + 1
      print("\n\t\tPixel Format Requested = %s" % text)
      if ddFmtVal != text:
        ddFmtVal = text
      print('\tb -- > :', a,b,c,d)
      self.DDBuildRes()

  def ddRes(self, xxx):
    global ddResVal, meta, combo, c
    text = combo['res'].get_active_text()
    if text is not None:
      c = c + 1
      print('expecting--> camRes : ', text)
      #if ddResVal != text:
      w, h = text.split('x')
      meta['width'], meta['height'] = (int(w), int(h))
      ddResVal = text
      print("\n\t\tResolution Requested = %s" % text)
      print('\tc -- > :',a,b,c,d)
      self.DDBuildFPS()

  def ddFPS(self, xxx):
    global ddFPSval, combo, d, cblock
    text = combo['FPS'].get_active_text()
    print('\nexpecting selected FPS---->', text)
    if text is not None:
      d = d + 1
      fText = float(text)
      if ddFPSval != fText:
        ddFPSval = fText
        meta['fps'] = fText
        print("\n\t\tFrameRate Requested = %s" % text)
      print('\td -- > :',a,b,c,d)
      cap(ddCamVal)
      #time.sleep(.5)
      #self.vMain.resize(1,1)
      #print('\n\n\n\n',self.vMain.get_allocation().width)
      #print(self.vPort.get_allocation().width)
      #print(self.vGrid.get_allocation().width)
      #print(self.viewer.get_allocation().width,'\n\n')


  def viewerDisplay(self):
    while True:
      if viewerOn:
        st = perf_counter()
        if frameArray[0] is not None:
          frame = wb_dict[ddWBtext](frameArray[0])
          #pixbuf resize
          #pixbuf = pixbuf.scale_simple(desired_width, desired_height, gtk.gdk.INTERP_BILINEAR)
          #or use numpy resize
          GLib.idle_add(self.viewer.set_from_pixbuf,np2pixbuf(frame))
          a = 1/float(meta['fps'])-(perf_counter()-st)
          if a > 0:
            time.sleep(a)
          else:
            time.sleep(.1)
        else:
          time.sleep(.5)
        vMain.resize(1,800)

  #############################################################################
  def main(self):
    global combo, frameArray, meta, inFrame
    
    inFrame = cv2.imread('banner.640.480.png')
    # !!!  After Camera Select
    frameArray = deque([inFrame], maxlen=(int(meta['fps']*30)))


    threadFrameGrabber = Thread(target=frameThread, daemon=True)
    threadFrameGrabber.start()

    self.windowMain = self.builder.get_object('vMain')
    self.windowMain.show()

    threadFrameViewer = threading.Thread(target=self.viewerDisplay, daemon=True)
    threadFrameViewer.start()
    Gtk.main()



def frameThread():
  global inFrame, frameArray, meta
  while True:
    if grabberOn:
      startTime = perf_counter()
      poll = ffmpegDecode.poll()
      # Is process alive
      if poll is None:
        inFrame = readFrameAsNp(ffmpegDecode, meta['height'], meta['width'])
        # Is their data in frame
        if inFrame is not None:
          frameArray.appendleft(inFrame)
      endTime = perf_counter()


if __name__ == "__main__":
  viewerOn = True
  grabberOn = True
  app = WindowMain()
  app.main()
  ffmpegDecode.terminate()



