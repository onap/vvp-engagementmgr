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
import random
from uuid import uuid4

from django.utils.timezone import timedelta
import mock
from engagementmanager.tests.test_base_entity import TestBaseEntity

from engagementmanager.apps import bus_service
from engagementmanager.bus.messages.daily_scheduled_message \
    import DailyScheduledMessage
from engagementmanager.models import Vendor, Engagement, Activity, Notification
from engagementmanager.utils.constants import \
    EngagementStage, ActivityType, Constants
from django.utils import timezone


def mocked_max_empty_date_negative(self, creation_time):
    max_empty_time = creation_time + timedelta(days=-1)
    return max_empty_time


def with_files(vf):
    list_of_files = list()
    for index in range(3):
        current_file_dict = dict()
        current_file_dict['id'] = ''.join(random.choice(
            '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ') for i in range(16))
        current_file_dict['name'] = 'file%d' % index
        current_file_dict['type'] = 'blob'
        current_file_dict['mode'] = '100644'
        list_of_files.append(current_file_dict)
    return list_of_files


def get_days_delta_plus_1(self, start_time, end_time):
    end_time = end_time + timedelta(days=1)
    return (end_time - start_time).days


def get_days_delta_plus_7(self, start_time, end_time):
    end_time = end_time + timedelta(days=7)
    return (end_time - start_time).days


def get_days_delta_plus_23(self, start_time, end_time):
    end_time = end_time + timedelta(days=23)
    return (end_time - start_time).days


def get_days_delta_plus_29(self, start_time, end_time):
    end_time = end_time + timedelta(days=29)
    return (end_time - start_time).days


def no_files(vf):
    return []


class TestNotifyInactiveEngagements(TestBaseEntity):

    def childSetup(self):

        self.createVendors(
            [Constants.service_provider_company_name, 'Amdocs', 'Other'])
        self.createDefaultRoles()

        # Create a user with role el
        self.el_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'el user',
            self.el,
            True)
        # For negative tests
        self.user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'user',
            self.standard_user,
            True)
        self.urlStr = self.urlPrefix + "engagement/@eng_uuid/checklist/new/"
        self.data = dict()
        self.template = self.creator.createDefaultCheckListTemplate()
        self.engagement = self.creator.createEngagement(
            uuid4(), 'Validation', None)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.el_user
        self.engagement.engagement_team.add(self.user)
        self.engagement.engagement_manual_id = str(timezone.now().year) + "-1"
        self.engagement.engagement_team.add(self.el_user)
        self.engagement.engagement_stage = EngagementStage.Active.name
        self.engagement.save()
        self.vendor = Vendor.objects.get(name='Other')
        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"),
            self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(
            self.randomGenerator("randomString"),
            self.engagement,
            self.deploymentTarget,
            False,
            self.vendor)

    @mock.patch(
        'validationmanager.em_integration.vm_api.' +
        'get_list_of_repo_files_callback',
        with_files)
    def testOnlyNotActiveEngagementsAreNotEffected(self):
        self.engagement.engagement_stage = EngagementStage.Archived.name
        self.engagement.save()

        bus_service.send_message(DailyScheduledMessage())
        updated_engagement = Engagement.objects.get(uuid=self.engagement.uuid)

        self.assertEqual(updated_engagement.is_with_files, False)

    @mock.patch(
        'engagementmanager.bus.handlers.' +
        'daily_notify_inactive_engagements_handler.' +
        'DailyNotifyInactiveEngagementsHandler.get_max_empty_date',
        mocked_max_empty_date_negative)
    @mock.patch(
        'validationmanager.em_integration.' +
        'vm_api.get_list_of_repo_files_callback',
        no_files)
    def testEngagementsWithouthFilesOlderThan30DaysAreArchive(self):
        bus_service.send_message(DailyScheduledMessage())
        updated_engagement = Engagement.objects.get(uuid=self.engagement.uuid)

        self.assertEqual(updated_engagement.is_with_files, False)
        self.assertEqual(updated_engagement.engagement_stage,
                         EngagementStage.Archived.name)

    @mock.patch(
        'validationmanager.em_integration.vm_api.' +
        'get_list_of_repo_files_callback',
        no_files)
    def testEngagementsWithouthFilesYoungerThan30DaysNotArchive(self):
        bus_service.send_message(DailyScheduledMessage())
        updated_engagement = Engagement.objects.get(uuid=self.engagement.uuid)

        self.assertEqual(updated_engagement.is_with_files, False)
        self.assertEqual(updated_engagement.engagement_stage,
                         EngagementStage.Active.name)

    @mock.patch(
        'validationmanager.em_integration.vm_api.' +
        'get_list_of_repo_files_callback',
        no_files)
    def testEngagementsWithouthFilesIsNotMarked(self):
        bus_service.send_message(DailyScheduledMessage())
        updated_engagement = Engagement.objects.get(uuid=self.engagement.uuid)

        self.assertEqual(updated_engagement.is_with_files, False)

    @mock.patch(
        'validationmanager.em_integration.vm_api.' +
        'get_list_of_repo_files_callback',
        with_files)
    def testEngagementsWithoFilesNotSentEmail(self):
        bus_service.send_message(DailyScheduledMessage())
        new_activity = Activity.objects.filter(
            engagement=self.engagement,
            activity_type=ActivityType.notice_empty_engagement.name
        )
        self.assertEqual(0, len(new_activity))

    @mock.patch(
        'validationmanager.em_integration.vm_api.' +
        'get_list_of_repo_files_callback',
        no_files)
    @mock.patch(
        'engagementmanager.bus.handlers.' +
        'daily_notify_inactive_engagements_handler.' +
        'DailyNotifyInactiveEngagementsHandler.get_days_delta',
        get_days_delta_plus_1)
    def testEngagementsWithoutFilesOneDayEmailNotSent(self):
        bus_service.send_message(DailyScheduledMessage())
        new_activity = Activity.objects.filter(
            engagement=self.engagement,
            activity_type=ActivityType.notice_empty_engagement.name
        )
        self.assertEqual(0, len(new_activity))

    @mock.patch(
        'validationmanager.em_integration.vm_api.' +
        'get_list_of_repo_files_callback',
        no_files)
    @mock.patch(
        'engagementmanager.bus.handlers.' +
        'daily_notify_inactive_engagements_handler.' +
        'DailyNotifyInactiveEngagementsHandler.get_days_delta',
        get_days_delta_plus_7)
    def testEngagementsWithoutFiles7DayEmailSent(self):
        bus_service.send_message(DailyScheduledMessage())
        new_activity = Activity.objects.get(
            engagement=self.engagement,
            activity_type=ActivityType.notice_empty_engagement.name
        )

        new_notifications = Notification.objects.filter(activity=new_activity)
        self.assertNotEqual(0, len(new_notifications))

        for notifcation in new_notifications:
            self.assertEqual(notifcation.is_sent, True)

    @mock.patch(
        'validationmanager.em_integration.' +
        'vm_api.get_list_of_repo_files_callback',
        no_files)
    @mock.patch(
        'engagementmanager.bus.handlers.' +
        'daily_notify_inactive_engagements_handler.' +
        'DailyNotifyInactiveEngagementsHandler.get_days_delta',
        get_days_delta_plus_23)
    def testEngagementsWithoutFiles23DayEmailSent(self):
        bus_service.send_message(DailyScheduledMessage())
        new_activity = Activity.objects.get(
            engagement=self.engagement,
            activity_type=ActivityType.notice_empty_engagement.name
        )

        new_notifications = Notification.objects.filter(activity=new_activity)
        self.assertNotEqual(0, len(new_notifications))

        for notifcation in new_notifications:
            self.assertEqual(notifcation.is_sent, True)

    @mock.patch(
        'validationmanager.em_integration.vm_api.' +
        'get_list_of_repo_files_callback',
        no_files)
    @mock.patch(
        'engagementmanager.bus.handlers.' +
        'daily_notify_inactive_engagements_handler.' +
        'DailyNotifyInactiveEngagementsHandler.get_days_delta',
        get_days_delta_plus_29)
    def testEngagementsWithoutFiles29DayEmailSent(self):
        bus_service.send_message(DailyScheduledMessage())
        new_activity = Activity.objects.get(
            engagement=self.engagement,
            activity_type=ActivityType.notice_empty_engagement.name
        )

        new_notifications = Notification.objects.filter(activity=new_activity)
        self.assertNotEqual(0, len(new_notifications))

        for notifcation in new_notifications:
            self.assertEqual(notifcation.is_sent, True)

    @mock.patch(
        'validationmanager.em_integration.' +
        'vm_api.get_list_of_repo_files_callback',
        with_files)
    def testEngagementsWithFilesIsMarked(self):

        bus_service.send_message(DailyScheduledMessage())
        updated_engagement = Engagement.objects.get(uuid=self.engagement.uuid)

        self.assertEqual(updated_engagement.is_with_files, True)
