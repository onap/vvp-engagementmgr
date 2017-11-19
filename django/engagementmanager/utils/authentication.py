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
from itsdangerous import URLSafeTimedSerializer
from rest_framework_jwt.settings import api_settings
from rest_framework_jwt.utils import jwt_decode_handler
from engagementmanager.models import IceUserProfile
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


def ice_jwt_decode_handler(token):
    decoded_dict = jwt_decode_handler(token)
    email = decoded_dict.get('email', None)
    user = IceUserProfile.objects.get(email=email)
    request_data_mgr.clear_old_request_data()
    request_data_mgr.set_user(user)
    return decoded_dict


class JWTAuthentication(object):
    """
    Simple token based authentication.
    Clients should authenticate by passing the token key in the
    "Authorization" HTTP header, prepended with the string "Token ".
    For example: Authorization: Token 401f7ac837da42b97f613d789819ff93537bee6a
    """

    def create_token(self, user_data):
        jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
        jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER

        payload = jwt_payload_handler(user_data)
        token = jwt_encode_handler(payload)
        return token

    def create_reset_password_token(self, user_data):
        """
        Create token for reset password flow.
        """
        encryptor = URLSafeTimedSerializer(api_settings.JWT_SECRET_KEY)
        return encryptor.dumps(user_data.email,
                               salt=api_settings.JWT_SECRET_KEY)

    def decode_reset_password_token(self, token):
        """
        Decoded the token created at reset password flow and
        return what was encrypted.
        """
        decryptor = URLSafeTimedSerializer(api_settings.JWT_SECRET_KEY)
        email = decryptor.loads(
            token,
            salt=api_settings.JWT_SECRET_KEY,
            max_age=3600
        )

        return email
