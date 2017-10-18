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
import traceback
import bleach
from rest_framework import status
from rest_framework.response import Response
from rest_framework.status import HTTP_401_UNAUTHORIZED, \
    HTTP_400_BAD_REQUEST, HTTP_500_INTERNAL_SERVER_ERROR
from engagementmanager.service.authorization_service import AuthorizationService
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


def auth(action, is_internal=False):
    """
    Check that given action is permitted by the user
    """
    def _dec(func):
        def _new_func(*args, **kwargs):
            auth_service = AuthorizationService()

            # Extract USER -  A MUST Have in KWARGS #
            user = request_data_mgr.get_user()
            if user == None:
                msg = "user couldn't be identified in the request"
                logger.error(msg)
                if (is_internal == True):
                    return msg, HTTP_400_BAD_REQUEST
                return Response(msg, status=status.HTTP_400_BAD_REQUEST)

            checklist_uuid = request_data_mgr.get_cl_uuid()
            eng_uuid = request_data_mgr.get_eng_uuid()

            try:
                result = None
                message = None
                result, message = auth_service.is_user_able_to(user, action, eng_uuid, checklist_uuid)
                logger.debug('Authorization Service : ' + action.name +
                             '. Result=' + str(result) + '. message=' + str(message))
                if result == False:
                    msg = "User not authorized: " + \
                        str(user.uuid) + ". eng_uuid=" + str(eng_uuid) + ". checklist_uuid=" + str(checklist_uuid)
                    if (is_internal == True):
                        return msg, HTTP_401_UNAUTHORIZED
                    msg = bleach.clean(msg, tags=['a', 'b'])
                    return Response(msg, status=status.HTTP_401_UNAUTHORIZED)

            except Exception as e:
                logger.error("=====================Exception=====================")
                msg = "A problem occurred while trying to authorize user.uuid= " + \
                    str(user.uuid) + ". eng_uuid=" + str(eng_uuid) + \
                    ". checklist_uuid=" + str(checklist_uuid) + "action=" + str(action)
                logger.error(str(e) + " Message: " + msg)
                logger.error(traceback.format_exc())
                logger.error("===================================================")

                if (is_internal == True):
                    return msg, HTTP_500_INTERNAL_SERVER_ERROR
                msg = "Action was failed to be performed"
                return Response(msg, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return func(*args, **kwargs)

        return _new_func

    return _dec
