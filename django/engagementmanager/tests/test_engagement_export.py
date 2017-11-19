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
from rest_framework.status import HTTP_200_OK,\
    HTTP_500_INTERNAL_SERVER_ERROR
from engagementmanager.models import Vendor, ECOMPRelease
from engagementmanager.service.engagement_service \
    import get_expanded_engs_for_export
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import EngagementStage, Constants
from engagementmanager.service.logging_service import LoggingServiceFactory
from django.conf import settings

logger = LoggingServiceFactory.get_logger()


class EngagementExportTestCase(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])
        self.createDefaultRoles()
        self.admin, self.el, self.standard_user = \
            self.creator.createAndGetDefaultRoles()
        self.peer_reviewer = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'peer-reviewer user', self.el, True)
        self.admin = self.creator.createUser(
            Vendor.objects.get(
                name=Constants.service_provider_company_name),
            Constants.service_provider_admin_mail,
            'Aa123456',
            'admin user',
            self.el,
            True)
        self.user = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            'Aa123456', 'user', self.standard_user, True)

        # Create an VF with Engagement (Active) - #1
        self.engagement = self.creator.createEngagement(
            'just-a-fake-uuid', 'Validation', None)
        self.engagement.engagement_team.add(self.user, self.admin)
        self.engagement.reviewer = self.admin
        self.engagement.peer_reviewer = self.peer_reviewer
        self.engagement.engagement_stage = EngagementStage.Active.name
        self.engagement.save()
        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"),
            self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(
            self.randomGenerator("randomString"),
            self.engagement,
            self.deploymentTarget,
            False,
            Vendor.objects.get(
                name=Constants.service_provider_company_name))
        self.vf.ecomp_release = ECOMPRelease.objects.create(
            uuid='uuid1', name='ActiveECOMPRelease')
        self.vf.save()

        # Create an VF with Engagement (Intake) - #2
        self.engagement2 = self.creator.createEngagement(
            'just-a-fake-uuid2', 'Validation', None)
        self.engagement2.engagement_team.add(self.user, self.admin)
        self.engagement2.reviewer = self.admin
        self.engagement2.peer_reviewer = self.peer_reviewer
        self.engagement2.engagement_stage = EngagementStage.Intake.name
        self.engagement2.save()
        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"),
            self.randomGenerator("randomString"))
        self.vf2 = self.creator.createVF(
            self.randomGenerator("randomString"),
            self.engagement2,
            self.deploymentTarget,
            False,
            Vendor.objects.get(
                name='Other'))
        self.vf2.ecomp_release = ECOMPRelease.objects.create(
            uuid='uuid2', name='IntakeECOMPRelease')
        self.vf2.save()

        self.token = self.loginAndCreateSessionToken(self.user)
        self.adminToken = self.loginAndCreateSessionToken(self.admin)

    def testFailExport(self):
        urlStr = self.urlPrefix + 'engagement/export/'
        self.printTestName("Failed export [start]")
        logger.debug(
            "action should fail (500), missing arguments - stage and keyword")
        response = self.c.get(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_500_INTERNAL_SERVER_ERROR)
        self.printTestName("Failed export [end]")

    def testSuccessExport(self):
        self.printTestName("Success export [start]")

        if settings.DATABASES["default"]["ENGINE"] == \
                "django.db.backends.sqlite3":
            return

        urlStr = self.urlPrefix + 'engagement/export/?stage=Active&keyword'
        logger.debug(
            "action should success (200), and return one active engagement")
        response = self.c.get(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(response.content) > 0, True)
        vfs, deployment_targets = get_expanded_engs_for_export(
            "Active", "", self.user)
        self.assertEqual(len(vfs) == 1, True)
        self.assertEqual('ecomp_release__name' in vfs[0] and vfs[0]
                         ['ecomp_release__name'] == "ActiveECOMPRelease", True)

        urlStr = self.urlPrefix + 'engagement/export/?stage=Intake&keyword'
        logger.debug(
            "action should success (200), and return one intake engagement")
        response = self.c.get(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(response.content) > 0, True)
        vfs, deployment_targets = get_expanded_engs_for_export(
            "Intake", "", self.user)
        self.assertEqual(len(vfs) == 1, True)
        self.assertEqual('ecomp_release__name' in vfs[0] and vfs[0]
                         ['ecomp_release__name'] == "IntakeECOMPRelease", True)

        # Check keyword filtering:
        urlStr = self.urlPrefix + 'engagement/export/?stage=All&keyword=Active'
        logger.debug(
            "action should success (200), and not return Intake engagement")
        response = self.c.get(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertEqual(len(response.content) > 0, True)
        vfs, deployment_targets = get_expanded_engs_for_export(
            "All", "Active", self.user)
        self.assertEqual(len(vfs) == 0, True)

        # Check overview sheet data procedure:
        logger.debug(
            "Check if the store procedure return data as expected \
            (suppose to return 4 rows of overview "
            "sheet) and by that assume that it exists")
        self.assertEqual(len(deployment_targets), 4)

        self.printTestName("Success export [end]")
