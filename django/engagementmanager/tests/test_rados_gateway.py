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
import time

from engagementmanager.bus.messages.hourly_scheduled_message import HourlyScheduledMessage
from engagementmanager.tests.test_base_transaction_entity import TestBaseTransactionEntity
from engagementmanager.apps import bus_service
from django.conf import settings
import mock
from rest_framework.status import HTTP_202_ACCEPTED
from engagementmanager.models import Vendor, Checklist
from engagementmanager.utils.constants import Constants, EngagementStage, CheckListState
from wheel.signatures import assertTrue


def get_or_create_bucket_mock(name):
    bucket = {'bucket': name,
              'categories': [
                  {'bytes_received': 0,
                   'bytes_sent': 1388,
                   'category': 'list_buckets',
                   'ops': 4,
                   'successful_ops': 4}],
              'epoch': 1499821200,
              'owner': 'staticfiles',
              'time': '2017-07-12 01:00:00.000000Z'}

    return bucket


def add_bucket_user_mock(user, bucket):
    RadosGatewayTestCase.users_added_to_mock.append(user)
    RadosGatewayTestCase.added_bucket = bucket
    print("*****RadosGatewayTestCase.added_bucket*****",
          RadosGatewayTestCase.added_bucket)


def remove_bucket_user_grants_mock(bucket, user):
    RadosGatewayTestCase.added_bucket = bucket
    RadosGatewayTestCase.users_added_to_mock.remove(user)


def blank_mock(vf):
    print("===--blank mock was activated--===")
    pass


def get_rgwa_uasge_mock(
        uid=None,
        start=None,
        end=None,
        show_entries=False,
        show_summary=False):
    print("===--get_rgwa_uasge_mock was invoked--===")
    return {
        "entries": [
            {
                "buckets": [
                    {
                        "bucket": "static-engagement-manual-id_static-vf-name",
                        "owner": "staticfiles",
                        "categories": [
                                 {
                                     "category": "put_obj",
                                     "bytes_sent": 0,
                                     "bytes_received": 2948046,
                                     "ops": 102,
                                     "successful_ops": 102
                                 }
                        ],
                        "time": "2017-09-07 21:00:00.000000Z",
                        "epoch": 1504818000
                    }
                ],
                "user": "staticfiles"
            }
        ]
    }


@mock.patch('validationmanager.em_integration.vm_api.get_or_create_bucket',
            get_or_create_bucket_mock)
@mock.patch('validationmanager.em_integration.vm_api.add_bucket_user',
            add_bucket_user_mock)
@mock.patch(
    'validationmanager.em_integration.vm_api.remove_bucket_user_grants',
    remove_bucket_user_grants_mock)
@mock.patch(
    'validationmanager.em_integration.vm_api.ensure_git_entities', blank_mock)
@mock.patch(
    'validationmanager.em_integration.vm_api.ensure_jenkins_job', blank_mock)
@mock.patch(
    'validationmanager.em_integration.vm_api.ensure_checklists', blank_mock)
class RadosGatewayTestCase(TestBaseTransactionEntity):
    users_added_to_mock = []
    added_bucket = None

    def changeEngagementStage(self, stage):
        self.urlStr = self.urlPrefix + "single-engagement/" + \
            str(self.engagement.uuid) + "/stage/@stage"
        datajson = json.dumps(self.data, ensure_ascii=False)
        response = self.c.put(
            self.urlStr.replace("@stage",
                                stage),
            datajson,
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)

    def waitForBucket(self):
        counter = 1
        while (RadosGatewayTestCase.added_bucket is None and counter <= 20):
            time.sleep(1)
        time.sleep(1)
        if RadosGatewayTestCase.added_bucket is None:
            raise Exception("Max retries exceeded, failing test...")
            return False
        elif RadosGatewayTestCase.added_bucket is not None:
            return True

    def childSetup(self):
        RadosGatewayTestCase.users_added_to_mock = []
        RadosGatewayTestCase.added_bucket = None
        settings.IS_SIGNAL_ENABLED = True
        self.s3_host = settings.AWS_S3_HOST
        self.s3_port = settings.AWS_S3_PORT

        vendor_uuid, self.service_provider = self.creator.createVendor(
            Constants.service_provider_company_name)
        self.urlStr = self.urlPrefix + "signup/"
        self.admin, self.el, self.standard_user = \
            self.creator.createAndGetDefaultRoles()

        self.data = dict()
        uuid, vendor = self.creator.createVendor(
            Constants.service_provider_company_name)
        self.user = self.creator.createUser(
            vendor,
            self.randomGenerator("email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.standard_user,
            True)

        self.params = '{"company":"' + str(self.user.company) + \
            '","full_name":"' + self.user.full_name + '","email":"' \
                      + self.user.email + '","phone_number":"' \
                      + self.user.phone_number + \
                      '","password":"' + self.user.user.password \
                      + '","regular_email_updates":"' + \
                      str(self.user.regular_email_updates) + \
                      '","is_service_provider_contact":"' + \
            str(self.user.is_service_provider_contact) + '"}'
        self.el_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'el user',
            self.el,
            True)
        self.admin_user = self.creator.createUser(
            Vendor.objects.get(name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '12323245435',
            'admin user',
            self.admin,
            True)
        self.peer_reviewer = self.creator.createUser(
            self.service_provider,
            self.randomGenerator("main-vendor-email"),
            self.randomGenerator("randomNumber"),
            self.randomGenerator("randomString"),
            self.el,
            True)

        self.engagement = self.creator.createEngagement(
            'just-a-fake-uuid', 'Validation', None)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.peer_reviewer
        self.engagement.engagement_team.add(self.el_user, self.user)
        self.engagement.engagement_manual_id = self.randomGenerator(
            "randomString")
        self.engagement.save()
        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"),
            self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(
            self.randomGenerator("randomString"),
            self.engagement,
            self.deploymentTarget,
            False,
            self.service_provider)
        self.userToken = self.loginAndCreateSessionToken(self.user)
        self.ELtoken = self.loginAndCreateSessionToken(self.el_user)

    def testCreateBucketWithUser(self):
        self.assertTrue(self.added_bucket is None)
        self.changeEngagementStage(EngagementStage.Active.name)
        self.assertTrue(RadosGatewayTestCase.added_bucket is not None)
        team_members_list = [
            entry for entry in self.engagement.engagement_team.all()]
        for team_member in team_members_list:
            assertTrue(any(team_member.full_name ==
                           entity.full_name for entity in
                           RadosGatewayTestCase.users_added_to_mock))

    def testDeleteUsersFromBucket(self):
        self.changeEngagementStage(EngagementStage.Active.name)
        self.changeEngagementStage(EngagementStage.Validated.name)
        self.waitForBucket()
        self.assertTrue(RadosGatewayTestCase.added_bucket is not None)
        self.assertTrue(RadosGatewayTestCase.users_added_to_mock == [])

    def testDeleteUsersFromBucketWhichNotCreated(self):
        self.assertTrue(RadosGatewayTestCase.added_bucket is None)
        self.changeEngagementStage(EngagementStage.Validated.name)
        self.waitForBucket()
        self.assertTrue(RadosGatewayTestCase.added_bucket is not None)
        self.assertTrue(RadosGatewayTestCase.users_added_to_mock == [])

    def testDeleteUsersFromBucketWhwenStageArchive(self):
        self.assertTrue(RadosGatewayTestCase.added_bucket is None)
        self.changeEngagementStage(EngagementStage.Archived.name)
        self.waitForBucket()
        self.assertTrue(RadosGatewayTestCase.added_bucket is not None)
        self.assertTrue(RadosGatewayTestCase.users_added_to_mock == [])

    @mock.patch(
        'validationmanager.rados.rgwa_client.RGWAClient.get_usage',
        get_rgwa_uasge_mock)
    def testImagePushedPolling(self):
        self.engagement.engagement_manual_id = "static-engagement-manual-id"
        self.engagement.save()
        self.vf.name = "static-vf-name"
        self.vf.save()
        self.template = self.creator.createDefaultCheckListTemplate()
        checklist = self.creator.createCheckList(
            "cl-name",
            "review",
            1,
            None,
            self.engagement,
            self.template,
            self.admin_user,
            self.el_user)
        self.changeEngagementStage(EngagementStage.Active.name)
        bus_service.send_message(HourlyScheduledMessage())
        self.assertEqual(
            Checklist.objects.get(
                engagement=self.engagement,
                state=CheckListState.automation.name).state,
            CheckListState.automation.name)
        # TODO: After adding Michael's Celery invoke function -> check that the
        # image scan actually ran O.K.
