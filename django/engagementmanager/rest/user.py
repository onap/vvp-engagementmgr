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
import uuid

from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.template.loader import get_template
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR

from engagementmanager import mail
from engagementmanager.decorator.auth import auth
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.models import IceUserProfile, Vendor
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.serializers import ThinIceUserProfileModelSerializer
from engagementmanager.service.authorization_service import Permissions
from engagementmanager.service.user_service import UserService
from engagementmanager.utils.authentication import JWTAuthentication
from engagementmanager.utils.constants import Constants
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.utils.validator import Validator
from engagementmanager.vm_integration import vm_client


@classDecorator([logFuncEntry])
class SetSsh(VvpApiView):

    def post(self, request):
        user = request_data_mgr.get_user()
        data = request.data
        if 'ssh_key' in data and data['ssh_key'] != user.ssh_public_key:
            user_service = UserService()
            user_service.validate_ssh_key(data['ssh_key'])
            user_service.setSSH(user, data['ssh_key'], 'set')
        user.save()
        vm_client.fire_event_in_bg(
            'send_ssh_key_created_or_updated_event', user)
        return Response()


@classDecorator([logFuncEntry])
class UpdatePassword(VvpApiView):

    def put(self, request):
        data = request.data
        msg = "OK"
        Validator.validatePassword(data['password'], data['confirm_password'])
        user = request_data_mgr.get_user()
        user.user.set_password(data['password'])
        user.user.temp_password = None
        user.user.save()
        self.logger.info("Reset Password finished successfully for user with uuid=" +
                         user.uuid + " Redirecting to Login")
        return Response(msg)


@classDecorator([logFuncEntry])
class SendResetPasswordInstructionMail(VvpApiView):
    permission_classes = (AllowAny,)

    def post(self, request):
        msg = "OK"
        user = None
        data = request.data

        if ('email' not in data or not data['email']):
            msg = "Email address is missing"
            self.logger.error(msg)
            return Response(msg, status=HTTP_400_BAD_REQUEST)

        Validator.validateEmail(data['email'])

        user = IceUserProfile.objects.get(email=data['email'])
        jwt_obj = JWTAuthentication()
        token = jwt_obj.create_reset_password_token(user.user)

        data['tempPassword'] = str(uuid.uuid1()).split("-")[0]
        data['login_link'] = str(
            settings.DOMAIN) + "/#/login?t=" + str(token)
        self.logger.debug(
            "The login link to reset Password: " + str(data['login_link']))

        if (user != None):
            body = get_template("{reset_pwd_template_dir}reset_pwd_instructions_mail_body.html"   .format(
                reset_pwd_template_dir=Constants.reset_pwd_template_dir))
            subject = get_template("{reset_pwd_template_dir}reset_pwd_instructions_mail_subject.html".format(
                reset_pwd_template_dir=Constants.reset_pwd_template_dir))

            user.user.temp_password = make_password(data['tempPassword'])
            user.user.save()
            user.save()

            try:
                mail.sendMail(data['email'], data, body, subject)
            except Exception as e:
                msg = "Something went wrong while trying to send reset-password mail to " + \
                    data['email'] + "\n error: " + e.message
                self.logger.error(
                    msg + " rolling back the temporary password from the DB")
                user.user.temp_password = None
                user.save()
                return Response(msg, status=HTTP_500_INTERNAL_SERVER_ERROR)
        return Response(msg)


@classDecorator([logFuncEntry])
class User(VvpApiView):

    def get(self, request):
        user = request_data_mgr.get_user()
        return Response(ThinIceUserProfileModelSerializer(user).data)

    def put(self, request):
        data_dont_save = JSONParser().parse(request)
        data = request.data
        errors_list = []
        self.validate_mandatory_fields(data, errors_list)
        user = request_data_mgr.get_user()
        user.company = Vendor.objects.get(name=data_dont_save['company'])
        user.phone_number = data['phone_number']
        user.full_name = data['full_name']
        if len(user.full_name) > 30:
            return Response("first name should be up to 30 characters", status=HTTP_400_BAD_REQUEST)

        self.handle_password_change(data, user)

        ssh_changed = self.handle_ssh_change(data, user)

        self.handle_notifications_settings_change(data, user)

        if len(errors_list) != 0:
            return Response(errors_list, status=HTTP_400_BAD_REQUEST)

        user.save()

        if ssh_changed:
            vm_client.fire_event_in_bg(
                'send_ssh_key_created_or_updated_event', user)

        userData = ThinIceUserProfileModelSerializer(user).data
        self.logger.info(
            "Account updated successfully for user with uuid=" + user.uuid)
        userData['password'] = ""
        return Response(userData)

    def handle_notifications_settings_change(self, data, user):
        if 'regular_email_updates' in data:
            user.regular_email_updates = data['regular_email_updates']
        if 'email_updates_daily_digest' in data:
            user.email_updates_daily_digest = data[
                'email_updates_daily_digest']
        if 'email_updates_on_every_notification' in data:
            user.email_updates_on_every_notification = data[
                'email_updates_on_every_notification']

    def handle_ssh_change(self, data, user):
        ssh_changed = False
        if 'ssh_key' in data and data['ssh_key'] != user.ssh_public_key:
            user_service = UserService()
            user_service.validate_ssh_key(data['ssh_key'])
            if not user.ssh_public_key:
                user_service.setSSH(user, data['ssh_key'], 'add')
            else:
                user_service.setSSH(user, data['ssh_key'], 'set')
            if data['ssh_key']:
                ssh_changed = True
        return ssh_changed

    def handle_password_change(self, data, user):
        if 'password' in data and data['password']:
            Validator.validatePassword(
                data['password'], data['confirm_password'])
            user.user.set_password(data['password'])
            user.user.save()

    def validate_mandatory_fields(self, data, errors_list):
        if ('company' not in data or not data['company'] or
            'full_name' not in data or not data['full_name'] or
            'email' not in data or not data['email'] or
                'phone_number' not in data or not data['phone_number']):
            msg = "One of the input parameters is missing. #"
            errors_list.append(msg)
            self.logger.error(msg)


@classDecorator([logFuncEntry])
class EngagementLeads(VvpApiView):

    @auth(Permissions.archive_engagement)
    def get(self, request):
        el_list = UserService().get_el_list()
        return Response(el_list)


@classDecorator([logFuncEntry])
class RGWAAccessKey(VvpApiView):

    def get(self, request):
        return Response({"rgwa_secret_key": UserService().get_user_rgwa_secret()})
