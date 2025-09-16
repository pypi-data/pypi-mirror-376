# Copyright (c) 2025 PaddlePaddle Authors. All Rights Reserved.
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

"""end2end_processing"""
from data_processor.steps.end2end_processing.args import (
    End2EndProcessorArguments,
    End2EndProcessorInferArguments,
)
from data_processor.steps.end2end_processing.processor import End2EndProcessor

__all__ = [
    "End2EndProcessor",
    "End2EndProcessorArguments",
    "End2EndProcessorInferArguments",
]
