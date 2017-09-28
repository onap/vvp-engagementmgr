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
from rest_framework.status import HTTP_204_NO_CONTENT, HTTP_200_OK
from engagementmanager.models import Vendor
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class VFCAPITestCase(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])
        self.createDefaultRoles()
        # Create a user with role el
        self.service_provider = Vendor.objects.get(name=Constants.service_provider_company_name)
        self.el_user = self.creator.createUser(self.service_provider, self.randomGenerator(
            "main-vendor-email"), self.randomGenerator("randomNumber"), self.randomGenerator("randomString"), self.el, True)
        logger.debug('-----------------------------------------------------')
        logger.debug('Created User:')
        logger.debug('UUID: ' + str(self.el_user.uuid))
        logger.debug('Full Name: ' + self.el_user.full_name)
        logger.debug('-----------------------------------------------------')
        self.peer_reviewer = self.creator.createUser(self.service_provider, self.randomGenerator(
            "main-vendor-email"), self.randomGenerator("randomNumber"), self.randomGenerator("randomString"), self.el, True)
        logger.debug('-----------------------------------------------------')
        logger.debug('Created Peer Reviewer:')
        logger.debug('UUID: ' + str(self.peer_reviewer.uuid))
        logger.debug('Full Name: ' + self.peer_reviewer.full_name)
        logger.debug('-----------------------------------------------------')

        # Create a user with role standard_user
        self.vendor = Vendor.objects.get(name='Other')
        self.user = self.creator.createUser(self.vendor, self.randomGenerator("email"), self.randomGenerator(
            "randomNumber"), self.randomGenerator("randomString"), self.standard_user, True)
        logger.debug('-----------------------------------------------------')
        logger.debug('Created User:')
        logger.debug('UUID: ' + str(self.user.uuid))
        logger.debug('Full Name: ' + self.user.full_name)
        logger.debug('-----------------------------------------------------')

        # Create an Engagement with team
        self.engagement = self.creator.createEngagement(self.randomGenerator(
            "randomString"), self.randomGenerator("randomString"), None)
        self.engagement.engagement_team.add(self.user, self.el_user, self.peer_reviewer)
        self.engagement.peer_reviewer = self.peer_reviewer
        self.engagement.reviewer = self.el_user
        self.engagement.save()
        logger.debug('-----------------------------------------------------')
        logger.debug('Created Engagement:')
        logger.debug('UUID: ' + str(self.engagement.uuid))
        logger.debug('-----------------------------------------------------')

        # Create a DT, DTSite, VF
        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"), self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(self.randomGenerator("randomString"),
                                        self.engagement, self.deploymentTarget, False, self.vendor)

        logger.debug('-----------------------------------------------------')
        logger.debug('Created VF:')
        logger.debug('UUID: ' + str(self.vendor.uuid))
        logger.debug('-----------------------------------------------------')

        self.token = self.loginAndCreateSessionToken(self.user)
        self.ELtoken = self.loginAndCreateSessionToken(self.el_user)

    def retrieveCurrentObjectsOfEngagementByFilter(self, method, detailOrObject, entity):
        if method == 'filter':
            list = entity.objects.filter(engagement=detailOrObject)
            return list
        elif method == 'get':
            list = entity.objects.get(uuid=detailOrObject)
            return list

    def loggerTestFailedOrSucceded(self, bool):
        if bool:
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            logger.debug(" Test Succeeded")
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        else:
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
            logger.debug("Test failed")
            logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")

    def testCreateDTSiteAddToVF(self):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(" Test started: Create DTSite and add to VF")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        self.deploymentTargetSite = self.creator.createDeploymentTargetSite(self.randomGenerator("randomString"))
        self.vf.deployment_target_sites.add(self.deploymentTargetSite)
        sites = self.vf.deployment_target_sites.all()
        num = 1
        for item in sites:
            logger.debug(str(num) + ". " + item.name)
        print("\n")
        if (self.vf.deployment_target_sites.all().count() > 0):
            self.loggerTestFailedOrSucceded(True)
        else:
            self.loggerTestFailedOrSucceded(False)

    def testDeleteVFC(self, expectedStatus=HTTP_204_NO_CONTENT):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(" Test started: Delete VFC")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        vfc = self.creator.createVFC(self.randomGenerator("randomString"), self.randomGenerator(
            "randomNumber"), self.vendor, self.vf, self.el_user)
        urlStr = self.urlPrefix + 'vf/' + str(vfc.uuid) + '/vfcs/' + str(vfc.uuid)
        if (vfc == None):
            logger.error("vfc wasn't created successfully before the deletion attempt")
            self.loggerTestFailedOrSucceded(False)
            self.assertEqual(500, expectedStatus)
        response = self.c.delete(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        logger.debug('Got response : ' + str(response.status_code))
        if (response.status_code == HTTP_204_NO_CONTENT):
            self.loggerTestFailedOrSucceded(True)
        else:
            self.loggerTestFailedOrSucceded(False)
        self.assertEqual(response.status_code, expectedStatus)

    def testGetVFC(self, expectedStatus=HTTP_200_OK):
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$")
        logger.debug(" Test started: Get VFCs")
        logger.debug("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$\n\n")
        vfc = self.creator.createVFC(self.randomGenerator("randomString"), self.randomGenerator(
            "randomNumber"), self.vendor, self.vf, self.el_user)
        vfc2 = self.creator.createVFC(self.randomGenerator("randomString"), self.randomGenerator(
            "randomNumber"), self.service_provider, self.vf, self.el_user)
        urlStr = self.urlPrefix + 'vf/' + str(self.vf.uuid) + '/vfcs/'
        if (vfc == None or vfc2 == None):
            logger.error("The VFCs were not created successfully before the deletion attempt")
            self.loggerTestFailedOrSucceded(False)
            self.assertEqual(500, expectedStatus)
        response = self.c.get(urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        logger.debug('Got response : ' + str(response.status_code))
        logger.debug("VFCs found in the VF(through the GET request):")
        logger.debug(str(response.content))
        if (response.status_code == HTTP_200_OK):
            self.loggerTestFailedOrSucceded(True)
        else:
            self.loggerTestFailedOrSucceded(False)
        self.assertEqual(response.status_code, expectedStatus)
