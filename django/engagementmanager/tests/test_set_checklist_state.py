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
from engagementmanager.models import Vendor, Checklist, ChecklistDecision, \
    ChecklistLineItem, ChecklistSection
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import CheckListLineType, \
    CheckListDecisionValue, CheckListState, ChecklistDefaultNames, Constants
from rest_framework.status import HTTP_200_OK
from uuid import uuid4
import json
from engagementmanager.service.logging_service import LoggingServiceFactory
from mocks.jenkins_mock.services.jenkins_tests_validation_service import JenkinsTestsResultsSvc

logger = LoggingServiceFactory.get_logger()


class TestChecklistSetState(TestBaseEntity):
    def initCLBody(self):
        self.clbodydata['checkListName'] = ChecklistDefaultNames.HEAT_TEMPLATES
        self.clbodydata['checkListTemplateUuid'] = str(self.template.uuid)
        self.clbodydata['checkListAssociatedFiles'] =\
            "[\"file0/f69f4ce7-51d5-409c-9d0e-ec6b1e79df28\"," \
            " \"file1/f69f4ce7-51d5-409c-9d0e-ec6b1e79df28\"," \
            " \"file2/f69f4ce7-51d5-409c-9d0e-ec6b1e79df28\"]"

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Amdocs'])
        self.vendor = Vendor.objects.get(name='Amdocs')
        self.createDefaultRoles()

        # For negative tests
        self.user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), self.randomGenerator("main-vendor-email"),
            '55501000199', 'user', self.standard_user, True)
        # Create users with role el (el+peer reviwer)
        self.el_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), self.randomGenerator("main-vendor-email"),
            '55501000199', 'el user', self.el, True)
        self.peer_review_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), self.randomGenerator("main-vendor-email"),
            '55501000199', 'peer-reviewer user', self.el, True)
        # Create a user with admin role
        self.admin_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), Constants.service_provider_admin_mail,
            '55501000199', 'admin user', self.admin, True)

        self.template = self.creator.createDefaultCheckListTemplate()
        self.engagement = self.creator.createEngagement(
            'just-a-fake-uuid', 'Validation', None)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.peer_review_user
        self.engagement.engagement_team.add(self.el_user, self.user)
        self.engagement.save()

        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"), self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(self.randomGenerator("randomString"),
                                        self.engagement, self.deploymentTarget, False, self.vendor)

        self.clbodydata = dict()
        self.initCLBody()
        self.checklist = Checklist.objects.create(uuid=uuid4(), name=self.clbodydata['checkListName'], validation_cycle=1, associated_files=self.clbodydata[
                                                  'checkListAssociatedFiles'], engagement=self.engagement, template=self.template, creator=self.el_user, owner=self.el_user)
        self.checklist.save()

        self.line_items = ChecklistLineItem.objects.filter(
            template=self.checklist.template)[:JenkinsTestsResultsSvc().num_of_auto_tests]

        self.decision = ChecklistDecision.objects.create(
            uuid=uuid4(), checklist=self.checklist, template=self.template, lineitem=self.line_items[0])
        self.decision2 = ChecklistDecision.objects.create(
            uuid=uuid4(), checklist=self.checklist, template=self.template, lineitem=self.line_items[1])
        self.decision.save()
        self.decision2.save()
        self.data = dict()
        self.peer_review_token = self.loginAndCreateSessionToken(
            self.peer_review_user)
        self.ELtoken = self.loginAndCreateSessionToken(self.el_user)
        self.admin_token = self.loginAndCreateSessionToken(self.admin_user)

    def initCLBody(self):
        self.clbodydata['checkListName'] = ChecklistDefaultNames.HEAT_TEMPLATES
        self.clbodydata['checkListTemplateUuid'] = str(self.template.uuid)
        self.clbodydata[
            'checkListAssociatedFiles'] = "[\"file0/f69f4ce7-51d5-409c-9d0e-ec6b1e79df28\", \"file1/f69f4ce7-51d5-409c-9d0e-ec6b1e79df28\", \"file2/f69f4ce7-51d5-409c-9d0e-ec6b1e79df28\"]"

    def loggerTestFailedOrSucceded(self, bool):
        if bool:
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            logger.debug(" Test Succeeded")
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        else:
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            logger.debug("Test failed")
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

    def testSetStateFullWorkFlow(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(" Test started: Full positive work flow")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + "checklist/@cl_uuid/state/"
        self.get_checklist_url = self.urlPrefix + "checklist/@cl_uuid"
        self.url_for_decision = self.urlPrefix + "checklist/decision/@decision_uuid"

        self.data['decline'] = "False"
        self.data['description'] = "BLA BLA BLA"
        datajson = json.dumps(self.data, ensure_ascii=False)

        logger.debug(
            "**********************************************************************")
        logger.debug("----- 1. Current state  is " +
                     self.checklist.state + " -----")
        logger.debug(
            "**********************************************************************")

        logger.debug(
            "----- 1.1 Wishing to move from pending state to automation state -----")
        logger.debug(
            "----- 1.2 Performing a request to move forward to the next state -----")
        response = self.c.put(self.urlStr.replace("@cl_uuid", str(self.checklist.uuid)), datajson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        logger.debug('1.3 Please Notice, you got a ' + str(response.status_code) +
                     ' response, and was expecting a ' + str(HTTP_200_OK) + ' response')
        self.assertEqual(response.status_code, HTTP_200_OK)

        logger.debug(
            "----- 2 Test engine Mock retrieved tests results, hence checklist state moved to review state. -----")
        logger.debug(
            "----- 3.1 changing decisions' review value to APPROVED -----")
        decisions = ChecklistDecision.objects.filter(checklist=self.checklist)
        for dec in decisions:
            self.data['value'] = "approved"
            datajson = json.dumps(self.data, ensure_ascii=False)
            response = self.c.put(self.url_for_decision.replace("@decision_uuid", str(dec.uuid)), datajson,
                                  content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        logger.debug(
            "----- 3.2 Wishing to move from review state to peer_review state -----")
        logger.debug(
            "----- 3.3 Performing a request to move forward to the next state -----")

        response = self.c.put(self.urlStr.replace("@cl_uuid", str(self.checklist.uuid)), datajson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        logger.debug('3.4 you got a ' + str(response.status_code) +
                     ' response, and was expecting a ' + str(HTTP_200_OK) + ' response')
        self.assertEqual(response.status_code, HTTP_200_OK)
        logger.debug(
            "----- 4.1 changing the cl peer_reviews' decisions values to NA -----")
        for dec in decisions:
            dec.peer_review_value = CheckListDecisionValue.not_relevant.name  # @UndefinedVariable
            dec.save()

        logger.debug(
            "----- 4.2 Wishing to move from peer_review state to approval state -----")
        logger.debug(
            "----- 4.3 Performing a request to move forward to the next state -----")
        response = self.c.put(self.urlStr.replace("@cl_uuid", str(self.checklist.uuid)), datajson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.peer_review_token})
        logger.debug('4.4 Please Notice, you got a ' + str(response.status_code) +
                     ' response, and was expecting a ' + str(HTTP_200_OK) + ' response')
        self.assertEqual(response.status_code, HTTP_200_OK)
        logger.debug(
            "----- 5.1 Wishing to move from approval state to handoff state -----")
        logger.debug(
            "----- 5.2 Performing a request to move forward to the next state -----")
        response = self.c.put(self.urlStr.replace("@cl_uuid", str(self.checklist.uuid)), datajson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.admin_token})
        logger.debug('Please Notice, you got a ' + str(response.status_code) +
                     ' response, and was expecting a ' + str(HTTP_200_OK) + ' response')
        self.assertEqual(response.status_code, HTTP_200_OK)
        logger.debug(
            "----- 6.1 Wishing to move from handoff state to closed state -----")
        logger.debug(
            "----- 6.2 Performing a request to move forward to the last state -----")
        response = self.c.put(self.urlStr.replace("@cl_uuid", str(self.checklist.uuid)), datajson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        logger.debug('Please Notice, you got a ' + str(response.status_code) +
                     ' response, and was expecting a ' + str(HTTP_200_OK) + ' response')
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.loggerTestFailedOrSucceded(True)

    '''
        This test checks that the signal is sent and responds with 200OK. Also that the signal logic change the checklist state to automation
    '''

    def testClFromPendingToAutomationSignal(self):

        self.urlStr = self.urlPrefix + "checklist/@cl_uuid/state/"
        self.get_checklist_url = self.urlPrefix + "checklist/@cl_uuid"
        self.url_for_decision = self.urlPrefix + "checklist/decision/@decision_uuid"

        self.data['decline'] = "False"
        self.data['description'] = "BLA BLA BLA"
        datajson = json.dumps(self.data, ensure_ascii=False)

        cl = Checklist.objects.get(uuid=self.checklist.uuid)
        cl.state = CheckListState.pending.name  # @UndefinedVariable
        cl.save()
        res1 = self.c.put(self.urlStr.replace("@cl_uuid", str(self.checklist.uuid)), datajson,
                          content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        self.assertEqual(res1.status_code, HTTP_200_OK)
