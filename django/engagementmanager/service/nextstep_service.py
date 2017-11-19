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
from django.db.models.query_utils import Q
from django.utils import timezone
from django.utils.timezone import timedelta
from engagementmanager.bus.messages.activity_event_message import \
    ActivityEventMessage
from engagementmanager.models import Engagement, IceUserProfile, \
    NextStep, VF
from engagementmanager.serializers import ThinNextStepModelSerializer, \
    UserNextStepModelSerializer
from engagementmanager.utils.activities_data import \
    UpdateNextStepsActivityData, AddNextStepsActivityData
from engagementmanager.service.engagement_service import \
    update_or_insert_to_recent_engagements
from engagementmanager.service.base_service import BaseSvc
from engagementmanager.utils.constants import Constants, NextStepType,\
    NextStepState, RecentEngagementActionType
from engagementmanager.utils.request_data_mgr import request_data_mgr
from engagementmanager.apps import bus_service
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class NextStepSvc(BaseSvc):
    default_next_steps = [
        {
            'position': 2,
            'stage': 'Intake',
            'text': 'Please work with your Engagement Lead (EL) ' +
            'to complete the necessary trial agreements.',
            'condition': lambda x, y: True,
            'type': NextStepType.trial_agreements.name
        },
        {
            'position': 3,
            'stage': 'Intake',
            'text': 'Please add your ' +
            Constants.service_provider_company_name +
            ' sponsor or vendor contact information.',
            'condition': lambda user, eng: False if
            (eng.contact_user) else True,
            'type': NextStepType.add_contact_person.name
        },
        {
            'position': 1,
            'stage': 'Active',
            'text': 'Please submit the first version of the VF package. ' +
            'If you have any problems or questions, please ' +
            'contact your Engagement Lead (EL)',
            'condition': lambda x, y: True,
            'type': NextStepType.submit_vf_package.name
        },
        {
            'position': 1,
            'stage': 'Validated',
            'text': 'Please schedule a time with your Engagement Lead (EL) ' +
            'to complete the handoff.',
            'condition': lambda x, y: True,
            'type': NextStepType.el_handoff.name
        }
    ]

    def get_user_next_steps(self, limit, state):
        user = request_data_mgr.get_user()

        nextSteps = NextStep.objects.filter(Q(assignees=user) & Q(
            state=state)).order_by('due_date').distinct()
        count = nextSteps.count()
        serializer = UserNextStepModelSerializer(nextSteps[:limit], many=True)
        return serializer, count

    def get_next_steps(self, eng_stage=None):
        user = request_data_mgr.get_user()
        eng_uuid = request_data_mgr.get_eng_uuid()

        ers = NextStep.objects.filter(
            Q(
                engagement__uuid=eng_uuid,
                owner=None,
                engagement_stage=eng_stage) | Q(
                owner=user,
                engagement_stage=eng_stage)).order_by('position')

        serializer = ThinNextStepModelSerializer(ers, many=True)
        for next_step in serializer.data:
            if next_step['files'] is not None:
                next_step['files'] = json.loads(next_step['files'])
            if 'engagement' in next_step and next_step['engagement'] \
                is not None and 'engagement_team' in next_step[
                    'engagement'] and \
                    next_step['engagement']['engagement_team'] is not None:
                for user in next_step['engagement']['engagement_team']:
                    if (user['ssh_public_key'] is not None):
                        del user['ssh_public_key']
        return serializer

    def addNextStep(self, dataList, desc=""):
        user = request_data_mgr.get_user()
        checklist_uuid = request_data_mgr.get_cl_uuid()
        eng_uuid = request_data_mgr.get_eng_uuid()

        nextStepObj = None

        engObj = Engagement.objects.get(uuid=eng_uuid)
        vfObj = VF.objects.get(engagement=engObj)

        nextStepData = []
        due_date = None

        for data in dataList:
            try:
                associated_files = json.dumps(
                    data['files'], ensure_ascii=False)
            except BaseException:
                associated_files = "[]"

            try:
                due_date = data['duedate']
            except BaseException:
                due_date = None

            nextStepObj = NextStep.objects.create(
                creator=user, last_updater=user, engagement=engObj,
                position=NextStep.objects.count() + 1,
                description=data[
                    'description'], state=NextStepState.Incomplete.name,
                engagement_stage=engObj.engagement_stage,
                files=associated_files, due_date=due_date)

            try:
                data['assigneesUuids']
            except BaseException:
                data['assigneesUuids'] = []

            for assigneesUuid in data['assigneesUuids']:
                assignee_user = None
                assignee_user = IceUserProfile.objects.get(uuid=assigneesUuid)
                nextStepObj.assignees.add(assignee_user)
                nextStepObj.save()
                update_or_insert_to_recent_engagements(
                    assignee_user.uuid,
                    vfObj,
                    RecentEngagementActionType.NEXT_STEP_ASSIGNED.name)

            nextStepData.append(ThinNextStepModelSerializer(nextStepObj).data)

            activity_data = AddNextStepsActivityData(
                VF.objects.get(engagement=engObj), user, engObj)
            bus_service.send_message(ActivityEventMessage(activity_data))

        if checklist_uuid is not None:
            from engagementmanager.service.checklist_state_service import \
                set_state
            set_state(True, checklist_uuid,
                      isMoveToAutomation=True, description=desc)
            logger.debug("Successfully added a \
            Next Step to engagement_uuid=" +
                         eng_uuid + " for checklist=" + checklist_uuid)

        return nextStepData

    '''
    This function shall return the update type in the next step
    (can be Completed or Denied)
    '''

    def validate_state_transition(self, user, current_state, next_state):
        update_type = next_state.name
        logger.debug('validating step transition by %s from %s to %s',
                     user.role.name, current_state, next_state)

        if (current_state == NextStepState.Completed and next_state ==
                NextStepState.Incomplete):
            if (user.role.name == 'el'):
                update_type = 'Denied'
            else:
                update_type = 'Reset'

        return update_type

    def create_default_next_steps_for_user(self, user, el_user):
        def cond(user): return False if (
            user.ssh_public_key and user.ssh_public_key != '') else True
        if cond(user):
            desc = "Please add your SSH key to be able to contribute."

            nextstep = NextStep.objects.create(
                creator=el_user,
                last_updater=el_user,
                position=1,
                description=desc,
                last_update_type='Added',
                state='Incomplete',
                engagement_stage='Intake',
                engagement=None,
                owner=user,
                next_step_type=NextStepType.set_ssh.name,
                due_date=timezone.now() + timedelta(days=1))
            nextstep.save()

    '''
    This method is for non-personal default next step only
    since it doesn't have an owner
    '''

    def create_default_next_steps(self, user, engagement, el_user):
        for step in self.default_next_steps:
            cond = step['condition']
            desc = step['text']
            ns_type = step['type']
            if cond(user, engagement):
                if (user.company == Constants.service_provider_company):
                    desc = desc.replace('$Contact', 'Vendor Contact')
                else:
                    desc = desc.replace(
                        '$Contact',
                        Constants.service_provider_company_name +
                        ' Sponsor Contact')
                logger.debug('Creating default next step : ' + desc)

                nextstep = NextStep.objects.create(
                    creator=el_user,
                    last_updater=el_user,
                    position=step['position'],
                    description=desc,
                    state='Incomplete',
                    engagement_stage=step['stage'],
                    engagement=engagement,
                    next_step_type=ns_type,
                    due_date=timezone.now() +
                    timedelta(
                        days=1))
                nextstep.assignees.add(el_user)
                nextstep.save()

            else:
                logger.debug(
                    'Skipping creation of default next step : ' + desc)

    def update_next_steps_order(self, nextsteps):
        counter = 0
        for nextstep in nextsteps:
            step = NextStep.objects.get(uuid=nextstep['uuid'])
            step.position = counter
            step.save()
            counter += 1

    def update_next_step(self, data):
        step = NextStep.objects.get(uuid=request_data_mgr.get_ns_uuid())

        if step.files != data['files']:
            step.files = json.dumps(data['files'], ensure_ascii=False)
        if data['duedate'] and data['duedate'] != step.due_date:
            step.due_date = data['duedate']
        if data['description'] and step.description != data['description']:
            step.description = data['description']
        if data['assigneesUuids'] != '':
            for user in step.assignees.all():
                step.assignees.remove(user)
            for assigneesUuid in data['assigneesUuids']:
                assigned_user = IceUserProfile.objects.get(uuid=assigneesUuid)
                eng_team = Engagement.objects.get(
                    uuid=request_data_mgr.get_eng_uuid()).\
                    engagement_team.all()
                if (assigned_user in eng_team):
                    step.assignees.add(assigned_user)
                    step.save()
                else:
                    logger.error(
                        "An attempt to edit a NS and assign a user who is " +
                        "not in the engagement team was conducted, " +
                        "user wasn't assigned!")
                    continue

        step.last_updater = request_data_mgr.get_user()
        step.last_update_time = timezone.now()
        step.last_update_type = 'Edited'
        step.save()

    def set_next_step_status(self, attr=None, state=None):

        step = NextStep.objects.get(uuid=request_data_mgr.get_ns_uuid())

        if attr == 'state':
            update_type = self.validate_state_transition(
                request_data_mgr.get_user(), NextStepState[step.state],
                NextStepState[state])
            step.state = state
            step.last_updater = request_data_mgr.get_user()
            step.last_update_time = timezone.now()
            step.last_update_type = update_type
            step.save()
        if step.engagement:
            activity_data = UpdateNextStepsActivityData(
                step.last_update_type,
                request_data_mgr.get_user(), step.engagement)
            bus_service.send_message(ActivityEventMessage(activity_data))
