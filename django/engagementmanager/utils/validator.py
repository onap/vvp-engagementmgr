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
'''
Taken from https://pypi.python.org/pypi/validate_email
'''
import re
import bleach
from validate_email import validate_email
from engagementmanager.utils.vvp_exceptions import VvpBadRequest
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class Validator(object):

    @staticmethod
    def validateEmail(email):
        if not validate_email(email):
            msg = "email address validation error"
            logger.error(msg)
            raise KeyError(msg)

    @staticmethod
    def validatePassword(password, confirm_password=False):
        if confirm_password is not False and password != confirm_password:
            msg = "'Password' and 'Confirm Password' do not match."
            logger.error(msg)
            raise VvpBadRequest(msg)
        if len(password) < 4:
            msg = "'Password' must be more than 4 letters."
            logger.error(msg)
            raise VvpBadRequest(msg)
        if len(password) > 32:
            msg = "'Password' must be less than 32 letters"
            logger.error(msg)
            raise VvpBadRequest(msg)

    @staticmethod
    def validateCheckListName(name):
        regex_pattern = "^[a-zA-Z0-9\&\ ]*$"
        pattern = re.compile(regex_pattern)

        return pattern.match(name)


def logEncoding(data):
    try:
        clean_data = bleach.clean(str(data))
        clean_data += " (User Input)"
    except Exception as e:
        clean_data = "couldnt bleach data"
        pass
    return clean_data
