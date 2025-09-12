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

from mct_quantizers.common.base_inferable_quantizer import BaseInferableQuantizer
from mct_quantizers.common.constants import FOUND_TORCH, ACTIVATION_HOLDER_QUANTIZER
from mct_quantizers.logger import Logger

if FOUND_TORCH:
    import torch

    class PytorchActivationQuantizationHolder(torch.nn.Module):
        """
        Pytorch module to hold an activation quantizer and quantize during inference.
        """
        def __init__(self,
                     activation_holder_quantizer: BaseInferableQuantizer,
                     **kwargs):
            """

            Args:
                activation_holder_quantizer: Quantizer to use during inference.
                **kwargs: Key-word arguments used by torch.nn.Module.
            """

            super(PytorchActivationQuantizationHolder, self).__init__(**kwargs)
            self.activation_holder_quantizer = activation_holder_quantizer
            self.activation_holder_quantizer.initialize_quantization(None,
                                                                     ACTIVATION_HOLDER_QUANTIZER + "_out",
                                                                     self)

        def forward(self, inputs):
            """
            Quantizes the input tensor using the activation quantizer of class PytorchActivationQuantizationHolder.

            Args:
                inputs: Input tensors to quantize with the activation quantizer.

            Returns: Output of the activation quantizer (quantized input tensor).

            """
            return self.activation_holder_quantizer(inputs)

        def convert_to_inferable_quantizers(self):
            """
            Convert a layer's quantizer to an inferable quantizer.
            Returns:
                None
            """
            if hasattr(self.activation_holder_quantizer, 'convert2inferable') and callable(
                    self.activation_holder_quantizer.convert2inferable):  # pragma: no cover
                self.activation_holder_quantizer = self.activation_holder_quantizer.convert2inferable()

else:
    class PytorchActivationQuantizationHolder:  # pragma: no cover
        def __init__(self, *args, **kwargs):
            Logger.critical('Installing Pytorch is mandatory '
                            'when using PytorchActivationQuantizationHolder. '
                            'Could not find the torch package.')  # pragma: no cover