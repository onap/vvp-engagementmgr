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
from engagementmanager.models import Vendor, Engagement, IceUserProfile, \
    Checklist
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.utils.constants import EngagementStage, Constants
from rest_framework.status import HTTP_200_OK, HTTP_401_UNAUTHORIZED
import json
from engagementmanager.service.logging_service import LoggingServiceFactory

logger = LoggingServiceFactory.get_logger()


class EngagementAdminOperationsTestCase(TestBaseEntity):

    def childSetup(self):
        self.createVendors([Constants.service_provider_company_name, 'Other'])
        self.createDefaultRoles()
        self.admin, self.el, self.standard_user = self.creator.createAndGetDefaultRoles()
        self.el_user = self.creator.createUser(Vendor.objects.get(name=Constants.service_provider_company_name),
                                               self.randomGenerator("main-vendor-email"), '55501000199',
                                               'el user', self.el, True)
        self.second_el_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), self.randomGenerator("main-vendor-email"), '55501000199',
                                                      'el user2', self.el, True)
        self.el_user_to_update = self.creator.createUser(
            Vendor.objects.get(name=Constants.service_provider_company_name),
            self.randomGenerator("main-vendor-email"), '55501000199',
            'el user 3', self.el, True)
        self.user = self.creator.createUser(Vendor.objects.get(name='Other'),
                                            self.randomGenerator("main-vendor-email"), '55501000199',
                                            'user', self.standard_user, True)
        self.admin_user = self.creator.createUser(Vendor.objects.get(
            name=Constants.service_provider_company_name), Constants.service_provider_admin_mail, '55501000199',
                                                  'admin user', self.admin, True)

        self.engagement = self.creator.createEngagement(
            'just-a-fake-uuid', 'Validation', None)
        self.engagement.engagement_team.add(
            self.user, self.el_user, self.second_el_user)
        self.engagement.reviewer = self.el_user
        self.engagement.peer_reviewer = self.second_el_user
        self.engagement.save()
        # Create a VF
        self.deploymentTarget = self.creator.createDeploymentTarget(self.randomGenerator("randomString"),
                                                                    self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(self.randomGenerator("randomString"), self.engagement, self.deploymentTarget,
                                        False, Vendor.objects.get(name='Other'))

        self.userToken = self.loginAndCreateSessionToken(self.user)
        self.elToken = self.loginAndCreateSessionToken(self.el_user)
        self.elUserToUpdateToken = self.loginAndCreateSessionToken(
            self.el_user_to_update)
        self.adminToken = self.loginAndCreateSessionToken(self.admin_user)

    def testGetAllEls(self):
        num_of_els = IceUserProfile.objects.filter(role=self.el).count()
        urlStr = self.urlPrefix + 'users/engagementleads/'
        print(urlStr)
        self.printTestName("testGetAllEls [Start]")
        logger.debug(
            "action should success (200), and return all els exists in the system")
        response = self.c.get(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.adminToken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

        data = json.loads(response.content)
        self.assertEqual(len(data), num_of_els)
        self.assertEqual(data[0]['full_name'] == 'el user 3' or data[
                         0]['full_name'] == 'el user', True)
        self.assertEqual(data[1]['full_name'] == 'el user 3' or data[
                         1]['full_name'] == 'el user2', True)
        self.printTestName("testGetAllEls [End]")

    def testArchiveEngagement(self):
        urlStr = self.urlPrefix + 'engagements/' + \
            str(self.engagement.uuid) + '/archive'
        print(urlStr)
        self.printTestName("testArchiveEngagement [Start]")
        logger.debug("action should success (202), and archive the engagement")
        response = self.c.put(urlStr, json.dumps({'reason': 'test_reason'}), content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.adminToken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

        eng_object = Engagement.objects.get(uuid=self.engagement.uuid)
        # @UndefinedVariable
        self.assertEqual(
            eng_object.engagement_stage, EngagementStage.Archived.name)
        self.assertEqual(eng_object.archive_reason, 'test_reason')
        self.printTestName("testArchiveEngagement [End]")

    def testArchiveEngagementValidateDate(self):
        urlStr = self.urlPrefix + 'engagements/' + \
            str(self.engagement.uuid) + '/archive'
        print(urlStr)
        self.printTestName("testArchiveEngagement [Start]")
        logger.debug("action should success (202), and archive the engagement")
        response = self.c.put(urlStr, json.dumps({'reason': 'test_reason'}), content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.adminToken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

        eng_object = Engagement.objects.get(uuid=self.engagement.uuid)
        self.assertEqual(eng_object.engagement_stage,
                         EngagementStage.Archived.name)  # @UndefinedVariable
        self.assertTrue(eng_object.archived_time)
        print(eng_object.archived_time)
        self.printTestName("testArchiveEngagement [End]")

    def testSetEngagementReviewer(self):
        urlStr = self.urlPrefix + 'engagements/' + \
            str(self.engagement.uuid) + '/reviewer/'
        print(urlStr)
        self.printTestName("testSetEngagementReviewer [Start]")
        logger.debug(
            "action should success (200), and set the engagement reviewer")
        response = self.c.put(urlStr, json.dumps({'reviewer': str(self.el_user_to_update.uuid)}), content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.adminToken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

        eng_object = Engagement.objects.get(uuid=self.engagement.uuid)
        self.assertEqual(
            eng_object.reviewer.uuid, str(self.el_user_to_update.uuid))
        self.printTestName("testSetEngagementReviewer [End]")

    def testSetEngagementPeerReviewer(self):
        urlStr = self.urlPrefix + 'engagements/' + \
            str(self.engagement.uuid) + '/peerreviewer/'
        print(urlStr)
        self.printTestName("testSetEngagementPeerReviewer [Start]")
        logger.debug(
            "action should success (200), and set the engagement peer reviewer")
        response = self.c.put(urlStr, json.dumps({'peerreviewer': str(self.el_user_to_update.uuid)}), content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.adminToken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

        eng_object = Engagement.objects.get(uuid=self.engagement.uuid)
        self.assertEqual(eng_object.peer_reviewer.uuid,
                         str(self.el_user_to_update.uuid))
        self.printTestName("testSetEngagementPeerReviewer [End]")

    def testNegativeGetAllEls(self):
        urlStr = self.urlPrefix + 'users/engagementleads/'
        print(urlStr)
        self.printTestName("testNegativeGetAllEls [Start]")
        logger.debug("action should failed due to missing permissions (401)")
        response = self.c.get(
            urlStr, **{'HTTP_AUTHORIZATION': "token " + self.elToken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.printTestName("testNegativeGetAllEls [End]")

    def testNegativeArchiveEngagement(self):
        urlStr = self.urlPrefix + 'engagements/' + \
            str(self.engagement.uuid) + '/archive'
        print(urlStr)
        self.printTestName("testNegativeArchiveEngagement [Start]")
        logger.debug("action should failed due to missing permissions (401)")
        response = self.c.put(urlStr, json.dumps({'reason': 'test_reason'}), content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.elToken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.printTestName("testNegativeArchiveEngagement [End]")

    def testNegativeSetEngagementReviewer(self):
        urlStr = self.urlPrefix + 'engagements/' + \
            str(self.engagement.uuid) + '/reviewer/'
        print(urlStr)
        self.printTestName("testNegativeSetEngagementReviewer [Start]")
        logger.debug("action should failed due to missing permissions (401)")
        response = self.c.put(urlStr, json.dumps({'reviewer': str(self.el_user_to_update.uuid)}), content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.elToken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.printTestName("testNegativeSetEngagementReviewer [End]")

    def testNegativeSetEngagementPeerReviewer(self):
        urlStr = self.urlPrefix + 'engagements/' + \
            str(self.engagement.uuid) + '/peerreviewer/'
        print(urlStr)
        self.printTestName("testNegativeSetEngagementPeerReviewer [Start]")
        logger.debug("action should failed due to missing permissions (401)")
        response = self.c.put(urlStr, json.dumps({'peerreviewer': str(self.el_user_to_update.uuid)}), content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.elToken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_401_UNAUTHORIZED)
        self.printTestName("testNegativeSetEngagementPeerReviewer [End]")

    def testSwitchEngagementReviewers(self):
        urlStr = self.urlPrefix + 'engagements/' + \
            str(self.engagement.uuid) + '/switch-reviewers/'
        print(urlStr)
        self.printTestName("testSetEngagementReviewer [Start]")
        logger.debug(
            "action should success (200), and switch between the engagement reviewer and peer reviewer")
        logger.debug("Reviewer: %s, PeerReviewer: %s" %
                     (self.engagement.reviewer, self.engagement.peer_reviewer))
        response = self.c.put(urlStr, json.dumps({'reviewer': str(self.second_el_user.uuid), 'peerreviewer': str(
            self.el_user.uuid)}), content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.adminToken})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, HTTP_200_OK)

        eng_object = Engagement.objects.get(uuid=self.engagement.uuid)
        self.assertEqual(
            eng_object.reviewer.uuid, str(self.second_el_user.uuid))
        self.assertEqual(
            eng_object.peer_reviewer.uuid, str(self.el_user.uuid))
        logger.debug("Reviewer: %s, PeerReviewer: %s" %
                     (eng_object.reviewer, eng_object.peer_reviewer))
        self.printTestName("testSetEngagementReviewer [End]")

    def testChecklistOwnerAfterChangeReviewer(self):
        urlStr = self.urlPrefix + 'engagements/' + \
            str(self.engagement.uuid) + '/reviewer/'
        print(urlStr)
        self.printTestName("testChecklistOwnerAfterChangeReviewer [Start]")
        cl_template = self.creator.createDefaultCheckListTemplate()
        checklist = self.creator.createCheckList(
            "cl-name", "review", 1, None, self.engagement, cl_template,
            self.admin_user, self.el_user)
        logger.debug(
            "action should success (200), set the engagement reviewer and change checklist owner")
        response = self.c.put(urlStr, json.dumps({'reviewer': str(self.el_user_to_update.uuid)}), content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.adminToken})
        print('Got response : ' + str(response.status_code))
        checklist = Checklist.objects.get(uuid=checklist.uuid)
        self.assertEqual(checklist.owner, self.el_user_to_update)
        self.printTestName("testChecklistOwnerAfterChangeReviewer [End]")

    def testChecklistOwnerAfterChangePeerReviewer(self):
        urlStr = self.urlPrefix + 'engagements/' + \
            str(self.engagement.uuid) + '/peerreviewer/'
        print(urlStr)
        self.printTestName("testChecklistOwnerAfterChangePeerReviewer [Start]")
        cl_template = self.creator.createDefaultCheckListTemplate()
        checklist = self.creator.createCheckList(
            "cl-name", "peer_review", 1, None, self.engagement, cl_template,
            self.admin_user, self.second_el_user)
        logger.debug(
            "action should success (200), set the engagement peer reviewer and change checklist owner")
        response = self.c.put(urlStr, json.dumps({'peerreviewer': str(self.el_user_to_update.uuid)}), content_type='application/json',
                              **{'HTTP_AUTHORIZATION': "token " + self.adminToken})
        print('Got response : ' + str(response.status_code))
        checklist = Checklist.objects.get(uuid=checklist.uuid)
        self.assertEqual(checklist.owner, self.el_user_to_update)
        self.printTestName("testChecklistOwnerAfterChangePeerReviewer [End]")

    def testChecklistOwnerAfterSwitchReviewers(self):
        urlStr = self.urlPrefix + 'engagements/' + \
            str(self.engagement.uuid) + '/switch-reviewers/'
        print(urlStr)
        self.printTestName("testChecklistOwnerAfterSwitchReviewers [Start]")
        cl_template = self.creator.createDefaultCheckListTemplate()
        checklist = self.creator.createCheckList(
            "cl-name", "review", 1, None, self.engagement, cl_template,
            self.admin_user, self.el_user)
        logger.debug(
            "action should success (200), switch between the engagement reviewer and peer reviewer and change checklist owner")
        logger.debug("Reviewer: %s, PeerReviewer: %s" %
                     (self.engagement.reviewer, self.engagement.peer_reviewer))
        response = self.c.put(urlStr, json.dumps({'reviewer': str(self.second_el_user.uuid), 'peerreviewer': str(
            self.el_user.uuid)}), content_type='application/json', **{'HTTP_AUTHORIZATION': "token " + self.adminToken})
        print('Got response : ' + str(response.status_code))
        checklist = Checklist.objects.get(uuid=checklist.uuid)
        self.assertEqual(checklist.owner, self.second_el_user)
        self.printTestName("testChecklistOwnerAfterSwitchReviewers [End]")
