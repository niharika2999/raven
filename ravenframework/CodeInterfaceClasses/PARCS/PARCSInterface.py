# Copyright 2017 Battelle Energy Alliance, LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""
Created on Oct 25, 2022
@author: khnguy22
comments: Interface for PARCS, replacing PARCS3
"""
import os
from . import SpecificParser
from ravenframework.CodeInterfaceBaseClass import CodeInterfaceBase
from .PARCSData import PARCSData

class PARCS(CodeInterfaceBase):
  """
    PARCS Interface. Reading output from PARCS then export to csv file.
  """
  def __init__(self):
    """
      Constructor
      @ In, None
      @ Out, None
    """
    CodeInterfaceBase.__init__(self)
    self.sequence = []   # this contains the sequence that needs to be run. [parcs]
    self.outputRoot = {} # the root of the output sequences

  def _readMoreXML(self,xmlNode):
    """
      Function to read the portion of the xml input that belongs to this specialized class and initialize
      some members based on inputs.
      @ In, xmlNode, xml.etree.ElementTree.Element, Xml element node
      @ Out, None.
    """
    CodeInterfaceBase._readMoreXML(self,xmlNode)
    sequence = xmlNode.find("sequence")
    if sequence is None:
      self.sequence = ['parcs'] #may be no need
    else:
      self.sequence = [elm.strip() for elm in sequence.text.split(",")]

  def findInps(self,inputFiles):
    """
      Locates the input files required by PARCS Interface
      @ In, inputFiles, list, list of Files objects
      @ Out, inputDict, dict, dictionary containing xml and a dummy input for PARCS
    """
    inputDict = {}
    parcsData = []
    parcsPerturb = []
    parcsInput = []
    for inputFile in inputFiles:
      if inputFile.getType().strip().lower() == "parcsdata":
        parcsData.append(inputFile)
      elif inputFile.getType().strip().lower() == "input":
        parcsInput.append(inputFile)
      else:
        parcsPerturb.append(inputFile)
    if len(parcsPerturb) > 1 or len(parcsData) > 1 or len(parcsInput) >1:
      print(parcsPerturb, parcsData, parcsInput)
      raise IOError('multiple PARCS data/perturbed input files have been found. Only one for each is allowed!')
    # Check if the input is available
    if len(parcsPerturb) <1 or len(parcsData) <1:
      raise IOError('PARCSdata/perturb input file has not been found. Please recheck!')
    # add inputs
    inputDict['PARCSData'] = parcsData
    inputDict['PARCSPerturb'] = parcsPerturb
    inputDict['PARCSInput'] = parcsInput
    return inputDict


  def generateCommand(self, inputFile, executable, clargs=None, fargs=None, preExec=None):
    """
      Generate a command to run PARCS using an input with sampled variables generated by specific parser.
      Commands are a list of tuples, indicating parallel/serial and the execution command to use.
      @ In, inputFile, string, input file name
      @ In, executable, string, executable name with absolute path (e.g. /home/path_to_executable/code.exe)
      @ In, clargs, dict, optional, dictionary containing the command-line flags the user can specify in the input
        (e.g. under the node < Code >< clargstype = 0 input0arg = 0 i0extension = 0 .inp0/ >< /Code >)
      @ In, fargs, dict, optional, a dictionary containing the axuiliary input file variables the user can specify
        in the input (e.g. under the node < Code >< fargstype = 0 input0arg = 0 aux0extension = 0 .aux0/ >< /Code >)
      @ In, preExec, string, optional, a string the command that needs to be pre-executed before the actual command here defined
      @ Out, returnCommand, tuple, tuple containing the generated command. returnCommand[0] is the command to run the
        code (string), returnCommand[1] is the name of the output root
    """
    inputDict = self.findInps(inputFile)
    parcsInput = str(inputDict['PARCSInput'][0]).split()[1]
    workingDir = os.path.dirname(parcsInput)
    parcsInput = parcsInput.replace(workingDir+os.sep,'').strip() # can use getfilename() too
    executeCommand = []
    seq = self.sequence[0] # only one sequence value
    self.outputRoot[seq.lower()] = inputDict['PARCSInput'][0].getBase()
    executeCommand.append(('parallel',executable+' '+parcsInput))
    returnCommand = executeCommand, list(self.outputRoot.values())[-1]
    return returnCommand

  def createNewInput(self, currentInputFiles, origInputFiles, samplerType, **Kwargs):
    """
      Generates new perturbed input files for PARCS (perturb xml file then generate inp)
      @ In, currentInputFiles, list,  list of current input files
      @ In, origInputFiles, list, list of the original input files
      @ In, samplerType, string, Sampler type (e.g. MonteCarlo, Adaptive, etc. see manual Samplers section)
      @ In, Kwargs, dict, dictionary of parameters. In this dictionary there is another dictionary called "SampledVars"
        where RAVEN stores the variables that got sampled (e.g. Kwargs['SampledVars'] => {'var1':10,'var2':40})
      @ Out, newInputFiles, list, list of new input files (modified or not)
    """
    perturbInput = str(self.findInps(currentInputFiles)['PARCSPerturb'][0]).split()[1]
    parcsInput = str(self.findInps(currentInputFiles)['PARCSInput'][0]).split()[1]
    parcsDataInput = str(self.findInps(currentInputFiles)['PARCSData'][0]).split()[1]
    workingDir = os.path.dirname(perturbInput)
    parcsInput = parcsInput.replace(workingDir+os.sep,'').strip()
    perturbedVal = Kwargs['SampledVars']
    parcsData = SpecificParser.DataParser(parcsDataInput)
    perturb = SpecificParser.PerturbedPaser(perturbInput, workingDir, parcsInput, perturbedVal)
    perturb.generatePARCSInput(parcsData)
    return currentInputFiles

  def checkForOutputFailure(self, output, workingDir):
    """
      This method is called by the RAVEN code at the end of each run  if the return code is == 0.
      This method needs to be implemented by the codes that, if the run fails, return a return code that is 0
      This can happen in those codes that record the failure of the job (e.g. not converged, etc.) as normal termination (returncode == 0)
      Check for ERROR error in PARCS output
      @ In, workingDir, string, current working dir
      @ Out, failure, bool, True if the job is failed, False otherwise
    """
    failure = False
    badWords  = ['ERROR']
    try:
      outputToRead = open(os.path.join(workingDir,'PATHS_message.out'),"r")
    except:
      return True
    readLines = outputToRead.readlines()
    for badMsg in badWords:
      if any(badMsg in x for x in readLines[-20:]):
        failure = True
    outputToRead.close()
    return failure

  def finalizeCodeOutput(self, command, output, workingDir):
    """
      This method converts the PARCS outputs into a RAVEN compatible CSV file
      @ In, command, string, the command used to run the just ended job
      @ In, output, string, the Output name root
      @ In, workingDir, string, current working dir
      @ Out, None
    """
    for _, val in self.outputRoot.items():
      if val is not None:
        depletionFile = os.path.join(workingDir,val+'.inp.dep')
        pinpowerFile = os.path.join(workingDir,val+'.inp.pin')
        outputParser = PARCSData(depletionFile, pinpowerFile)
        outputParser.writeCSV(os.path.join(workingDir,output+".csv"))