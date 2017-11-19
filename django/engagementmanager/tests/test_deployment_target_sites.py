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
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED
from engagementmanager.models import Vendor
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import Constants
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class DeploymentTargetSitesTestCase(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])
        self.createDefaultRoles()

        # Create users:
        self.admin, self.el, self.standard_user = \
            self.creator.createAndGetDefaultRoles()
        self.el_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            'Aa123456',
            'el user1',
            self.el,
            True)
        self.peer_reviewer = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'peer-reviewer user', self.el, True)
        self.user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"),
            'Aa123456',
            'user',
            self.standard_user,
            True)
        self.admin_user = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            Constants.service_provider_admin_mail,
            'Aa123456',
            'admin user',
            self.admin,
            True)

        # Create an Engagement with team
        self.engagement = self.creator.createEngagement(
            'just-a-fake-uuid', 'Validation', None)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.peer_reviewer
        self.engagement.engagement_team.add(self.user, self.el_user)
        self.engagement.save()
        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"),
            self.randomGenerator("randomString"))
        self.vendor = Vendor.objects.get(
            name=Constants.service_provider_company_name)
        self.vf = self.creator.createVF(
            self.randomGenerator("randomString"),
            self.engagement,
            self.deploymentTarget,
            False,
            self.vendor)

        # Login with users:
        self.user_token = self.loginAndCreateSessionToken(self.user)
        self.el_token = self.loginAndCreateSessionToken(self.el_user)
        self.admin_token = self.loginAndCreateSessionToken(self.admin_user)

    def testPostDeploymentTargetSitesForStandardUser(self):
        urlStr = self.urlPrefix + 'dtsites/'

        myjson = '{"name": "Middletown (ICENJ)", "vf_uuid": "' + \
            str(self.vf.uuid) + '"}'
        print(myjson)

        response = self.c.post(
            urlStr,
            myjson,
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.user_token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)

    def testPostDeploymentTargetSitesForELUser(self):
        urlStr = self.urlPrefix + 'dtsites/'

        myjson = '{"name": "Middletown (ICENJ)", "vf_uuid": "' + \
            str(self.vf.uuid) + '"}'
        print(myjson)

        response = self.c.post(
            urlStr,
            myjson,
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.el_token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def testPostDeploymentTargetSitesForAdminUser(self):
        urlStr = self.urlPrefix + 'dtsites/'

        myjson = '{"name": "Middletown (ICENJ)", "vf_uuid": "' + \
            str(self.vf.uuid) + '"}'
        print(myjson)

        response = self.c.post(
            urlStr,
            myjson,
            content_type='application/json',
            **{'HTTP_AUTHORIZATION': "token " + self.admin_token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

    def testGetDeploymentTargetSitesForStandardUser(self):
        urlStr = self.urlPrefix + 'vf/' + str(self.vf.uuid) + '/dtsites/'
        print(urlStr)
        self.printTestName("testGetDeploymentTargetSites [Start]")
        logger.debug("action should unauthorized (401)")
        response = self.c.get(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.user_token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.printTestName("testGetDeploymentTargetSites [End]")

    def testGetDeploymentTargetSitesForELUser(self):
        urlStr = self.urlPrefix + 'vf/' + str(self.vf.uuid) + '/dtsites/'
        print(urlStr)
        self.printTestName("testGetDeploymentTargetSitesForELUser [Start]")
        logger.debug("action should authorized (200)")
        response = self.c.get(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.el_token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.printTestName("testGetDeploymentTargetSitesForELUser [End]")

    def testGetDeploymentTargetSitesForAdminUser(self):
        urlStr = self.urlPrefix + 'vf/' + str(self.vf.uuid) + '/dtsites/'
        print(urlStr)
        self.printTestName("testGetDeploymentTargetSitesForAdminUser [Start]")
        logger.debug("action should authorized (200)")
        response = self.c.get(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.admin_token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.printTestName("testGetDeploymentTargetSitesForAdminUser [End]")

    def testDelDeploymentTargetSitesForStandardUser(self):
        urlStr = self.urlPrefix + 'vf/' + str(self.vf.uuid) + '/dtsites/'
        print(urlStr)
        logger.debug("action should unauthorized (401)")
        response = self.c.delete(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.user_token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
