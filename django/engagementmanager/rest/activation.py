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
from django.conf import settings
from django.template.loader import get_template
from django.utils import timezone
from itsdangerous import SignatureExpired
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from engagementmanager import mail
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.models import IceUserProfile
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.utils.constants import Constants
from engagementmanager.utils.vvp_exceptions import VvpObjectNotAvailable, VvpGeneralException, VvpBadRequest
from engagementmanager.views_helper import generateActivationLink, getFirstEngByUser
from engagementmanager.vm_integration import vm_client
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


@classDecorator([logFuncEntry])
class ResendActivationMail(VvpApiView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, user_uuid, format=None):
        ice_user_obj = IceUserProfile.objects.get(uuid=user_uuid)

        data = {'activation_link': generateActivationLink(ice_user_obj.user.activation_token, ice_user_obj),
                'full_name': ice_user_obj.full_name}

        # updating the activation time
        ice_user_obj.user.activation_token_create_time = timezone.now()

        ice_user_obj.save()
        self.logger.debug("Activation Link: " + data['activation_link'])

        body = get_template("{activate_template_dir}activate_mail_body.html".format(
            activate_template_dir=Constants.activate_template_dir))
        subject = get_template("{activate_template_dir}activate_mail_subject.html".format(
            activate_template_dir=Constants.activate_template_dir))
        mail.sendMail(ice_user_obj.email, data, body, subject)

        return Response()


@classDecorator([logFuncEntry])
class ActivateUser(VvpApiView):
    permission_classes = (IsAuthenticatedOrReadOnly,)

    def get(self, request, format=None, **kwargs):
        user_profile = IceUserProfile.objects.get(uuid=kwargs['uu_id'])
        user = user_profile.user
        if user is None:
            raise VvpObjectNotAvailable(
                "User's retrieved in the activation API doesn't exist.")

        if user.is_active:
            raise VvpGeneralException(
                "User's retrieved in the activation API is active.")

        if user.activation_token != kwargs['token']:
            raise VvpBadRequest(
                "User's activation token is not equal to the token in the activation path param.")

        created = user.activation_token_create_time
        current = timezone.now()
        if created.year == current.year and created.month == current.month and (created.day == current.day or
                                                                                created.day == current.day - 1):
            delta = current - created
            if abs(delta).total_seconds() / 3600.0 <= settings.TOKEN_EXPIRATION_IN_HOURS:
                user.is_active = True
                user.save()
                self.logger.debug(
                    "User " + user_profile.full_name + " is activated successfully, redirecting to Login")
                user = IceUserProfile.objects.get(email=user.email)
                eng = getFirstEngByUser(user)
                result = {'activation_success': True, }
                if eng is not None:
                    result['engagement_uuid'] = str(eng.uuid)
                vm_client.send_create_user_in_rgwa_event(user)
                return Response(result)
        else:
            raise SignatureExpired("User's activation token expired.")
        
        return Response({'activation_success': False, })
