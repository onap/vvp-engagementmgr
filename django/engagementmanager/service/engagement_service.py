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
from django.conf import settings
from django.core.exceptions import PermissionDenied
from django.db import connection
from django.db.models.aggregates import Count
from django.db.models.expressions import F
from django.db.models.query_utils import Q
from django.utils import timezone
from django.utils.datastructures import OrderedSet
from engagementmanager.bus.messages.activity_event_message import \
    ActivityEventMessage
from engagementmanager.slack_client.api import SlackClient
from engagementmanager.models import VF, Engagement, RecentEngagement, \
    EngagementStatus, VFC, IceUserProfile, Checklist
from engagementmanager.serializers import \
    SuperThinIceUserProfileModelSerializer, VFModelSerializerForSignal
from engagementmanager.utils.constants import Roles, EngagementStage, \
    ChecklistDefaultNames
from engagementmanager.utils.dates import parse_date
from engagementmanager.utils.activities_data import \
    ChangeEngagementStageActivityData
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.vm_integration import vm_client
from validationmanager.utils.clients import get_gitlab_client
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


def update_engagement_status(user, description, eng_status_uuid, engagement):
    try:
        status = EngagementStatus.objects.get(uuid=eng_status_uuid)
        status.description = description
        status.update_time = timezone.now()
        status.save()
        msg = "Status was successfully updated " +\
            "with a for engagement with uuid: " + \
            engagement.uuid
        logger.debug(msg)
    except RecentEngagement.DoesNotExist:
        EngagementStatus.objects.create(
            creator=user, description=description)
        msg = "Status was successfully created with a " +\
            "for engagement with uuid: " + \
            engagement.uuid
        logger.debug(msg)


def insert_engagement_status(user, description, engagement):
    created_eng = EngagementStatus.objects.create(
        creator=user, description=description, engagement=engagement)
    msg = "Status was successfully created \
    with a for engagement with uuid: " + engagement.uuid
    logger.debug(msg)
    return created_eng


def update_or_insert_to_recent_engagements(
        original_user_uuid, vf, action_type):
    try:
        user_uuid = ''
        try:
            user_uuid = original_user_uuid.urn[9:]
        except BaseException:
            user_uuid = original_user_uuid
        recent_engs = RecentEngagement.objects.filter(
            user_uuid=user_uuid, vf=vf.uuid).order_by('-last_update')

        if len(recent_engs) == 0:
            raise RecentEngagement.DoesNotExist()
        else:
            recent_eng = recent_engs[0]

        if (recent_eng.action_type != action_type):
            recent_eng.action_type = action_type
            recent_eng.last_update = timezone.now()
            msg = "Recent engagement table was successfully updated " +\
                "the row for a user with uuid: " + \
                user_uuid + " and vf uuid: " + vf.uuid + \
                "with a new action type: " + action_type
            logger.debug(msg)
            recent_eng.save()
        else:
            recent_eng.last_update = timezone.now()
            msg = "Recent engagement table was successfully updated " +\
                "the last_update row for a user with uuid: " + \
                user_uuid + " and vf uuid: " + vf.uuid
            logger.debug(msg)
            recent_eng.save()
        RecentEngagement.objects.filter(
            last_update__lt=datetime.now() -
            timedelta(
                days=settings.RECENT_ENG_TTL)).delete()
    except RecentEngagement.DoesNotExist:
        RecentEngagement.objects.create(
            user_uuid=user_uuid, vf=vf, action_type=action_type)
        msg = "Recent engagement table was successfully updated " +\
            "with a new row for a user with uuid: " + \
            str(user_uuid) + " and vf uuid: " + str(vf.uuid)
        logger.debug(msg)


def get_dashboard_expanded_engs(stage, keyword, offset, limit, user):
    """
    Expecting:
           stage: one of the choices in the defined constants.
           keyword: string
           offset: non-negative number to start the pull from them + 9
           (Negative indexing (i.e. Entry.objects.all()[-1]) is not
           supported - according to Django 21.12.16).
           user: user object of the requesting client.
    Result:
           Query-set of engs that match the parameters provided (10 objects).
    """
    engStageList = [
        EngagementStage.Intake.name,
        EngagementStage.Active.name,
        EngagementStage.Validated.name,
        EngagementStage.Completed.name]  # @UndefinedVariable

    q_object = Q()
    q_vfc_object = Q()
    if len(keyword) >= 1:
        q_object &= Q(name__icontains=keyword) | Q(
            engagement__engagement_manual_id__icontains=keyword) | Q(
            engagement__engagement_team__email__icontains=keyword) | Q(
            engagement__engagement_team__full_name__icontains=keyword)
        q_vfc_object &= Q(name__icontains=keyword)

    if stage == "All":
        q_object &= Q(engagement__engagement_stage__in=engStageList)
        q_vfc_object &= Q(vf__engagement__engagement_stage__in=engStageList)
    else:
        q_object &= Q(engagement__engagement_stage=stage)
        q_vfc_object &= Q(vf__engagement__engagement_stage=stage)

    # @UndefinedVariable
    if (user.role.name != Roles.admin.name and
            user.role.name != Roles.admin_ro.name):
        q_object &= Q(engagement__engagement_team__uuid=user.uuid)
        q_vfc_object &= Q(vf__engagement__engagement_team__uuid=user.uuid)

    vf_list_uuids = VF.objects.filter(q_object).values_list(
        'uuid', flat=True).order_by('engagement__target_completion_date')
    vfc_vflist_uuids = VFC.objects.filter(q_vfc_object).values_list(
        'vf__uuid', flat=True).order_by(
            'vf__engagement__target_completion_date')

    vf_list_uuids = OrderedSet(vf_list_uuids)
    for current_vf in OrderedSet(vfc_vflist_uuids):
        vf_list_uuids.add(current_vf)
    num_of_objects = len(vf_list_uuids)

    vf_final_array = []
    vf_list = VF.objects.filter(
        uuid__in=vf_list_uuids) .annotate(
        vf__name=F('name'),
        vendor__name=F('vendor__name'),
    ) .values(
            'vf__name',
            'version',
            'deployment_target__version',
            'engagement__peer_reviewer__uuid',
            'ecomp_release__name',
            'engagement__engagement_stage',
            'engagement__engagement_manual_id',
            'engagement__uuid',
            'engagement__heat_validated_time',
            'engagement__image_scan_time',
            'engagement__aic_instantiation_time',
            'engagement__asdc_onboarding_time',
            'engagement__target_completion_date',
            'engagement__progress',
            'target_lab_entry_date',
            'engagement__started_state_time',
            'vendor__name',
            'engagement__validated_time',
            'engagement__completed_time',
            'uuid') .annotate(
                vf_uuid_count=Count(
                    'uuid',
                    distinct=True)) .order_by(
                        'engagement__target_completion_date')[
                        int(offset):int(offset) +
        limit]
    for current_vf in vf_list:
        eng = Engagement.objects.get(uuid=current_vf['engagement__uuid'])
        starred_users = eng.starred_engagement.all()
        current_vf['starred_users'] = list()
        if starred_users:
            for current_starred in starred_users:
                current_vf['starred_users'].append(current_starred.uuid)
        vf_final_array.append(current_vf)
    data = {'array': vf_final_array, 'num_of_objects': num_of_objects}
    return data

# Extension method for get_dashboard_expanded_engs which adds additional
# data required by export process.


def get_expanded_engs_for_export(stage, keyword, user):
    # TODO replace this 1000000 with No limit value
    data = get_dashboard_expanded_engs(
        stage, keyword, 0, 10000000, user)

    vf_list = data["array"]

    for vf in vf_list:
        eng = Engagement.objects.get(uuid=vf['engagement__uuid'])
        latest_status = EngagementStatus.objects.filter(
            engagement=eng).distinct().order_by('-update_time')[:1]
        peer_reviewer = eng.peer_reviewer
        reviewer = eng.reviewer
        vf['vf_engagement__peer_reviewer'] = peer_reviewer
        vf['vf_engagement__reviewer'] = reviewer
        if latest_status.count() > 0:
            vf['engagement__latest_status'] = latest_status[0].description
        else:
            vf['engagement__latest_status'] = "--"

        vf['vfcs'] = "--"
        vf['vfcs__number'] = "0"
        vfObject = VF.objects.get(uuid=vf['uuid'])
        if vfObject is not None:
            vfcs = vfObject.vfc_set.values_list('name', flat=True)
            if vfcs.count() > 0:
                vf['vfcs'] = ', '.join(vfcs)
                vf['vfcs__number'] = vfcs.count()

    # Overview statistics:
    cursor = connection.cursor()
    cursor.callproc("generate_excel_overview_sheet", (stage, keyword,))
    deployment_targets = cursor.fetchall()
    cursor.execute("COMMIT")

    return vf_list, deployment_targets


def is_eng_stage_eql_to_requested_one(engagement, requested_stage):
    if engagement.engagement_stage == requested_stage:
        msg = "An attempt to change the Engagement's stage (uuid: " + \
            engagement.uuid + \
            ") to the same stage it is current in(" + \
            engagement.engagement_stage + ") was made."
        logger.debug(msg)
        return True
    return False


def set_engagement_stage(eng_uuid, stage):
    engagement = Engagement.objects.get(uuid=eng_uuid)
    vfObj = engagement.vf
    if is_eng_stage_eql_to_requested_one(engagement, stage):
        msg = "Action denied."
        raise ValueError(msg)
    else:
        engagement.engagement_stage = stage
        engagement.intake_time = timezone.now()
        engagement.save()
        logger.debug("Engagement's stage was modified in DB to: %s" % stage)
        logger.debug("firing an event to gitlab")
        vm_client.fire_event_in_bg('send_provision_new_vf_event', vfObj)
        msg = send_notifications_and_create_activity_after_eng_stage_update(
            engagement)
        return msg


def send_notifications_and_create_activity_after_eng_stage_update(engagement):
    # send notifications
    res = get_engagement_manual_id_and_vf_name(engagement)
    slack_client = SlackClient()
    slack_client.update_for_change_of_the_engagement_stage(
        res['engagement_manual_id'], res['vf_name'],
        engagement.engagement_stage)

    activity_data = ChangeEngagementStageActivityData(VF.objects.get(
        engagement=engagement), engagement.engagement_stage, engagement)
    from engagementmanager.apps import bus_service
    bus_service.send_message(ActivityEventMessage(activity_data))

    logger.debug(
        "Engagement's stage (eng_uuid: " +
        engagement.uuid +
        ") was successfully changed to: " +
        engagement.engagement_stage)
    return "OK"


def set_progress_for_engagement(progress=None):
    prog = int(progress)
    if prog < 0 or prog > 100:
        msg = 'set_progress_for_engagement failed: Progress ' +\
            'value is invalid (out of bounds). Should be 0-100'
        logger.debug(msg)
        raise ValueError(msg)
    else:
        eng = Engagement.objects.get(uuid=request_data_mgr.get_eng_uuid())
        eng.progress = progress
        eng.save()


def vf_retreiver(user, star=False, recent=False, eng_uuid=""):
    engStageList = [
        EngagementStage.Intake.name,
        EngagementStage.Active.name,
        EngagementStage.Validated.name,
        EngagementStage.Completed.name]
    # @UndefinedVariable
    if (user.role.name == Roles.admin.name or
            user.role.name == Roles.admin_ro.name):
        if star:
            vf_list = VF.objects.filter(
                engagement__engagement_stage__in=engStageList) .filter(
                engagement__starred_engagement__uuid=user.uuid).\
                distinct().order_by(
                    'engagement__engagement_manual_id') .values(
                'uuid',
                'name',
                'is_service_provider_internal',
                'engagement__creator__uuid',
                'engagement__engagement_manual_id',
                'engagement__peer_reviewer__uuid',
                'engagement__peer_reviewer__email',
                'engagement__reviewer__uuid',
                'engagement__reviewer__email',
                'engagement__uuid')

            for vf in vf_list:
                red_dot_activity = RecentEngagement.objects.filter(
                    vf=vf['uuid']).values(
                        'action_type').order_by('-last_update')[:1]
                if (red_dot_activity.count() > 0):
                    vf['action_type'] = red_dot_activity[0]['action_type']
                else:
                    vf['action_type'] = ''

            return vf_list

        elif recent:
            recent = RecentEngagement.objects.filter(
                vf__engagement__engagement_stage__in=engStageList) .filter(
                user_uuid=user.uuid).distinct().order_by(
                    '-last_update') .values(
                'vf__uuid',
                'vf__name',
                'vf__is_service_provider_internal',
                'vf__engagement__creator__uuid',
                'vf__engagement__engagement_manual_id',
                'vf__engagement__peer_reviewer__uuid',
                'vf__engagement__peer_reviewer__email',
                'vf__engagement__reviewer__uuid',
                'vf__engagement__reviewer__email',
                'vf__engagement__uuid',
                'action_type',
                'last_update')[
                :20]
            return recent

        else:
            if eng_uuid != "":
                vf_list = VF.objects.filter(
                    engagement__engagement_stage__in=engStageList) .filter(
                    engagement__uuid=eng_uuid).distinct().order_by(
                        'engagement__engagement_manual_id') .values(
                    'uuid',
                    'name',
                    'is_service_provider_internal',
                    'engagement__creator__uuid',
                    'engagement__engagement_manual_id',
                    'engagement__peer_reviewer__uuid',
                    'engagement__peer_reviewer__email',
                    'engagement__reviewer__uuid',
                    'engagement__reviewer__email',
                    'engagement__uuid')
            else:
                vf_list = VF.objects.filter(
                    engagement__engagement_stage__in=engStageList)\
                    .filter().distinct().order_by(
                        'engagement__engagement_manual_id')\
                    .values(
                        'uuid',
                        'name',
                        'is_service_provider_internal',
                        'engagement__creator__uuid',
                        'engagement__engagement_manual_id',
                        'engagement__peer_reviewer__uuid',
                        'engagement__peer_reviewer__email',
                        'engagement__reviewer__uuid',
                        'engagement__reviewer__email',
                        'engagement__uuid'
                )

            return vf_list
    else:
        if star:
            if eng_uuid != "":
                vf_list = VF.objects.filter(
                    engagement__engagement_stage__in=engStageList) .filter(
                    Q(
                        engagement__uuid=eng_uuid,
                        engagement__engagement_team__uuid=user.uuid,
                        engagement__starred_engagement__uuid=user.uuid) | Q(
                        engagement__uuid=eng_uuid,
                        engagement__peer_reviewer=user,
                        engagement__starred_engagement__uuid=user.uuid)) \
                    .values(
                    'uuid',
                    'name',
                    'is_service_provider_internal',
                    'engagement__creator__uuid',
                    'engagement__engagement_manual_id',
                    'engagement__peer_reviewer__uuid',
                    'engagement__peer_reviewer__email',
                    'engagement__reviewer__uuid',
                    'engagement__reviewer__email',
                    'engagement__uuid')
            else:
                vf_list = VF.objects.filter(
                    engagement__engagement_stage__in=engStageList) .filter(
                    Q(
                        engagement__engagement_team__uuid=user.uuid,
                        engagement__starred_engagement__uuid=user.uuid) | Q(
                        engagement__peer_reviewer=user,
                        engagement__starred_engagement__uuid=user.uuid)).\
                    distinct().order_by(
                        'engagement__engagement_manual_id') .values(
                    'uuid',
                    'name',
                    'is_service_provider_internal',
                    'engagement__creator__uuid',
                    'engagement__engagement_manual_id',
                    'engagement__peer_reviewer__uuid',
                    'engagement__peer_reviewer__email',
                    'engagement__reviewer__uuid',
                    'engagement__reviewer__email',
                    'engagement__uuid')
            for vf in vf_list:
                red_dot_activity = RecentEngagement.objects.filter(
                    vf=vf['uuid']).values(
                        'action_type').order_by('-last_update')[:1]
                if (red_dot_activity.count() > 0):
                    vf['action_type'] = red_dot_activity[0]['action_type']
                else:
                    vf['action_type'] = ''

            return vf_list

        elif recent:
            recent = RecentEngagement.objects.filter(
                vf__engagement__engagement_stage__in=engStageList) .filter(
                Q(
                    user_uuid=user.uuid,
                    vf__engagement__engagement_team__uuid=user.uuid) | Q(
                    user_uuid=user.uuid,
                    vf__engagement__peer_reviewer=user)).distinct().order_by(
                        '-last_update') .values(
                    'vf__uuid',
                    'vf__name',
                    'vf__is_service_provider_internal',
                    'vf__engagement__creator__uuid',
                    'vf__engagement__engagement_manual_id',
                    'vf__engagement__peer_reviewer__uuid',
                    'vf__engagement__peer_reviewer__email',
                    'vf__engagement__reviewer__uuid',
                    'vf__engagement__reviewer__email',
                    'vf__engagement__uuid',
                    'action_type',
                    'last_update')[
                        :20]
            return recent
        else:
            if eng_uuid != "":
                vf_list = VF.objects.filter(
                    engagement__engagement_stage__in=engStageList) .filter(
                    Q(
                        engagement__uuid=eng_uuid,
                        engagement__engagement_team__uuid=user.uuid) | Q(
                        engagement__uuid=eng_uuid,
                        engagement__peer_reviewer=user)).distinct().order_by(
                            'engagement__engagement_manual_id') .values(
                    'uuid',
                    'name',
                    'is_service_provider_internal',
                    'engagement__creator__uuid',
                    'engagement__engagement_manual_id',
                    'engagement__peer_reviewer__uuid',
                    'engagement__peer_reviewer__email',
                    'engagement__reviewer__uuid',
                    'engagement__reviewer__email',
                    'engagement__uuid')
            else:
                vf_list = VF.objects.filter(
                    engagement__engagement_stage__in=engStageList) .filter(
                    Q(
                        engagement__engagement_team__uuid=user.uuid) | Q(
                        engagement__peer_reviewer=user)).distinct().order_by(
                            'engagement__engagement_manual_id') .values(
                    'uuid',
                    'name',
                    'is_service_provider_internal',
                    'engagement__creator__uuid',
                    'engagement__engagement_manual_id',
                    'engagement__peer_reviewer__uuid',
                    'engagement__peer_reviewer__email',
                    'engagement__reviewer__uuid',
                    'engagement__reviewer__email',
                    'engagement__uuid')
            return vf_list


def star_an_engagement(user, eng_uuid):
    msg = "Engagement was successfully starred."
    engObj = None
    try:
        engObj = Engagement.objects.get(
            uuid=eng_uuid, starred_engagement__uuid=user.uuid)
        engObj.starred_engagement.remove(user)
        msg = "Engagement was successfully un-starred."
    except Engagement.DoesNotExist:
        engObj = Engagement.objects.get(uuid=eng_uuid)
        engObj.starred_engagement.add(user)
        engObj.save()

    return msg


def archive_engagement(eng_uuid, reason):
    msg = "Engagement was successfully archived."
    engagement = Engagement.objects.get(uuid=eng_uuid)
    # get the vf
    vf = VF.objects.get(engagement__uuid=engagement.uuid)
    gitlab = get_gitlab_client()
    project_id = "%s/%s" % (vf.engagement.engagement_manual_id,
                            vf.name.replace(' ', '_'))
    formated_vf = VFModelSerializerForSignal(vf).data

    # @UndefinedVariable
    engagement.engagement_stage = EngagementStage.Archived.name
    engagement.archive_reason = reason
    engagement.archived_time = timezone.now()
    engagement.save()
    vm_client.send_remove_all_standard_users_from_project_event(
        gitlab, project_id, formated_vf)
    # send notifications
    res = get_engagement_manual_id_and_vf_name(engagement)
    slack_client = SlackClient()
    slack_client.update_for_archived_engagement(
        res['engagement_manual_id'], res['vf_name'], reason)
    return msg


def set_engagement_reviewer(eng_uuid, reviewer_uuid):
    result = None
    engagement = Engagement.objects.get(uuid=eng_uuid)

    reviewer = IceUserProfile.objects.get(uuid=reviewer_uuid)
    if engagement.peer_reviewer != reviewer:
        old_reviewer = engagement.reviewer
        engagement.engagement_team.remove(old_reviewer)
        engagement.engagement_team.add(reviewer)

        checklist_lists_creator = Checklist.objects.filter(
            engagement__uuid=eng_uuid, creator=old_reviewer)
        for checklist in checklist_lists_creator:
            checklist.creator = reviewer
            checklist.save()

        checklist_lists_owner = Checklist.objects.filter(
            engagement__uuid=eng_uuid, owner=old_reviewer)
        for checklist in checklist_lists_owner:
            checklist.owner = reviewer
            checklist.save()

        engagement.reviewer = reviewer
        engagement.save()

        # send notifications
        res = get_engagement_manual_id_and_vf_name(engagement)
        slack_client = SlackClient()
        slack_client.update_reviewer_or_peer_reviewer(
            res['engagement_manual_id'],
            res['vf_name'],
            reviewer,
            old_reviewer,
            'reviewer')

        result = reviewer
    else:
        return result

    return SuperThinIceUserProfileModelSerializer(result).data


def set_engagement_peer_reviewer(eng_uuid, peer_reviewer_uuid):
    result = None
    engagement = Engagement.objects.get(uuid=eng_uuid)
    peer_reviewer = IceUserProfile.objects.get(uuid=peer_reviewer_uuid)
    if engagement.reviewer != peer_reviewer:
        old_peer_reviewer = engagement.peer_reviewer
        engagement.engagement_team.remove(old_peer_reviewer)
        engagement.engagement_team.add(peer_reviewer)

        checklist_lists_owner = Checklist.objects.filter(
            engagement__uuid=eng_uuid, owner=old_peer_reviewer)
        for checklist in checklist_lists_owner:
            checklist.owner = peer_reviewer
            checklist.save()

        engagement.peer_reviewer = peer_reviewer
        engagement.save()

        # send notifications
        res = get_engagement_manual_id_and_vf_name(engagement)
        slack_client = SlackClient()
        slack_client.update_reviewer_or_peer_reviewer(
            res['engagement_manual_id'],
            res['vf_name'],
            peer_reviewer,
            old_peer_reviewer,
            'peer reviewer')

        result = peer_reviewer
    else:
        return result

    return SuperThinIceUserProfileModelSerializer(result).data


def switch_engagement_reviewers(eng_uuid, reviewer_uuid, peer_reviewer_uuid):
    engagement = Engagement.objects.get(uuid=eng_uuid)
    peer_reviewer = IceUserProfile.objects.get(uuid=peer_reviewer_uuid)
    old_peer_reviewer = engagement.peer_reviewer
    reviewer = IceUserProfile.objects.get(uuid=reviewer_uuid)
    old_reviewer = engagement.reviewer

    checklist_owners = Checklist.objects.filter(
        Q(engagement__uuid=eng_uuid) & (
            Q(owner=old_reviewer) | Q(owner=old_peer_reviewer)))

    for checklist in checklist_owners:
        if checklist.owner == reviewer:
            checklist.owner = peer_reviewer
        if checklist.owner == peer_reviewer:
            checklist.owner = reviewer
        checklist.save()

    engagement.peer_reviewer = peer_reviewer
    engagement.reviewer = reviewer
    engagement.save()

    # send notifications
    res = get_engagement_manual_id_and_vf_name(engagement)
    slack_client = SlackClient()
    slack_client.update_reviewer_or_peer_reviewer(
        res['engagement_manual_id'],
        res['vf_name'],
        reviewer,
        old_reviewer,
        'reviewer')
    slack_client.update_reviewer_or_peer_reviewer(
        res['engagement_manual_id'],
        res['vf_name'],
        peer_reviewer,
        old_peer_reviewer,
        'peer reviewer')

    return {"reviewer": reviewer_uuid, "peerreviewer": peer_reviewer_uuid}


def get_engagement_manual_id_and_vf_name(engagement):
    # get the engagement
    engagement_manual_id = engagement.engagement_manual_id

    # get the vf
    vf = VF.objects.get(engagement__uuid=engagement.uuid)
    vf_name = ""
    if vf is not None:
        vf_name = vf.name

    return {'engagement_manual_id': engagement_manual_id, 'vf_name': vf_name}


def update_engagement(engagement_dict):
    engagement = Engagement.objects.get(uuid=engagement_dict['uuid'])

    engagement.target_completion_date = parse_date(
        engagement_dict['target_completion_date'])
    engagement.heat_validated_time = parse_date(
        engagement_dict['heat_validated_time'])
    engagement.image_scan_time = parse_date(engagement_dict['image_scan_time'])
    engagement.aic_instantiation_time = parse_date(
        engagement_dict['aic_instantiation_time'])
    engagement.asdc_onboarding_time = parse_date(
        engagement_dict['asdc_onboarding_time'])
    if 0 <= engagement_dict['progress'] <= 100:
        engagement.progress = engagement_dict['progress']
    else:
        return None

    engagement.save()
    return engagement


def remove_user_from_engagement_team(eng_uuid, user, removed_user_uuid):
    msg = "User was successfully removed from the engagement team"
    # @UndefinedVariable
    if ((removed_user_uuid == user.uuid) or
        (removed_user_uuid != user.uuid and (
            user.role.name == Roles.admin.name or
            user.role.name == Roles.el.name))):
        engagement = Engagement.objects.get(uuid=eng_uuid)
        requested_user = IceUserProfile.objects.get(uuid=removed_user_uuid)
        if (engagement.peer_reviewer == requested_user or
            engagement.reviewer == requested_user
                or engagement.creator == requested_user or
                engagement.contact_user == requested_user):
            msg = "Reviewer/Peer Reviewer/Creator/Contact " +\
                "user cannot be removed from engagement team."
            logger.error(msg)
            raise PermissionDenied
        engagement.engagement_team.remove(requested_user)
        engagement.save()
        logger.debug(msg)
    else:
        msg = "removed user is not equal to conducting " +\
            "user or user is not an admin."
        logger.error(msg)
        raise PermissionDenied


def update_eng_validation_details(cl):
    setattr(cl.engagement,
            ChecklistDefaultNames.VALIDATION_DATE_ARRAY[cl.name],
            timezone.now())
    cl.engagement.save()
