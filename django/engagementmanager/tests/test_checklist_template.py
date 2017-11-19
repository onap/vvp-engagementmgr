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

import mock
from rest_framework.status import HTTP_200_OK, HTTP_404_NOT_FOUND,\
    HTTP_500_INTERNAL_SERVER_ERROR

from engagementmanager.models import Vendor
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants


def dummy_true():
    return True


@mock.patch(
    'engagementmanager.service.checklist_service.' +
    'CheckListSvc.decline_all_template_checklists',
    dummy_true)
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
        self.admin_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            Constants.service_provider_admin_mail,
            '55501000199',
            'admin user',
            self.admin,
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
        self.urlStrForSave = self.urlPrefix + "checklist/template/"
        self.urlStrForGetTmpl = self.urlPrefix + \
            "checklist/template/@template_uuid"
        self.urlStrForGetTmpls = self.urlPrefix + "checklist/templates/"
        self.data = dict()
        self.template = self.creator.createDefaultCheckListTemplate()
        self.engagement = self.creator.createEngagement(
            'just-a-fake-uuid', 'Validation', None)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.el_user
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
        self.data['uuid'] = str(self.template.uuid)
        self.data['name'] = self.template.name
        self.data['sections'] = list()
        li1 = dict()
        li1["uuid"] = "newEntity"
        li1["name"] = "li1_name"
        li1["description"] = "li1_description"
        li1["validation_instructions"] = "li1_validation_instructions"

        sec1 = dict()
        sec1["uuid"] = "newEntity"
        sec1["name"] = "sec1_name"
        sec1["description"] = "sec1_description"
        sec1["validation_instructions"] = "sec1_validation_instructions"

        sec1["lineItems"] = list()
        sec1["lineItems"].append(li1)

        self.data['sections'].append(sec1)
        print(self.data)

    def getOrCreateChecklistTemplate(
            self, urlStr, expectedStatus=HTTP_200_OK, httpMethod="GET"):
        if (httpMethod == "GET"):
            if (urlStr == self.urlStrForGetTmpls):
                response = self.c.get(
                    urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
            else:
                response = self.c.get(
                    urlStr.replace("@template_uuid", str(
                        self.template.uuid)),
                    **{'HTTP_AUTHORIZATION': "token " + self.token})
        elif (httpMethod == "PUT"):
            datajson = json.dumps(self.data, ensure_ascii=False)
            response = self.c.put(
                urlStr,
                datajson,
                content_type='application/json',
                **{'HTTP_AUTHORIZATION': "token " + self.token})
            print('Got response : ' + str(response.status_code) +
                  " Expecting " + str(expectedStatus))
        print('Got response : ' + str(response.status_code) +
              " Expecting " + str(expectedStatus))
        self.assertEqual(response.status_code, expectedStatus)
        return response

    def testSaveChecklistTemplate(self):
        self.initBody()
        self.token = self.loginAndCreateSessionToken(self.admin_user)
        print("testSaveChecklistTemplate")
        self.getOrCreateChecklistTemplate(self.urlStrForSave, httpMethod="PUT")

    def testSaveChecklistTemplateMissingTemplateUuid(self):
        self.initBody()
        self.token = self.loginAndCreateSessionToken(self.admin_user)
        self.data['uuid'] = ""
        print("testSaveChecklistTemplateMissingTemplateUuid")
        self.getOrCreateChecklistTemplate(
            self.urlStrForSave,
            expectedStatus=HTTP_404_NOT_FOUND,
            httpMethod="PUT")

    def testSaveChecklistTemplateNotExistingTemplate(self):
        self.initBody()
        self.token = self.loginAndCreateSessionToken(self.admin_user)
        print("testSaveChecklistTemplateNoExistanceTemplate")
        self.data['uuid'] = 'fake_uuid'
        self.getOrCreateChecklistTemplate(
            self.urlStrForSave,
            expectedStatus=HTTP_404_NOT_FOUND,
            httpMethod="PUT")

    def testSaveChecklistTemplateMissingKey(self):
        self.initBody()
        self.token = self.loginAndCreateSessionToken(self.admin_user)
        print("testSaveChecklistTemplateNoExistanceTemplate")
        # take the first line item (li1_name) which is newEntity and remove its
        # name, expect 500
        self.data['sections'][0]["lineItems"][0]["name"] = None
        self.getOrCreateChecklistTemplate(
            self.urlStrForSave,
            expectedStatus=HTTP_500_INTERNAL_SERVER_ERROR,
            httpMethod="PUT")

    def testGetChecklistTemplates(self):
        self.initBody()
        self.token = self.loginAndCreateSessionToken(self.admin_user)
        print("testSaveChecklistTemplate")
        self.getOrCreateChecklistTemplate(
            self.urlStrForGetTmpls, httpMethod="GET")

    def testGetChecklistTemplate(self):
        self.initBody()
        self.token = self.loginAndCreateSessionToken(self.admin_user)
        print("testSaveChecklistTemplate")
        self.getOrCreateChecklistTemplate(
            self.urlStrForGetTmpl, httpMethod="GET")
