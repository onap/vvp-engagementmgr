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
from django.utils import timezone
from engagementmanager.apps import bus_service
from engagementmanager.bus.messages.activity_event_message import \
    ActivityEventMessage
from engagementmanager.slack_client.api import SlackClient
from engagementmanager.models import IceUserProfile, Engagement, \
    DeploymentTarget, VF, Role, NextStep, ECOMPRelease
from engagementmanager.serializers import VFModelSerializer
from engagementmanager.service.checklist_state_service import \
    insert_to_recent_engagements
from engagementmanager.service.engagement_service import \
    update_or_insert_to_recent_engagements
from engagementmanager.service.logging_service import LoggingServiceFactory
from engagementmanager.service.nextstep_service import NextStepSvc
from engagementmanager.utils.constants import Constants, NextStepType, \
    NextStepState, RecentEngagementActionType, Roles
from engagementmanager.utils.activities_data import \
    UserJoinedEngagementActivityData
from engagementmanager.utils.validator import logEncoding
from engagementmanager.vm_integration import vm_client
import random
import re


logger = LoggingServiceFactory.get_logger()


def addEntityIfNotExist(entity, entityObj):
    entResultSet = entity.objects.filter(uuid=entityObj.uuid)

    if entResultSet.exists():
        logger.debug(str(entityObj) + " Exists with UUID |" + entityObj.uuid)
        was_created = False
    else:
        entityObj.save()
        was_created = True

    return entity.objects.get(uuid=entityObj.uuid), was_created


def createEngagement(user, manual_el_id=False):
    eng_manual_id = str(timezone.now().year) + "-" + \
        str(Engagement.objects.count() + 31)
    eng = Engagement(
        engagement_manual_id=eng_manual_id, creator=user)
    elUser = None
    randUser = None
    elRole = Role.objects.get(name=Roles.el.name)  # @UndefinedVariable
    if user.role == elRole:
        manual_el_id = user.email

    # Attaching EL and Peer Reviewer to the Engagment
    if user.role != elRole:
        if not manual_el_id:
            # Fetch a random EL
            qs = IceUserProfile.objects.all().filter(role=elRole)
            if qs.count() > 0:
                randUser = qs[random.randint(0, qs.count() - 1)]
                elUser = IceUserProfile.objects.get(uuid=randUser.uuid)
        else:
            # Set el manually, for example when using import from xls el is
            # already assigned
            elUser = IceUserProfile.objects.get(email=manual_el_id)
    else:
        logger.debug("Since the user " + user.full_name +
                     " is an EL, no need to find another one")
        elUser = user

    logger.debug("Selected engagement lead=" + elUser.full_name)
    eng.reviewer = elUser

    # Fetch another random el to be a Peer Reviewer
    qs = IceUserProfile.objects.all().filter(
        role=elRole, user__is_active=True).exclude(uuid=elUser.uuid)
    prUser = None
    if qs.count() > 0:
        randUser = qs[random.randint(0, qs.count() - 1)]
        prUser = IceUserProfile.objects.get(uuid=randUser.uuid)
        eng.peer_reviewer = prUser
        logger.debug("Selected peer reviewer=" + prUser.full_name)

    engObj, was_created = addEntityIfNotExist(Engagement, eng)

    return engObj, elUser, prUser


def is_str_supports_git_naming_convention(item):
    """
    validates that string can contain only letters, digits hyphen and dot.
    Also, String cannot end with dot
    """
    return bool(re.compile("^[a-zA-Z0-9-]*$").match(item))


def createVF(user, request):
    """
    Create DeploymentTarget
    Create Engagement
    Create Application_Service_Infrastructure
    Create VF
    """
    dataList = request.data
    vfList = []

    for data in dataList:
        logger.debug("Processing VF - " + str(data))

        if ('virtual_function' not in data or not data['virtual_function'] or
            'version' not in data or not data['version'] or
            'target_lab_entry_date' not in data or not
            data['target_lab_entry_date'] or
            'target_aic_uuid' not in data or not data['target_aic_uuid'] or
            'ecomp_release' not in data or not data['ecomp_release'] or
                'is_service_provider_internal' not in data):
            raise KeyError("One of the input parameters are missing")

        # Set el manually, for example when using import from xls el is
        # already assigned
        if 'manual_el_id' in data:
            manual_el_id = data['manual_el_id']
        else:
            manual_el_id = False
        engObj, elUser, prUser = createEngagement(user, manual_el_id)

        if engObj is None or elUser is None:
            raise ValueError("Couldn't fetch engagement or engagement lead")

        if user is not None and engObj is not None:
            NextStepSvc().create_default_next_steps(user, engObj, elUser)

        i_target_aic_uuid = data['target_aic_uuid']
        dtObj = DeploymentTarget.objects.get(uuid=i_target_aic_uuid)

        i_ecomp_release = data['ecomp_release']
        ecompObj = ECOMPRelease.objects.get(uuid=i_ecomp_release)

        i_vfName = data['virtual_function']
        if not is_str_supports_git_naming_convention(i_vfName):
            msg = "VF Name can contain only letters, digits hyphen and dot.\
            VF Name cannot end with dot"
            logger.error(msg)
            raise ValueError(msg)
        i_vfVersion = data['version']
        i_is_service_provider_internal = data['is_service_provider_internal']
        i_target_lab_entry_date = data['target_lab_entry_date']

        vf = VF(name=i_vfName,
                version=i_vfVersion,
                engagement=engObj,
                deployment_target=dtObj,
                ecomp_release=ecompObj,
                is_service_provider_internal=i_is_service_provider_internal,
                vendor=user.company,
                target_lab_entry_date=i_target_lab_entry_date
                )

        vfObj, was_created = addEntityIfNotExist(VF, vf)

        insert_to_recent_engagements(
            user, RecentEngagementActionType.NEW_VF_CREATED.name, vfObj)

        addUsersToEngTeam(engObj.uuid, [user, elUser, prUser])
        sendSlackNotifications(engObj.uuid, [user, elUser, prUser])
        # trigger repo creation as soon as vf is created and users are added to
        # team
        if was_created:
            vm_client.fire_event_in_bg('send_provision_new_vf_event', vfObj)
        vfData = VFModelSerializer(vfObj).data
        vfList.append(vfData)

    return vfList


def updateValidationDetails(request):
    # if data['target_aic_uuid'] is not None and data['target_aic_uuid'] !=
    # "":
    data = request.data
    logger.debug("Processing VF_Details - " + str(data))
    vf = VF.objects.get(uuid=data['vf_uuid'])
    if 'target_aic_uuid' in data:
        dt_obj = DeploymentTarget.objects.get(uuid=data['target_aic_uuid'])
        vf.deployment_target = dt_obj
    if 'ecomp_release' in data:  # is not None and data['ecomp_release'] != "":
        ecomp_obj = ECOMPRelease.objects.get(uuid=data['ecomp_release'])
        vf.ecomp_release = ecomp_obj
    if 'version' in data:
        vf.version = data['version']
    vf.save()


def checkAndModifyIfSSHNextStepExist(user):
    SSHStep = None
    qs = NextStep.objects.filter(
        owner=user, next_step_type=NextStepType.set_ssh.name)
    if qs is None or qs.count() == 0:
        return None
    else:
        SSHStep = NextStep.objects.get(
            owner=user, next_step_type=NextStepType.set_ssh.name)

    # @UndefinedVariable
    if SSHStep.state in (
            NextStepState.Incomplete.name) and user.ssh_public_key:
        SSHStep.state = 'Completed'
        SSHStep.last_update_time = timezone.now()
        SSHStep.last_update_type = 'Completed'
        SSHStep.save()

    return SSHStep


def addUsersToEngTeam(eng_uuid, newUserList):
    """
    If the user isn't an EL and their doesn't have an SSH step then,
    create personal SSH next step for him.
    """
    engObj = Engagement.objects.get(uuid=eng_uuid)
    vfObj = engObj.vf
    el_user = IceUserProfile.objects.get(uuid=engObj.reviewer.uuid)
    if not el_user:
        el_user = newUserList[1]
    for newUser in newUserList:
        engObj.engagement_team.add(newUser)
        update_or_insert_to_recent_engagements(
            newUser.uuid, vfObj,
            RecentEngagementActionType.JOINED_TO_ENGAGEMENT.name)
        SSHStep = checkAndModifyIfSSHNextStepExist(newUser)
        if not SSHStep and newUser != el_user:
            NextStepSvc().create_default_next_steps_for_user(newUser, el_user)
    if vfObj is not None:
        activity_data = UserJoinedEngagementActivityData(
            vfObj, newUserList, engObj)
        bus_service.send_message(ActivityEventMessage(activity_data))


def sendSlackNotifications(eng_uuid, newUserList):
    """
    Send Slack notifications to the reviewer,
    peer reviewer and also the engagements channel
    """
    # get the engagement
    engagement = Engagement.objects.get(uuid=eng_uuid)
    engagement_manual_id = ""
    if engagement is not None:
        engagement_manual_id = engagement.engagement_manual_id

    # get the vf
    vf = VF.objects.get(engagement__uuid=eng_uuid)
    vf_name = ""
    if vf is not None:
        vf_name = vf.name

    # get the creator
    creator = engagement.creator

    # get the reviewer
    reviewer = IceUserProfile.objects.get(uuid=engagement.reviewer.uuid)
    if not reviewer:
        reviewer = newUserList[1]

    # get the peer reviewer
    peer_reviewer = IceUserProfile.objects.get(
        uuid=engagement.peer_reviewer.uuid)
    if not peer_reviewer:
        peer_reviewer = newUserList[2]

    # send Slack messages when a new engagement is created
    slack_client = SlackClient()
    slack_client.send_slack_notifications_for_new_engagement(
        engagement_manual_id, vf_name, reviewer, peer_reviewer, creator)


def getVfByEngUuid(engUuid):
    vfList = VF.objects.filter(engagement__uuid=engUuid)
    if vfList:
        logger.debug("Found VF name=" + vfList[0].name)
        if len(vfList) > 1:
            logger.warning(
                "!! There seems to be more than one VF attached to the\
                engagement with uuid=" + logEncoding(engUuid))
        # Assumption: the list only has one item because the relation
        # Engagement-VF is 1:1 business wise
        return vfList[0]
    else:
        logger.error(
            "There are no VFs in the engagement identified\
            by eng_uuid=" + logEncoding(engUuid))
        return None


def generateActivationLink(activationToken, user):
    return str(settings.DOMAIN) + Constants.activation_prefix + \
        str(user.uuid) + "/" + activationToken


def getFirstEngByUser(user):
    engList = Engagement.objects.filter(engagement_team__uuid=user.uuid)
    if engList.exists():
        logger.debug("user was found in a an ENG:" + str(engList[0]))
        return engList[0]
    else:
        logger.debug("user wasn't found in an ENG")
        return None


def createUserTemplate(company, full_name, role, phone,
                       is_service_provider_contact,
                       ssh_key=None, regular_email_updates=False, user=None):
    data = {
        'company': company,
        'phone_number': phone,
        'full_name': full_name,
        'role': role,
        'create_time': timezone.now(),
        'is_service_provider_contact': is_service_provider_contact,
        'regular_email_updates': regular_email_updates,
        'ssh_public_key': ssh_key,
    }
    if user:
        data['user'] = user
    return data
