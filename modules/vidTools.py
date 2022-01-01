import os, subprocess, time, json
import ffmpeg, cv2
import numpy as np


### Functions based on ffmpeg-python video tensorflow example
def readFrameAsNp(stream, height, width):
  # Note: RGB24 == 3 bytes per pixel.
  frameSize = height * width * 3
  in_bytes = stream.stdout.read(frameSize)
  if len(in_bytes) == 0:
    frame = None
  else:
    assert len(in_bytes) == frameSize
    frame = (
      np
      .frombuffer(in_bytes, np.uint8)
      .reshape([height, width, 3])
    )
  return frame

def writeFrameAsByte(ffmpegEncode, frame):
  ffmpegEncode.stdin.write(
    frame
    .astype(np.uint8)
    .tobytes()
  )

def vid2np(in_filename):
  #f v4l2 -framerate 6 -video_size 1280x720  <-- hmm
  args = (
      ffmpeg
      .input(in_filename)
      .output('pipe:', format='rawvideo', pix_fmt='bgr24')  # bgr24 for opencv
      .global_args("-hide_banner")
      .compile()
  )
  return subprocess.Popen(args, stdout=subprocess.PIPE)

def np2vid(out_filename, fps_out, in_file, heightOut, widthOut):
  global AUDIO
  codec = 'h264'
  if AUDIO == True :
    pipeline2 = ffmpeg.input(in_file)   #  ?  should these 2 be outside
    audio = pipeline2.audio
    args = (
      ffmpeg
      .input('pipe:', format='rawvideo', pix_fmt='rgb24',
        s='{}x{}'.format(widthOut, heightOut),
        framerate=fps_out )
      .output(audio, out_filename , pix_fmt='yuv420p', **{'c:v': codec}, 
        shortest=None, acodec='copy')
      .global_args("-hide_banner")
      .overwrite_output()
      .compile()
    )
  else:
    args = (
      ffmpeg
      .input('pipe:', format='rawvideo', pix_fmt='rgb24', 
        s='{}x{}'.format(widthOut, heightOut), 
        framerate=fps_out )
      .output(out_filename , pix_fmt='yuv420p', **{'c:v': codec})
      .global_args("-hide_banner")
      .overwrite_output()
      .compile()
    )
  return subprocess.Popen(args, stdin=subprocess.PIPE)

def getMetaVideo(inputVid):
  meta = dict()
  process = subprocess.Popen(['ffmpeg', '-hide_banner', '-i', inputVid, '-y' ],
          stdout=subprocess.PIPE, stderr=subprocess.STDOUT,universal_newlines=True)

  for line in process.stdout:
    global Audio
    if ' Video:' in line:
      l_split = line.split(',')
      for segment in l_split[1:]:
        if 'fps' in segment:
          s = segment.strip().split(' ')
          fps = float(s[0])
          meta.update({'fps' : fps})
        elif 'x' in segment:
          s = segment.strip().split('x')
          width = int(s[0])
          meta.update({'width' : width})
          s2 = s[1].split(' ')
          height = int(s2[0])
          meta.update({'height' : height})
    if 'Duration:' in line:
      s = line.split(',')
      ss = s[0].split(' ')
      sss = ss[3].strip().split(':')
      if sss[0] == 'N/A':
        seconds = 0
      else:
        seconds = float(sss[0])*60*60 + float(sss[1])*60 + float(sss[2])
      meta.update({'seconds' : seconds})
    if 'Audio:' in line:
      AUDIO = True
  print(json.dumps(meta, indent=2))
  return meta

def actionCommander(pressedKey, window):
  global breakBool
  # Quit
  if pressedKey == ord('q'):
    breakBool = True
    time.sleep(1)
    quit()
  elif cv2.getWindowProperty(window,cv2.WND_PROP_VISIBLE) < 1:
    breakBool = True
    time.sleep(1)
    quit()
  # set default settings
  if pressedKey == ord('d'):
    print('--- something done ---')

##############


### This is where all the magic happens
def processFrame(frame) :
  global INCR

  win = 'ffmpeg example'
  cv2.imshow(win, frame)

  actionCommander(cv2.waitKey(1) & 0xFF, win)

  INCR += 1
  return frame



if __name__ == '__main__':
  INCR = 0
  breakBool = False
  AUDIO = False

  inputVid = '/dev/video4'
  outputVid = 'output.ffmpeg.mp4'
  
  meta = getMetaVideo(inputVid)
  
  ffmpegDecode = vid2np(inputVid)
  ffmpegEncode = np2vid(outputVid, meta['fps'], inputVid, meta['height'], meta['width'])
  
  while breakBool == False:
    timeMark = time.process_time()
    inFrame = readFrameAsNp(ffmpegDecode, meta['height'], meta['width'])
    if inFrame is None:
      break

    outFrame = processFrame(inFrame)
    print(INCR)
    writeFrameAsByte(ffmpegEncode, outFrame)

  ffmpegDecode.wait()

  #Waiting for ffmpegEncode
  ffmpegEncode.stdin.close()
  ffmpegEncode.wait()

