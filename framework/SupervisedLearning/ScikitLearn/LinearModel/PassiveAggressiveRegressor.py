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
  Passive Aggressive Regressor

"""
#Internal Modules (Lazy Importer)--------------------------------------------------------------------
#Internal Modules (Lazy Importer) End----------------------------------------------------------------

#External Modules------------------------------------------------------------------------------------
#External Modules End--------------------------------------------------------------------------------

#Internal Modules------------------------------------------------------------------------------------
from SupervisedLearning.ScikitLearn import ScikitLearnBase
from utils import InputData, InputTypes
#Internal Modules End--------------------------------------------------------------------------------

class PassiveAggressiveRegressor(ScikitLearnBase):
  """
    Passive Aggressive Regressor
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
    import sklearn.linear_model
    self.model = sklearn.linear_model.PassiveAggressiveRegressor

  @classmethod
  def getInputSpecification(cls):
    """
      Method to get a reference to a class that specifies the input data for
      class cls.
      @ In, cls, the class for which we are retrieving the specification
      @ Out, inputSpecification, InputData.ParameterInput, class to use for
        specifying input of cls.
    """
    specs = super(PassiveAggressiveRegressor, cls).getInputSpecification()
    specs.description = r"""The \xmlNode{PassiveAggressiveRegressor}
                        is a a regression algorithm similar to the Perceptron algorithm
                        but with a regularization parameter C.
                        \\The passive-aggressive algorithms are a family of algorithms for
                        large-scale learning.
                        \zNormalizationPerformed{PassiveAggressiveRegressor}
                        """
    specs.addSub(InputData.parameterInputFactory("C", contentType=InputTypes.FloatType,
                                                 descr=r"""Maximum step size (regularization).""", default=1.0))
    specs.addSub(InputData.parameterInputFactory("fit_intercept", contentType=InputTypes.BoolType,
                                                 descr=r"""Whether the intercept should be estimated or not. If False,
                                                  the data is assumed to be already centered.""", default=True))
    specs.addSub(InputData.parameterInputFactory("max_iter", contentType=InputTypes.IntegerType,
                                                 descr=r"""The maximum number of passes over the training data (aka epochs).""", default=1000))
    specs.addSub(InputData.parameterInputFactory("tol", contentType=InputTypes.FloatType,
                                                 descr=r"""The stopping criterion.""", default=1e-3))
    specs.addSub(InputData.parameterInputFactory("epsilon", contentType=InputTypes.FloatType,
                                                 descr=r"""If the difference between the current prediction and the
                                                 correct label is below this threshold, the model is not updated.""",
                                                 default=0.1))
    specs.addSub(InputData.parameterInputFactory("early_stopping", contentType=InputTypes.BoolType,
                                                 descr=r"""hether to use early stopping to terminate training when validation score is not
                                                 improving. If set to True, it will automatically set aside a stratified fraction of training
                                                 data as validation and terminate training when validation score is not improving by at least
                                                 tol for n_iter_no_change consecutive epochs.""", default=False))
    specs.addSub(InputData.parameterInputFactory("validation_fraction", contentType=InputTypes.FloatType,
                                                 descr=r"""The proportion of training data to set aside as validation set for early stopping.
                                                 Must be between 0 and 1. Only used if early_stopping is True.""", default=0.1))
    specs.addSub(InputData.parameterInputFactory("n_iter_no_change", contentType=InputTypes.IntegerType,
                                                descr=r"""Number of iterations with no improvement to wait before early stopping.""", default=5))
    specs.addSub(InputData.parameterInputFactory("shuffle", contentType=InputTypes.BoolType,
                                                 descr=r"""Whether or not the training data should be shuffled after each epoch.""", default=True))
    specs.addSub(InputData.parameterInputFactory("loss", contentType=InputTypes.makeEnumType("loss", "lossType",['epsilon_insensitive', ' squared_epsilon_insensitive']),
                                                 descr=r"""The loss function to be used: epsilon_insensitive: equivalent to PA-I.
                                                 squared_epsilon_insensitive: equivalent to PA-II.""", default='epsilon_insensitive'))
    specs.addSub(InputData.parameterInputFactory("random_state", contentType=InputTypes.IntegerType,
                                                 descr=r"""Used to shuffle the training data, when shuffle is set to
                                                 True. Pass an int for reproducible output across multiple function calls.""",
                                                 default=None))
    specs.addSub(InputData.parameterInputFactory("verbose", contentType=InputTypes.IntegerType,
                                                 descr=r"""The verbosity level""", default=0))
    specs.addSub(InputData.parameterInputFactory("warm_start", contentType=InputTypes.BoolType,
                                                 descr=r"""When set to True, reuse the solution of the previous call
                                                 to fit as initialization, otherwise, just erase the previous solution.""", default=False))
    specs.addSub(InputData.parameterInputFactory("average", contentType=InputTypes.BoolType,
                                                 descr=r"""When set to True, computes the averaged SGD weights and
                                                 stores the result in the coef_ attribute. """, default=False))
    return specs

  def _handleInput(self, paramInput):
    """
      Function to handle the common parts of the distribution parameter input.
      @ In, paramInput, ParameterInput, the already parsed input.
      @ Out, None
    """
    super()._handleInput( paramInput)
    settings, notFound = paramInput.findNodesAndExtractValues(['C','fit_intercept','max_iter',
                                                               'tol','early_stopping','validation_fraction',
                                                               'n_iter_no_change','shuffle','loss', 'epsilon',
                                                               'random_state', 'verbose', 'warm_start', 'average'])
    # notFound must be empty
    assert(not notFound)
    self.initializeModel(settings)
