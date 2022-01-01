#! /usr/bin/python3
import numpy as np
import cv2

if __name__ == "__main__":
  print('  --- This file just has some functions ---  ')

#10
#def matchCamNames():
#  out = subprocess.Popen(['python', 'matchCamNames.py'],
#          stdout=subprocess.PIPE,
#          stderr=subprocess.STDOUT)
#  stdout,stderr = out.communicate()
#  listAsString = stdout.decode('UTF-8)').splitlines()[-1]
#  print(listAsString)
#  listAsList = ast.literal_eval(listAsString)
#  return listAsList

# BGR-->RGB no white balance applied
def wb_none(img: np.array):
  result = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
  '''Takes a BGR image array and returns a RGB image array
  [cv2]
  '''
  return result

# BGR-->RGB w/ normalization in LAB color space
## https://stackoverflow.com/questions/46390779/automatic-white-balancing-with-grayworld-assumption
## user:norok2
def wb_npGrayworld(img: np.array):
  result = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
  avg_a = np.average(result[:, :, 1])
  avg_b = np.average(result[:, :, 2])
  result[:, :, 1] = result[:, :, 1] - ((avg_a - 128) * (result[:, :, 0] / 255.0) * 1.1)
  result[:, :, 2] = result[:, :, 2] - ((avg_b - 128) * (result[:, :, 0] / 255.0) * 1.1)
  result = cv2.cvtColor(result, cv2.COLOR_LAB2RGB)
  '''Takes a BGR image array and white balanced RGB image array
  [numpy, cv2]
  '''
  return result

# xphoto from openc-contrib
def wb_xphoto(img: np.array):
  wb = cv2.xphoto.createGrayworldWB()
  wb.setSaturationThreshold(0.99)
  bgrWB = wb.balanceWhite(img)
  result = cv2.cvtColor(bgrWB, cv2.COLOR_BGR2RGB)
  '''Takes a BGR image array and white balanced RGB image array
  [cv2[xphoto]]
  '''
  return result

