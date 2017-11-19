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
from rest_framework.response import Response
from rest_framework.views import exception_handler
from engagementmanager.utils.exception_message_factory import \
    ExceptionMessageFactory
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


def ice_exception_handler(exc, context):
    """
    our own exception handler so we will catch every exception \
    occurred in rest and print it's stack into log
    :param exc: The exception
    :param context: The context which the exception occurred in.
    """
    response = exception_handler(exc, context)

    if exc is not None:
        message_factory = ExceptionMessageFactory()
        exception_msg_obj = message_factory.get_exception_message(exc)
        data = {'detail': exception_msg_obj['msg']}

        if exception_msg_obj['include_exception']:
            data['detail'] += str(exc)
        if 'include_additional_exc_str' in exception_msg_obj and \
                exception_msg_obj['include_additional_exc_str']:
            data['exception_message'] = str(exc)

        response = Response(data, status=exception_msg_obj['status'])

        logger.error("General exception occurred in rest framework: %s", exc)
        logger.debug(
            "***************************************************************")
        logger.debug(traceback.format_exc())
        logger.debug(
            "***************************************************************")

    return response
