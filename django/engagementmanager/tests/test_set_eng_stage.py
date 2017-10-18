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
from rest_framework.status import HTTP_202_ACCEPTED,\
    HTTP_401_UNAUTHORIZED
from engagementmanager.models import Vendor
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import EngagementStage, Constants
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class TestEngagementSetStage(TestBaseEntity):

    def childSetup(self):

        self.createVendors([Constants.service_provider_company_name, 'Amdocs'])
        self.vendor = Vendor.objects.get(name='Amdocs')
        self.service_provider = Vendor.objects.get(name=Constants.service_provider_company_name)
        self.createDefaultRoles()

        # For negative tests
        self.user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), self.randomGenerator("main-vendor-email"),
            '55501000199', 'user', self.standard_user, True)
        # Create users with role el (el+peer reviwer)
        self.el_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), self.randomGenerator("main-vendor-email"),
            '55501000199', 'el user', self.el, True)
        self.peer_reviewer = self.creator.createUser(self.service_provider, self.randomGenerator(
            "main-vendor-email"), self.randomGenerator("randomNumber"), self.randomGenerator("randomString"), self.el, True)
        # Create a user with admin role
        self.admin_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), Constants.service_provider_admin_mail,
            '55501000199', 'admin user', self.admin, True)

        self.engagement = self.creator.createEngagement('just-a-fake-uuid', 'Validation', None)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.peer_reviewer
        self.engagement.engagement_team.add(self.el_user, self.user)
        self.engagement.save()

        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"), self.randomGenerator("randomString"))
#         self.asInfrastructure = self.creator.createApplicationServiceInfrastructure(self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(self.randomGenerator("randomString"),
                                        self.engagement, self.deploymentTarget, False, self.vendor)
#         self.vf.service_infrastructures.add(self.asInfrastructure)

        self.data = dict()
        self.user_token = self.loginAndCreateSessionToken(self.user)
        self.ELtoken = self.loginAndCreateSessionToken(self.el_user)
        self.admin_token = self.loginAndCreateSessionToken(self.admin_user)

    def loggerTestFailedOrSucceded(self, bool):
        if bool:
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            logger.debug(" Test Succeeded")
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        else:
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            logger.debug("Test failed")
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

    def testSetEngagementStageFullWorkFlowELUser(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(" Test started: change from Intake to Active, using --EL-- user!")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        self.urlStr = self.urlPrefix + "single-engagement/" + str(self.engagement.uuid) + "/stage/@stage"
        self.get_engagement_url = self.urlPrefix + "single-engagement/" + str(self.engagement.uuid)
        datajson = json.dumps(self.data, ensure_ascii=False)

        logger.debug("**********************************************************************")
        logger.debug("----- 1. Current stage  is " + self.engagement.engagement_stage + " -----")
        logger.debug("**********************************************************************")

        logger.debug("----- 1.1 Wishing to move from Intake stage to Active stage -----")
        logger.debug("----- 1.2 Performing a request to move forward to the next stage -----")
        response = self.c.put(self.urlStr.replace("@stage", EngagementStage.Active.name), datajson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        response2 = self.c.get(self.get_engagement_url, {}, content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})

        # Check if the correct activity was created for stage change to Active
        self.notifcation_url = self.urlPrefix + "engagement/" + str(self.engagement.uuid) + "/activities/"
        response3 = self.c.get(self.notifcation_url, {}, content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        received_notification = json.loads(response3.content)[0]['description']
        should_be = "Engagement stage is now Active for the following VF: ##vf_name##"
        self.assertEqual(should_be, received_notification)
        self.assertEqual(self.vf.name in json.loads(response3.content)[0]['metadata'], True)
        logger.debug('1.3 Please Notice, you got a ' + str(response.status_code) +
                     ' response, and was expecting a ' + str(HTTP_202_ACCEPTED) + ' response')
        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)
        logger.debug("----- 2 Wishing to move from Active stage to Validated stage -----")
        logger.debug("----- 2.1 Performing a request to move forward to the next stage -----")
        response = self.c.put(self.urlStr.replace("@stage", EngagementStage.Validated.name), datajson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        logger.debug('2.3 Please Notice, you got a ' + str(response.status_code) +
                     ' response, and was expecting a ' + str(HTTP_202_ACCEPTED) + ' response')
        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)
        logger.debug("----- 3.1 Wishing to move from Validated stage to Completed stage -----")
        logger.debug("----- 3.2 Performing a request to move forward to the next stage -----")
        response = self.c.put(self.urlStr.replace("@stage", EngagementStage.Completed.name), datajson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.ELtoken})
        logger.debug('2.4 you got a ' + str(response.status_code) +
                     ' response, and was expecting a ' + str(HTTP_202_ACCEPTED) + ' response')
        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)
        self.loggerTestFailedOrSucceded(True)

    def testSetEngagementStageFullWorkFlowAdminUser(self):

        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(" Test started: change from Intake to Active, using --ADMIN-- user!")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + "single-engagement/" + str(self.engagement.uuid) + "/stage/@stage"
        self.get_engagement_url = self.urlPrefix + "single-engagement/" + str(self.engagement.uuid)
        datajson = json.dumps(self.data, ensure_ascii=False)

        logger.debug("**********************************************************************")
        logger.debug("----- 1. Current stage  is " + self.engagement.engagement_stage + " -----")
        logger.debug("**********************************************************************")

        logger.debug("----- 1.1 Wishing to move from Intake stage to Active stage -----")
        logger.debug("----- 1.2 Performing a request to move forward to the next stage -----")
        response = self.c.put(self.urlStr.replace("@stage", EngagementStage.Active.name), datajson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.admin_token})
        logger.debug('1.3 Please Notice, you got a ' + str(response.status_code) +
                     ' response, and was expecting a ' + str(HTTP_202_ACCEPTED) + ' response')
        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)
        self.loggerTestFailedOrSucceded(False)
        logger.debug("----- 2 Wishing to move from Active stage to Validated stage -----")
        logger.debug("----- 2.1 Performing a request to move forward to the next stage -----")
        response = self.c.put(self.urlStr.replace("@stage", EngagementStage.Validated.name), datajson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.admin_token})
        logger.debug('2.3 Please Notice, you got a ' + str(response.status_code) +
                     ' response, and was expecting a ' + str(HTTP_202_ACCEPTED) + ' response')
        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)
        logger.debug("----- 3 Wishing to move from Validated stage to Completed stage -----")
        logger.debug("----- 3.1 Performing a request to move forward to the next stage -----")
        response = self.c.put(self.urlStr.replace("@stage", EngagementStage.Completed.name), datajson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.admin_token})
        logger.debug('2.4 you got a ' + str(response.status_code) +
                     ' response, and was expecting a ' + str(HTTP_202_ACCEPTED) + ' response')
        self.assertEqual(response.status_code, HTTP_202_ACCEPTED)
        self.loggerTestFailedOrSucceded(True)

    def test_negative_set_eng_Stage(self):

        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(" Test started: Negative test to change stage with un authorized user")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

        self.urlStr = self.urlPrefix + "single-engagement/" + str(self.engagement.uuid) + "/stage/@stage"
        self.get_engagement_url = self.urlPrefix + "single-engagement/" + str(self.engagement.uuid)
        datajson = json.dumps(self.data, ensure_ascii=False)

        logger.debug("**********************************************************************")
        logger.debug("----- 1. Current stage  is " + self.engagement.engagement_stage + " -----")
        logger.debug("**********************************************************************")

        logger.debug("----- 1.1 Wishing to try move from Intake stage to Active stage AND FAIL! -----")
        logger.debug("----- 1.2 Performing a request to move forward to the next stage -----")
        response = self.c.put(self.urlStr.replace("@stage", EngagementStage.Active.name), datajson,
                              content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.user_token})
        logger.debug('1.3 Please Notice, you got a ' + str(response.status_code) +
                     ' response, and was expecting a ' + str(HTTP_401_UNAUTHORIZED) + ' response')
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.loggerTestFailedOrSucceded(True)
