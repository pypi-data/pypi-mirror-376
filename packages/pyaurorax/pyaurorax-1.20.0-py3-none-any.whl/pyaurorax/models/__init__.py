# Copyright 2024 University of Calgary
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
"""
Interact with various auroral models, such as the TREx Auroral Transport Model (ATM).
"""

# pull in classes
from .atm import (
    ATMForwardOutputFlags,  # noqa
    ATMInverseOutputFlags,  # noqa
    ATMForwardResult,  # noqa
    ATMInverseResult,  # noqa
)

# imports for this file
from .atm import ATMManager

__all__ = [
    "ModelsManager",
]


class ModelsManager:
    """
    The ModelsManager object is initialized within every PyAuroraX object. It acts as a way to access 
    the submodules and carry over configuration information in the super class.
    """

    def __init__(self, aurorax_obj):
        self.__aurorax_obj = aurorax_obj

        # initialize sub-modules
        self.__atm = ATMManager(self.__aurorax_obj)

    # ------------------------------------------
    # properties for submodule managers
    # ------------------------------------------
    @property
    def atm(self):
        """
        Access to the `atm` submodule from within a PyAuroraX object.
        """
        return self.__atm
