# Copyright 2023 Sony Semiconductor Israel, Inc. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================

from mct_quantizers.pytorch.quantizers.base_quantizer_autograd_function import BaseQuantizerAutogradFunction


class BaseWeightQuantizerAutogradFunction(BaseQuantizerAutogradFunction):
    """
    Custom autograd function for weights quantizer.
    It provides a way to define a custom forward and symbolic operation
    and currently does not implement a backward operation.
    """

    @staticmethod
    def is_signed():
        return True
