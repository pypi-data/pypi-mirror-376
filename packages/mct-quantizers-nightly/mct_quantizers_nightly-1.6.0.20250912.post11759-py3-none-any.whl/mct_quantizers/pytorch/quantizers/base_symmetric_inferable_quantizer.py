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
from typing import List

import numpy as np

from mct_quantizers.common.base_inferable_quantizer import mark_quantizer, QuantizerID
from mct_quantizers.common.constants import FOUND_TORCH
from mct_quantizers.common.quant_info import QuantizationMethod

if FOUND_TORCH:
    from mct_quantizers.pytorch.quantizers.base_pytorch_inferable_quantizer import BasePyTorchInferableQuantizer


    @mark_quantizer(quantization_target=None,
                    quantization_method=[QuantizationMethod.SYMMETRIC],
                    identifier=QuantizerID.INFERABLE)
    class BaseSymmetricInferableQuantizer(BasePyTorchInferableQuantizer):

        def __init__(self,
                     num_bits: int,
                     threshold: List[float],
                     signed: bool):
            """
            Initialize the quantizer with the specified parameters.

            Args:
                num_bits: number of bits to use for quantization
                threshold: threshold for quantizing weights
                signed: whether or not to use signed quantization
            """

            super(BaseSymmetricInferableQuantizer, self).__init__()

            assert isinstance(threshold, list), f'Threshold is expected to be a list, but is of type {type(threshold)}'

            self.signed = signed
            self.threshold_np = np.asarray(threshold)
            self.num_bits = num_bits

            if signed:
                self.min_quantized_domain = -2 ** (num_bits - 1)
                self.max_quantized_domain = 2 ** (num_bits - 1) - 1
                self.scales = self.threshold_np / 2 ** (num_bits - 1)
            else:
                self.min_quantized_domain = 0
                self.max_quantized_domain = (2 ** num_bits) - 1
                self.scales = self.threshold_np / 2 ** num_bits



else:
    class BaseSymmetricInferableQuantizer:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            raise Exception('Installing torch is mandatory '
                            'when using BaseSymmetricInferableQuantizer. '
                            'Could not find torch package.')
