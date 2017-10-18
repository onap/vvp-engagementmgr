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
import json

from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.models import IceUserProfile
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.service.login_service import LoginSvc
from engagementmanager.utils.authentication import JWTAuthentication


@classDecorator([logFuncEntry])
class Login(VvpApiView):
    permission_classes = (AllowAny,)

    def post(self, request, param):
        data = request.data
        jwt_obj = JWTAuthentication()
        msg = ""
        user_profile = IceUserProfile.objects.get(email=data['email'])
        login_svc = LoginSvc()

        reset_password_param = None
        if param:
            reset_password_param = param

        reset_password_email, is_reset_pwd_flow = login_svc.identify_reset_password(jwt_obj, reset_password_param)

        if not user_profile.user.is_active:
            msg = login_svc.render_user_not_active_message(data['email'])
        else:
            if is_reset_pwd_flow:
                msg = login_svc.reset_password(
                    reset_password_email, data['password'], msg, user_profile)
            else:
                user_profile.user.User = login_svc.authenticate_user(
                    data['email'], data['password'], msg)

            msg = login_svc.get_serialized_user_data(
                is_reset_pwd_flow, user_profile, jwt_obj, user_profile.user)

            if 'invitation' in data:
                login_svc.handle_invite_token(data, msg, user_profile)

            self.logger.debug("login has passed successfully for [email=" + data['email'] + "]")
            login_svc.update_last_login(user_profile)

        return Response(msg)
