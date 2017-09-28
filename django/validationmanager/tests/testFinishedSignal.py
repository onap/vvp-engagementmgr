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

from django.conf import settings
from rest_framework.status import HTTP_200_OK

from engagementmanager.models import Vendor, ChecklistSection, ChecklistDecision, ChecklistLineItem
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import CheckListLineType,\
    CheckListDecisionValue, Constants


class TestTestFinishedSignalCase(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Amdocs'])
        self.createDefaultRoles()

        self.el_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"), '55501000199', 'el user', self.el, True)
        self.user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"), '55501000199', 'user', self.standard_user, True)
        self.peer_reviewer = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"), '55501000199', 'peer-reviewer user', self.el, True)
        token = settings.WEBHOOK_TOKEN
        self.urlStr = "/v/hook/test-complete/" + token

        self.req = dict()
        self.token = self.loginAndCreateSessionToken(self.el_user)
        self.template = self.creator.createDefaultCheckListTemplate()
        self.engagement = self.creator.createEngagement('just-a-fake-uuid', 'Validation', None)
        self.engagement.engagement_team.add(self.el_user, self.user)
        self.checklist = self.creator.createCheckList(
            'some-checklist', 'Automation', 1, '{}', self.engagement, self.template, self.el_user, self.peer_reviewer)
        self.section = ChecklistSection.objects.create(uuid=uuid4(), name=self.randomGenerator("randomString"), weight=1.0, description=self.randomGenerator(
            "randomString"), validation_instructions=self.randomGenerator("randomString"), template=self.template)
        self.line_item = ChecklistLineItem.objects.create(uuid=uuid4(), name=self.randomGenerator("randomString"), weight=1.0, description=self.randomGenerator(
            "randomString"), line_type=CheckListLineType.auto.name, validation_instructions=self.randomGenerator("randomString"), template=self.template, section=self.section)  # @UndefinedVariable
        self.decision = ChecklistDecision.objects.create(
            uuid=uuid4(), checklist=self.checklist, template=self.template, lineitem=self.line_item)
        self.vendor = Vendor.objects.get(name=Constants.service_provider_company_name)
        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"), self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(self.randomGenerator("randomString"),
                                        self.engagement, self.deploymentTarget, False, self.vendor)

    def initBody(self):
        self.req['checklist'] = dict()
        self.req['checklist']['checklist_uuid'] = str(self.checklist.uuid)
        decisionData = dict()
        decisionData['line_item_id'] = str(self.line_item.uuid)
        decisionData['value'] = CheckListDecisionValue.approved.name  # @UndefinedVariable
        decisionData['audit_log_text'] = "audiot text blah blaj"
        self.req['checklist']['decisions'] = [decisionData]
        self.req['build'] = dict()
        self.req['build']['phase'] = 'FINALIZED'
        self.req['build']['url'] = "http://samplejob"
        self.req['build']['log'] = "Jenkins Log Example"

    ### TESTS ###
    def testFinishedSignalPositive(self):
        if not settings.IS_SIGNAL_ENABLED:
            return

        self.initBody()
        datajson = json.dumps(self.req, ensure_ascii=False)
        response = self.c.post(self.urlStr, datajson, content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.token})

        print('Got response : ' + str(response.status_code) +
              " Expecting 200. response body:  " + response.reason_phrase)
        self.assertEqual(response.status_code, HTTP_200_OK)
