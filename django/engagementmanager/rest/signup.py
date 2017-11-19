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
import uuid

from django.template.loader import get_template
from django.utils import timezone
from rest_framework import status
from rest_framework.parsers import JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from engagementmanager import mail
from engagementmanager.decorator.class_decorator import classDecorator
from engagementmanager.decorator.log_func_entry import logFuncEntry
from engagementmanager.models import Vendor, Engagement, Role, Invitation, \
    IceUserProfile, CustomUser
from engagementmanager.rest.vvp_api_view import VvpApiView
from engagementmanager.serializers import\
    SuperThinIceUserProfileModelSerializer
from engagementmanager.service.invite_service import markInvitationAsAccepted
from engagementmanager.service.user_service import UserService
from engagementmanager.utils.constants import Constants, Roles
from engagementmanager.utils.validator import Validator, logEncoding
from engagementmanager.views_helper import generateActivationLink, \
    createUserTemplate


@classDecorator([logFuncEntry])
class SignUp(VvpApiView):
    permission_classes = (AllowAny,)

    def post(self, request):
        data = request.data
        data_dont_save = JSONParser().parse(request)

        if ('company' not in data or not data['company'] or
            'full_name' not in data or not data['full_name'] or
            'email' not in data or not data['email'] or
            'password' not in data or not data['password'] or
            'phone_number' not in data or not data['phone_number'] or
                'regular_email_updates' not in data):
            msg = "One of the input parameters is missing"
            self.logger.error(msg)
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        Validator.validatePassword(data['password'])

        i_full_name = data['full_name']
        i_email = data['email']
        i_phone_number = data['phone_number']
        i_password = data['password']
        i_regular_email_updates = data['regular_email_updates']
        i_is_service_provider_contact = False

        add_without_confirm = False

        user_svc = UserService()

        if 'add_from_import_excel' in data:
            add_without_confirm = True

        Validator.validateEmail(i_email)

        if data_dont_save['company'] == \
                Constants.service_provider_company_name:
            i_is_service_provider_contact = True

        mailTokens = i_email.split("@")
        if mailTokens[1] not in Constants.service_provider_mail_domain and \
                i_is_service_provider_contact:
            msg = "Email address should be with service provider domain for \
            signees that their company =" + \
                Constants.service_provider_company_name
            self.logger.error(logEncoding(msg))
            return Response(msg, status=status.HTTP_400_BAD_REQUEST)

        iceuser = IceUserProfile.objects.filter(email=i_email)
        if (not iceuser.exists()):
            roleObj = Role.objects.get(
                name=Roles.standard_user.name)  # @UndefinedVariable
            activationToken = str(uuid.uuid4().hex)
            i_company = Vendor.objects.get(name=data_dont_save['company'])

            user_object = CustomUser.objects.create_user(
                username=i_email, email=i_email, password=i_password,
                activation_token=activationToken,
                activation_token_create_time=timezone.now(), is_active=False)
            info = createUserTemplate(
                i_company, i_full_name, roleObj, i_phone_number,
                i_is_service_provider_contact,
                None, i_regular_email_updates, user_object)
            newUserObj, is_profile_created = \
                IceUserProfile.objects.update_or_create(
                    email=user_object.email, defaults=info)

            self.logger.debug(
                "Creating Non activated User: " + str(newUserObj))
            userData = SuperThinIceUserProfileModelSerializer(newUserObj).data
            # If we eng_uuid and inviter_uuid is supplied it means that this
            # user was invited. We want to add them to the engagement team
            # of the inviter

            if 'invitation' in data:
                invitation = Invitation.objects.get(
                    invitation_token=data['invitation'])
                self.logger.debug(
                    "Looks like user " + i_full_name +
                    " has arrived to the sign-up page from an invite email \
                    initiated by user with uuid=" +
                    invitation.invited_by_user_uuid + ". Adding them to the \
                    inviter's engagement_team...")

                userData['eng_uuid'] = invitation.engagement_uuid
                if data["is_contact_user"] == "true":
                    engObj = Engagement.objects.get(
                        uuid=invitation.engagement_uuid)
                    engObj.contact_user = newUserObj
                    self.logger.debug(
                        "Attaching the user (" + newUserObj.full_name +
                        ") to the engagement's (" + engObj.uuid +
                        ") contact_user")
                    engObj.save()

                user_svc.addUserToEngAndFireProvisionVfSig(
                    newUserObj, invitation)

                otherInviteObj = Invitation.objects.filter(
                    accepted=False, email=i_email).exclude(
                    uuid=invitation.uuid)

                if data['is_contact_user'] == "true" or \
                        data['is_contact_user'] == "True":
                    engObj = Engagement.objects.get(
                        uuid=invitation.engagement_uuid)
                    engObj.contact_user = newUserObj
                    self.logger.debug(
                        "Attaching the user (" + newUserObj.full_name +
                        ") to the engagement's (" +
                        engObj.uuid + ") contact_user")
                    engObj.save()

                markInvitationAsAccepted(data['invitation'])
                for inviteObj in otherInviteObj:
                    user_svc.addUserToEngAndFireProvisionVfSig(
                        newUserObj, inviteObj)
                    markInvitationAsAccepted(inviteObj.invitation_token)

            if (add_without_confirm):
                newUserObj.is_active = True
                newUserObj.save()
            else:
                data['activation_link'] = generateActivationLink(
                    activationToken, newUserObj)
                self.logger.debug(
                    "Activation Link: " + data['activation_link'])

                body = get_template(
                    "{activate_template_dir}activate_mail_body.html".format(
                        activate_template_dir=Constants.activate_template_dir))
                subject = get_template(
                    "{activate_template_dir}activate_mail_subject.html".format(
                        activate_template_dir=Constants.activate_template_dir))
                mail.sendMail(i_email, data, body, subject)

            self.logger.debug(
                "sign-up has passed successfully for [email=" + i_email + "]")

            return Response(userData)
        else:
            msg = "email " + i_email + \
                " already exists, no need to perform signup, try to login"
            self.logger.info(logEncoding(msg))
            return Response(msg, status=status.HTTP_409_CONFLICT)
