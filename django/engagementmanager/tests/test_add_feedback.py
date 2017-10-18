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
import random

from rest_framework.status import HTTP_200_OK, HTTP_400_BAD_REQUEST
from engagementmanager.tests.test_base_entity import TestBaseEntity
from engagementmanager.models import Vendor
from engagementmanager.utils.constants import Constants
from engagementmanager.utils.request_data_mgr import request_data_mgr


class TestAddContactTestCase(TestBaseEntity):

    def childSetup(self):

        self.createVendors([Constants.service_provider_company_name, 'Other'])
        self.createDefaultRoles()
        self.reviewer = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"), '55501000199', 'reviewer user', self.el, True)
        self.peer_reviewer = self.creator.createUser(Vendor.objects.get(
            name='Other'), self.randomGenerator("main-vendor-email"),
            '55501000199', 'peer-reviewer user', self.el, True)
        # Create an Engagement with team
        self.engagement = self.creator.createEngagement(
            '123456789', 'Validation', None)
        self.engagement.reviewer = self.reviewer
        self.engagement.peer_reviewer = self.peer_reviewer
        self.engagement.save()
        print('-----------------------------------------------------')
        print('Created Engagement:')
        print('UUID: ' + str(self.engagement.uuid))
        print('-----------------------------------------------------')

        # Create a VF
        self.deploymentTarget = self.creator.createDeploymentTarget(
            self.randomGenerator("randomString"), self.randomGenerator("randomString"))
        self.vf = self.creator.createVF(self.randomGenerator("randomString"), self.engagement,
                                        self.deploymentTarget, False, Vendor.objects.get(name='Other'))

        self.urlStr = self.urlPrefix + "add-feedback/"
        self.data = dict()
        self.token = self.loginAndCreateSessionToken(self.reviewer)

    def initBody(self):
        self.data['description'] = Vendor.objects.get(
            name=Constants.service_provider_company_name).name + "ruslan gafiulin"

    def addFeedback(self, expectedStatus=HTTP_200_OK):
        self.feedbackData = json.dumps(self.data, ensure_ascii=False)
        response = self.c.post(self.urlStr, self.feedbackData, content_type='application/json',
                               **{'HTTP_AUTHORIZATION': "token " + self.token})
        print('Got response : ' + str(response.status_code))
        self.assertEqual(response.status_code, expectedStatus)
        return response

    ### TESTS ###

    def testAddFeedbackForNonExistingContact(self):
        self.initBody()
        self.data['description'] = str(self.engagement.uuid)
        self.data['eng_uuid'] = str(self.engagement.uuid)
        self.addFeedback()

    def testNegativeAddFeedbackWithoutDescription(self):
        self.initBody()
        self.data['description'] = ""
        self.data['eng_uuid'] = str(self.engagement.uuid)
        self.addFeedback(HTTP_400_BAD_REQUEST)
