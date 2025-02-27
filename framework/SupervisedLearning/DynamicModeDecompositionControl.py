
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
  Created on Oct 01, 2020

  @author: Haoyu Wang, Andrea Alfonsi

  Dynamic Mode Decomposition with Control (The class is based on the DynamicModeDecomposition class)
"""
#External Modules------------------------------------------------------------------------------------
import sys
import numpy as np
import scipy
from sklearn import neighbors
from scipy import spatial
import matplotlib.pyplot as plt
#External Modules End--------------------------------------------------------------------------------

#Internal Modules------------------------------------------------------------------------------------
from utils import mathUtils
from utils import InputData, InputTypes
from .DynamicModeDecomposition import DMD
#Internal Modules End--------------------------------------------------------------------------------

class DMDC(DMD):
  """
    This surrogate is aimed to construct a "time-dep" surrogate based on
    Dynamic Mode Decomposition with control.
    Ref. Proctor, Joshua L., Steven L. Brunton, and J. Nathan Kutz.
        "Dynamic mode decomposition with control."
        SIAM Journal on Applied Dynamical Systems 15, no. 1 (2016): 142-161.

    Updated on November 19, 2021

    @author: Haoyu Wang, Argonne National Laboratory
             Andrea Alfonsi, Idaho National Laboratory
  """
  info = {'problemtype':'regression', 'normalize':True}

  @classmethod
  def getInputSpecification(cls):
    """
      Method to get a reference to a class that specifies the input data for
      class cls.
      @ In, cls, the class for which we are retrieving the specification
      @ Out, inputSpecification, InputData.ParameterInput, class to use for
        specifying input of cls.
    """
    specs = super().getInputSpecification()
    specs.description = r"""The \xmlString{DMDC} contains a single ROM type similar to DMD, aimed to
        construct a time-dependent surrogate model based on Dynamic
        Mode Decomposition with Control (ref. \cite{proctor2016dynamic}).
        In addition to perform a ``dimensionality reduction regression'' like DMD, this surrogate will
        calculate the state-space representation matrices A, B and  C in a discrete time domain:
        \begin{itemize}
          \item $x[k+1]=A*x[k]+B*u[k]$
          \item $y[k+1]=C*x[k+1]$
        \end{itemize}

        In order to use this Reduced Order Model, the \xmlNode{ROM} attribute
        \xmlAttr{subType} needs to be set equal to \xmlString{DMDC}.
        \\
        Once the ROM  is trained (\textbf{Step} \xmlNode{RomTrainer}), its
        parameters/coefficients can be exported into an XML file
        via an \xmlNode{OutStream} of type \xmlAttr{Print}. The following variable/parameters can be exported (i.e.
        \xmlNode{what} node
        in \xmlNode{OutStream} of type \xmlAttr{Print}):
        \begin{itemize}
          \item \xmlNode{rankSVD}, see XML input specifications below
          \item \xmlNode{actuators}, XML node containing the list of actuator variables (u),
                see XML input specifications below
          \item \xmlNode{stateVariables}, XML node containing the list of system state variables (x),
                see XML input specifications below
          \item \xmlNode{initStateVariables}, XML node containing the list of system state variables
                (x\_init) that are used for initializing the model in ``evaluation'' mode,
                see XML input specifications below
          \item \xmlNode{outputs}, XML node containing the list of system output variables (y)
          \item \xmlNode{dmdTimeScale}, XML node containing the the array of time scale in the DMD space,
                which is time axis in traning data (Time)
          \item \xmlNode{UNorm}, XML node containing the norminal values of actuators,
                which are the initial actuator values in the training data
          \item \xmlNode{XNorm}, XML node containing the norminal values of state variables,
                which are the initial state values in the training data
          \item \xmlNode{XLast}, XML node containing the last value of state variables,
                which are the final state values in the training data (before nominal value subtraction)
          \item \xmlNode{YNorm}, XML node containing the norminal values of output variables,
                which are the initial output values in the training data
          \item \xmlNode{Atilde},  XML node containing the A matrix in discrete time domain
                (imaginary part, matrix shape, and real part)
          \item \xmlNode{Btilde}, XML node containing the B matrix in discrete time domain
                (imaginary part, matrix shape, and real part)
          \item \xmlNode{Ctilde}, XML node containing the C matrix in discrete time domain
                (imaginary part, matrix shape, and real part)
        \end{itemize}"""
    specs.popSub("dmdType")
    specs.addSub(InputData.parameterInputFactory("actuators", contentType=InputTypes.StringListType,
                                                 descr=r"""defines the actuators (i.e. system input parameters)
                                                  of this model. Each actuator variable (u1, u2, etc.) needs to
                                                  be listed here."""))
    specs.addSub(InputData.parameterInputFactory("stateVariables", contentType=InputTypes.StringListType,
                                                 descr=r"""defines the state variables (i.e. system variable vectors)
                                                  of this model. Each state variable (x1, x2, etc.) needs to be listed
                                                  here. The variables indicated in \xmlNode{stateVariables} must be
                                                  listed in the \xmlNode{Target} node too."""))
    specs.addSub(InputData.parameterInputFactory("initStateVariables", contentType=InputTypes.StringListType,
                                                 descr=r"""defines the state variables' ids  that should be used as
                                                  initialization variable
                                                  in the evaluation stage (for the evaluation of the model).
                                                  These variables are used for the first time step to initiate
                                                  the rolling time-step prediction of the state variables, ``exited''
                                                  by the \xmlNode{actuators} signal. The variables listed in
                                                  \xmlNode{initStateVariables} must be listed in the  \xmlNode{Features}
                                                  node too.""", default=[]))
    specs.addSub(InputData.parameterInputFactory("subtractNormUXY", contentType=InputTypes.BoolType,
                                                 descr=r"""True if the initial values need to be subtracted from the
                                                 actuators (u), state (x) and outputs (y) if any. False if the subtraction
                                                 is not needed.""", default=False))
    return specs

  def __init__(self):
    """
      DMDc constructor
    """
    super().__init__()
    self.printTag = 'DMDC'
    self.dynamicFeatures = True
    # variables filled up in the training stages
    self.__Btilde = {} # B matrix
    self.__Ctilde = {} # C matrix
    self.actuatorVals = None # Actuator values (e.g. U), the variable names are in self.ActuatorID
    self.stateVals = None # state values (e.g. X)
    self.outputVals = None # output values (e.g. Y)
    self.parameterValues = None #  parameter values

  def _handleInput(self, paramInput):
    """
      Function to handle the common parts of the model parameter input.
      @ In, paramInput, InputData.ParameterInput, the already parsed input.
      @ Out, None
    """
    super()._handleInput(paramInput)
    settings, notFound = paramInput.findNodesAndExtractValues(['actuators','stateVariables', 'initStateVariables',
                                                               'subtractNormUXY'])
    # notFound must be empty
    assert(not notFound)
    ### Extract the Actuator Variable Names (u)
    self.actuatorsID = settings.get('actuators')
    ### Extract the State Variable Names (x)
    self.stateID = settings.get('stateVariables')
    ### Extract the Initilalization State Variable Names (x). Optional. If not
    ### found, the state is initialized with the initial values in the state field
    self.initStateID = settings.get('initStateVariables')
    # whether to subtract the nominal(initial) value from U, X and Y signal for calculation
    self.dmdParams['centerUXY'] = settings.get('subtractNormUXY')
    # some checks
    # check if state ids in target
    if not (set(self.stateID) <= set(self.target)):
      self.raiseAnError(IOError,'stateVariables must also be listed among <Target> variables!')
    # check if state ids in target
    if not (set(self.initStateID) <= set(self.features)):
      self.raiseAnError(IOError,'initStateVariables must also be listed among <Features> variables!')

    ### Extract the Output Names (Output, Y)
    self.outputID = [x for x in self.target if x not in (set(self.stateID) | set([self.pivotParameterID]))]
    # check if there are parameters
    self.parametersIDs = list(set(self.features) - set(self.actuatorsID) - set(self.initStateID))

  def __trainLocal__(self,featureVals,targetVals):
    """
      Perform training on input database stored in featureVals.
      @ In, featureVals, numpy.ndarray, shape=[n_samples,n_timeStep, n_dimensions], an array of input data # Not use for ARMA training
      @ In, targetVals, numpy.ndarray, shape = [n_samples,n_timeStep, n_dimensions], an array of time series data
    """
    ### Extract the Pivot Values (Actuator, U) ###
    self.neigh = None
    if len(self.parametersIDs):
      self.parameterValues =  np.asarray([featureVals[:, :, self.features.index(par)] for par in self.parametersIDs]).T[0, :, :]
      self.neigh = neighbors.KNeighborsRegressor(n_neighbors=1)
      y = np.asarray (range(featureVals.shape[0]))
      self.neigh.fit(self.parameterValues, y)
    # self.ActuatorVals is Num_Entries*2 array, the snapshots of [u1, u2]. Shape is [n_samples, n_timesteps, n_actuators]
    self.actuatorVals = np.asarray([featureVals[:, :, self.features.index(act)] for act in self.actuatorsID]).T
    ### Extract the time marks "self.pivotValues" (discrete, in time step marks) ###
    ### the pivotValues must be all the same
    self.pivotValues = targetVals[0, :, self.target.index(self.pivotParameterID)].flatten()
    # self.outputVals is Num_Entries*2 array, the snapshots of [y1, y2]. Shape is [n_samples, n_timesteps, n_targets]
    self.outputVals =  np.asarray([targetVals[:, :,self.target.index(out)] for out in self.outputID]).T
    ### Extract the State Values (State, X) ###
    # self.outputVals is Num_Entries*2 array, the snapshots of [y1, y2]. Shape is [n_samples, n_timesteps, n_state_variables]
    self.stateVals =  np.asarray([targetVals[:, :, self.target.index(st)] for st in self.stateID]).T
    # create matrices
    self.__Atilde = np.zeros((featureVals.shape[0], len(self.stateID), len(self.stateID)))
    self.__Btilde = np.zeros((featureVals.shape[0], len(self.stateID), len(self.actuatorsID)))
    self.__Ctilde = np.zeros((featureVals.shape[0], len(self.outputID), len(self.stateID)))
    for smp in range(featureVals.shape[0]):
      X1 = (self.stateVals[:-1,smp,:]    - self.stateVals[0,smp,:]).T    if self.dmdParams['centerUXY'] else self.stateVals[:-1,smp,:].T
      X2 = (self.stateVals[1:,smp,:]     - self.stateVals[0,smp,:]).T    if self.dmdParams['centerUXY'] else self.stateVals[1:,smp,:].T
      U =  (self.actuatorVals[:-1,smp,:] - self.actuatorVals[0,smp,:]).T if self.dmdParams['centerUXY'] else self.actuatorVals[:-1,smp,:].T
      Y1 = (self.outputVals[:-1,smp,:]   - self.outputVals[0,smp,:]).T   if self.dmdParams['centerUXY'] else self.outputVals[:-1,smp,:].T
      # compute A,B,C matrices
      self.__Atilde[smp,:,:] , self.__Btilde[smp,:,:], self.__Ctilde[smp,:,:] = self._evaluateMatrices(X1, X2, U, Y1, self.dmdParams['rankSVD'])
    # Default timesteps (even if the time history is not equally spaced in time, we "trick" the dmd to think it).
    self.timeScales = dict.fromkeys( ['training','dmd'],{'t0': self.pivotValues[0], 'intervals': len(self.pivotValues[:]) - 1, 'dt': self.pivotValues[1]-self.pivotValues[0]})

  #######
  def __evaluateLocal__(self,featureVals):
    """
      This method is used to inquire the DMD to evaluate (after normalization that in
      this case is not performed)  a set of points contained in featureVals.
      a KDTree algorithm is used to construct a weighting function for the reconstructed space
      @ In, featureVals, numpy.ndarray, shape= (n_requests, n_timeStep, n_dimensions), an array of input data
      @ Out, returnEvaluation , dict, dictionary of values for each target (and pivot parameter)
    """
    indeces = [0]
    if len(self.parametersIDs):
      # extract the scheduling parameters (feats)
      feats = np.asarray([featureVals[:, :, self.features.index(par)] for par in self.parametersIDs]).T[0, :, :]
      # using nearest neighbour method to identify the index
      indeces = self.neigh.predict(feats).astype(int)
    nreqs = len(indeces)
    ### Initialize the final return value ###
    returnEvaluation = {}
    ### Extract the Actuator signal U ###
    uVector = []
    for varID in self.actuatorsID:
      varIndex = self.features.index(varID)
      uVector.append(featureVals[:, :, varIndex]) # uVector is a list now
      returnEvaluation.update({varID: featureVals[:, :, varIndex] if nreqs > 1 else featureVals[:, :, varIndex].flatten()})
    uVector = np.asarray(uVector) # the uVector is not centralized yet
    # Get the time steps for evaluation
    tsEval = uVector.shape[-1] # ts_Eval = 100

    ### Extract the initial state vector shape(n_requests,n_stateID)
    initStates = np.asarray([featureVals[:, :, self.features.index(par)] for par in self.initStateID]).T[0, :, :]
    # Initiate the evaluation array for evalX and evalY
    evalX = np.zeros((len(indeces), tsEval, len(self.initStateID)))
    evalY = np.zeros((len(indeces), tsEval, len(self.outputID)))

    for cnt, index in enumerate(indeces):
      # Centralize uVector and initState when required.
      if self.dmdParams['centerUXY']:
        uVector = uVector - self.actuatorVals[0, index, :]
        initStates = initStates - self.stateVals[0, index, :]
      evalX[cnt, 0, :] = initStates
      evalY[cnt, 0, :] = np.dot(self.__Ctilde[index, :, :], evalX[cnt, 0, :])
      ### perform the self-propagation of X, X[k+1] = A*X[k] + B*U[k] ###
      for i in range(tsEval-1):
        xPred = np.reshape(self.__Atilde[index,:,:].dot(evalX[cnt,i,:]) + self.__Btilde[index,:,:].dot(uVector[cnt,:,i]),(-1,1)).T
        evalX[cnt, i+1, :] = xPred
        evalY[cnt, i+1, :] = np.dot(self.__Ctilde[index,:,:], evalX[cnt,i+1,:])
      # De-Centralize evalX and evalY when required.
      if self.dmdParams['centerUXY']:
        evalX = evalX + self.stateVals[0, index, :]
        evalY = evalY + self.outputVals[0, index, :]
    ### Store the results to the dictionary "returnEvaluation"
    for varID in self.stateID:
      varIndex = self.stateID.index(varID)
      returnEvaluation.update({varID: evalX[: , :, varIndex] if nreqs > 1 else evalX[: , :, varIndex].flatten()})
    for varID in self.outputID:
      varIndex = self.outputID.index(varID)
      returnEvaluation.update({varID: evalY[: , :, varIndex] if nreqs > 1 else evalY[: , :, varIndex].flatten()})

    returnEvaluation[self.pivotParameterID] = np.asarray([self.pivotValues] * nreqs) if nreqs > 1 else self.pivotValues
    return returnEvaluation

  def writeXMLPreamble(self, writeTo, targets = None):
    """
      Specific local method for printing anything desired to xml file at the begin of the print.
      @ In, writeTo, xmlUtils.StaticXmlElement instance, element to write to
      @ In, targets, list, list of targets for whom information should be written.
      @ Out, None
    """
    # add description
    super().writeXMLPreamble
    if not self.amITrained:
      self.raiseAnError(RuntimeError,'ROM is not yet trained!')
    description  = ' This XML file contains the main information of the DMDC ROM.'
    description += ' The method is explained in:'
    description += ' Proctor, Joshua L., Steven L. Brunton, and J. Nathan Kutz. '
    description += ' "Dynamic mode decomposition with control." '
    description += ' SIAM Journal on Applied Dynamical Systems 15, no. 1 (2016): 142-161.'
    writeTo.addScalar('ROM',"description",description)

  def writeXML(self, writeTo, targets = None, skip = None):
    """
      Adds requested entries to XML node.
      @ In, writeTo, xmlTuils.StaticXmlElement, element to write to
      @ In, targets, list, optional, list of targets for whom information should be written
      @ In, skip, list, optional, list of targets to skip
      @ Out, None
    """

    if skip is None: # skip =  None
      skip = []

    what = ['dmdType','rankSVD','acturators',
            'stateVariables','outputs','initStateVariables',
            'Atilde','Btilde','Ctilde','UNorm','XNorm','YNorm',
            'XLast','dmdTimeScale']

    if targets is None: # targets = None
      readWhat = what
    else:
      readWhat = targets

    for s in skip: # skip is empty, so nothing to skip
      if s in readWhat:
        readWhat.remove(s) # "readWhat" remains unchanged.

    if not set(readWhat) <= set(what): # when "readWhat" contains something outside of "what", raise error
      self.raiseAnError(IOError, "The following variables specified in <what> node are not recognized: "+ ",".join(np.setdiff1d(readWhat, what).tolist()) )
    else:
      what = readWhat

    target = 'DMDcModel'

    toAdd = ['dmdType','rankSVD']
    self.dmdParams['rankSVD'] = self.dmdParams['rankSVD'] if self.dmdParams['rankSVD'] is not None else -1

    for add in toAdd: # toAdd = ['dmdType','rankSVD']
      if add in what :
        writeTo.addScalar(target,add,self.dmdParams[add])

    targNode = writeTo._findTarget(writeTo.getRoot(), target)
    if "acturators" in what:
      writeTo.addScalar(target, "acturators", ' '.join(self.actuatorsID))
    if "stateVariables" in what:
      writeTo.addScalar(target, "stateVariables", ' '.join(self.stateID))
    if "initStateVariables" in what:
      writeTo.addScalar(target, "initStateVariables", ' '.join(self.initStateID))
    if "outputs" in what:
      writeTo.addScalar(target, "outputs", ' '.join(self.outputID))
    if "dmdTimeScale" in what:
      writeTo.addScalar(target,"dmdTimeScale",' '.join(['%.3d' % elm for elm in self._getTimeScale()]))

    for smp in range(self.stateVals.shape[1]):
      attributeDict = {}
      if len(self.parametersIDs):
        attributeDict = {self.parametersIDs[index]:'%.6e' % self.parameterValues[smp,index] for index in range(len(self.parametersIDs))}
      attributeDict["sample"] = str(smp)

      if "UNorm" in what and self.dmdParams['centerUXY']:
        valCont = " ".join(['%.8e' % elm for elm in self.actuatorVals[0, smp, :].T.flatten().tolist()])
        writeTo.addVector("UNorm","realization",valCont, root=targNode, attrs=attributeDict)

      if "XNorm" in what and self.dmdParams['centerUXY']:
        valCont = " ".join(['%.8e' % elm for elm in self.stateVals[0, smp, :].T.flatten().tolist()])
        writeTo.addVector("XNorm","realization",valCont, root=targNode, attrs=attributeDict)

      if "XLast" in what:
        valCont = " ".join(['%.8e' % elm for elm in self.stateVals[-1, smp, :].T.flatten().tolist()])
        writeTo.addVector("XLast","realization",valCont, root=targNode, attrs=attributeDict)

      if "YNorm" in what and self.dmdParams['centerUXY']:
        valCont = " ".join(['%.8e' % elm for elm in self.outputVals[0, smp, :].T.flatten().tolist()])
        writeTo.addVector("YNorm","realization",valCont, root=targNode, attrs=attributeDict)

      if "Atilde" in what:
        valDict = {'real': " ".join(['%.8e' % elm for elm in self.__Atilde[smp, :, :].T.real.flatten().tolist()]),
                   'imaginary':" ".join(['%.8e' % elm for elm in self.__Atilde[smp, :, :].T.imag.flatten().tolist()]),
                   "matrixShape":",".join(str(x) for x in np.shape(self.__Atilde[smp, :, :]))}
        writeTo.addVector("Atilde","realization",valDict, root=targNode, attrs=attributeDict)

        valDict = {'real': " ".join(['%.8e' % elm for elm in self.__Btilde[smp, :, :].T.real.flatten().tolist()]),
                   'imaginary':" ".join(['%.8e' % elm for elm in self.__Btilde[smp, :, :].T.imag.flatten().tolist()]),
                   "matrixShape":",".join(str(x) for x in np.shape(self.__Btilde[smp, :, :]))}
        writeTo.addVector("Btilde","realization",valDict, root=targNode, attrs=attributeDict)

      if "Ctilde" in what and len(self.outputID) > 0:
        valDict = {'real': " ".join(['%.8e' % elm for elm in self.__Ctilde[smp, :, :].T.real.flatten().tolist()]),
                   'imaginary':" ".join(['%.8e' % elm for elm in self.__Ctilde[smp, :, :].T.imag.flatten().tolist()]),
                   "matrixShape":",".join(str(x) for x in np.shape(self.__Ctilde[smp, :, :]))}
        writeTo.addVector("Ctilde","realization",valDict, root=targNode, attrs=attributeDict)

  def _evaluateMatrices(self, X1, X2, U, Y1, rankSVD):
    """
      Evaluate the the matrices (A and B tilde)
      @ In, X1, np.ndarray, n dimensional state vectors (n*L)
      @ In, X2, np.ndarray, n dimensional state vectors (n*L)
      @ In, U, np.ndarray, m-dimension control vector by L (m*L)
      @ In, Y1, np.ndarray, m-dimension output vector by L (y*L)
      @ In, rankSVD, int, rank of the SVD
      @ Out, A, np.ndarray, the A matrix
      @ Out, B, np.ndarray, the B matrix
      @ Out, C, np.ndarray, the C matrix
    """
    n = len(X2)
    # Omega Matrix, stack X1 and U
    omega = np.concatenate((X1, U), axis=0)
    # SVD
    uTrucSVD, sTrucSVD, vTrucSVD = mathUtils.computeTruncatedSingularValueDecomposition(omega, rankSVD, False, False)
    # Find the truncation rank triggered by "s>=SminValue"
    rankTruc = sum(map(lambda x : x>=1e-6, sTrucSVD.tolist()))
    if rankTruc < uTrucSVD.shape[1]:
        uTruc = uTrucSVD[:, :rankTruc]
        vTruc = vTrucSVD[:, :rankTruc]
        sTruc = np.diag(sTrucSVD)[:rankTruc, :rankTruc]
    else:
        uTruc = uTrucSVD
        vTruc = vTrucSVD
        sTruc = np.diag(sTrucSVD)

    # QR decomp. sTruc=qsTruc*rsTruc, qsTruc unitary, rsTruc upper triangular
    qsTruc, rsTruc = np.linalg.qr(sTruc)
    # if rsTruc is singular matrix, raise an error
    if np.linalg.det(rsTruc) == 0:
      self.raiseAnError(RuntimeError, "The R matrix is singlular, Please check the singularity of [X1;U]!")
    beta = X2.dot(vTruc).dot(np.linalg.inv(rsTruc)).dot(qsTruc.T)
    A = beta.dot(uTruc[0:n, :].T)
    B = beta.dot(uTruc[n:, :].T)
    C = Y1.dot(scipy.linalg.pinv2(X1))

    return A, B, C


