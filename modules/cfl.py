#! /usr/bin/python3

# make dictionaries of specfice funtions from modules in 'modules' dir
##  funtion moved to main script

import os, sys

def curateFunctionLists(moduleDir):
  imports = []
  for file in os.listdir(moduleDir):
    if file.endswith(".py"):
      imports.append(file.split('.py')[0])

  modules = {}
  for x in imports:
    try:
      modules[x] = __import__(x)
      print("Successfully imported ", x, '.')
    except ImportError:
      print("Error importing ", x, '.')

  dictWB = {}  # white blance
  dictOF = {}  # other function
  for i in modules:
    for j in dir(modules[i]):
      if j.startswith('wb_'):
        dictWB.update( { j[3:] : getattr(modules[i], j )} )
      if j.startswith('of_'):
        dictOF.update( { j[3:] : getattr(modules[i], j )} )

  return dictWB, dictOF 

if __name__ == "__main__":
  moduleDir = os.path.dirname(os.path.realpath(__file__))
  sys.path.insert(1, moduleDir)
  print(curateFunctionLists(moduleDir))

