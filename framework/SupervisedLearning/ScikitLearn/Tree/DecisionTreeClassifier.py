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
  DecisionTreeClassifier
  A decision tree classifier.

"""
#Internal Modules (Lazy Importer)--------------------------------------------------------------------
#Internal Modules (Lazy Importer) End----------------------------------------------------------------

#External Modules------------------------------------------------------------------------------------
#External Modules End--------------------------------------------------------------------------------

#Internal Modules------------------------------------------------------------------------------------
from SupervisedLearning.ScikitLearn import ScikitLearnBase
from utils import InputData, InputTypes
#Internal Modules End--------------------------------------------------------------------------------

class DecisionTreeClassifier(ScikitLearnBase):
  """
    DecisionTreeClassifier
    A decision tree classifier.
  """
  info = {'problemtype':'classification', 'normalize':True}

  def __init__(self):
    """
      Constructor that will appropriately initialize a supervised learning object
      @ In, None
      @ Out, None
    """
    super().__init__()
    import sklearn
    import sklearn.tree
    self.model = sklearn.tree.DecisionTreeClassifier

  @classmethod
  def getInputSpecification(cls):
    """
      Method to get a reference to a class that specifies the input data for
      class cls.
      @ In, cls, the class for which we are retrieving the specification
      @ Out, inputSpecification, InputData.ParameterInput, class to use for
        specifying input of cls.
    """
    specs = super(DecisionTreeClassifier, cls).getInputSpecification()
    specs.description = r"""The \xmlNode{DecisionTreeClassifier} is a classifier that is based on the
                         decision tree logic.
                         \zNormalizationPerformed{DecisionTreeClassifier}
                         """
    specs.addSub(InputData.parameterInputFactory("criterion", contentType=InputTypes.makeEnumType("criterion", "criterionType",['gini','entropy']),
                                                 descr=r"""The function to measure the quality of a split. Supported criteria are ``gini'' for the
                                                 Gini impurity and ``entropy'' for the information gain.""", default='gini'))
    specs.addSub(InputData.parameterInputFactory("splitter", contentType=InputTypes.makeEnumType("splitter", "splitterType",['best','random']),
                                                 descr=r"""The strategy used to choose the split at each node. Supported strategies are ``best''
                                                 to choose the best split and ``random'' to choose the best random split.""", default='best'))
    specs.addSub(InputData.parameterInputFactory("max_depth", contentType=InputTypes.IntegerType,
                                                 descr=r"""The maximum depth of the tree. If None, then nodes are expanded until all leaves are pure
                                                 or until all leaves contain less than min_samples_split samples.""", default=None))
    specs.addSub(InputData.parameterInputFactory("min_samples_split", contentType=InputTypes.IntegerType,
                                                 descr=r"""The minimum number of samples required to split an internal node""", default=2))
    specs.addSub(InputData.parameterInputFactory("min_samples_leaf", contentType=InputTypes.IntegerType,
                                                 descr=r"""The minimum number of samples required to be at a leaf node. A split point at any
                                                 depth will only be considered if it leaves at least min\_samples\_leaf training samples in each
                                                 of the left and right branches. This may have the effect of smoothing the model, especially
                                                 in regression.""", default=1))
    specs.addSub(InputData.parameterInputFactory("min_weight_fraction_leaf", contentType=InputTypes.FloatType,
                                                 descr=r"""The minimum weighted fraction of the sum total of weights (of all the input samples)
                                                 required to be at a leaf node. Samples have equal weight when sample_weight is not provided.""", default=0.0))
    specs.addSub(InputData.parameterInputFactory("max_features", contentType=InputTypes.makeEnumType("maxFeatures", "maxFeaturesType",['auto','sqrt','log2']),
                                                 descr=r"""The strategy to compute the number of features to consider when looking for the best split:
                                                  \begin{itemize}
                                                    \item sqrt: $max\_features=sqrt(n\_features)$
                                                    \item log2: $max\_features=log2(n\_features)$
                                                    \item auto: automatic selection
                                                  \end{itemize}
                                                  \nb the search for a split does not stop until at least one valid partition of the node
                                                  samples is found, even if it requires to effectively inspect more than max_features features.""", default=None))
    specs.addSub(InputData.parameterInputFactory("max_leaf_nodes", contentType=InputTypes.IntegerType,
                                                 descr=r"""Grow a tree with max\_leaf\_nodes in best-first fashion. Best nodes are defined as relative reduction
                                                 in impurity. If None then unlimited number of leaf nodes.""", default=None))
    specs.addSub(InputData.parameterInputFactory("min_impurity_decrease", contentType=InputTypes.FloatType,
                                                 descr=r"""A node will be split if this split induces a decrease of the impurity greater than or equal to this value.
                                                 The weighted impurity decrease equation is the following:
                                                 $N\_t / N * (impurity - N\_t\_R / N\_t * right_impurity - N\_t\_L / N\_t * left\_impurity)$
                                                 where $N$ is the total number of samples, $N\_t$ is the number of samples at the current node, $N\_t\_L$ is the number
                                                 of samples in the left child, and $N\_t\_R$ is the number of samples in the right child.
                                                 $N$, $N\_t$, $N\_t]\_R$ and $N\_t\_L$ all refer to the weighted sum, if sample_weight is passed.""", default=0.0))
    # new in sklearn 0.22
    # specs.addSub(InputData.parameterInputFactory("ccp_alpha", contentType=InputTypes.FloatType,
    #                                              descr=r"""Complexity parameter used for Minimal Cost-Complexity Pruning. The subtree with the largest cost
    #                                              complexity that is smaller than ccp_alpha will be chosen. By default, no pruning is performed. """, default=0.0))
    specs.addSub(InputData.parameterInputFactory("random_state", contentType=InputTypes.IntegerType,
                                                 descr=r"""Controls the randomness of the estimator. The features are
                                                 always randomly permuted at each split, even if splitter is set to
                                                 "best". When max\_features < n\_features, the algorithm will select
                                                 max_features at random at each split before finding the best split
                                                 among them. But the best found split may vary across different runs,
                                                 even if max\_features=n\_features. That is the case, if the improvement
                                                 of the criterion is identical for several splits and one split has to
                                                 be selected at random. To obtain a deterministic behaviour during
                                                 fitting, random\_state has to be fixed to an integer.""",
                                                 default=None))
    return specs

  def _handleInput(self, paramInput):
    """
      Function to handle the common parts of the distribution parameter input.
      @ In, paramInput, ParameterInput, the already parsed input.
      @ Out, None
    """
    super()._handleInput(paramInput)
    settings, notFound = paramInput.findNodesAndExtractValues(['criterion', 'splitter', 'max_depth','min_samples_split',
                                                               'min_samples_leaf','min_weight_fraction_leaf','max_features',
                                                               'max_leaf_nodes','min_impurity_decrease',
                                                               'random_state'])
    # notFound must be empty
    assert(not notFound)
    self.initializeModel(settings)
