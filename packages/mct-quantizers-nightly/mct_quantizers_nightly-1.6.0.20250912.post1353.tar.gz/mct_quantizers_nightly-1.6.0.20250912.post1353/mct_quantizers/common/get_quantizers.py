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
from mct_quantizers.common.base_inferable_quantizer import QuantizationTarget, QuantizerID
from mct_quantizers.common.constants import QUANTIZATION_TARGET, QUANTIZATION_METHOD, QUANTIZER_ID
from mct_quantizers.common.get_all_subclasses import get_all_subclasses
from mct_quantizers.common.quant_info import QuantizationMethod
from mct_quantizers.logger import Logger


def get_inferable_quantizer_class(quant_target: QuantizationTarget,
                                  quant_method: QuantizationMethod,
                                  quantizer_base_class: type) -> type:
    """
    Searches for an inferable quantizer class that matches the requested QuantizationTarget and QuantizationMethod.
    Exactly one class should be found.

    Args:
        quant_target: QuantizationTarget value (Weights or Activation) which indicates what is the target for
            quantization to use the quantizer for.
        quant_method: A list of QuantizationMethod values to indicate all type of quantization methods that the
            quantizer supports.
        quantizer_base_class: A type of quantizer that the requested quantizer should inherit from.

    Returns: A class of a quantizer that inherits from the given quantizer_base_class.

    """
    qat_quantizer_classes = get_all_subclasses(quantizer_base_class)

    filtered_quantizers = list(filter(lambda q_class: getattr(q_class, QUANTIZATION_TARGET) == quant_target and
                                                      getattr(q_class, QUANTIZATION_METHOD) is not None and
                                                      quant_method in getattr(q_class, QUANTIZATION_METHOD) and
                                                      getattr(q_class, QUANTIZER_ID) is QuantizerID.INFERABLE,
                                      qat_quantizer_classes))

    if len(filtered_quantizers) != 1:
        Logger.error(f"Found {len(filtered_quantizers)} quantizer for target {quant_target.value} "
                     f"that matches the requested quantization method {quant_method.name} "
                     f"but there should be exactly one."
                     f"The possible quantizers that were found are {filtered_quantizers}.")

    return filtered_quantizers[0]
