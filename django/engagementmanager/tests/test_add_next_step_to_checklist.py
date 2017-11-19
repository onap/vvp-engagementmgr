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
from uuid import uuid4

from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED

from engagementmanager.models import Vendor
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants


class TestAddNextStepToChecklistTestCase(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])
        self.vendor = Vendor.objects.get(
            name=Constants.service_provider_company_name)
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
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.el_user.uuid))
        print('Full Name: ' + self.el_user.full_name)
        print('-----------------------------------------------------')

        # Create a user with role el
        self.peer_reviewer_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'peer-reviewer user',
            self.el,
            True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.el_user.uuid))
        print('Full Name: ' + self.el_user.full_name)
        print('-----------------------------------------------------')

        self.user2 = self.creator.createUser(
            Vendor.objects.get(
                name='Other'),
            self.randomGenerator("main-vendor-email"),
            '55501000199',
            'user',
            self.standard_user,
            True)
        print('-----------------------------------------------------')
        print('Created User:')
        print('UUID: ' + str(self.user2.uuid))
        print('Full Name: ' + self.user2.full_name)
        print('-----------------------------------------------------')

        # Create an Engagement with team
        self.engagement = self.creator.createEngagement(
            '123456789', 'Validation', None)
        self.engagement.reviewer = self.el_user
        self.engagement.engagement_team.add(self.el_user)
        self.engagement.peer_reviewer = self.peer_reviewer_user
        self.engagement.save()
        print('-----------------------------------------------------')
        print('Created Engagement:')
        print('UUID: ' + str(self.engagement.uuid))
        print('-----------------------------------------------------')

        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"),
            self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(
            self.randomGenerator("randomString"),
            self.engagement,
            self.deploymentTarget,
            False,
            self.vendor)
        print('-----------------------------------------------------')
        print('Created VF:')
        print('UUID: ' + str(self.vf.uuid))
        print('-----------------------------------------------------')

        self.template = self.creator.createDefaultCheckListTemplate()
        self.data = dict()
        self.data['checkListName'] = "ice checklist for test"
        self.data['checkListTemplateUuid'] = str(self.template.uuid)
        self.data['checkListAssociatedFiles'] = []
        for i in range(0, 2):
            self.data['checkListAssociatedFiles'].append("file" + str(i))
        self.token = self.loginAndCreateSessionToken(self.el_user)
        datajson = json.dumps(self.data, ensure_ascii=False)
        self.clUrlStr = self.urlPrefix + "engagement/@eng_uuid/checklist/new/"
        self.checklist = self.c.post(
            self.clUrlStr.replace(
                "@eng_uuid", str(
                    self.engagement.uuid)), datajson,
            content_type='application/json', **{
                'HTTP_AUTHORIZATION': "token " + self.token})

        self.urlStr = self.urlPrefix + \
            "engagement/@eng_uuid/checklist/@checklist_uuid/nextstep/"
        self.nextStepList = []

    def initBody(self):
        assigneesData = [str(self.el_user.uuid), str(self.user2.uuid)]
        files = ["f1", "f2"]
        self.data['assigneesUuids'] = assigneesData
        self.data['description'] = "Good Bye Norma Jin"
        self.data['files'] = files
        self.data['duedate'] = "2016-12-01"
        self.nextStepList.append(self.data)

        assigneesData = [str(self.el_user.uuid)]
        files = ["f5"]
        self.data['assigneesUuids'] = assigneesData
        self.data['description'] = "Don't cry for me Argentina"
        self.data['files'] = files
        self.data['duedate'] = "2017-06-28"
        self.nextStepList.append(self.data)

    def testAddNextStepForCheckListPositive(self):
        self.initBody()
        self.nextStepList = json.dumps(self.nextStepList, ensure_ascii=False)
        self.urlStr = self.urlStr.replace(
            "@checklist_uuid", json.loads(
                self.checklist.content)['uuid']).replace(
            "@eng_uuid", str(
                self.engagement.uuid))
        response = self.c.post(self.urlStr,
                               self.nextStepList,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        return response

    def testAddNextStepForCheckListNegative(self):
        self.initBody()
        self.nextStepList = json.dumps(self.nextStepList, ensure_ascii=False)
        self.urlStr = self.urlStr.replace("@checklist_uuid", json.loads(
            self.checklist.content)['uuid']).replace("@eng_uuid", str(uuid4()))
        response = self.c.post(self.urlStr,
                               self.nextStepList,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('------------------------------> Got response : ' +
              str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        return response
