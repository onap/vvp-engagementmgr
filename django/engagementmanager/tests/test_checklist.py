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

from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED, \
    HTTP_400_BAD_REQUEST

from engagementmanager.models import ChecklistTemplate, ChecklistLineItem
from engagementmanager.models import Vendor
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants


class TestChecklistTestCase(TestBaseEntity):

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
        self.peer_reviewer = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'peer-reviewer user', self.el, True)
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
        self.engagement.peer_reviewer = self.peer_reviewer
        self.engagement.engagement_team.add(self.user)
        self.engagement.engagement_team.add(self.el_user)
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

    def initBody(self):
        self.data['checkListName'] = "ice checklist for test"
        self.data['checkListTemplateUuid'] = str(self.template.uuid)
        self.data['checkListAssociatedFiles'] = list()
        self.data['checkListAssociatedFiles'].append("file0")
        self.data['checkListAssociatedFiles'].append("file1")
        self.data['checkListAssociatedFiles'].append("file2")

    def getOrCreateChecklist(
            self, expectedStatus=HTTP_200_OK, httpMethod="GET"):
        if (httpMethod == "GET"):
            response = self.c.get(self.urlStr.replace("@eng_uuid", str(
                self.engagement.uuid)), **{'HTTP_AUTHORIZATION': "token "
                                           + self.token})
        elif (httpMethod == "POST"):
            datajson = json.dumps(self.data, ensure_ascii=False)
            response = self.c.post(
                self.urlStr.replace("@eng_uuid", str(self.engagement.uuid)),
                datajson,
                content_type='application/json',
                **{'HTTP_AUTHORIZATION': "token "
                   + self.token})

        print('Got response : ' + str(response.status_code) +
              " Expecting " + str(expectedStatus))
        self.assertEqual(response.status_code, expectedStatus)
        return response

    def testGetChecklistPositive(self):
        self.token = self.loginAndCreateSessionToken(self.el_user)
        print("testGetChecklistPositive")
        self.getOrCreateChecklist(HTTP_200_OK)

    def testGetChecklistNegativeNoEng(self):
        self.token = self.loginAndCreateSessionToken(self.el_user)
        self.engagement.uuid = uuid4()
        print("testGetChecklistPositive")
        self.getOrCreateChecklist(HTTP_401_UNAUTHORIZED)
#

    def testPostChecklistPositive(self):
        self.initBody()
        self.token = self.loginAndCreateSessionToken(self.el_user)
        print("testPostChecklistPositive")
        self.getOrCreateChecklist(HTTP_200_OK, "POST")

    def testPostChecklistNegativeNotElUser(self):
        self.initBody()
        self.token = self.loginAndCreateSessionToken(self.user)
        print("testPostChecklistNegativeNotElUser")
        self.getOrCreateChecklist(HTTP_401_UNAUTHORIZED, "POST")

    def testPostChecklistNegativeNoEng(self):
        self.initBody()
        self.token = self.loginAndCreateSessionToken(self.el_user)
        self.engagement.uuid = uuid4()
        print("testPostChecklistNegativeNoEng")
        self.getOrCreateChecklist(HTTP_401_UNAUTHORIZED, "POST")

    def testPostChecklistNegativeMissingParam(self):
        self.token = self.loginAndCreateSessionToken(self.el_user)
        print("testPostChecklistNegativeMissingParam")
        self.getOrCreateChecklist(HTTP_400_BAD_REQUEST, "POST")

    def testPostTestEngineDecisions(self):
        self.initBody()
        self.token = self.loginAndCreateSessionToken(self.el_user)
        print("testGetChecklistPositive")
        response = self.getOrCreateChecklist(HTTP_200_OK, "POST")

        checklist = json.loads(response.content)
        self.urlStr = self.urlPrefix + "checklist/@checklist_uuid/testengine/"

        # ChecklistLineItem.objects.get(uuid=decision['line_item_id']);

        print(checklist['template']['uuid'])
        template = ChecklistTemplate.objects.get(
            uuid=checklist['template']['uuid'])
        print(template)
        line_items = ChecklistLineItem.objects.filter(template=template)
        for line_item in line_items:
            print(line_item)

        return
        self.data = dict()
        self.data['decisions'] = "{123}"
        datajson = json.dumps(self.data, ensure_ascii=False)
        response = self.c.get(self.urlStr.replace("@checklist_uuid",
                                                  str(checklist['uuid'])),
                              content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.token})

        print(json.loads(response.content))

        return

        self.data = dict()
        self.data['decisions'] = "{123}"
        datajson = json.dumps(self.data, ensure_ascii=False)
        response = self.c.post(self.urlStr.replace("@checklist_uuid",
                                                   str(checklist['uuid'])),
                               datajson,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.token})
