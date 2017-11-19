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
from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST,\
    HTTP_401_UNAUTHORIZED, HTTP_500_INTERNAL_SERVER_ERROR,\
    HTTP_405_METHOD_NOT_ALLOWED
from engagementmanager.models import Vendor, Checklist, ChecklistAuditLog, \
    ChecklistDecision, ChecklistLineItem, ChecklistSection
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import CheckListLineType, \
    CheckListDecisionValue, CheckListState, Constants
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class AuditLogAndDecisionAPITest(TestBaseEntity):

    def childSetup(self):

        self.createVendors(
            [Constants.service_provider_company_name, 'Amdocs', 'Other'])
        self.createDefaultRoles()

        # Create a user with role el
        self.el_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            '12323245435',
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
            '12323245435',
            'user',
            self.standard_user,
            True)

        self.template = self.creator.createDefaultCheckListTemplate()
        self.engagement = self.creator.createEngagement(
            uuid4(), 'Validation', None)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.peer_reviewer
        self.engagement.save()
        self.engagement.engagement_team.add(self.el_user, self.user)
        self.clbodydata = dict()
        self.initCLBody()
        self.auditdata = dict()
        self.checklist = Checklist.objects.create(
            uuid=uuid4(),
            name=self.clbodydata['checkListName'],
            validation_cycle=1,
            associated_files=self.clbodydata['checkListAssociatedFiles'],
            engagement=self.engagement,
            template=self.template,
            creator=self.el_user,
            owner=self.el_user)
        self.section = ChecklistSection.objects.create(
            uuid=uuid4(),
            name=self.randomGenerator("randomString"),
            weight=1.0,
            description=self.randomGenerator("randomString"),
            validation_instructions=self.randomGenerator("randomString"),
            template=self.template)
        self.line_item = ChecklistLineItem.objects.create(
            uuid=uuid4(),
            name=self.randomGenerator("randomString"),
            weight=1.0,
            description=self.randomGenerator("randomString"),
            line_type=CheckListLineType.auto.name,
            validation_instructions=self.randomGenerator("randomString"),
            template=self.template,
            section=self.section)  # @UndefinedVariable
        self.decision = ChecklistDecision.objects.create(
            uuid=uuid4(),
            checklist=self.checklist,
            template=self.template,
            lineitem=self.line_item)
        self.section.save()
        self.line_item.save()
        self.decision.save()
        self.checklist.save()
        self.token = self.loginAndCreateSessionToken(self.user)
        self.ELtoken = self.loginAndCreateSessionToken(self.el_user)

    def initCLBody(self):
        self.clbodydata['checkListName'] = "ice-checklist-for-test"
        self.clbodydata['checkListTemplateUuid'] = str(self.template.uuid)
        self.clbodydata[
            'checkListAssociatedFiles'] = "\
            [\"file0/f69f4ce7-51d5-409c-9d0e-ec6b1e79df28\",\
             \"file1/f69f4ce7-51d5-409c-9d0e-ec6b1e79df28\",\
              \"file2/f69f4ce7-51d5-409c-9d0e-ec6b1e79df28\"]"

    def loggerTestFailedOrSucceded(self, bool_flag):
        if bool_flag:
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            logger.debug(" Test Succeeded")
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        else:
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            logger.debug("Test failed")
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

    def testCreateAuditLogViaChecklistPositive(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(" Test started: Create AuditLog Via Checklist")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + "checklist/@cl_uuid/auditlog/"

        logger.debug("Creating a checklist")
        self.auditdata['description'] = "description text"
        datajson = json.dumps(self.auditdata, ensure_ascii=False)

        response = self.c.post(self.urlStr.replace("@cl_uuid",
                                                   str(self.checklist.uuid)),
                               datajson,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token "
                                  + self.ELtoken})
        logger.debug('Got response : ' + str(response.status_code) +
                     " Expecting " + str(HTTP_200_OK))

        check = True
        try:
            ChecklistAuditLog.objects.get(checklist=self.checklist)
        except ChecklistAuditLog.DoesNotExist:
            check = False

        if (response.status_code == HTTP_200_OK and check):
            self.loggerTestFailedOrSucceded(True)
            self.assertEqual(response.status_code, HTTP_200_OK)
        else:
            self.loggerTestFailedOrSucceded(False)
            self.assertEqual(response.status_code, HTTP_200_OK)

    def testCreateAuditLogViaChecklistNegativeEmptyDescription(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(
            " Negative Test started: Create AuditLog Via \
            Checklist with empty description")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + "checklist/@cl_uuid/auditlog/"

        logger.debug("Creating a checklist")

        self.auditdata['description'] = ""
        datajson = json.dumps(self.auditdata, ensure_ascii=False)

        response = self.c.post(self.urlStr.replace("@cl_uuid",
                                                   str(self.checklist.uuid)),
                               datajson,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token "
                                  + self.ELtoken})
        logger.debug('Got response : ' + str(response.status_code) +
                     " Expecting " + str(HTTP_400_BAD_REQUEST))

        if (response.status_code == HTTP_400_BAD_REQUEST):
            self.loggerTestFailedOrSucceded(True)
            self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        else:
            self.loggerTestFailedOrSucceded(False)
            self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def testCreateAuditLogViaChecklistNegativeBadCLUuid(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(
            " Negative Test started: Create AuditLog Via \
            Checklist with bad CL uuid")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + "checklist/@cl_uuid/auditlog/"

        logger.debug("Creating a checklist")

        self.auditdata['description'] = "description text"
        datajson = json.dumps(self.auditdata, ensure_ascii=False)

        response = self.c.post(self.urlStr.replace("@cl_uuid",
                                                   str(uuid4())),
                               datajson,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.token})
        logger.debug('Got response : ' + str(response.status_code) +
                     " Expecting " + str(HTTP_500_INTERNAL_SERVER_ERROR))

        if (response.status_code == HTTP_500_INTERNAL_SERVER_ERROR):
            self.loggerTestFailedOrSucceded(True)
        else:
            self.loggerTestFailedOrSucceded(False)

        self.assertEqual(response.status_code, HTTP_500_INTERNAL_SERVER_ERROR)

    def testCreateAuditLogViaDecisionPositive(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(" Test started: Create AuditLog Via Decision")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + \
            "checklist/decision/@decision_uuid/auditlog/"

        logger.debug("Creating a checklist")

        self.auditdata['description'] = "description text"
        datajson = json.dumps(self.auditdata, ensure_ascii=False)

        response = self.c.post(self.urlStr.replace("@decision_uuid",
                                                   str(self.decision.uuid)),
                               datajson,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token "
                                  + self.ELtoken})
        logger.debug('Got response : ' + str(response.status_code) +
                     " Expecting " + str(HTTP_200_OK))

        check = ChecklistAuditLog.objects.get(decision=self.decision)
        if (response.status_code == HTTP_200_OK and check):
            self.loggerTestFailedOrSucceded(True)
        else:
            self.loggerTestFailedOrSucceded(False)
            self.assertEqual(response.status_code, HTTP_200_OK)

    def testCreateAuditLogViaDecisionNegativeEmptyDescription(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(
            " Negative Test started: Create AuditLog Via \
            Decision with empty description")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + \
            "checklist/decision/@decision_uuid/auditlog/"

        logger.debug("Creating a checklist")

        self.auditdata['description'] = ""
        datajson = json.dumps(self.auditdata, ensure_ascii=False)

        response = self.c.post(self.urlStr.replace("@decision_uuid",
                                                   str(self.decision.uuid)),
                               datajson,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token "
                                  + self.ELtoken})
        logger.debug('Got response : ' + str(response.status_code) +
                     " Expecting " + str(HTTP_400_BAD_REQUEST))

        if (response.status_code == HTTP_400_BAD_REQUEST):
            self.loggerTestFailedOrSucceded(True)
            self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        else:
            self.loggerTestFailedOrSucceded(False)
            self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def testCreateAuditLogViaDecisionNegativeBadCLUuid(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(
            " Negative Test started: Create AuditLog Via \
            Decision with bad Decision uuid")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + \
            "checklist/decision/@decision_uuid/auditlog/"

        logger.debug("Creating a checklist")

        self.auditdata['description'] = "description text"
        datajson = json.dumps(self.auditdata, ensure_ascii=False)

        response = self.c.post(self.urlStr.replace("@decision_uuid",
                                                   str(uuid4())),
                               datajson,
                               content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token "
                                  + self.ELtoken})
        logger.debug('Got response : ' + str(response.status_code) +
                     " Expecting " + str(HTTP_400_BAD_REQUEST))

        if (response.status_code == HTTP_400_BAD_REQUEST):
            self.loggerTestFailedOrSucceded(True)
            self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        else:
            self.loggerTestFailedOrSucceded(False)
            self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def testSetDecisionPositive(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(" Test started: Set decision's value to approved")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + "checklist/decision/@decision_uuid"

        logger.debug("Creating a checklist")

        self.checklist.state = CheckListState.review.name
        self.checklist.owner = self.el_user
        self.checklist.save()
        # @UndefinedVariable
        self.auditdata['value'] = CheckListDecisionValue.approved.name
        datajson = json.dumps(self.auditdata, ensure_ascii=False)

        response = self.c.put(
            self.urlStr.replace("@decision_uuid",
                                str(self.decision.uuid)),
            datajson,
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        logger.debug('Got response : ' + str(response.status_code) +
                     " Expecting " + str(HTTP_200_OK))

        check = ChecklistDecision.objects.get(checklist=self.checklist)
        if (response.status_code == HTTP_200_OK and
                check.review_value == 'approved'):
            self.loggerTestFailedOrSucceded(True)
            self.assertEqual(response.status_code, HTTP_200_OK)
        else:
            self.loggerTestFailedOrSucceded(False)
            self.assertEqual(response.status_code, HTTP_200_OK)

    def testSetDecisionNegativeOwnerDifferentThanUser(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(" Negative Test started: Owner Different Than User")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + "checklist/decision/@decision_uuid"

        logger.debug("Creating a checklist")

        self.checklist.state = CheckListState.review.name
        self.checklist.owner = self.user
        self.checklist.save()
        # @UndefinedVariable
        self.auditdata['value'] = CheckListDecisionValue.approved.name
        datajson = json.dumps(self.auditdata, ensure_ascii=False)

        response = self.c.put(
            self.urlStr.replace("@decision_uuid",
                                str(self.decision.uuid)),
            datajson,
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        logger.debug('Got response : ' + str(response.status_code) +
                     " Expecting " + str(HTTP_401_UNAUTHORIZED))

        if (response.status_code == HTTP_401_UNAUTHORIZED):
            self.loggerTestFailedOrSucceded(True)
            self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        else:
            self.loggerTestFailedOrSucceded(False)
            self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def testSetDecisionNegativeInvalidDecisionValue(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug("Negative Test started: Invalid Decision Value")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + "checklist/decision/@decision_uuid"

        logger.debug("Creating a checklist")

        self.checklist.state = CheckListState.review.name
        self.checklist.owner = self.el_user
        self.checklist.save()
        self.auditdata['value'] = self.randomGenerator("randomString")
        datajson = json.dumps(self.auditdata, ensure_ascii=False)

        response = self.c.put(
            self.urlStr.replace("@decision_uuid",
                                str(self.decision.uuid)),
            datajson,
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        logger.debug('Got response : ' + str(response.status_code) +
                     " Expecting " + str(HTTP_400_BAD_REQUEST))

        if (response.status_code == HTTP_400_BAD_REQUEST):
            self.loggerTestFailedOrSucceded(True)
            self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        else:
            self.loggerTestFailedOrSucceded(False)
            self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def testSetDecisionNegativeInvalidChecklistState(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug("Negative Test started: Invalid checklist state")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + "checklist/decision/@decision_uuid"

        logger.debug("Creating a checklist")

        self.checklist.state = self.randomGenerator(
            "randomString")  # @UndefinedVariable
        self.checklist.owner = self.el_user
        self.checklist.save()
        # @UndefinedVariable
        self.auditdata['value'] = CheckListDecisionValue.approved.name
        datajson = json.dumps(self.auditdata, ensure_ascii=False)

        response = self.c.put(
            self.urlStr.replace("@decision_uuid",
                                str(self.decision.uuid)),
            datajson,
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        logger.debug('Got response : ' + str(response.status_code) +
                     " Expecting " + str(HTTP_400_BAD_REQUEST))

        if (response.status_code == HTTP_400_BAD_REQUEST):
            self.loggerTestFailedOrSucceded(True)
            self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        else:
            self.loggerTestFailedOrSucceded(False)
            self.assertEqual(response.status_code,
                             HTTP_405_METHOD_NOT_ALLOWED)
