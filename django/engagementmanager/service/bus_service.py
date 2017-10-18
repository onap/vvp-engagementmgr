#  
# ============LICENSE_START========================================== 
# org.onap.vvp/engagementmgr
# ===================================================================
# Copyright © 2017 AT&T Intellectual Property. All rights reserved.
# ===================================================================
#
# Unless otherwise specified, all software contained herein is licensed
# under the Apache License, Version 2.0 (the “License”);
# you may not use this software except in compliance with the License.
# You may obtain a copy of the License at
#
#             http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
#
#
# Unless otherwise specified, all documentation contained herein is licensed
# under the Creative Commons License, Attribution 4.0 Intl. (the “License”);
# you may not use this documentation except in compliance with the License.
# You may obtain a copy of the License at
#
#             https://creativecommons.org/licenses/by/4.0/
#
# Unless required by applicable law or agreed to in writing, documentation
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# ============LICENSE_END============================================
#
# ECOMP is a trademark and service mark of AT&T Intellectual Property.
from engagementmanager.bus.handlers.service_bus_base_handler import ServiceBusBaseHandler

from engagementmanager.utils.vvp_exceptions import VvpGeneralException


class BusService:
    handlers_pairs = []

    def __init__(self):
        pass

    def register(self, handler, message_type):
        if not isinstance(handler, ServiceBusBaseHandler):
            raise VvpGeneralException("You can't register handler which is not from type of ServiceBusBaseHandler")

        handler_pair = self.__get_or_create_handler_pair(message_type)
        handler_pair["handlers"].append(handler)

    def send_message(self, message):
        handler_pair = self.__get_or_create_handler_pair(type(message))

        for handler in handler_pair["handlers"]:
            handler.validate_message(message)
            handler.handle_message(message)

    def __get_or_create_handler_pair(self, message_type):
        result = None
        for handler_pair in self.handlers_pairs:
            if handler_pair["type"] == message_type:
                result = handler_pair
                break

        if result is None:
            result = {"type": message_type, "handlers": []}
            self.handlers_pairs.append(result)

        return result
