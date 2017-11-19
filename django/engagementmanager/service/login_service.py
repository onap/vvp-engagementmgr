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
import bleach
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from rest_framework.exceptions import NotAcceptable

from engagementmanager.models import Invitation, VF
from engagementmanager.serializers import ThinIceUserProfileModelSerializer
from engagementmanager.service.base_service import BaseSvc
from engagementmanager.service.invite_service import markInvitationAsAccepted
from engagementmanager.utils.vvp_exceptions import VvpConflict
from engagementmanager.utils.validator import logEncoding
from engagementmanager.views_helper import addUsersToEngTeam
from engagementmanager.vm_integration import vm_client


class LoginSvc(BaseSvc):

    def get_user_by_email(self, email):
        user_model = get_user_model()
        user = user_model._default_manager.get(email=email)
        return user

    def update_last_login(self, user_profile):
        user_profile.user.last_login = timezone.now()
        user_profile.user.save()
        user_profile.save()

    def authenticate_user(self, i_email, i_password, msg):
        user = authenticate(username=i_email, password=i_password)
        if not user:
            msg = "User or Password does not match"
            self.logger.error(msg)
            raise PermissionDenied(msg)
        return user

    def reset_password(self, reset_password_email, i_password,
                       msg, user_profile):
        token_user = self.get_user_by_email(reset_password_email)
        if user_profile.user.id != token_user.id:
            msg = self.render_user_conflict_message(
                user_profile.user, token_user)
        temp_encrypted_password = user_profile.user.temp_password
        is_temp_password_ok = check_password(
            i_password, temp_encrypted_password)
        if is_temp_password_ok:
            self.logger.debug(
                "Temporary Passwords match...\
                 Checking temporary password expiration")
        else:
            msg = "User or Password does not match"
            self.logger.error(msg + " in Reset Password flow")
            raise PermissionDenied(msg)
        return msg

    def render_user_conflict_message(self, user, user_from_token):
        msg = "User Conflict"
        self.logger.error(msg + ". user uuid =" + user.id +
                          ", user from token uuid=" + user_from_token.id)
        raise VvpConflict

    def render_user_not_active_message(self, i_email):
        msg = "User " + i_email + " is not active hence cannot perform login"
        self.logger.error(msg)
        msg = bleach.clean(msg, tags=['a', 'b'])
        raise NotAcceptable(msg)

    def identify_reset_password(self, jwt_obj, reset_password_param):
        email = None
        is_reset_pwd_flow = False

        if reset_password_param is not None:
            is_reset_pwd_flow = True
            self.logger.debug(
                "Reset Password flow is identified.\
                 Checking temporary password expiration. t="
                + reset_password_param)
            token_arr = reset_password_param.split("token")
            if len(token_arr) > 0:
                email = jwt_obj.decode_reset_password_token(str(token_arr[1]))
            else:
                self.logger.error(
                    "token doesn't include token prefix: "
                    + logEncoding(reset_password_param))
                is_reset_pwd_flow = False
        return email, is_reset_pwd_flow

    def handle_invite_token(self, data, user_data, user_profile):
        data['invitation'] = data['invitation'].strip()
        invitation = Invitation.objects.get(
            invitation_token=data['invitation'])
        addUsersToEngTeam(invitation.engagement_uuid, [user_profile])
        vf_obj = VF.objects.get(engagement__uuid=invitation.engagement_uuid)
        vm_client.fire_event_in_bg('send_provision_new_vf_event', vf_obj)
        user_data['eng_uuid'] = invitation.engagement_uuid
        markInvitationAsAccepted(data['invitation'])

    def get_serialized_user_data(self, is_reset_pwd_flow, user_profile,
                                 jwt_obj, user):
        user_data = ThinIceUserProfileModelSerializer(user_profile).data
        user_data['isResetPwdFlow'] = is_reset_pwd_flow
        user_data['token'] = jwt_obj.create_token(user)
        if user_profile.ssh_public_key:
            user_data['ssh_public_key'] = "exists"
        else:
            user_data['ssh_public_key'] = ""

        return user_data
