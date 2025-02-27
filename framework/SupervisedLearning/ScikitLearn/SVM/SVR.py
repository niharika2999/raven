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
  Created on Jan 21, 2020

  @author: alfoa, wangc
  Support Vector Regression

"""
#Internal Modules (Lazy Importer)--------------------------------------------------------------------
from utils.importerUtils import importModuleLazy
#Internal Modules (Lazy Importer) End----------------------------------------------------------------

#External Modules------------------------------------------------------------------------------------
np = importModuleLazy("numpy")
import ast
#External Modules End--------------------------------------------------------------------------------

#Internal Modules------------------------------------------------------------------------------------
from SupervisedLearning.ScikitLearn import ScikitLearnBase
from utils import utils
from utils import InputData, InputTypes
#Internal Modules End--------------------------------------------------------------------------------

class SVR(ScikitLearnBase):
  """
    Support Vector Regressor
  """
  info = {'problemtype':'regression', 'normalize':True}

  def __init__(self):
    """
      Constructor that will appropriately initialize a supervised learning object
      @ In, None
      @ Out, None
    """
    super().__init__()
    import sklearn
    import sklearn.svm
    self.model = sklearn.svm.SVR

  @classmethod
  def getInputSpecification(cls):
    """
      Method to get a reference to a class that specifies the input data for
      class cls.
      @ In, cls, the class for which we are retrieving the specification
      @ Out, inputSpecification, InputData.ParameterInput, class to use for
        specifying input of cls.
    """
    specs = super(SVR, cls).getInputSpecification()
    specs.description = r"""The \xmlNode{SVR} \textit{Support Vector Regression} is an epsilon-Support Vector Regression.
                            The free parameters in this model are C and epsilon. The implementations is a based on libsvm.
                            The implementation is based on libsvm. The fit time complexity
                            is more than quadratic with the number of samples which makes it hard
                            to scale to datasets with more than a couple of 10000 samples.
                            \zNormalizationPerformed{SVR}
                            """
    # penalty
    specs.addSub(InputData.parameterInputFactory('C', contentType=InputTypes.FloatType,
                                                 descr=r"""Regularization parameter. The strength of the regularization is inversely
                                                           proportional to C.
                                                           Must be strictly positive. The penalty is a squared l2 penalty..""", default=1.0))
    specs.addSub(InputData.parameterInputFactory("kernel", contentType=InputTypes.makeEnumType("kernel", "kernelType",['linear','poly',
                                                                                                                       'rbf','sigmoid']),
                                                 descr=r"""Specifies the kernel type to be used in the algorithm. It must be one of
                                                            ``linear'', ``poly'', ``rbf'' or ``sigmoid''.""", default='rbf'))
    specs.addSub(InputData.parameterInputFactory("degree", contentType=InputTypes.IntegerType,
                                                 descr=r"""Degree of the polynomial kernel function ('poly').Ignored by all other kernels.""",
                                                 default=3))
    specs.addSub(InputData.parameterInputFactory("gamma", contentType=InputTypes.FloatType,
                                                 descr=r"""Kernel coefficient for ``poly'', ``rbf'' or ``sigmoid''. If not input, then it uses
                                                           $1 / (n_features * X.var())$ as value of gamma""", default="scale"))
    specs.addSub(InputData.parameterInputFactory("coef0", contentType=InputTypes.FloatType,
                                                 descr=r"""Independent term in kernel function""", default=0.0))
    specs.addSub(InputData.parameterInputFactory("tol", contentType=InputTypes.FloatType,
                                                 descr=r"""Tolerance for stopping criterion""", default=1e-3))
    specs.addSub(InputData.parameterInputFactory("cache_size", contentType=InputTypes.FloatType,
                                                 descr=r"""Size of the kernel cache (in MB)""", default=200.))
    specs.addSub(InputData.parameterInputFactory("epsilon", contentType=InputTypes.FloatType,
                                                 descr=r"""Epsilon in the epsilon-SVR model. It specifies the epsilon-tube
                                                           within which no penalty is associated in the training loss function
                                                           with points predicted within a distance epsilon from the actual
                                                           value.""", default=0.1))
    specs.addSub(InputData.parameterInputFactory("shrinking", contentType=InputTypes.BoolType,
                                                 descr=r"""Whether to use the shrinking heuristic.""", default=True))
    specs.addSub(InputData.parameterInputFactory("max_iter", contentType=InputTypes.IntegerType,
                                                 descr=r"""Hard limit on iterations within solver.``-1'' for no limit""", default=-1))
    specs.addSub(InputData.parameterInputFactory("verbose", contentType=InputTypes.BoolType,
                                                 descr=r"""Enable verbose output. Note that this setting takes advantage
                                                 of a per-process runtime setting in libsvm that, if enabled, may not
                                                 work properly in a multithreaded context.""", default=False))
    return specs

  def _handleInput(self, paramInput):
    """
      Function to handle the common parts of the distribution parameter input.
      @ In, paramInput, ParameterInput, the already parsed input.
      @ Out, None
    """
    super()._handleInput(paramInput)
    settings, notFound = paramInput.findNodesAndExtractValues(['C', 'kernel', 'degree', 'gamma', 'coef0',
                                                             'tol', 'cache_size', 'epsilon', 'shrinking', 'max_iter',
                                                             'verbose'])
    # notFound must be empty
    assert(not notFound)
    self.initializeModel(settings)
