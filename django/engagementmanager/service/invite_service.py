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
from datetime import datetime, timedelta
from uuid import uuid4
import bleach
from django.conf import settings
from django.template.loader import get_template
from engagementmanager import mail
from engagementmanager.models import Invitation, IceUserProfile, Engagement
from engagementmanager.utils.constants import Roles, Constants
from engagementmanager.utils.vvp_exceptions import VvpBadRequest
from engagementmanager.utils.validator import Validator, logEncoding
from engagementmanager.views_helper import getVfByEngUuid
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


def enforce_invitation_throttling(eng_uuid, invited_email, inviterUser, invitedUser):
    assert eng_uuid is not None
    assert invited_email is not None

    invitation = Invitation.objects.filter(engagement_uuid=eng_uuid, email=invited_email)
    if len(invitation) > 0:
        logger.warn("Oops, looks like an invitation with following details already exists: " + str(invitation))
        return False

    if ((invitedUser != None and invitedUser.role.name != Roles.admin.name and
                 invitedUser.role.name != Roles.el.name) or invitedUser == None):
        numOfInvitationinLast24H = Invitation.objects.filter(email=invited_email,
                                                             create_time__gte=datetime.now() - timedelta(
                                                                 hours=24)).count()
        if numOfInvitationinLast24H >= 5:
            logger.warn(
                "Oops, looks like invited email (" + invited_email + ") which isn't EL nor admin has reached its "
                                                                     "max invitations (5) in the last 24 hours")
            return False

    if ((invitedUser != None and invitedUser.role.name == Roles.standard_user.name) or
            (invitedUser != None and invitedUser.role.name == Roles.admin_ro.name) or
            invitedUser == None):
        numOfInvitationinLast24H = Invitation.objects.filter(invited_by_user_uuid=inviterUser.uuid,
                                                             create_time__gte=datetime.now() - timedelta(
                                                                 hours=24)).count()
        if numOfInvitationinLast24H >= 25:
            logger.warn(
                "Oops, looks like a standard-user/admin-readonly inviter "
                "(" + inviterUser.email + ") has reached its max invitations (25) in the last 24 hours")
            return False
    return True


def generateInviteMail(data, inviterUser, invitedUser, is_contact_user):
    vf = getVfByEngUuid(data['eng_uuid'])
    if vf is not None:
        data['vf_name'] = vf.name
    else:
        data['vf_name'] = "-"
        logger.error("Couldn't fetch VF by engagement uuid=" + logEncoding(data['eng_uuid']))

    body = get_template("{invite_template_dir}invite_mail_body.html".format(
        invite_template_dir=Constants.invite_template_dir))
    subject = get_template("{invite_template_dir}invite_mail_subject.html".format(
        invite_template_dir=Constants.invite_template_dir))

    data['dashboard_link'] = str(settings.DOMAIN) + "/#/dashboard/"
    invitation = Invitation.objects.create(engagement_uuid=data['eng_uuid'],
                                           invited_by_user_uuid=inviterUser.uuid, email=data['email'],
                                           invitation_token=uuid4())

    if invitedUser is not None:
        data['invite_link'] = str(settings.DOMAIN) + "/#/login?invitation=" + str(invitation.invitation_token)
        data['instruction'] = "To accept this invitation, please click this link:"
        logger.debug("Invited Contact with email " + data['email'] + "already exist in the DB. Sending them an email "
                                                                     "with link to login page. link=" + data[
            'invite_link'])
        if is_contact_user:
            logger.debug("Updating the Engagement with uuid=" + data[
                'eng_uuid'] + " to have this contact user: " + invitedUser.full_name)
            engObj = Engagement.objects.get(uuid=data['eng_uuid'])
            engObj.contact_user = invitedUser
            engObj.save()

    else:
        prefix = str(settings.DOMAIN) + "/#/signUp?invitation=" + \
            str(invitation.invitation_token) + "&email=" + data['email']
        suffix = ""
        if 'full_name' in data and data['full_name'] and 'phone_number' in data and data['phone_number']:
            suffix += "&full_name=" + data['full_name'] + "&phone_number=" + data['phone_number']
            if data.get('company'):
                suffix += "&company=" + data['company']

        data['invite_link'] = prefix + suffix
        data['instruction'] = "To create an account and accept this invitation, please click this link:"

        if is_contact_user:
            data['invite_link'] += "&is_contact_user=true"
            logger.debug("The invite mail is sent to a contact person (VF Contact or "
                         + Constants.service_provider_company_name + " Sponsor)")

        logger.debug(
            "Invited Person doesn't exists, sending them an email with link to signup. link=" + data['invite_link'])

    return body, subject, invitation


def inviteUserToSignUpOrLogin(inviterUser, data, is_contact_user):
    invitedUser = None

    Validator.validateEmail(data['email'])

    data['email'] = bleach.clean(data['email'], tags=['a', 'b'])
    rs = IceUserProfile.objects.filter(email=data['email'])

    if len(rs) > 0:
        invitedUser = IceUserProfile.objects.get(email=data['email'])

    is_invite_ok = enforce_invitation_throttling(data['eng_uuid'], data['email'], inviterUser, invitedUser)

    if is_invite_ok == False:
        msg = "Invite couldn't be created"
        logger.error(msg)
        raise VvpBadRequest(msg)

    body, subject, invitation = generateInviteMail(data, inviterUser, invitedUser, is_contact_user)

    try:
        mail.sendMail(data['email'], data, body, subject)
    except Exception as e:
        logger.error(e)
        msg = "Something went wrong while trying to send mail to " + data['email'] + " from " + inviterUser.email
        logger.error(msg)
        if invitation:
            logger.error("Rolling back the invitation (" + invitation + ") due to problems in sending its mail")
            invitation.delete()
        raise Exception(msg)


def markInvitationAsAccepted(invitation_token):
    invitation = Invitation.objects.get(invitation_token=invitation_token)
    invitation.accepted = True
    invitation.save()
    logger.debug("Marking Invitation [" + str(invitation) + "] as accepted")
